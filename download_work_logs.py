#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
  하이디라오 영등포점 — 작업일보 PDF 다운로드
═══════════════════════════════════════════════════════════
  Lark 채팅방의 작업일보 PDF를 '일일작업일보' 폴더에 저장

  사용법:
    python3 download_work_logs.py              # 미다운로드 파일만
    python3 download_work_logs.py --all        # 전체 재다운로드
    python3 download_work_logs.py --token      # 새 토큰 발급 후 실행
"""

import json, os, sys, re, time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ── 설정 ──
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR   = os.path.join(BASE_DIR, '일일작업일보')
DATA_FILE  = os.path.join(BASE_DIR, '작업일지_데이터.json')
TOKEN_FILE = os.path.join(BASE_DIR, 'lark_user_token.txt')
APP_ID     = 'cli_a97aa70eeca15e15'
APP_SECRET = 'l37gyqepLXhdTjLW7L9UngWh5jV6jtQw'
DOMAIN     = 'https://open.larksuite.com'
KST        = timezone(timedelta(hours=9))


def log(msg):
    now = datetime.now(KST).strftime('%H:%M:%S')
    print(f'[{now}] {msg}')


def get_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def refresh_token():
    """브라우저 OAuth로 새 User Access Token 발급"""
    import http.server, webbrowser, threading
    from urllib.parse import urlparse, parse_qs

    PORT   = 9877
    result = {'code': None}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            p = parse_qs(urlparse(self.path).query)
            if '/callback' in self.path and 'code' in p:
                result['code'] = p['code'][0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/html;charset=utf-8')
                self.end_headers()
                self.wfile.write('✅ 인증 완료! 창을 닫으세요.'.encode())
            else:
                self.send_response(200); self.end_headers()
        def log_message(self, *a): pass

    srv = http.server.HTTPServer(('localhost', PORT), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()

    scopes = 'im:chat:readonly im:message im:message.group_msg im:message.group_msg:get_as_user'
    url = (f'{DOMAIN}/open-apis/authen/v1/authorize?'
           f'app_id={APP_ID}&redirect_uri=http://localhost:{PORT}/callback'
           f'&state=download&scope={scopes}')
    log('🔐 브라우저에서 Lark 로그인 대기...')
    webbrowser.open(url)

    for _ in range(120):
        if result['code']: break
        time.sleep(1)
    srv.shutdown()

    if not result['code']:
        log('❌ 인증 타임아웃')
        return None

    # App Token
    d = json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET}).encode()
    r = Request(f'{DOMAIN}/open-apis/auth/v3/app_access_token/internal',
                data=d, headers={'Content-Type': 'application/json'})
    with urlopen(r, timeout=15) as resp:
        app_token = json.loads(resp.read().decode())['app_access_token']

    # User Token
    d2 = json.dumps({'grant_type': 'authorization_code', 'code': result['code']}).encode()
    r2 = Request(f'{DOMAIN}/open-apis/authen/v1/oidc/access_token',
                 data=d2, headers={'Content-Type': 'application/json',
                                   'Authorization': f'Bearer {app_token}'})
    with urlopen(r2, timeout=15) as resp:
        tok = json.loads(resp.read().decode())

    user_token = tok['data']['access_token']
    with open(TOKEN_FILE, 'w') as f:
        f.write(user_token)
    log('✅ 새 User Token 발급 완료')
    return user_token


def download_file(token, message_id, file_key, save_path):
    """
    Lark 파일 다운로드 API:
    GET /open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file
    (User Token 필요 — App Token은 지원 안 됨)
    """
    url = f'{DOMAIN}/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file'
    req = Request(url, headers={
        'Authorization': f'Bearer {token}',
    })
    try:
        with urlopen(req, timeout=60) as resp:
            # Content-Type 확인
            content_type = resp.getheader('Content-Type', '')
            data = resp.read()

            # JSON 에러 응답 여부 확인
            if 'application/json' in content_type:
                try:
                    err = json.loads(data.decode('utf-8'))
                    code = err.get('code', 0)
                    if code in [99991668, 99991663, 99991661]:
                        log(f'    ⚠️ 토큰 만료! --token 옵션으로 재인증 필요')
                        return 'token_expired'
                    log(f'    ❌ API 에러 {code}: {err.get("msg", "")}')
                    return False
                except:
                    pass

            # 파일 저장
            with open(save_path, 'wb') as f:
                f.write(data)
            return True

    except HTTPError as e:
        err_body = e.read().decode() if hasattr(e, 'read') else str(e)
        if e.code == 401 or '99991668' in err_body or '99991663' in err_body:
            log(f'    ⚠️ 토큰 만료!')
            return 'token_expired'
        log(f'    ❌ HTTP {e.code}: {err_body[:100]}')
        return False
    except Exception as e:
        log(f'    ❌ 다운로드 오류: {e}')
        return False


def load_work_logs():
    if not os.path.exists(DATA_FILE):
        log('❌ 작업일지_데이터.json 파일 없음')
        return None
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def make_safe_filename(log_date, original_name):
    """저장할 파일명 생성 — 날짜_원본이름.pdf (한글화 적용)"""
    safe = original_name.strip()
    # 중국어 파일명을 한국어로 변환
    safe = safe.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지")
    safe = safe.replace(".pdf.pdf", ".pdf")
    
    if safe.startswith(log_date):
        return safe
    return f'{log_date}_{safe}'


def main():
    log('')
    log('═' * 55)
    log('  📥 하이디라오 작업일보 PDF 다운로드')
    log('═' * 55)

    # 토큰
    if '--token' in sys.argv:
        token = refresh_token()
    else:
        token = get_token()

    if not token:
        log('❌ 토큰 없음! python3 download_work_logs.py --token')
        return

    # 저장 폴더 생성
    os.makedirs(SAVE_DIR, exist_ok=True)
    log(f'📂 저장 폴더: {SAVE_DIR}')

    # 작업일지 데이터 로드
    data = load_work_logs()
    if not data:
        return

    logs = data.get('logs', [])
    log(f'📋 총 {len(logs)}개 작업일지 확인')

    # 이미 다운로드된 파일 목록
    existing_files = set(os.listdir(SAVE_DIR))
    log(f'💾 이미 저장된 파일: {len(existing_files)}개\n')

    force_all = '--all' in sys.argv
    downloaded = 0
    skipped    = 0
    failed     = 0
    token_expired = False

    for i, log_entry in enumerate(logs):
        log_date   = log_entry.get('log_date', '')
        file_name  = log_entry.get('file_name', '')
        file_key   = log_entry.get('file_key', '')
        message_id = log_entry.get('message_id', '')

        if not file_key or not file_name or not message_id:
            log(f'  [{i+1:02d}/{len(logs)}] ⚠️ {log_date} — 파일 키 또는 메시지 ID 없음, 건너뜀')
            skipped += 1
            continue

        # 저장 파일명 결정
        save_name = make_safe_filename(log_date, file_name)
        save_path = os.path.join(SAVE_DIR, save_name)

        # 이미 존재하면 스킵 (--all이면 강제 재다운로드)
        if not force_all and (save_name in existing_files or os.path.exists(save_path)):
            size_kb = os.path.getsize(save_path) / 1024 if os.path.exists(save_path) else 0
            log(f'  [{i+1:02d}/{len(logs)}] ✓ {log_date} — 이미 있음 ({size_kb:.0f}KB)')
            skipped += 1
            continue

        log(f'  [{i+1:02d}/{len(logs)}] ⬇️  {log_date} — {file_name[:50]}')
        result = download_file(token, message_id, file_key, save_path)

        if result == 'token_expired':
            token_expired = True
            # 부분 파일 삭제
            if os.path.exists(save_path) and os.path.getsize(save_path) < 1000:
                os.remove(save_path)
            break
        elif result:
            size_kb = os.path.getsize(save_path) / 1024
            log(f'              ✅ 저장 완료 ({size_kb:.0f}KB)')
            downloaded += 1
            existing_files.add(save_name)
        else:
            failed += 1
            # 실패한 빈 파일 삭제
            if os.path.exists(save_path) and os.path.getsize(save_path) == 0:
                os.remove(save_path)

        # API 레이트 리밋 방지
        time.sleep(0.5)

    log('')
    log('═' * 55)
    if token_expired:
        log('  ⚠️ 토큰 만료로 중단됨!')
        log('  👉 python3 download_work_logs.py --token 으로 재실행')
    else:
        log(f'  ✅ 다운로드 완료!')
        log(f'     새로 다운로드: {downloaded}개')
        log(f'     이미 존재:    {skipped}개')
        log(f'     실패:         {failed}개')

        # 최종 폴더 상태
        final_files = [f for f in os.listdir(SAVE_DIR) if f.endswith('.pdf')]
        final_files.sort()
        log(f'\n  📂 일일작업일보 폴더 ({len(final_files)}개):')
        for fn in final_files:
            sz = os.path.getsize(os.path.join(SAVE_DIR, fn)) / 1024
            log(f'     📄 {fn} ({sz:.0f}KB)')
    log('═' * 55)


if __name__ == '__main__':
    main()
