#!/usr/bin/env python3
"""라크 채팅 데이터 → 이벤트 트래커 JS 코드 생성"""
import json

with open('lark_messages_by_date.json', encoding='utf-8') as f:
    date_groups = json.load(f)

# 20건 이상 활발한 날짜만 선별
significant = []
for date_str in sorted(date_groups.keys()):
    msgs = date_groups[date_str]
    if len(msgs) < 20:
        continue
    significant.append((date_str, msgs))

print(f'{len(significant)}개 주요 대화일 선별 (20건 이상)')

evt_num = 33
js_entries = []

for date_str, msgs in significant:
    # 상세 내용 구성
    detail_lines = []
    for m in msgs[:15]:
        text = m['text'][:120].replace('`', "'").replace('\\', '').replace('\n', ' ')
        detail_lines.append(f"[{m['time']}] {text}")
    
    if len(msgs) > 15:
        detail_lines.append(f'... 외 {len(msgs)-15}건')
    
    details = '\\n'.join(detail_lines)
    
    # 요약
    summary_texts = [m['text'][:40].replace('"', "'").replace('\n', ' ') for m in msgs[:3]]
    summary = f'{len(msgs)}건 대화 — ' + ' | '.join(summary_texts)
    if len(summary) > 120:
        summary = summary[:117] + '...'
    
    evt_id = f'EVT-{evt_num:03d}'
    
    entry = '  {\n'
    entry += f'    id: "{evt_id}", date: "{date_str}", category: "chat",\n'
    entry += f'    title: "라크 시공 그룹 대화 — {date_str} ({len(msgs)}건)",\n'
    entry += f'    summary: "{summary}",\n'
    entry += f'    details: `시공 그룹 채팅 ({len(msgs)}건):\\n\\n{details}`,\n'
    entry += '    decisions: [],\n'
    entry += '    linkedEvents: [],\n'
    entry += '    source: "Lark 시공그룹 채팅"\n'
    entry += '  }'
    
    js_entries.append(entry)
    evt_num += 1

print(f'이벤트 ID 범위: EVT-033 ~ EVT-{evt_num-1:03d}')
print(f'총 {len(js_entries)}개 채팅 이벤트')

# JS 코드 저장
js_code = ',\n\n'.join(js_entries)
with open('chat_events_js.txt', 'w', encoding='utf-8') as f:
    f.write(js_code)

# builtInIds 저장
all_ids = [f"'EVT-{i:03d}'" for i in range(1, evt_num)]
with open('builtin_ids.txt', 'w', encoding='utf-8') as f:
    f.write(', '.join(all_ids))

print(f'\n💾 chat_events_js.txt, builtin_ids.txt 저장됨')
