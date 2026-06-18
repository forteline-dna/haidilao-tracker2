#!/usr/bin/env python3
import json
import os
import re
import unicodedata
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.parse
import time

KST = timezone(timedelta(hours=9))

# Normalized directory names for macOS (NFD)
def get_nfd_path(path):
    return unicodedata.normalize('NFD', path)

BASE_DIR = '/Users/jason-mac/Documents/안티그래비티/0616 lark mcp연결'
RAW_MSG_FILE = os.path.join(BASE_DIR, 'lark_raw_messages.json')
OUTPUT_DIR = get_nfd_path(os.path.join(BASE_DIR, '라크 대화내용'))
MOM_DIR = get_nfd_path(os.path.join(BASE_DIR, '회의록'))

# Find Drawings directory dynamically since it may have trailing spaces in filesystem
drawing_dirs = [d for d in os.listdir(BASE_DIR) if d.startswith(unicodedata.normalize('NFD', '도면수정내용'))]
DRAWING_DIR = get_nfd_path(os.path.join(BASE_DIR, drawing_dirs[0])) if drawing_dirs else get_nfd_path(os.path.join(BASE_DIR, '도면수정내용 '))

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Translation Cache
CACHE_FILE = os.path.join(BASE_DIR, 'translation_cache.json')
translation_cache = {}
if os.path.exists(CACHE_FILE):
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            translation_cache = json.load(f)
        print(f"Loaded {len(translation_cache)} translations from cache.")
    except Exception as e:
        print(f"Error loading cache: {e}")

