#!/usr/bin/env python3
"""
하이디라오 영등포점 시공일지 자동 업데이트 스크립트
Lark 시공그룹 채팅에서 새 작업일지(施工日志)를 감지하고
작업일지_데이터.json 및 하이디라오_작업일지.html을 자동 업데이트합니다.

사용법:
  python3 auto_update_work_logs.py          # 수동 실행
  python3 auto_update_work_logs.py --token  # 새 토큰 발급 후 실행
"""

import json, re, sys, os
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

# ── 설정 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ID = 'cli_a97aa70eeca15e15'
APP_SECRET = 'l37gyqepLXhdTjLW7L9UngWh5jV6jtQw'
DOMAIN = 'https://open.larksuite.com'
CHAT_ID = 'oc_943f27f012a4da28abb89083bc7095a3'
KST = timezone(timedelta(hours=9))
TOKEN_FILE = os.path.join(BASE_DIR, 'lark_user_token.txt')
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')
HTML_FILE = os.path.join(BASE_DIR, '하이디라오_작업일지.html')
HTML_TEMPLATE = os.path.join(BASE_DIR, '하이디라오_작업일지_template.html')
RAW_MSG_FILE = os.path.join(BASE_DIR, 'lark_raw_messages.json')
LAST_CHECK_FILE = os.path.join(BASE_DIR, '.last_worklog_check')

# 작업 카테고리 키워드 사전
WORK_CATEGORIES = {
    '철거/해체': ['拆除', '철거', '해체', '拆墙', '拆掉'],
    '먹매김/방선': ['放线', '먹매김', '방선', '먹작업', '弹线'],
    '벽체/조적': ['砌墙', '砌筑', '벽체', '조적', '隔墙', '벽돌'],
    '배관/급배수': ['排水', '给水', '배관', '급수', '배수', '管道', '水管', '地漏'],
    '전기/배선': ['电气', '전기', '布线', '배선', '电箱', '配电', '桥架', '线管', '분전반'],
    '소방': ['消防', '소방', '防火', '방화', '排烟', '배연'],
    '방수': ['防水', '방수', '闭水', '누수', '漏水'],
    'HVAC/공조': ['空调', '에어컨', '新风', '신풍', '风机', '排风', '通风', '환기'],
    '천장/조형': ['天花', '천장', '吊顶', '석고보드'],
    '도면/설계': ['图纸', '도면', '变更', '변경', '设计'],
    '자재/발주': ['材料', '자재', '发주', '발주', '下单', '订单'],
    '검수/확인': ['验收', '검수', '确认', '확인', '检查'],
    '타일/마감': ['瓷砖', '타일', '마감', '贴砖'],
}


def log(msg):
    now = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{now}] {msg}')


def get_token():
    """저장된 User Access Token 읽기"""
    if not os.path.exists(TOKEN_FILE):
        log('❌ 토큰 파일 없음. --token 옵션으로 재인증 필요')
        return None
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def refresh_token_via_oauth():
    """브라우저를 열어 새 User Access Token 발급"""
    import http.server, webbrowser, threading, time
    from urllib.parse import urlencode, urlparse, parse_qs

    PORT = 9877
    REDIRECT_URI = f'http://localhost:{PORT}/callback'
    auth_result = {'code': None}

    class H(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            p = parse_qs(urlparse(self.path).query)
            if '/callback' in self.path and 'code' in p:
                auth_result['code'] = p['code'][0]
                self.send_response(200)
                self.send_header('Content-Type', 'text/html;charset=utf-8')
                self.end_headers()
                self.wfile.write('✅ 인증 성공! 이 창을 닫으세요.'.encode())
            else:
                self.send_response(200)
                self.end_headers()
        def log_message(self, *a): pass

    srv = http.server.HTTPServer(('localhost', PORT), H)
    t = threading.Thread(target=srv.serve_forever, daemon=True)
    t.start()

    scopes = 'im:chat:readonly im:message im:message.group_msg im:message.group_msg:get_as_user'
    auth_url = (f'{DOMAIN}/open-apis/authen/v1/authorize?'
                f'app_id={APP_ID}&redirect_uri={REDIRECT_URI}'
                f'&state=worklog_refresh&scope={scopes}')
    log('🔐 브라우저에서 Lark 로그인해주세요!')
    webbrowser.open(auth_url)

    for i in range(120):
        if auth_result['code']:
            break
        time.sleep(1)
    srv.shutdown()

    if not auth_result['code']:
        log('❌ 타임아웃')
        return None

    # App Access Token
    d = json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET}).encode()
    r = Request(f'{DOMAIN}/open-apis/auth/v3/app_access_token/internal',
                data=d, headers={'Content-Type': 'application/json'})
    with urlopen(r, timeout=15) as resp:
        app_token = json.loads(resp.read().decode())['app_access_token']

    # User Access Token
    d2 = json.dumps({'grant_type': 'authorization_code', 'code': auth_result['code']}).encode()
    r2 = Request(f'{DOMAIN}/open-apis/authen/v1/oidc/access_token',
                 data=d2, headers={'Content-Type': 'application/json',
                                   'Authorization': f'Bearer {app_token}'})
    with urlopen(r2, timeout=15) as resp:
        tok = json.loads(resp.read().decode())

    user_token = tok['data']['access_token']
    with open(TOKEN_FILE, 'w') as f:
        f.write(user_token)
    log('✅ 새 User Token 발급 완료!')
    return user_token


