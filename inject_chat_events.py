#!/usr/bin/env python3
"""
하이디라오_이벤트트래커.html에 채팅 이벤트 추가 및 역방향 링크 삽입
"""
import json, re

HTML_PATH = "/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결/하이디라오_이벤트트래커.html"

# 파일 읽기
with open(HTML_PATH, "r", encoding="utf-8") as f:
    html = f.read()

# 1. 채팅 이벤트 JS 코드 읽기
with open("chat_events_linked.txt", "r", encoding="utf-8") as f:
    chat_js = f.read()

# 2. 역방향 링크 읽기
with open("reverse_links.json", "r", encoding="utf-8") as f:
    reverse_links = json.load(f)

# 3. builtInIds 읽기
with open("builtin_ids_final.txt", "r", encoding="utf-8") as f:
    builtin_ids = f.read().strip()

# === STEP 1: EVENTS 배열 끝에 채팅 이벤트 삽입 ===
# "EVT-032" 이벤트의 닫는 중괄호와 배열 닫기 ]; 사이에 삽입
old_end = """    source: "2026.05.19 회의록.docx"
  }
];"""
new_end = f"""    source: "2026.05.19 회의록.docx"
  }},

  // ── 라크 시공 그룹 채팅 이벤트 (자동 수집) ──
{chat_js}
];"""

if old_end in html:
    html = html.replace(old_end, new_end)
    print("✅ 채팅 이벤트 21개 삽입 완료")
else:
    print("❌ EVENTS 배열 끝 패턴을 찾을 수 없음")
    # 디버깅
    idx = html.find('source: "2026.05.19 회의록.docx"')
    if idx >= 0:
        print(f"  발견 위치: {idx}")
        print(f"  주변 텍스트: {repr(html[idx:idx+100])}")

# === STEP 2: 기존 이벤트에 역방향 linkedEvents 추가 ===
for evt_id, chat_ids in reverse_links.items():
    # 현재 linkedEvents 배열을 찾아서 채팅 이벤트 ID 추가
    pattern = f'id: "{evt_id}"'
    idx = html.find(pattern)
    if idx < 0:
        print(f"  ⚠️ {evt_id} 못 찾음")
        continue

    # 이 이벤트의 linkedEvents 배열 찾기
    search_start = idx
    search_end = html.find("source:", search_start)
    if search_end < 0:
        continue

    section = html[search_start:search_end]
    linked_match = re.search(r'linkedEvents:\s*\[([^\]]*)\]', section)
    if not linked_match:
        continue

    old_linked = linked_match.group(1).strip()
    # 이미 있는 ID 파싱
    existing_ids = [s.strip().strip('"').strip("'") for s in old_linked.split(",") if s.strip()]
    # 새 채팅 ID 추가 (중복 방지)
    for cid in chat_ids:
        if cid not in existing_ids:
            existing_ids.append(cid)

    new_linked = ", ".join([f'"{e}"' for e in existing_ids])
    old_full = linked_match.group(0)
    new_full = f"linkedEvents: [{new_linked}]"

    html = html[:search_start] + section.replace(old_full, new_full) + html[search_end:]
    print(f"  🔗 {evt_id}: +{len(chat_ids)}개 채팅 링크 추가")

# === STEP 3: builtInIds 업데이트 ===
old_builtin_pattern = re.search(
    r"const builtInIds = new Set\(\[\s*(.*?)\s*\]\);",
    html,
    re.DOTALL
)
if old_builtin_pattern:
    old_section = old_builtin_pattern.group(0)
    new_section = f"const builtInIds = new Set([{builtin_ids}]);"
    # Wrap nicely
    ids_list = builtin_ids.split(", ")
    lines = []
    for i in range(0, len(ids_list), 8):
        chunk = ", ".join(ids_list[i:i+8])
        lines.append(f"    {chunk}")
    formatted_ids = ",\n".join(lines)
    new_section = f"const builtInIds = new Set([\n{formatted_ids}\n  ]);"
    html = html.replace(old_section, new_section)
    print(f"\n✅ builtInIds 업데이트: {len(ids_list)}개 ID")

# === 저장 ===
with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n🎉 하이디라오_이벤트트래커.html 업데이트 완료!")
print(f"  - 채팅 이벤트 21개 추가 (EVT-033 ~ EVT-053)")
print(f"  - 기존 19개 이벤트에 역방향 링크 추가")
print(f"  - builtInIds 업데이트")
