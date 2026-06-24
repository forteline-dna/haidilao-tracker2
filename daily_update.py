#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
  하이디라오 영등포점 — 통합 자동 업데이트 스크립트
═══════════════════════════════════════════════════════════
  매일 자동 실행하여:
    1. Lark 시공그룹 채팅에서 새 메시지 수집
    2. 이벤트 트래커(하이디라오_이벤트트래커.html) 업데이트
    3. 작업일지(하이디라오_작업일지.html) 업데이트

  사용법:
    python3 daily_update.py               # 수동 실행 (최근 26시간)
    python3 daily_update.py --token       # 새 토큰 발급 후 실행
    python3 daily_update.py --full        # 전체 기간 재수집
"""

import json, re, sys, os, html as html_mod
from datetime import datetime, timezone, timedelta, date as dt_date
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode
from collections import defaultdict

# ── 설정 ──
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
APP_ID = 'cli_a97aa70eeca15e15'
APP_SECRET = 'l37gyqepLXhdTjLW7L9UngWh5jV6jtQw'
DOMAIN = 'https://open.larksuite.com'
CHAT_ID = 'oc_943f27f012a4da28abb89083bc7095a3'
KST = timezone(timedelta(hours=9))

TOKEN_FILE = os.path.join(BASE_DIR, 'lark_user_token.txt')
REFRESH_FILE = os.path.join(BASE_DIR, 'lark_refresh_token.txt')
RAW_MSG_FILE = os.path.join(BASE_DIR, 'lark_raw_messages.json')
TRACKER_HTML = os.path.join(BASE_DIR, '하이디라오_이벤트트래커.html')
TRACKER_DATA_JS = os.path.join(BASE_DIR, '이벤트_데이터.js')
WORKLOG_HTML = os.path.join(BASE_DIR, '하이디라오_작업일지.html')
WORKLOG_DATA = os.path.join(BASE_DIR, '작업일지_데이터.json')
LOG_FILE = os.path.join(BASE_DIR, '.daily_update.log')

# 채팅 이벤트 임계값 (이 수 이상이면 이벤트 생성)
MIN_MSG_FOR_EVENT = 20

# ── 기존 이벤트 토픽 매핑 (EVT-001~032) ──
EXISTING_EVENTS_TOPICS = {
    "EVT-001": {"date": "2026-04-03", "topics": ["회의", "현장인계", "에스컬레이터", "소방"]},
    "EVT-003": {"date": "2026-04-03", "topics": ["에스컬레이터", "철거"]},
    "EVT-004": {"date": "2026-04-03", "topics": ["소방"]},
    "EVT-005": {"date": "2026-04-15", "topics": ["먹매김", "현장미팅"]},
    "EVT-006": {"date": "2026-04-15", "topics": ["먹매김", "마감선"]},
    "EVT-007": {"date": "2026-04-15", "topics": ["설계변경", "소방", "바닥", "경사로", "타일", "칸막이"]},
    "EVT-008": {"date": "2026-04-20", "topics": ["에스컬레이터", "철거", "먹작업"]},
    "EVT-009": {"date": "2026-04-20", "topics": ["공정지연", "에스컬레이터"]},
    "EVT-010": {"date": "2026-04-20", "topics": ["먹작업", "화상회의"]},
    "EVT-011": {"date": "2026-04-20", "topics": ["설계팀", "점검연기"]},
    "EVT-012": {"date": "2026-04-24", "topics": ["설계검토", "배기", "벽돌", "칸막이", "소방", "층고", "자재"]},
    "EVT-013": {"date": "2026-04-24", "topics": ["배기", "바닥배기"]},
    "EVT-014": {"date": "2026-04-24", "topics": ["벽돌", "타일"]},
    "EVT-015": {"date": "2026-04-24", "topics": ["칸막이", "통로"]},
    "EVT-016": {"date": "2026-04-24", "topics": ["소방", "도면"]},
    "EVT-017": {"date": "2026-05-07", "topics": ["설계변경", "소방", "펫룸", "천장", "방화"]},
    "EVT-018": {"date": "2026-05-08", "topics": ["착공", "인원", "소방도면"]},
    "EVT-019": {"date": "2026-05-08", "topics": ["소방도면"]},
    "EVT-020": {"date": "2026-05-12", "topics": ["급배수", "전기", "설계변경", "식기세척기"]},
    "EVT-021": {"date": "2026-05-19", "topics": ["주간회의", "천장고", "보일러실", "경사로", "급기", "배기", "배연창"]},
    "EVT-022": {"date": "2026-05-19", "topics": ["경사로", "석재"]},
    "EVT-023": {"date": "2026-05-22", "topics": ["설계변경", "소방통로", "천장", "펫존", "창고"]},
    "EVT-024": {"date": "2026-04-24", "topics": ["자재", "유리", "방화문"]},
    "EVT-025": {"date": "2026-04-24", "topics": ["걸레받이", "타일"]},
    "EVT-026": {"date": "2026-04-24", "topics": ["HVAC", "급배수", "소방", "전기", "에어컨", "천장"]},
    "EVT-027": {"date": "2026-05-08", "topics": ["케이블", "전력", "광고"]},
    "EVT-028": {"date": "2026-05-08", "topics": ["자재", "샘플", "발주"]},
    "EVT-029": {"date": "2026-05-08", "topics": ["화장실", "걸레받이", "방화판"]},
    "EVT-030": {"date": "2026-05-19", "topics": ["급기", "배기", "신풍", "압력"]},
    "EVT-031": {"date": "2026-05-19", "topics": ["보일러실"]},
    "EVT-032": {"date": "2026-05-19", "topics": ["배연창", "소방"]},
}

# 키워드 매핑 (중국어/한국어 → 토픽)
KEYWORD_MAP = {
    "电梯": "에스컬레이터", "拆除": "철거", "放线": "먹매김", "먹매김": "먹매김",
    "消防": "소방", "소방": "소방", "防火": "방화", "방화": "방화",
    "图纸": "도면", "도면": "도면", "变更": "설계변경", "변경": "설계변경",
    "施工": "시공", "시공": "시공", "验收": "검수",
    "材料": "자재", "자재": "자재", "发주": "발주", "발주": "발주",
    "电气": "전기", "전기": "전기", "电箱": "전기", "배관": "급배수",
    "排风": "배기", "배기": "배기", "新风": "신풍", "급기": "급기",
    "风机": "배기", "배연": "배연창",
    "天花": "천장", "천장": "천장", "层高": "층고",
    "瓷砖": "타일", "타일": "타일", "벽돌": "벽돌",
    "隔墙": "칸막이", "玻璃": "유리",
    "防水": "방수", "방수": "방수",
    "空调": "에어컨", "冷热水": "급배수", "给排水": "급배수",
    "锅炉": "보일러실", "热水器": "보일러실", "热水房": "보일러실",
    "设备间": "설비실", "洗碗机": "식기세척기",
}

# 작업일지 카테고리 키워드
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
    line = f'[{now}] {msg}'
    print(line)
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(line + '\n')
    except:
        pass


# ═══════════════════════════════════════════════════════
#  PART 0: Lark API 헬퍼
# ═══════════════════════════════════════════════════════

def get_token():
    if not os.path.exists(TOKEN_FILE):
        return None
    with open(TOKEN_FILE) as f:
        return f.read().strip()


def get_refresh_token():
    if not os.path.exists(REFRESH_FILE):
        return None
    with open(REFRESH_FILE) as f:
        return f.read().strip()


def _get_app_token():
    """App Access Token 발급 (내부용)"""
    d = json.dumps({'app_id': APP_ID, 'app_secret': APP_SECRET}).encode()
    r = Request(f'{DOMAIN}/open-apis/auth/v3/app_access_token/internal',
                data=d, headers={'Content-Type': 'application/json'})
    with urlopen(r, timeout=15) as resp:
        return json.loads(resp.read().decode())['app_access_token']


def _save_tokens(tok_data):
    """OIDC 응답에서 access_token + refresh_token 저장"""
    user_token = tok_data['access_token']
    with open(TOKEN_FILE, 'w') as f:
        f.write(user_token)
    rt = tok_data.get('refresh_token')
    if rt:
        with open(REFRESH_FILE, 'w') as f:
            f.write(rt)
    return user_token


def refresh_via_refresh_token():
    """저장된 refresh_token으로 브라우저 없이 자동 갱신.
    성공 시 새 User Token 반환, 실패 시 None (→ 수동 재인증 필요)."""
    rt = get_refresh_token()
    if not rt:
        return None
    try:
        app_token = _get_app_token()
        d = json.dumps({'grant_type': 'refresh_token', 'refresh_token': rt}).encode()
        r = Request(f'{DOMAIN}/open-apis/authen/v1/oidc/refresh_access_token',
                    data=d, headers={'Content-Type': 'application/json',
                                     'Authorization': f'Bearer {app_token}'})
        with urlopen(r, timeout=15) as resp:
            tok = json.loads(resp.read().decode())
        if tok.get('code') not in (0, None) or 'data' not in tok:
            log(f'  ⚠️ refresh_token 갱신 거부 (code={tok.get("code")}): {tok.get("msg","")}')
            return None
        user_token = _save_tokens(tok['data'])
        log('  🔄 refresh_token으로 자동 갱신 성공')
        return user_token
    except Exception as e:
        log(f'  ⚠️ 자동 갱신 실패: {e}')
        return None


def refresh_token():
    """브라우저 OAuth로 새 User Access Token 발급"""
    import http.server, webbrowser, threading, time
    from urllib.parse import urlparse, parse_qs

    PORT = 9877
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
           f'&state=daily&scope={scopes}')
    log('🔐 브라우저에서 Lark 로그인 대기...')
    webbrowser.open(url)

    import time
    for _ in range(120):
        if result['code']: break
        time.sleep(1)
    srv.shutdown()

    if not result['code']:
        log('❌ 인증 타임아웃')
        return None

    # App Token
    app_token = _get_app_token()

    # User Token
    d2 = json.dumps({'grant_type': 'authorization_code', 'code': result['code']}).encode()
    r2 = Request(f'{DOMAIN}/open-apis/authen/v1/oidc/access_token',
                 data=d2, headers={'Content-Type': 'application/json',
                                   'Authorization': f'Bearer {app_token}'})
    with urlopen(r2, timeout=15) as resp:
        tok = json.loads(resp.read().decode())

    user_token = _save_tokens(tok['data'])
    log('✅ 새 User Token 발급 완료 (refresh_token 저장됨)')
    return user_token


def fetch_messages(token, hours_back=26):
    """최근 N시간 메시지 수집"""
    now_ts = int(datetime.now(KST).timestamp())
    start_ts = str(now_ts - hours_back * 3600)
    end_ts = str(now_ts)
    return _fetch_messages_range(token, start_ts, end_ts)


def fetch_all_messages(token):
    """전체 기간 메시지 수집 (4/1~현재)"""
    start_ts = str(int(datetime(2026, 4, 1, tzinfo=KST).timestamp()))
    end_ts = str(int(datetime.now(KST).timestamp()))
    return _fetch_messages_range(token, start_ts, end_ts)


def _fetch_messages_range(token, start_ts, end_ts):
    all_msgs = []
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
        req = Request(url, headers={
            'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'
        })
        try:
            with urlopen(req, timeout=30) as resp:
                result = json.loads(resp.read().decode())
        except HTTPError as e:
            err = e.read().decode() if hasattr(e, 'read') else str(e)
            if '99991668' in err or '99991663' in err:
                log('⚠️ 토큰 만료! --token 옵션으로 재인증 필요')
                return None
            log(f'❌ API: {err[:200]}')
            return all_msgs
        except Exception as e:
            log(f'❌ 네트워크: {e}')
            return all_msgs

        if result.get('code') != 0:
            if result.get('code') in [99991668, 99991663]:
                log('⚠️ 토큰 만료!')
                return None
            log(f'❌ API 응답: {result.get("msg", "")}')
            return all_msgs

        items = result.get('data', {}).get('items', [])
        all_msgs.extend(items)
        if not result.get('data', {}).get('has_more'):
            break
        page_token = result.get('data', {}).get('page_token', '')

    return all_msgs


def parse_msg_text(m):
    """메시지에서 텍스트 추출"""
    msg_type = m.get('msg_type', '')
    content_str = m.get('body', {}).get('content', '{}')
    if msg_type == 'text':
        try:
            return json.loads(content_str).get('text', '')
        except:
            return content_str
    elif msg_type == 'post':
        try:
            content = json.loads(content_str)
            texts = []
            title = content.get('title', '')
            if title: texts.append(title)
            for lang, paragraphs in content.items():
                if isinstance(paragraphs, list):
                    for para in paragraphs:
                        if isinstance(para, list):
                            for elem in para:
                                if isinstance(elem, dict) and elem.get('tag') == 'text':
                                    texts.append(elem.get('text', ''))
            return ' '.join(texts)
        except:
            return ''
    return ''


def msg_timestamp(m):
    ts = int(m.get('create_time', '0'))
    if ts > 1e12: ts /= 1000
    return datetime.fromtimestamp(ts, tz=KST)


# ═══════════════════════════════════════════════════════
#  PART 1: 이벤트 트래커 업데이트
# ═══════════════════════════════════════════════════════

def get_existing_chat_event_ids():
    """이벤트_데이터.js에서 현재 존재하는 채팅 이벤트 ID 추출"""
    if not os.path.exists(TRACKER_DATA_JS):
        return set(), 0
    with open(TRACKER_DATA_JS, encoding='utf-8') as f:
        js_content = f.read()
    ids = set(re.findall(r'id:\s*"(EVT-\d+)".*?category:\s*"chat"', js_content))
    # 마지막 EVT 번호
    all_ids = re.findall(r'EVT-(\d+)', js_content)
    max_num = max(int(x) for x in all_ids) if all_ids else 0
    return ids, max_num


def get_existing_chat_dates():
    """이벤트_데이터.js에서 이미 존재하는 채팅 이벤트 날짜 추출"""
    if not os.path.exists(TRACKER_DATA_JS):
        return set()
    with open(TRACKER_DATA_JS, encoding='utf-8') as f:
        js_content = f.read()
    # title: "라크 시공 그룹 대화 — 2026-XX-XX (N건)" 패턴
    dates = set(re.findall(r'라크 시공 그룹 대화 — (\d{4}-\d{2}-\d{2})', js_content))
    return dates


def group_messages_by_date(messages):
    """메시지를 날짜별로 그룹화"""
    date_groups = defaultdict(list)
    for m in messages:
        if m.get('msg_type') not in ('text', 'post'):
            continue
        try:
            dt = msg_timestamp(m)
        except:
            continue
        text = parse_msg_text(m)
        if text.strip() and len(text.strip()) > 2:
            date_groups[dt.strftime('%Y-%m-%d')].append({
                'time': dt.strftime('%H:%M'),
                'text': text.strip()
            })
    return dict(date_groups)


def build_chat_event_js(evt_id, date_str, msgs):
    """날짜별 메시지로 채팅 이벤트 JS 코드 생성"""
    all_text = " ".join([m["text"] for m in msgs])

    # 토픽 추출
    found_topics = set()
    for kw, topic in KEYWORD_MAP.items():
        if kw in all_text:
            found_topics.add(topic)

    # 기존 이벤트와 연결
    linked = []
    for eid, info in EXISTING_EVENTS_TOPICS.items():
        evt_date = info["date"]
        evt_topics = set(info["topics"])
        if evt_date == date_str:
            linked.append(eid)
            continue
        chat_dt = datetime.strptime(date_str, "%Y-%m-%d")
        evt_dt = datetime.strptime(evt_date, "%Y-%m-%d")
        day_diff = abs((chat_dt - evt_dt).days)
        common = found_topics & evt_topics
        if day_diff <= 3 and len(common) >= 1:
            linked.append(eid)
        elif len(common) >= 2:
            linked.append(eid)

    linked = sorted(set(linked), key=lambda x: int(x.split("-")[1]))

    # 상세 내용
    detail_lines = []
    for m in msgs[:15]:
        text = m["text"][:120].replace("`", "'").replace("\\", "").replace("\n", " ")
        detail_lines.append(f'[{m["time"]}] {text}')
    if len(msgs) > 15:
        detail_lines.append(f"... 외 {len(msgs)-15}건")
    details = "\\n".join(detail_lines)

    # 요약
    summary_texts = [m["text"][:40].replace('"', "'").replace("\n", " ") for m in msgs[:3]]
    summary = f'{len(msgs)}건 대화 — ' + " | ".join(summary_texts)
    if len(summary) > 120:
        summary = summary[:117] + "..."

    linked_str = ", ".join([f'"{e}"' for e in linked])

    js = f"""  {{
    id: "{evt_id}", date: "{date_str}", category: "chat",
    title: "라크 시공 그룹 대화 — {date_str} ({len(msgs)}건)",
    summary: "{summary}",
    details: `시공 그룹 채팅 ({len(msgs)}건):\\n\\n{details}`,
    decisions: [],
    linkedEvents: [{linked_str}],
    source: "Lark 시공그룹 채팅"
  }}"""

    return js, linked


def update_event_tracker(messages):
    """이벤트 트래커 데이터 파일(이벤트_데이터.js)에 새 채팅 이벤트 추가"""
    if not os.path.exists(TRACKER_DATA_JS):
        log('⚠️ 이벤트 트래커 데이터 JS 파일 없음')
        return 0

    existing_dates = get_existing_chat_dates()
    _, max_evt_num = get_existing_chat_event_ids()

    date_groups = group_messages_by_date(messages)

    # 신규 이벤트 빌드
    new_events = []
    next_num = max_evt_num + 1

    for date_str in sorted(date_groups.keys()):
        if date_str in existing_dates:
            continue
        msgs = date_groups[date_str]
        if len(msgs) < MIN_MSG_FOR_EVENT:
            continue

        evt_id = f"EVT-{next_num:03d}"
        js, linked = build_chat_event_js(evt_id, date_str, msgs)
        new_events.append({'id': evt_id, 'js': js, 'linked': linked})
        next_num += 1

    if not new_events:
        log('ℹ️ 이벤트 트래커: 신규 채팅 이벤트 없음')
        return 0

    # JS 파일 수정
    with open(TRACKER_DATA_JS, encoding='utf-8') as f:
        js_content = f.read()

    # EVENTS 배열의 끝 찾기
    insert_pattern = '];\n\n// ===== CATEGORY CONFIG ====='
    insert_pos = js_content.find(insert_pattern)
    if insert_pos < 0:
        config_pos = js_content.find('// ===== CATEGORY CONFIG =====')
        if config_pos > 0:
            insert_pos = js_content.rfind('\n];', 0, config_pos)
            if insert_pos > 0:
                insert_pos = insert_pos + 1
            
    if insert_pos < 0:
        log('❌ 이벤트_데이터.js 내 EVENTS 배열의 끝을 찾을 수 없음')
        return 0

    new_events_js = ",\n\n".join([e['js'] for e in new_events])
    js_content = js_content[:insert_pos] + ",\n\n" + new_events_js + "\n" + js_content[insert_pos:]

    # 3) 역방향 링크 추가
    reverse_links = defaultdict(list)
    for e in new_events:
        for lid in e['linked']:
            reverse_links[lid].append(e['id'])

    for evt_id, chat_ids in reverse_links.items():
        pattern = f'id: "{evt_id}"'
        idx = js_content.find(pattern)
        if idx < 0:
            continue
        search_end = js_content.find("source:", idx)
        if search_end < 0:
            continue
        section = js_content[idx:search_end]
        linked_match = re.search(r'linkedEvents:\s*\[([^\]]*)\]', section)
        if not linked_match:
            continue
        old_linked = linked_match.group(1).strip()
        existing_ids = [s.strip().strip('"').strip("'") for s in old_linked.split(",") if s.strip()]
        for cid in chat_ids:
            if cid not in existing_ids:
                existing_ids.append(cid)
        new_linked = ", ".join([f'"{e}"' for e in existing_ids])
        old_full = linked_match.group(0)
        new_full = f"linkedEvents: [{new_linked}]"
        js_content = js_content[:idx] + section.replace(old_full, new_full) + js_content[search_end:]

    with open(TRACKER_DATA_JS, 'w', encoding='utf-8') as f:
        f.write(js_content)

    log(f'✅ 이벤트 트래커: {len(new_events)}개 신규 채팅 이벤트 추가!')
    for e in new_events:
        log(f'  ✨ {e["id"]}')

    return len(new_events)


# ═══════════════════════════════════════════════════════
#  PART 2: 작업일지 업데이트
# ═══════════════════════════════════════════════════════

def update_work_logs(messages):
    """작업일지 데이터 + HTML 업데이트"""
    # 기존 데이터 로드
    if os.path.exists(WORKLOG_DATA):
        with open(WORKLOG_DATA, encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            'project': '하이디라오 영등포점 (海底捞韩国永登浦店)',
            'data_source': 'Lark 시공그룹 채팅 자동 수집',
            'total_logs': 0, 'period': '', 'logs': [],
        }

    existing_dates = set(l['log_date'] for l in data['logs'])
    date_texts = group_messages_by_date(messages)
    added = 0

    for m in messages:
        if m.get('msg_type') != 'file':
            continue
        try:
            dt = msg_timestamp(m)
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

        date_match = re.search(r'(\d{8})', fname)
        if date_match:
            ds = date_match.group(1)
            log_date = f'{ds[:4]}-{ds[4:6]}-{ds[6:8]}'
        else:
            log_date = dt.strftime('%Y-%m-%d')

        if log_date in existing_dates:
            continue

        # 대화 컨텍스트
        day_msgs = date_texts.get(log_date, [])
        all_text = ' '.join([dm['text'] for dm in day_msgs])
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
            is_work = any(kw in dm['text'] for kws in WORK_CATEGORIES.values() for kw in kws)
            if is_work:
                highlights.append(f'[{dm["time"]}] {dm["text"][:100]}')

        new_log = {
            'log_date': log_date,
            'upload_date': dt.strftime('%Y-%m-%d'),
            'upload_time': dt.strftime('%H:%M'),
            'file_name': fname,
            'file_key': fkey,
            'message_id': m.get('message_id', ''),
            'sender_id': m.get('sender', {}).get('id', ''),
            'work_categories': matched_cats,
            'day_highlights': highlights[:8],
            'total_messages': len(day_msgs),
        }
        data['logs'].append(new_log)
        existing_dates.add(log_date)
        added += 1
        log(f'  ✨ 작업일지: {log_date} — {fname}')

    if added > 0:
        data['logs'].sort(key=lambda x: x['log_date'])
        data['total_logs'] = len(data['logs'])
        if data['logs']:
            data['period'] = f'{data["logs"][0]["log_date"]} ~ {data["logs"][-1]["log_date"]}'
        data['last_updated'] = datetime.now(KST).strftime('%Y-%m-%d %H:%M:%S KST')

        with open(WORKLOG_DATA, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # HTML 업데이트
        if os.path.exists(WORKLOG_HTML):
            with open(WORKLOG_HTML, encoding='utf-8') as f:
                html = f.read()
            pattern = r'const WORK_LOGS = \{.*?\};'
            js_data = json.dumps(data, ensure_ascii=False)
            # re.sub에서 백슬래시가 축소되는 버그 방지
            escaped_js_data = js_data.replace('\\', '\\\\')
            new_html = re.sub(pattern, f'const WORK_LOGS = {escaped_js_data};', html, count=1, flags=re.DOTALL)
            with open(WORKLOG_HTML, 'w', encoding='utf-8') as f:
                f.write(new_html)
            log(f'✅ 작업일지: {added}개 추가 (총 {data["total_logs"]}개)')
    else:
        log('ℹ️ 작업일지: 신규 시공일지 없음')

    return added


# ═══════════════════════════════════════════════════════
#  PART 3: RAW 메시지 보관 업데이트
# ═══════════════════════════════════════════════════════

def update_raw_messages(messages):
    """lark_raw_messages.json에 새 메시지 병합"""
    if os.path.exists(RAW_MSG_FILE):
        with open(RAW_MSG_FILE, encoding='utf-8') as f:
            existing = json.load(f)
    else:
        existing = []

    existing_ids = set(m.get('message_id', '') for m in existing)
    new_count = 0
    for m in messages:
        mid = m.get('message_id', '')
        if mid and mid not in existing_ids:
            existing.append(m)
            existing_ids.add(mid)
            new_count += 1

    if new_count > 0:
        existing.sort(key=lambda x: x.get('create_time', '0'))
        with open(RAW_MSG_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        log(f'📦 Raw 메시지: {new_count}개 추가 (총 {len(existing)}개)')

    return new_count


# ═══════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════

def main():
    log('')
    log('═' * 55)
    log('  🔄 하이디라오 통합 자동 업데이트')
    log('═' * 55)

    # 토큰 처리
    if '--token' in sys.argv:
        token = refresh_token()
        if not token:
            return
    else:
        token = get_token()
        if not token:
            log('❌ 토큰 없음! python3 daily_update.py --token')
            return

    # 메시지 수집 (토큰 만료 시 refresh_token으로 1회 자동 갱신 후 재시도)
    def _collect(tok):
        if '--full' in sys.argv:
            log('📨 전체 기간 메시지 수집 중...')
            return fetch_all_messages(tok)
        log('📨 최근 26시간 메시지 확인 중...')
        return fetch_messages(tok, hours_back=26)

    messages = _collect(token)
    if messages is None:
        log('💡 토큰 만료 — refresh_token으로 자동 갱신 시도...')
        new_token = refresh_via_refresh_token()
        if new_token:
            token = new_token
            messages = _collect(token)
    if messages is None:
        log('❌ 자동 갱신 실패. 수동 재인증 필요: python3 daily_update.py --token')
        return

    log(f'  {len(messages)}개 메시지 수신')

    if len(messages) == 0:
        log('ℹ️ 새 메시지 없음. 종료.')
        return

    # Raw 보관
    update_raw_messages(messages)

    # 이벤트 트래커 업데이트 (채팅 이벤트)
    log('')
    log('── 이벤트 트래커 업데이트 ──')
    evt_added = update_event_tracker(messages)

    # 회의록 문서 → meeting 이벤트 자동 추가
    log('')
    log('── 회의록 자동 처리 ──')
    mtg_added = 0
    try:
        sys.path.insert(0, BASE_DIR)
        import meeting_minutes
        mtg_added = meeting_minutes.process_meeting_minutes(token, messages)
    except Exception as e:
        log(f'⚠️ 회의록 처리 실패(건너뜀): {e}')

    # 작업일지 업데이트
    log('')
    log('── 작업일지 업데이트 ──')
    wl_added = update_work_logs(messages)

    # 공종별 작업자 파싱 + 고도화 (PDF 인원표 → trades, 채팅 → 상세, HTML 동기화)
    log('')
    log('── 공종별 작업자 파싱 + 고도화 ──')
    try:
        sys.path.insert(0, BASE_DIR)
        import parse_and_apply, enhance_work_logs
        parse_and_apply.main()
        enhance_work_logs.main()
        with open(WORKLOG_DATA, encoding='utf-8') as f:
            _data = json.load(f)
        parse_and_apply.update_html(_data)
        log('✅ 공종별 작업자 파싱/고도화/HTML 동기화 완료')
    except Exception as e:
        log(f'⚠️ 공종별 고도화 실패(건너뜀): {e}')

    # 요약
    log('')
    log('═' * 55)
    log(f'  🏁 업데이트 완료!')
    log(f'     이벤트 트래커: +{evt_added}개 채팅 이벤트')
    log(f'     회의록:       +{mtg_added}개 회의 이벤트')
    log(f'     작업일지:     +{wl_added}개 시공일지')
    log('═' * 55)


if __name__ == '__main__':
    main()