def fetch_recent_messages(token, hours_back=26):
    """최근 N시간 이내 메시지만 수집"""
    from urllib.parse import urlencode

    now = datetime.now(KST)
    start_ts = str(int((now - timedelta(hours=hours_back)).timestamp()))
    end_ts = str(int(now.timestamp()))

    all_msgs = []
    page_token = ''
    while True:
        params = {
            'container_id_type': 'chat',
            'container_id': CHAT_ID,
            'page_size': 50,
            'sort_type': 'ByCreateTimeDesc',
            'start_time': start_ts,
            'end_time': end_ts,
        }
        if page_token:
            params['page_token'] = page_token
        url = f'{DOMAIN}/open-apis/im/v1/messages?{urlencode(params)}'
        req = Request(url, headers={
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        })
        try:
            with urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
        except HTTPError as e:
            err = e.read().decode() if hasattr(e, 'read') else str(e)
            if '99991668' in err or '99991663' in err:
                log('⚠️ 토큰 만료. --token 옵션으로 재인증 필요')
                return None
            log(f'❌ API 오류: {err}')
            return []
        except Exception as e:
            log(f'❌ 네트워크 오류: {e}')
            return []

        if result.get('code') != 0:
            msg = result.get('msg', '')
            if 'token' in msg.lower() or result.get('code') in [99991668, 99991663]:
                log('⚠️ 토큰 만료. --token 옵션으로 재인증 필요')
                return None
            log(f'❌ API 응답 오류: {json.dumps(result, ensure_ascii=False)[:200]}')
            return []

        items = result.get('data', {}).get('items', [])
        all_msgs.extend(items)
        if not result.get('data', {}).get('has_more'):
            break
        page_token = result.get('data', {}).get('page_token', '')

    return all_msgs


def extract_work_log_from_messages(messages):
    """메시지에서 시공일지 파일 추출"""
    new_logs = []
    for m in messages:
        if m.get('msg_type') != 'file':
            continue
        ts = int(m.get('create_time', '0'))
        if ts > 1e12:
            ts /= 1000
        try:
            dt = datetime.fromtimestamp(ts, tz=KST)
        except:
            continue
        try:
            content = json.loads(m.get('body', {}).get('content', '{}'))
            fname = content.get('file_name', '')
            fkey = content.get('file_key', '')
        except:
            continue

        if '施工日志' not in fname and '施工日报' not in fname:
            continue

        # 파일명 한글화 적용
        fname = fname.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지")
        fname = fname.replace(".pdf.pdf", ".pdf")

        # 파일명에서 날짜 추출
        date_match = re.search(r'(\d{8})', fname)
        if date_match:
            ds = date_match.group(1)
            log_date = f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}'
        else:
            log_date = dt.strftime('%Y-%m-%d')

        new_logs.append({
            'log_date': log_date,
            'upload_date': dt.strftime('%Y-%m-%d'),
            'upload_time': dt.strftime('%H:%M'),
            'file_name': fname,
            'file_key': fkey,
            'message_id': m.get('message_id', ''),
            'sender_id': m.get('sender', {}).get('id', ''),
        })

    return new_logs


