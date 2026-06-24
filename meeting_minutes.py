#!/usr/bin/env python3
"""
═══════════════════════════════════════════════════════════
  하이디라오 영등포점 — 회의록 자동 처리 모듈
═══════════════════════════════════════════════════════════
  라크 채팅에 올라온 회의록 문서(.doc/.docx)를 감지 →
    1. 회의록/auto/ 폴더에 다운로드
    2. macOS textutil 로 텍스트 추출
    3. 날짜/제목/내용 파싱
    4. 이벤트_데이터.js 에 meeting 이벤트(EVT-XXX) 추가

  daily_update.py / morning_update.py 의 파이프라인에서 호출됨.
  단독 점검:  python3 meeting_minutes.py --scan   (회의록 폴더 파싱 미리보기)
"""

import json, re, os, sys, subprocess, unicodedata
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
TRACKER_DATA_JS = os.path.join(BASE_DIR, '이벤트_데이터.js')
MEETING_DIR     = os.path.join(BASE_DIR, '회의록')
AUTO_DIR        = os.path.join(MEETING_DIR, 'auto')
DOMAIN          = 'https://open.larksuite.com'
KST             = timezone(timedelta(hours=9))

# 회의록 문서로 인정할 키워드 (파일명 기준) + 확장자
MEETING_KEYWORDS = ('회의록', '회의', '화상회의', '会议', '会议录', '会议纪要', '纪要')
MEETING_EXTS     = ('.doc', '.docx')


def _log(msg):
    print(msg, flush=True)


# ════════════════════════════════════════
#  감지 / 다운로드 / 텍스트 추출
# ════════════════════════════════════════

def is_meeting_file(fname):
    """파일명이 회의록 문서인지 판별 (macOS NFD 파일명 대응 위해 NFC 정규화)"""
    if not fname:
        return False
    fname = unicodedata.normalize('NFC', fname)
    if not fname.lower().endswith(MEETING_EXTS):
        return False
    return any(kw in fname for kw in MEETING_KEYWORDS)


def download_file(token, message_id, file_key, save_path):
    """라크 메시지 첨부파일 다운로드 (User Token 필요). 성공 True / 만료 'TOKEN_EXPIRED' / 실패 False"""
    url = f'{DOMAIN}/open-apis/im/v1/messages/{message_id}/resources/{file_key}?type=file'
    req = Request(url, headers={'Authorization': f'Bearer {token}'})
    try:
        with urlopen(req, timeout=60) as resp:
            data = resp.read()
        if not data or len(data) < 100:
            return False
        with open(save_path, 'wb') as f:
            f.write(data)
        return True
    except HTTPError as e:
        body = e.read().decode() if hasattr(e, 'read') else str(e)
        if e.code == 401 or any(c in body for c in ['99991668', '99991663', '99991661']):
            return 'TOKEN_EXPIRED'
        _log(f'  ❌ 다운로드 HTTP {e.code}: {body[:120]}')
        return False
    except Exception as e:
        _log(f'  ❌ 다운로드 오류: {e}')
        return False


def doc_to_text(path):
    """macOS textutil 로 .doc/.docx → 평문 텍스트"""
    try:
        out = subprocess.run(
            ['textutil', '-convert', 'txt', '-stdout', path],
            capture_output=True, timeout=60
        )
        if out.returncode != 0:
            _log(f'  ⚠️ textutil 실패: {out.stderr.decode()[:120]}')
            return ''
        return unicodedata.normalize('NFC', out.stdout.decode('utf-8', errors='replace'))
    except Exception as e:
        _log(f'  ⚠️ textutil 오류: {e}')
        return ''


# ════════════════════════════════════════
#  파싱 (날짜 / 제목 / 요약 / 본문)
# ════════════════════════════════════════

def extract_date(fname, text, fallback_dt=None):
    """파일명 → 본문 → 메시지시각 순으로 회의 날짜(YYYY-MM-DD) 추출"""
    for src in (fname, text[:300] if text else ''):
        m = re.search(r'(20\d{2})[.\-_/년\s]{0,2}(\d{1,2})[.\-_/월\s]{0,2}(\d{1,2})', src)
        if m:
            y, mo, d = m.group(1), m.group(2).zfill(2), m.group(3).zfill(2)
            if 1 <= int(mo) <= 12 and 1 <= int(d) <= 31:
                return f'{y}-{mo}-{d}'
    if fallback_dt:
        return fallback_dt.strftime('%Y-%m-%d')
    return ''