def save_cache():
    try:
        with open(CACHE_FILE, 'w', encoding='utf-8') as f:
            json.dump(translation_cache, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving cache: {e}")

def translate_to_korean(text):
    if not text or not text.strip():
        return ""
    
    # Check if contains Chinese characters
    if not re.search(r'[\u4e00-\u9fff]', text):
        return ""
        
    if text in translation_cache:
        return translation_cache[text]
        
    max_retries = 3
    for attempt in range(max_retries):
        try:
            q = urllib.parse.quote(text)
            url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl=ko&dt=t&q={q}"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                parts = [x[0] for x in data[0] if x and isinstance(x, list) and len(x) > 0 and isinstance(x[0], str)]
                translated = "".join(parts)
                if translated:
                    translation_cache[text] = translated
                    save_cache()
                    print(f"Translated (Attempt {attempt+1}): {text[:20]}... -> {translated[:20]}...")
                    time.sleep(0.2)
                    return translated
        except Exception as e:
            wait_time = 2 ** attempt
            print(f"Error translating '{text[:20]}...' (Attempt {attempt+1}/{max_retries}): {e}. Waiting {wait_time}s...")
            time.sleep(wait_time)
            
    return ""

# 1. Load Messages
print("📂 Loading lark_raw_messages.json...")
if not os.path.exists(RAW_MSG_FILE):
    print(f"❌ Error: {RAW_MSG_FILE} not found!")
    exit(1)

with open(RAW_MSG_FILE, 'r', encoding='utf-8') as f:
    messages = json.load(f)

# 2. Extract User ID to Name Map
user_map = {
    'cli_a6ba21656ff1d00e': 'Lark Doc Bot',
    'cli_a96624c60d795cc0': 'Lark Calendar Bot',
    'ou_dcf810368fcf1ea9ea36fe91798e59cf': '사용자 (dcf81036)'
}

for msg in messages:
    for m in msg.get('mentions', []):
        uid = m.get('id')
        name = m.get('name')
        if uid and name:
            user_map[uid] = name

print(f"👤 Resolved {len(user_map)} users/bots from mentions and defaults.")

# 3. Message Content Parser
def parse_message_content(msg, user_map):
    msg_type = msg.get("msg_type", "")
    body = msg.get("body", {})
    content_str = body.get("content", "{}")
    
    if msg.get("deleted"):
        return "_[회수된 메시지]_"
        
    try:
        content = json.loads(content_str)
    except:
        content = content_str

    if isinstance(content, str):
        return content

    if msg_type == "text":
        return content.get("text", "")
    elif msg_type == "post":
        title = content.get("title", "")
        paragraphs = content.get("content", [])
        lines = []
        if title:
            lines.append(f"**{title}**")
        
        for para in paragraphs:
            para_text = ""
            for el in para:
                tag = el.get("tag")
                if tag == "text":
                    para_text += el.get("text", "")
                elif tag == "a":
                    para_text += f"[{el.get('text', '')}]({el.get('href', '')})"
                elif tag == "at":
                    at_id = el.get("user_id", "")
                    at_name = el.get("user_name", "") or user_map.get(at_id, at_id)
                    para_text += f"@{at_name}"
                elif tag == "img":
                    para_text += "[🖼️ 이미지]"
            if para_text:
                lines.append(para_text)
        return "\n".join(lines)
    elif msg_type == "image":
        return f"[🖼️ 이미지 첨부]"
    elif msg_type == "file":
        return f"[📁 파일 첨부: {content.get('file_name', '알 수 없음')}]"
    elif msg_type == "media":
        return f"[🎥 미디어 첨부: {content.get('file_name', '알 수 없음')}]"
    elif msg_type == "audio":
        return f"[🎵 음성 메시지]"
    elif msg_type == "interactive":
        header = content.get("header", {}).get("title", {}).get("content", "")
        texts = []
        if header:
            texts.append(f"**{header}**")
        
        def extract_interactive_texts(obj):
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k in ["text", "content"] and isinstance(v, str):
                        texts.append(v)
                    else:
                        extract_interactive_texts(v)
            elif isinstance(obj, list):
                for item in obj:
                    extract_interactive_texts(item)
        extract_interactive_texts(content)
        if texts:
            return "\n".join(texts)
        return "[📇 카드 메시지]"
    else:
        return f"[{msg_type} 타입 메시지]"

def resolve_mentions(text, mentions):
    if not mentions or not text:
        return text
    for m in mentions:
        key = m.get("key")
        name = m.get("name")
        if key and name:
            text = text.replace(key, f"@{name}")
    return text

# 4. Find Related Files Helper
def find_related_files(date_str):
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return []
        
    patterns = [
        date_str,
        dt.strftime("%Y.%m.%d"),
        dt.strftime("%Y%m%d"),
        dt.strftime("%y%m%d"),
        dt.strftime("%m%d"),  # MMDD (e.g. 0512 or 0507)
    ]
    
    related = []
    
    # Helper to check if filename contains pattern
    def matches_patterns(name):
        # normalize to NFD for proper comparison on mac
        norm_name = unicodedata.normalize('NFD', name)
        return any(p in norm_name for p in patterns)
    
    # Scan MoM directory
    if os.path.exists(MOM_DIR):
        for name in os.listdir(MOM_DIR):
            if matches_patterns(name):
                related.append({
                    "type": "회의록",
                    "name": name,
                    "relative_path": f"../회의록/{name}"
                })
                
    # Scan Drawings directory
    if os.path.exists(DRAWING_DIR):
        for name in os.listdir(DRAWING_DIR):
            if matches_patterns(name):
                related.append({
                    "type": "설계변경",
                    "name": name,
                    "relative_path": f"../도면수정내용/{name}"
                })
                
    return related

# 5. Group Messages by Date
print("Grouping and translating messages...")
daily_chats = {}
for msg in messages:
    ts = int(msg.get('create_time', '0'))
    if ts > 1e12:
        ts /= 1000
    try:
        dt = datetime.fromtimestamp(ts, tz=KST)
    except:
        continue
    
    date_str = dt.strftime('%Y-%m-%d')
    if date_str not in daily_chats:
        daily_chats[date_str] = []
        
    sender_id = msg.get("sender", {}).get("id")
    msg_type = msg.get("msg_type")
    if msg_type == "system":
        sender_name = "System"
    else:
        sender_name = user_map.get(sender_id, f"사용자 ({sender_id[:8]})" if sender_id else "알 수 없음")
    
    text = parse_message_content(msg, user_map)
    text = resolve_mentions(text, msg.get("mentions", []))
    
    # Translate text if it contains Chinese characters
    translated = translate_to_korean(text.strip())
    
    daily_chats[date_str].append({
        "time": dt.strftime('%H:%M'),
        "sender": sender_name,
        "content": text.strip(),
        "translated_content": translated,
        "msg_type": msg.get("msg_type")
    })

print(f"📅 Grouped messages into {len(daily_chats)} days.")

# Save final translation cache
save_cache()

# 6. Generate Daily Markdown Files
sorted_dates = sorted(daily_chats.keys())
index_entries = []

for date_str in sorted_dates:
    chat_list = daily_chats[date_str]
    msg_count = len(chat_list)
    if msg_count == 0:
        continue
        
    # Find participants
    participants = sorted(list(set(c["sender"] for c in chat_list)))
    
    # Find related documents
    related_docs = find_related_files(date_str)
    
    # Day of week
    weekday_kr = ['월요일', '화요일', '수요일', '목요일', '금요일', '토요일', '일요일'][datetime.strptime(date_str, "%Y-%m-%d").weekday()]
    
    filename = f"{date_str}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    # Write Daily Chat Log
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(f"# 💬 라크 시공 그룹 대화 — {date_str} ({weekday_kr})\n\n")
        
        # Meta info block
        f.write("> **[일일 요약 정보]**\n")
        f.write(f"> - **날짜**: {date_str} ({weekday_kr})\n")
        f.write(f"> - **총 메시지**: {msg_count}건\n")
        f.write(f"> - **참여자**: {', '.join(participants)}\n")
        
        if related_docs:
            f.write("> - **관련 문서**:\n")
            for doc in related_docs:
                f.write(f">   - [{doc['type']}] [{doc['name']}]({doc['relative_path']})\n")
        f.write("\n---\n\n")
        
        # Chat log list
        for chat in chat_list:
            content = chat["content"]
            translated = chat.get("translated_content", "")
            
            if "\n" in content:
                # Multiline content formatting
                lines = content.split("\n")
                content_str = "\n" + "\n".join(f"  > {line}" for line in lines)
                if translated:
                    # Append translation at the end of the block (avoiding backslash in f-string)
                    translated_escaped = translated.replace("\n", "\n  > ")
                    content_str += "\n  > \n  > 🌐 **번역**: " + translated_escaped
            else:
                content_str = f" {content}"
                if translated:
                    # Append translation on the next line (avoiding backslash in f-string)
                    translated_escaped = translated.replace("\n", "\n  > ")
                    content_str += f"\n  > 🌐 **번역**: {translated_escaped}"
                    
            f.write(f"- **[{chat['time']}] {chat['sender']}**:{content_str}\n")
            
    # Record for index
    index_entries.append({
        "date": date_str,
        "weekday": weekday_kr,
        "count": msg_count,
        "participants": participants,
        "related_docs": related_docs,
        "link": f"./{filename}"
    })
    print(f"✍️ Written {filename} with {msg_count} messages.")

# 7. Generate README.md Index
readme_path = os.path.join(OUTPUT_DIR, 'README.md')
with open(readme_path, 'w', encoding='utf-8') as f:
    f.write("# 📂 Lark 시공 그룹 대화록 아카이브\n\n")
    f.write("이 폴더는 하이디라오 영등포점 시공과 관련된 Lark 단체 채팅방의 전체 대화 기록을 날짜별로 보관하고 있습니다.\n\n")
    
    # Project Info
    f.write("## 📌 프로젝트 정보\n")
    f.write("- **프로젝트명**: 하이디라오 영등포점 시공\n")
    f.write(f"- **아카이브 기간**: {sorted_dates[0]} ~ {sorted_dates[-1]}\n")
    f.write(f"- **총 대화수**: {len(messages)}건\n")
    f.write(f"- **참여자 수**: {len(user_map)}명/봇\n\n")
    
    # Participants List
    f.write("## 👥 전체 참여자 목록\n")
    for uid, name in sorted(user_map.items(), key=lambda x: x[1]):
        if 'Bot' in name:
            f.write(f"- `{name}` (자동 알림 봇)\n")
        else:
            f.write(f"- **{name}** (`{uid}`)\n")
    f.write("\n")
    
    # Table of Contents
    f.write("## 📅 날짜별 대화 목록\n\n")
    f.write("| 날짜 | 요일 | 메시지 수 | 주요 참여자 | 관련 회의록 / 설계변경 |\n")
    f.write("| :--- | :--- | :---: | :--- | :--- |\n")
    for entry in index_entries:
        parts_str = ", ".join(entry["participants"][:4])
        if len(entry["participants"]) > 4:
            parts_str += f" 외 {len(entry['participants'])-4}명"
            
        doc_links = []
        for doc in entry["related_docs"]:
            doc_links.append(f"[{doc['type']}]({doc['relative_path']})")
        doc_str = ", ".join(doc_links) if doc_links else "-"
        
        f.write(f"| [{entry['date']}]({entry['link']}) | {entry['weekday'][:3]} | {entry['count']} | {parts_str} | {doc_str} |\n")

print("📝 Created README.md index.")
print("✨ Done!")
