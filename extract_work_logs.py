#!/usr/bin/env python3
"""
라크 채팅에서 작업일지(시공일지) 데이터를 추출하여 구조화합니다.
- PDF 파일 첨부 메시지에서 작업일지 날짜, 파일명, 업로드 시각 추출
- 해당 날짜 주변의 대화 메시지에서 작업 내용 키워드 추출
- JSON + 이벤트 트래커 JS 형식으로 출력
"""
import json, re
from datetime import datetime, timezone, timedelta
from collections import defaultdict

KST = timezone(timedelta(hours=9))

with open('lark_raw_messages.json', encoding='utf-8') as f:
    msgs = json.load(f)

# ── 1단계: 시공일지 PDF 파일 추출 ──
work_logs = []
for m in msgs:
    if m.get('msg_type') != 'file':
        continue
    ts = int(m.get('create_time', '0'))
    if ts > 1e12: ts /= 1000
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

    # 시공일지 패턴 매칭
    if '施工日志' not in fname and '施工日报' not in fname:
        continue

    # 파일명에서 날짜 추출 (20260416 형식)
    date_match = re.search(r'(\d{8})', fname)
    if date_match:
        log_date_str = date_match.group(1)
        log_date = f'{log_date_str[:4]}-{log_date_str[4:6]}-{log_date_str[6:8]}'
    else:
        log_date = dt.strftime('%Y-%m-%d')

    work_logs.append({
        'log_date': log_date,
        'upload_date': dt.strftime('%Y-%m-%d'),
        'upload_time': dt.strftime('%H:%M'),
        'file_name': fname,
        'file_key': fkey,
        'message_id': m.get('message_id', ''),
        'sender_id': m.get('sender', {}).get('id', ''),
    })

# 날짜순 정렬
work_logs.sort(key=lambda x: x['log_date'])

print(f'✅ 총 {len(work_logs)}개 시공일지 발견\n')

# ── 2단계: 각 일지 날짜 전후의 대화에서 작업 내용 추출 ──
# 날짜별 텍스트 메시지 인덱스
date_texts = defaultdict(list)
for m in msgs:
    if m.get('msg_type') not in ('text', 'post'):
        continue
    ts = int(m.get('create_time', '0'))
    if ts > 1e12: ts /= 1000
    try:
        dt = datetime.fromtimestamp(ts, tz=KST)
    except:
        continue
    date_str = dt.strftime('%Y-%m-%d')
    body = m.get('body', {})
    content_str = body.get('content', '{}')
    if m.get('msg_type') == 'text':
        try:
            content = json.loads(content_str)
            text = content.get('text', '')
        except:
            text = content_str
    elif m.get('msg_type') == 'post':
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
            text = ' '.join(texts)
        except:
            text = ''
    else:
        text = ''
    if text.strip() and len(text.strip()) > 3:
        date_texts[date_str].append({
            'time': dt.strftime('%H:%M'),
            'text': text.strip()
        })

# 작업 카테고리 키워드 사전
work_categories = {
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

# 각 일지에 해당 날짜의 작업 내용 추가
for log in work_logs:
    date = log['log_date']
    day_msgs = date_texts.get(date, [])
    all_text = ' '.join([m['text'] for m in day_msgs])

    # 작업 카테고리 매칭
    matched_categories = []
    for cat_name, keywords in work_categories.items():
        for kw in keywords:
            if kw in all_text:
                matched_categories.append(cat_name)
                break

    log['work_categories'] = matched_categories

    # 주요 대화 내용 (의미 있는 것만)
    significant_msgs = []
    for m in day_msgs:
        text = m['text']
        # 너무 짧거나 @ 멘션만 있는 건 제외
        if len(text) < 10:
            continue
        if text.startswith('@') and len(text) < 20:
            continue
        # 작업 관련 내용만
        is_work = False
        for keywords in work_categories.values():
            for kw in keywords:
                if kw in text:
                    is_work = True
                    break
            if is_work:
                break
        if is_work:
            significant_msgs.append(f'[{m["time"]}] {text[:100]}')

    log['day_highlights'] = significant_msgs[:8]
    log['total_messages'] = len(day_msgs)

# ── 3단계: 구조화된 JSON 저장 ──
output = {
    'project': '하이디라오 영등포점 (海底捞韩国永登浦店)',
    'data_source': 'Lark 시공그룹 채팅 자동 수집',
    'total_logs': len(work_logs),
    'period': f'{work_logs[0]["log_date"]} ~ {work_logs[-1]["log_date"]}',
    'logs': work_logs
}

with open('작업일지_데이터.json', 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f'📅 기간: {output["period"]}')
print(f'📊 총 {output["total_logs"]}일 시공일지\n')

# 월별 통계
monthly = defaultdict(int)
for log in work_logs:
    month = log['log_date'][:7]
    monthly[month] += 1
print('월별 시공일지 수:')
for month in sorted(monthly):
    print(f'  {month}: {monthly[month]}일')

# 작업 카테고리 통계
cat_count = defaultdict(int)
for log in work_logs:
    for cat in log['work_categories']:
        cat_count[cat] += 1
print('\n작업 카테고리 빈도:')
for cat, cnt in sorted(cat_count.items(), key=lambda x: -x[1]):
    print(f'  {cat}: {cnt}일')

# 누락일 확인
from datetime import date as dt_date
start = dt_date(2026, 4, 16)
end = dt_date(2026, 6, 16)
log_dates = set(log['log_date'] for log in work_logs)
missing = []
current = start
while current <= end:
    ds = current.strftime('%Y-%m-%d')
    if ds not in log_dates:
        missing.append(ds)
    current += timedelta(days=1)
print(f'\n⚠️ 누락일 ({len(missing)}일):')
for d in missing:
    wd = ['월','화','수','목','금','토','일'][datetime.strptime(d, '%Y-%m-%d').weekday()]
    print(f'  {d} ({wd})')

print(f'\n💾 작업일지_데이터.json 저장 완료!')