def clean_lines(text):
    """텍스트를 의미있는 줄 리스트로 정리"""
    lines = []
    for ln in text.replace('\r', '\n').split('\n'):
        ln = ln.strip().replace('\xa0', ' ')
        ln = re.sub(r'\s{2,}', ' ', ln)
        if ln and not re.fullmatch(r'[（(]\s*\d+\s*/\s*\d+\s*[)）]', ln):  # 페이지번호 제외
            lines.append(ln)
    return lines


def extract_title(lines, date_str):
    """회의제목 추출 (없으면 날짜 기반 기본 제목)"""
    for i, ln in enumerate(lines):
        if re.search(r'회의\s*제목|会议\s*主题|회의\s*명', ln):
            # 같은 줄 뒤쪽 또는 다음 줄
            after = re.sub(r'.*?(회의\s*제목|会议\s*主题|회의\s*명)\s*[:：]?', '', ln).strip()
            if len(after) >= 2:
                return after[:50]
            if i + 1 < len(lines) and len(lines[i+1]) >= 2:
                return lines[i+1][:50]
    return f'회의 — {date_str}'


def extract_summary(lines):
    """회의내용 섹션 앞부분으로 요약 생성"""
    body = []
    started = False
    for ln in lines:
        if not started and re.search(r'회의\s*내용|会议\s*内容|논의|议题|安排', ln):
            started = True
            continue
        if started:
            # 번호/불릿 항목 위주로 수집
            cleaned = re.sub(r'^[•\-\d]+[.\)、]?\s*', '', ln)
            if len(cleaned) >= 4:
                body.append(cleaned)
        if len(body) >= 3:
            break
    if not body:
        body = [ln for ln in lines if len(ln) >= 6][:3]
    summary = ' | '.join(b[:40] for b in body[:3])
    return (summary[:117] + '...') if len(summary) > 120 else summary


def build_meeting_event_js(evt_id, date_str, title, summary, lines, source):
    """meeting 이벤트 JS 코드 생성"""
    detail_lines = []
    for ln in lines[:40]:
        t = ln[:140].replace('`', "'").replace('\\', '').replace('$', '＄')
        detail_lines.append(t)
    if len(lines) > 40:
        detail_lines.append(f'... 외 {len(lines)-40}줄 (원문: {source})')
    details = '\\n'.join(detail_lines)

    safe_title = title.replace('"', "'").replace('\n', ' ')
    safe_sum   = summary.replace('"', "'").replace('\n', ' ')
    safe_src   = source.replace('"', "'")

    js = f"""  {{
    id: "{evt_id}", date: "{date_str}", category: "meeting",
    title: "{safe_title}",
    summary: "{safe_sum}",
    details: `회의록 자동 수집:\\n\\n{details}`,
    decisions: [],
    linkedEvents: [],
    source: "{safe_src}"
  }}"""
    return js


# ════════════════════════════════════════
#  이벤트_데이터.js 읽기/쓰기
# ════════════════════════════════════════

def get_existing_sources_and_maxnum():
    """등록된 source 파일명 집합 + 최대 EVT 번호"""
    if not os.path.exists(TRACKER_DATA_JS):
        return set(), 0
    js = open(TRACKER_DATA_JS, encoding='utf-8').read()
    sources = set(re.findall(r'source:\s*"([^"]+)"', js))
    nums = re.findall(r'EVT-(\d+)', js)
    return sources, (max(int(x) for x in nums) if nums else 0)


def insert_events(events_js_list):
    """meeting 이벤트들을 EVENTS 배열 끝에 삽입"""
    js = open(TRACKER_DATA_JS, encoding='utf-8').read()
    insert_pattern = '];\n\n// ===== CATEGORY CONFIG ====='
    pos = js.find(insert_pattern)
    if pos < 0:
        cfg = js.find('// ===== CATEGORY CONFIG =====')
        if cfg > 0:
            pos = js.rfind('\n];', 0, cfg)
            if pos > 0:
                pos += 1
    if pos < 0:
        _log('❌ 이벤트_데이터.js 의 EVENTS 배열 끝을 찾지 못함')
        return False
    block = ',\n\n' + ',\n\n'.join(events_js_list) + '\n'
    js = js[:pos] + block + js[pos:]
    with open(TRACKER_DATA_JS, 'w', encoding='utf-8') as f:
        f.write(js)
    return True