def extract_day_context(messages, target_date):
    """특정 날짜의 대화 컨텍스트 추출"""
    day_msgs = []
    for m in messages:
        if m.get('msg_type') not in ('text', 'post'):
            continue
        ts = int(m.get('create_time', '0'))
        if ts > 1e12:
            ts /= 1000
        try:
            dt = datetime.fromtimestamp(ts, tz=KST)
        except:
            continue
        if dt.strftime('%Y-%m-%d') != target_date:
            continue

        body = m.get('body', {})
        content_str = body.get('content', '{}')
        if m.get('msg_type') == 'text':
            try:
                text = json.loads(content_str).get('text', '')
            except:
                text = content_str
        elif m.get('msg_type') == 'post':
            try:
                content = json.loads(content_str)
                texts = []
                title = content.get('title', '')
                if title:
                    texts.append(title)
                for lang, paragraphs in content.items():
                    if isinstance(paragraphs, list):
                        for para in paragraphs:
                            if isinstance(para, list):
                                for elem in para:
                                    if isinstance(elem, dict) and elem.get('tag') == 'text':
                                        texts.append(elem.get('text', ''))
                text = ' '.join(texts)
            except:
                text = ''
        else:
            text = ''

        if text.strip() and len(text.strip()) > 3:
            day_msgs.append({
                'time': dt.strftime('%H:%M'),
                'text': text.strip()
            })

    # 작업 카테고리 매칭
    all_text = ' '.join([m['text'] for m in day_msgs])
    matched_categories = []
    for cat_name, keywords in WORK_CATEGORIES.items():
        for kw in keywords:
            if kw in all_text:
                matched_categories.append(cat_name)
                break

    # 주요 대화 추출
    highlights = []
    for m in day_msgs:
        if len(m['text']) < 10:
            continue
        is_work = False
        for keywords in WORK_CATEGORIES.values():
            for kw in keywords:
                if kw in m['text']:
                    is_work = True
                    break
            if is_work:
                break
        if is_work:
            highlights.append(f'[{m["time"]}] {m["text"][:100]}')

    return {
        'work_categories': matched_categories,
        'day_highlights': highlights[:8],
        'total_messages': len(day_msgs),
    }


def update_data(new_logs, messages):
    """작업일지_데이터.json 업데이트"""
    # 기존 데이터 로드
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'project': '하이디라오 영등포점 (海底捞韩国永登浦店)',
            'data_source': 'Lark 시공그룹 채팅 자동 수집',
            'total_logs': 0,
            'period': '',
            'logs': [],
        }

    existing_dates = set(log['log_date'] for log in data['logs'])
    added = 0

    for new_log in new_logs:
        if new_log['log_date'] in existing_dates:
            continue

        # 대화 컨텍스트 추출
        context = extract_day_context(messages, new_log['log_date'])
        new_log.update(context)

        data['logs'].append(new_log)
        existing_dates.add(new_log['log_date'])
        added += 1
        log(f'  ✨ 신규: {new_log["log_date"]} — {new_log["file_name"]}')

    if added > 0:
        # 날짜순 정렬
        data['logs'].sort(key=lambda x: x['log_date'])
        data['total_logs'] = len(data['logs'])
        if data['logs']:
            data['period'] = f'{data["logs"][0]["log_date"]} ~ {data["logs"][-1]["log_date"]}'
        data['last_updated'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f'✅ {added}개 신규 시공일지 추가 (총 {data["total_logs"]}개)')
    else:
        log('ℹ️ 신규 시공일지 없음')

    return added, data


def regenerate_html(data):
    """하이디라오_작업일지.html 재생성"""
    # HTML 템플릿 읽기 (WORK_LOG_DATA_PLACEHOLDER 부분만 교체)
    if os.path.exists(HTML_FILE):
        with open(HTML_FILE, encoding='utf-8') as f:
            html = f.read()

        # 기존 데이터 교체
        pattern = r'const WORK_LOGS = \{.*?\};'
        js_data = json.dumps(data, ensure_ascii=False)
        replacement = f'const WORK_LOGS = {js_data};'

        # 멀티라인 매칭
        new_html = re.sub(pattern, replacement, html, count=1, flags=re.DOTALL)

        with open(HTML_FILE, 'w', encoding='utf-8') as f:
            f.write(new_html)
        log('✅ 하이디라오_작업일지.html 업데이트 완료!')
    else:
        log('⚠️ HTML 파일 없음, 수동 생성 필요')


def save_last_check():
    """마지막 체크 시각 저장"""
    with open(LAST_CHECK_FILE, 'w') as f:
        f.write(datetime.now(KST).isoformat())


def main():
    log('=' * 50)
    log('🔄 시공일지 자동 업데이트 시작')
    log('=' * 50)

    # 토큰 발급 모드
    if '--token' in sys.argv:
        token = refresh_token_via_oauth()
        if not token:
            return
    else:
        token = get_token()
        if not token:
            log('💡 python3 auto_update_work_logs.py --token 으로 재인증하세요')
            return

    # 최근 26시간 메시지 수집 (하루 + 여유)
    log('📨 최근 메시지 확인 중...')
    messages = fetch_recent_messages(token, hours_back=26)
    if messages is None:
        log('💡 토큰 만료! python3 auto_update_work_logs.py --token 으로 재인증하세요')
        return
    log(f'  {len(messages)}개 메시지 수신')

    # 시공일지 파일 추출
    new_logs = extract_work_log_from_messages(messages)
    log(f'  {len(new_logs)}개 시공일지 파일 감지')

    # 데이터 업데이트
    added, data = update_data(new_logs, messages)

    # HTML 재생성
    if added > 0:
        regenerate_html(data)

    save_last_check()
    log('🏁 업데이트 완료!\n')


if __name__ == '__main__':
    main()
