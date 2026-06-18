#!/usr/bin/env python3
"""
기존 이벤트와 채팅 이벤트를 날짜/키워드 기반으로 연결하고,
이벤트 트래커 HTML에 삽입할 최종 JS 코드를 생성합니다.
"""
import json

# ── 기존 이벤트 날짜/주제 매핑 ──
existing_events = {
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

# ── 채팅 이벤트에서 키워드 추출 및 매칭 ──
with open("lark_messages_by_date.json", encoding="utf-8") as f:
    date_groups = json.load(f)

# 주제 키워드 매핑 (중국어/한국어 → 기존 이벤트 토픽)
keyword_map = {
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
    "CCTV": "CCTV", "스피커": "스피커",
}

significant = []
for date_str in sorted(date_groups.keys()):
    msgs = date_groups[date_str]
    if len(msgs) < 20:
        continue
    significant.append((date_str, msgs))

evt_num = 33
chat_events = []

for date_str, msgs in significant:
    all_text = " ".join([m["text"] for m in msgs])

    # 채팅에서 발견된 토픽 추출
    found_topics = set()
    for kw, topic in keyword_map.items():
        if kw in all_text:
            found_topics.add(topic)

    # 기존 이벤트와 매칭
    linked = []
    for evt_id, info in existing_events.items():
        evt_date = info["date"]
        evt_topics = set(info["topics"])

        # 1. 같은 날짜 → 무조건 연결
        if evt_date == date_str:
            linked.append(evt_id)
            continue

        # 2. 근접 날짜 (±3일) + 토픽 매칭 → 연결
        from datetime import datetime
        chat_dt = datetime.strptime(date_str, "%Y-%m-%d")
        evt_dt = datetime.strptime(evt_date, "%Y-%m-%d")
        day_diff = abs((chat_dt - evt_dt).days)

        common_topics = found_topics & evt_topics
        if day_diff <= 3 and len(common_topics) >= 1:
            linked.append(evt_id)
        # 3. 토픽이 2개 이상 겹치면 먼 날짜도 연결
        elif len(common_topics) >= 2:
            linked.append(evt_id)

    # 중복 제거, 정렬
    linked = sorted(set(linked), key=lambda x: int(x.split("-")[1]))

    evt_id = f"EVT-{evt_num:03d}"

    # 상세 내용 구성
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

    entry = "  {\n"
    entry += f'    id: "{evt_id}", date: "{date_str}", category: "chat",\n'
    entry += f'    title: "라크 시공 그룹 대화 — {date_str} ({len(msgs)}건)",\n'
    entry += f'    summary: "{summary}",\n'
    entry += f'    details: `시공 그룹 채팅 ({len(msgs)}건):\\n\\n{details}`,\n'
    entry += "    decisions: [],\n"
    entry += f"    linkedEvents: [{linked_str}],\n"
    entry += '    source: "Lark 시공그룹 채팅"\n'
    entry += "  }"

    chat_events.append({
        "id": evt_id,
        "date": date_str,
        "count": len(msgs),
        "linked": linked,
        "js": entry,
    })
    evt_num += 1

# ── 기존 이벤트 → 채팅 역방향 연결도 수집 ──
reverse_links = {}  # EVT-00X → [EVT-033, EVT-034, ...]
for ce in chat_events:
    for linked_id in ce["linked"]:
        if linked_id not in reverse_links:
            reverse_links[linked_id] = []
        reverse_links[linked_id].append(ce["id"])

print("=" * 60)
print("📊 채팅 ↔ 기존 이벤트 연결 결과")
print("=" * 60)

for ce in chat_events:
    linked_str = ", ".join(ce["linked"]) if ce["linked"] else "(없음)"
    print(f'\n{ce["id"]} ({ce["date"]}, {ce["count"]}건):')
    print(f'  → 연결된 기존 이벤트: {linked_str}')

print("\n" + "=" * 60)
print("📋 기존 이벤트 → 채팅 역방향 연결")
print("=" * 60)
for evt_id in sorted(reverse_links.keys(), key=lambda x: int(x.split("-")[1])):
    chats = reverse_links[evt_id]
    print(f'  {evt_id} ← {", ".join(chats)}')

# ── JS 코드 저장 ──
js_code = ",\n\n".join([ce["js"] for ce in chat_events])
with open("chat_events_linked.txt", "w", encoding="utf-8") as f:
    f.write(js_code)

# builtInIds
all_ids = [f"'EVT-{i:03d}'" for i in range(1, evt_num)]
with open("builtin_ids_final.txt", "w", encoding="utf-8") as f:
    f.write(", ".join(all_ids))

# 역방향 연결 저장
with open("reverse_links.json", "w", encoding="utf-8") as f:
    json.dump(reverse_links, f, ensure_ascii=False, indent=2)

print(f"\n💾 chat_events_linked.txt 저장 ({len(chat_events)}개 이벤트)")
print(f"💾 builtin_ids_final.txt 저장 (EVT-001 ~ EVT-{evt_num-1:03d})")
print(f"💾 reverse_links.json 저장 ({len(reverse_links)}개 역방향 연결)")