# ════════════════════════════════════════
#  파이프라인 진입점
# ════════════════════════════════════════

def parse_file_to_event(path, fname, max_num, fallback_dt=None):
    """단일 회의록 파일 → (evt_js, evt_id, date) 또는 None"""
    text = doc_to_text(path)
    if not text or len(text.strip()) < 30:
        _log(f'  ⚠️ 본문 추출 실패/너무 짧음: {fname}')
        return None
    lines = clean_lines(text)
    date_str = extract_date(fname, text, fallback_dt)
    if not date_str:
        _log(f'  ⚠️ 날짜 추출 실패: {fname}')
        return None
    title   = extract_title(lines, date_str)
    summary = extract_summary(lines)
    evt_id  = f'EVT-{max_num+1:03d}'
    js = build_meeting_event_js(evt_id, date_str, title, summary, lines, fname)
    return {'js': js, 'id': evt_id, 'date': date_str, 'title': title}


def process_meeting_minutes(token, messages):
    """라크 메시지에서 회의록 문서를 찾아 다운로드·파싱·트래커 반영. 추가 개수 반환."""
    if not os.path.exists(TRACKER_DATA_JS):
        _log('⚠️ 이벤트 트래커 JS 없음 — 회의록 처리 건너뜀')
        return 0

    sources, max_num = get_existing_sources_and_maxnum()
    os.makedirs(AUTO_DIR, exist_ok=True)

    new_events = []
    for m in messages:
        if m.get('msg_type') != 'file':
            continue
        try:
            content = json.loads(m.get('body', {}).get('content', '{}'))
            fname = content.get('file_name', '')
            fkey  = content.get('file_key', '')
            msg_id = m.get('message_id', '')
        except Exception:
            continue
        if not is_meeting_file(fname) or not fkey or not msg_id:
            continue
        if fname in sources:
            continue  # 이미 등록된 회의록

        ts = int(m.get('create_time', '0'))
        if ts > 1e12:
            ts /= 1000
        fallback_dt = datetime.fromtimestamp(ts, tz=KST)

        save_path = os.path.join(AUTO_DIR, fname)
        if not os.path.exists(save_path):
            _log(f'  ⬇️ 회의록 다운로드: {fname[:55]}')
            r = download_file(token, msg_id, fkey, save_path)
            if r == 'TOKEN_EXPIRED':
                _log('  ❌ 회의록 다운로드 중 토큰 만료')
                break
            if not r:
                continue

        evt = parse_file_to_event(save_path, fname, max_num + len(new_events), fallback_dt)
        if evt:
            new_events.append(evt)
            sources.add(fname)
            _log(f'  ✨ {evt["id"]} [{evt["date"]}] {evt["title"]}')

    if not new_events:
        _log('ℹ️ 회의록: 신규 없음')
        return 0

    if insert_events([e['js'] for e in new_events]):
        _log(f'✅ 회의록: {len(new_events)}개 신규 회의 이벤트 추가!')
        return len(new_events)
    return 0


# ════════════════════════════════════════
#  단독 점검 모드
# ════════════════════════════════════════

def _scan_folder():
    """회의록 폴더의 문서를 파싱만 해서 미리보기 (트래커 변경 없음)"""
    sources, max_num = get_existing_sources_and_maxnum()
    found = []
    for root, _, files in os.walk(MEETING_DIR):
        for f in files:
            if is_meeting_file(f):
                found.append(os.path.join(root, f))
    print(f'회의록 문서 {len(found)}개 발견 / 등록된 source {len(sources)}개\n')
    sources = {unicodedata.normalize('NFC', s) for s in sources}
    for path in sorted(found):
        fname = unicodedata.normalize('NFC', os.path.basename(path))
        registered = '✓등록' if fname in sources else '✗미등록'
        evt = parse_file_to_event(path, fname, max_num)
        if evt:
            print(f'[{registered}] {evt["date"]}  {evt["title"]}  ←  {fname}')
        else:
            print(f'[{registered}] (파싱실패)  ←  {fname}')


if __name__ == '__main__':
    if '--scan' in sys.argv:
        _scan_folder()
    else:
        print('이 모듈은 daily_update.py / morning_update.py 에서 호출됩니다.')
        print('회의록 폴더 파싱 미리보기:  python3 meeting_minutes.py --scan')
