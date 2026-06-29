#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
  하이디라오 영등포점 — 매일 오전 9시 자동 실행 스크립트
═══════════════════════════════════════════════════════════
  1. Lark 채팅에서 최근 26시간 메시지 수집
  2. 새 작업일보(施工日志) PDF → 일일작업일보 폴더에 저장
  3. 작업일지_데이터.json 업데이트
  4. 하이디라오_작업일지.html 업데이트
  5. 실행 결과 로그 기록

  launchd로 매일 09:00 KST에 자동 실행됨
  수동 실행: python3 morning_update.py
"""

import json, re, os, sys, time
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from collections import defaultdict

# ── 경로 설정 ──
BASE_DIR  = os.path.dirname(os.path.abspath(__file__))
SAVE_DIR  = os.path.join(BASE_DIR, '일일작업일보')
DATA_FILE = os.path.join(BASE_DIR, '작업일지_데이터.json')
HTML_FILE = os.path.join(BASE_DIR, '하이디라오_작업일지.html')
TOKEN_FILE = os.path.join(BASE_DIR, 'lark_user_token.txt')
LOG_FILE  = os.path.join(BASE_DIR, 'morning_update.log')

# ── Lark API 설정 ──
APP_ID     = 'cli_a97aa70eeca15e15'
APP_SECRET = 'l37gyqepLXhdTjLW7L9UngWh5jV6jtQw'
DOMAIN     = 'https://open.larksuite.com'
CHAT_ID    = 'oc_943f27f012a4da28abb89083bc7095a3'
KST        = timezone(timedelta(hours=9))

# 작업 카테고리 키워드
WORK_CATEGORIES = {
    '철거/해체':   ['拆除', '철거', '해체', '拆墙', '拆掉'],
    '먹매김/방선': ['放线', '먹매김', '방선', '먹작업', '弹线'],
    '벽체/조적':   ['砌墙', '砌筑', '벽체', '조적', '隔墙', '벽돌'],
    '배관/급배수': ['排水', '给水', '배관', '급수', '배수', '管道', '水管', '地漏'],
    '전기/배선':   ['电气', '전기', '布线', '배선', '电箱', '配电', '桥架', '线管'],
    '소방':        ['消防', '소방', '防火', '방화', '排烟', '배연'],
    '방수':        ['防水', '방수', '闭水', '누수', '漏水'],
    'HVAC/공조':   ['空调', '에어컨', '新风', '신풍', '风机', '排风', '通风', '환기'],
    '천장/조형':   ['天花', '천장', '吊顶', '석고보드'],
    '도면/설계':   ['图纸', '도면', '变更', '변경', '设计'],
    '자재/발주':   ['材料', '자재', '发주', '발주', '下单', '订단'],
    '검수/확인':   ['验收', '검수', '确认', '확인', '检查'],
    '타일/마감':   ['瓷砖', '타일', '마감', '贴砖'],
}


# ════════════════════════════════════════
#  로깅
# ════════════════════════════════════════

def log(msg, level='INFO'):
    now = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S')
    line = f'[{now}] {msg}'
    print(line, flush=True)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass


# ════════════════════════════════════════
#  Lark API 헬퍼
# ════════════════════════════════════════

def get_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def lark_get(token, url, timeout=30):
    """Lark API GET 요청. 토큰 만료 시 'TOKEN_EXPIRED' 반환."""
    req = Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        with urlopen(req, timeout=timeout) as resp:
            ct = resp.getheader('Content-Type', '')
            data = resp.read()
            if 'application/json' in ct:
                result = json.loads(data.decode('utf-8'))
                code = result.get('code', 0)
                if code in [99991668, 99991663, 99991661]:
                    return 'TOKEN_EXPIRED'
                return result
            return data  # binary (PDF)
    except HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        if e.code == 401 or any(c in body for c in ['99991668', '99991663']):
            return 'TOKEN_EXPIRED'
        log(f'HTTP {e.code}: {body[:150]}')
        return None
    except Exception as e:
        log(f'네트워크 오류: {e}')
        return None


def fetch_messages(token, hours_back=26):
    """최근 N시간 메시지 수집 (text/post/file 모두)"""
    from urllib.parse import urlencode
    now_ts   = int(datetime.now(KST).timestamp())
    start_ts = str(now_ts - hours_back * 3600)
    end_ts   = str(now_ts)

    all_msgs   = []
    page_token = ''
    while True:
        params = {
            'container_id_type': 'chat', 'container_id': CHAT_ID,
            'page_size': 50, 'sort_type': 'ByCreateTimeAsc',
            'start_time': start_ts, 'end_time': end_ts,
        }
        if page_token:
            params['page_token'] = page_token
        url = f'{DOMAIN}/open-apis/im/v1/messages?{urlencode(params)}'
        result = lark_get(token, url, timeout=30)
        if result == 'TOKEN_EXPIRED':
            return 'TOKEN_EXPIRED'
        if not result:
            break
        items = result.get('data', {}).get('items', [])
        all_msgs.extend(items)
        if not result.get('data', {}).get('has_more'):
            break
        page_token = result.get('data', {}).get('page_token', '')
    return all_msgs


def parse_msg_text(m):
    msg_type    = m.get('msg_type', '')
    content_str = m.get('body', {}).get('content', '{}')
    if msg_type == 'text':
        try:
            return json.loads(content_str).get('text', '')
        except:
            return content_str
    elif msg_type == 'post':
        try:
            content = json.loads(content_str)
            texts = [content.get('title', '')]
            for lang, paragraphs in content.items():
                if isinstance(paragraphs, list):
                    for para in paragraphs:
                        if isinstance(para, list):
                            for elem in para:
                                if isinstance(elem, dict) and elem.get('tag') == 'text':
                                    texts.append(elem.get('text', ''))
            return ' '.join(t for t in texts if t)
        except:
            return ''
    return ''


def msg_timestamp(m):
    ts = int(m.get('create_time', '0'))
    if ts > 1e12: ts /= 1000
    return datetime.fromtimestamp(ts, tz=KST)


def group_messages_by_date(messages):
    date_groups = defaultdict(list)
    for m in messages:
        if m.get('msg_type') not in ('text', 'post'):
            continue
        try:
            dt   = msg_timestamp(m)
            text = parse_msg_text(m).strip()
            if text and len(text) > 2:
                date_groups[dt.strftime('%Y-%m-%d')].append({
                    'time': dt.strftime('%H:%M'),
                    'text': text,
                })
        except:
            continue
    return dict(date_groups)


# ════════════════════════════════════════
#  STEP 1: PDF 다운로드
# ════════════════════════════════════════

def download_pdf(token, message_id, file_key, save_path):
    """
    GET /open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file
    User Token 필요 (App Token 불가)
    """
    url = f'{DOMAIN}/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file'
    result = lark_get(token, url, timeout=60)
    if result == 'TOKEN_EXPIRED':
        return 'TOKEN_EXPIRED'
    if result is None:
        return False
    if isinstance(result, bytes):
        # PDF 시그니처 확인
        if not result.startswith(b'%PDF'):
            log(f'  ⚠️ PDF 시그니처 없음: {result[:20]}')
            return False
        with open(save_path, 'wb') as f:
            f.write(result)
        return True
    log(f'  ❌ 예상치 못한 응답: {str(result)[:100]}')
    return False


def step_download(token, messages):
    """새 작업일보 PDF 다운로드 → 일일작업일보 폴더"""
    os.makedirs(SAVE_DIR, exist_ok=True)
    existing = set(os.listdir(SAVE_DIR))

    downloaded = 0
    token_expired = False

    for m in messages:
        if m.get('msg_type') != 'file':
            continue
        try:
            content = json.loads(m.get('body', {}).get('content', '{}'))
            fname   = content.get('file_name', '')
            fkey    = content.get('file_key', '')
            msg_id  = m.get('message_id', '')
        except:
            continue

        # 작업일보 파일만 처리 (施工日志 또는 施工日报)
        if '施工日志' not in fname and '施工日报' not in fname:
            continue
        if not fkey or not msg_id:
            continue

        # 파일명 한글화 적용
        fname = fname.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지")
        fname = fname.replace(".pdf.pdf", ".pdf")

        # 날짜 파싱
        dt = msg_timestamp(m)
        date_match = re.search(r'(\d{8})', fname)
        if date_match:
            ds = date_match.group(1)
            log_date = f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}'
        else:
            log_date = dt.strftime('%Y-%m-%d')

        # 저장 파일명
        save_name = fname if fname.startswith(log_date) else f'{log_date}_{fname}'
        save_path = os.path.join(SAVE_DIR, save_name)

        if save_name in existing or os.path.exists(save_path):
            log(f'  ✓ PDF 이미 있음: {log_date}')
            continue

        log(f'  ⬇️  PDF 다운로드: {log_date} — {fname[:60]}')
        result = download_pdf(token, msg_id, fkey, save_path)

        if result == 'TOKEN_EXPIRED':
            token_expired = True
            break
        elif result:
            sz = os.path.getsize(save_path) / 1024
            log(f'     ✅ 저장 완료 ({sz:.0f}KB)')
            downloaded += 1
            existing.add(save_name)
        else:
            if os.path.exists(save_path) and os.path.getsize(save_path) == 0:
                os.remove(save_path)

        time.sleep(0.4)

    return downloaded, token_expired


# ════════════════════════════════════════
#  STEP 2: 작업일지 데이터 업데이트
# ════════════════════════════════════════

def step_update_data(messages):
    """작업일지_데이터.json + 하이디라오_작업일지.html 업데이트"""
    # 기존 데이터 로드
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'project': '하이디라오 영등포점 (海底捞韩国永登浦店)',
            'data_source': 'Lark 시공그룹 채팅 자동 수집',
            'total_logs': 0, 'period': '', 'logs': [],
        }

    existing_dates = set(l['log_date'] for l in data['logs'])
    date_texts     = group_messages_by_date(messages)
    added          = 0

    for m in messages:
        if m.get('msg_type') != 'file':
            continue
        try:
            dt      = msg_timestamp(m)
            content = json.loads(m.get('body', {}).get('content', '{}'))
            fname   = content.get('file_name', '')
            fkey    = content.get('file_key', '')
        except:
            continue

        if '施工日志' not in fname and '施工日报' not in fname:
            continue

        # 파일명 한글화 적용
        fname = fname.replace("海底捞韩国永登浦店项目施工日志", "하이디라오 한국 영등포점 프로젝트 시공일지")
        fname = fname.replace(".pdf.pdf", ".pdf")

        date_match = re.search(r'(\d{8})', fname)
        if date_match:
            ds = date_match.group(1)
            log_date = f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}'
        else:
            log_date = dt.strftime('%Y-%m-%d')

        if log_date in existing_dates:
            continue

        day_msgs    = date_texts.get(log_date, [])
        all_text    = ' '.join(dm['text'] for dm in day_msgs)
        matched_cats = []
        for cat_name, keywords in WORK_CATEGORIES.items():
            for kw in keywords:
                if kw in all_text:
                    matched_cats.append(cat_name)
                    break

        highlights = []
        for dm in day_msgs:
            if len(dm['text']) < 10:
                continue
            if any(kw in dm['text'] for kws in WORK_CATEGORIES.values() for kw in kws):
                highlights.append(f'[{dm["time"]}] {dm["text"][:100]}')

        new_log = {
            'log_date':      log_date,
            'upload_date':   dt.strftime('%Y-%m-%d'),
            'upload_time':   dt.strftime('%H:%M'),
            'file_name':     fname,
            'file_key':      fkey,
            'message_id':    m.get('message_id', ''),
            'sender_id':     m.get('sender', {}).get('id', ''),
            'work_categories': matched_cats,
            'day_highlights':  highlights[:8],
            'total_messages':  len(day_msgs),
        }
        data['logs'].append(new_log)
        existing_dates.add(log_date)
        added += 1
        log(f'  ✨ 데이터 추가: {log_date} — {fname}')

    if added > 0:
        data['logs'].sort(key=lambda x: x['log_date'])
        data['total_logs'] = len(data['logs'])
        data['period']       = f'{data["logs"][0]["log_date"]} ~ {data["logs"][-1]["log_date"]}'
        data['last_updated'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')

        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        log(f'  💾 작업일지_데이터.json 저장 (총 {data["total_logs"]}개)')

        # HTML 업데이트
        if os.path.exists(HTML_FILE):
            with open(HTML_FILE, encoding='utf-8') as f:
                html = f.read()
            # 작업내용 중국어 → 한국어 변환 (HTML용, 원본 JSON은 중국어 유지)
            from work_i18n import translate_data_for_html
            data_html = translate_data_for_html(data, BASE_DIR)
            js_data = json.dumps(data_html, ensure_ascii=False)
            # 특수문자 이스케이프
            js_data = js_data.replace('\r', '\\r').replace('\n', '\\n')
            # re.sub에서 백슬래시가 축소되는 버그 방지
            escaped_js_data = js_data.replace('\\', '\\\\')
            new_html = re.sub(
                r'const WORK_LOGS = \{.*?\};',
                f'const WORK_LOGS = {escaped_js_data};',
                html, count=1, flags=re.DOTALL
            )
            with open(HTML_FILE, 'w', encoding='utf-8') as f:
                f.write(new_html)
            log(f'  🌐 하이디라오_작업일지.html 업데이트 완료')
    else:
        log('  ℹ️ 새 작업일보 없음')

    return added


# ════════════════════════════════════════
#  STEP 4: 공종별 작업자 파싱 + 고도화
# ════════════════════════════════════════

def step_enrich():
    """PDF에서 공종별 인원 파싱 → 채팅 기반 공종 상세/번역 → HTML 동기화.
    parse_and_apply(전체 PDF 재파싱) → enhance_work_logs → HTML 재동기화 순서."""
    sys.path.insert(0, BASE_DIR)
    try:
        import parse_and_apply, enhance_work_logs
        # 1) PDF 공종표 파싱 (trades, 총인원, 시공내용) → JSON + HTML
        parse_and_apply.main()
        # 2) 채팅 기반 공종 상세 + worker_count + 한국어 번역 → JSON
        enhance_work_logs.main()
        # 3) 최종 JSON으로 HTML 재동기화 (enhance가 JSON만 갱신하므로)
        with open(DATA_FILE, encoding='utf-8') as f:
            data = json.load(f)
        parse_and_apply.update_html(data)
        log('  ✅ 공종별 작업자 파싱/고도화/HTML 동기화 완료')
        return True
    except Exception as e:
        log(f'  ⚠️ 공종별 고도화 실패(건너뜀): {e}')
        return False


# ════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════

def main():
    start_time = datetime.now(KST)
    log('')
    log('═' * 55)
    log(f'  🌅 하이디라오 작업일보 오전 자동 업데이트')
    log(f'  📅 {start_time.strftime("%Y-%m-%d %H:%M:%S KST")}')
    log('═' * 55)

    # 토큰 확인
    token = get_token()
    if not token:
        log('❌ 토큰 없음! 수동으로 python3 morning_update.py --token 실행 필요')
        log('   (launchd는 브라우저 인증을 자동으로 처리할 수 없습니다)')
        return 1

    # 메시지 수집 (어제 오전 6시 ~ 현재)
    log('')
    log('── STEP 1: Lark 메시지 수집 ──')
    messages = fetch_messages(token, hours_back=28)  # 여유 있게 28시간
    if messages == 'TOKEN_EXPIRED':
        # refresh_token으로 브라우저 없이 자동 갱신 시도
        log('  토큰 만료 — refresh_token으로 자동 갱신 시도...')
        sys.path.insert(0, BASE_DIR)
        try:
            from daily_update import refresh_via_refresh_token
            new_token = refresh_via_refresh_token()
        except Exception as e:
            log(f'  ⚠️ 자동 갱신 모듈 오류: {e}')
            new_token = None
        if new_token:
            token = new_token
            messages = fetch_messages(token, hours_back=28)
        if messages == 'TOKEN_EXPIRED' or not new_token:
            log('❌ 자동 갱신 실패! 수동 재인증 필요: python3 morning_update.py --token')
            return 1
    if not messages:
        log('  ℹ️ 새 메시지 없음')
        return 0

    file_msgs = [m for m in messages if m.get('msg_type') == 'file']
    text_msgs = [m for m in messages if m.get('msg_type') in ('text', 'post')]
    log(f'  📨 총 {len(messages)}개 메시지 (파일: {len(file_msgs)}개, 텍스트: {len(text_msgs)}개)')

    # PDF 다운로드
    log('')
    log('── STEP 2: 작업일보 PDF 다운로드 ──')
    pdf_count, token_expired = step_download(token, messages)
    if token_expired:
        log('❌ PDF 다운로드 중 토큰 만료')

    # 데이터 + HTML 업데이트
    log('')
    log('── STEP 3: 작업일지 데이터/HTML 업데이트 ──')
    data_count = step_update_data(messages)

    # 공종별 작업자 파싱 + 고도화 (PDF 인원표 → trades, 채팅 → 상세)
    log('')
    log('── STEP 4: 공종별 작업자 파싱 + 고도화 ──')
    step_enrich()

    # 이벤트 트래커 업데이트 (라크 채팅 → 채팅 이벤트)
    log('')
    log('── STEP 5: 이벤트 트래커 업데이트 ──')
    evt_count = 0
    try:
        sys.path.insert(0, BASE_DIR)
        from daily_update import update_event_tracker
        evt_count = update_event_tracker(messages)
    except Exception as e:
        log(f'  ⚠️ 이벤트 트래커 업데이트 실패(건너뜀): {e}')

    # 회의록 문서 → meeting 이벤트 자동 추가
    log('')
    log('── STEP 6: 회의록 자동 처리 ──')
    try:
        sys.path.insert(0, BASE_DIR)
        import meeting_minutes
        meeting_minutes.process_meeting_minutes(token, messages)
    except Exception as e:
        log(f'  ⚠️ 회의록 처리 실패(건너뜀): {e}')

    # 완료 요약
    elapsed = (datetime.now(KST) - start_time).seconds
    log('')
    log('═' * 55)
    log(f'  ✅ 업데이트 완료! ({elapsed}초 소요)')
    log(f'     새 PDF 저장:   {pdf_count}개')
    log(f'     데이터 추가:   {data_count}개')
    log(f'     이벤트 추가:   {evt_count}개')
    if token_expired:
        log('  ⚠️ 토큰 만료로 일부 PDF 미다운로드')
        log('     → python3 morning_update.py --token 으로 재실행')
    log('═' * 55)
    log('')

    return 0


if __name__ == '__main__':
    # --token 옵션: 수동 토큰 재발급
    if '--token' in sys.argv:
        # daily_update.py의 refresh_token 함수 재사용
        sys.path.insert(0, BASE_DIR)
        try:
            from daily_update import refresh_token
            token = refresh_token()
            if token:
                log('✅ 새 토큰 발급 완료. 일반 실행을 다시 시작합니다...')
                # 토큰 저장 후 정상 실행
                sys.argv = [sys.argv[0]]
                sys.exit(main())
        except Exception as e:
            log(f'❌ 토큰 발급 실패: {e}')
            sys.exit(1)
    else:
        sys.exit(main())
