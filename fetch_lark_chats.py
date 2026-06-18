#!/usr/bin/env python3
"""
하이디라오 영등포점 — Lark 시공 그룹 채팅 데이터 수집 스크립트

사용법:
  python3 fetch_lark_chats.py --app-id <APP_ID> --app-secret <APP_SECRET>

기능:
  1. Lark API 인증 (tenant_access_token)
  2. 채팅 그룹 목록에서 시공 그룹 찾기
  3. 메시지 수집 및 날짜별 그룹화
  4. 이벤트 트래커용 JSON 출력
"""

import argparse
import json
import sys
import os
from datetime import datetime, timezone, timedelta
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

KST = timezone(timedelta(hours=9))

# === Lark API 설정 ===
LARK_DOMAIN = "https://open.larksuite.com"
FEISHU_DOMAIN = "https://open.feishu.cn"

# 시공 그룹 키워드 (그룹 이름에 포함된 단어로 검색)
GROUP_KEYWORDS = ["海底捞", "永登浦", "施工", "하이디라오"]


def api_request(url, token=None, method="GET", data=None):
    """Lark API 요청 유틸리티"""
    headers = {"Content-Type": "application/json; charset=utf-8"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    body = json.dumps(data).encode("utf-8") if data else None
    req = Request(url, data=body, headers=headers, method=method)

    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        error_body = e.read().decode("utf-8")
        print(f"❌ HTTP 오류 {e.code}: {error_body}", file=sys.stderr)
        return {"code": e.code, "msg": error_body}
    except URLError as e:
        print(f"❌ 연결 오류: {e.reason}", file=sys.stderr)
        return {"code": -1, "msg": str(e.reason)}


def get_tenant_token(app_id, app_secret, domain=LARK_DOMAIN):
    """Tenant Access Token 발급"""
    url = f"{domain}/open-apis/auth/v3/tenant_access_token/internal"
    result = api_request(url, method="POST", data={
        "app_id": app_id,
        "app_secret": app_secret
    })

    if result.get("code") == 0 or "tenant_access_token" in result:
        token = result.get("tenant_access_token")
        expire = result.get("expire", 0)
        print(f"✅ 토큰 발급 성공 (만료: {expire}초)")
        return token
    else:
        # Larksuite 실패 시 Feishu 도메인으로 재시도
        if domain == LARK_DOMAIN:
            print(f"⚠️  Larksuite 도메인 실패, Feishu 도메인으로 재시도...")
            return get_tenant_token(app_id, app_secret, FEISHU_DOMAIN)
        print(f"❌ 토큰 발급 실패: {result.get('msg')}")
        return None


def list_chats(token, domain=LARK_DOMAIN):
    """채팅 그룹 목록 조회"""
    all_chats = []
    page_token = ""

    while True:
        params = {"page_size": 100}
        if page_token:
            params["page_token"] = page_token

        url = f"{domain}/open-apis/im/v1/chats?{urlencode(params)}"
        result = api_request(url, token=token)

        if result.get("code") != 0:
            print(f"❌ 채팅 목록 조회 실패: {result.get('msg')}")
            break

        items = result.get("data", {}).get("items", [])
        all_chats.extend(items)

        if not result.get("data", {}).get("has_more"):
            break
        page_token = result.get("data", {}).get("page_token", "")

    print(f"📋 총 {len(all_chats)}개 채팅 그룹 발견")
    return all_chats


def find_construction_group(chats):
    """시공 그룹 찾기"""
    matches = []
    for chat in chats:
        name = chat.get("name", "")
        desc = chat.get("description", "")
        combined = f"{name} {desc}"

        if any(kw in combined for kw in GROUP_KEYWORDS):
            matches.append(chat)
            print(f"  🔍 매칭: [{chat.get('chat_id')}] {name}")

    if not matches:
        print("⚠️  시공 그룹을 찾을 수 없습니다.")
        print("    그룹 이름에 다음 키워드가 포함되어야 합니다:", GROUP_KEYWORDS)
        print("\n    발견된 모든 그룹:")
        for chat in chats:
            print(f"      - [{chat.get('chat_id')}] {chat.get('name', '(이름 없음)')}")

    return matches


def get_messages(token, chat_id, start_time=None, end_time=None, domain=LARK_DOMAIN):
    """채팅 메시지 수집"""
    all_messages = []
    page_token = ""

    while True:
        params = {
            "container_id_type": "chat",
            "container_id": chat_id,
            "page_size": 50,
            "sort_type": "ByCreateTimeAsc"
        }
        if start_time:
            params["start_time"] = start_time
        if end_time:
            params["end_time"] = end_time
        if page_token:
            params["page_token"] = page_token

        url = f"{domain}/open-apis/im/v1/messages?{urlencode(params)}"
        result = api_request(url, token=token)

        if result.get("code") != 0:
            print(f"❌ 메시지 조회 실패: {result.get('msg')}")
            break

        items = result.get("data", {}).get("items", [])
        all_messages.extend(items)
        print(f"  📨 {len(all_messages)}개 메시지 수집 중...", end="\r")

        if not result.get("data", {}).get("has_more"):
            break
        page_token = result.get("data", {}).get("page_token", "")

    print(f"\n✅ 총 {len(all_messages)}개 메시지 수집 완료")
    return all_messages


def parse_message_content(msg):
    """메시지 내용 파싱"""
    msg_type = msg.get("msg_type", "")
    body = msg.get("body", {})
    content_str = body.get("content", "{}")

    try:
        content = json.loads(content_str)
    except (json.JSONDecodeError, TypeError):
        content = {"text": content_str}

    if msg_type == "text":
        return content.get("text", "")
    elif msg_type == "post":
        # 리치 텍스트 — 중첩 구조에서 텍스트 추출
        texts = []
        title = content.get("title", "")
        if title:
            texts.append(title)
        for lang_content in content.values():
            if isinstance(lang_content, list):
                for paragraph in lang_content:
                    if isinstance(paragraph, list):
                        for element in paragraph:
                            if isinstance(element, dict) and element.get("tag") == "text":
                                texts.append(element.get("text", ""))
        return "\n".join(texts)
    elif msg_type == "image":
        return "[이미지]"
    elif msg_type == "file":
        return f"[파일: {content.get('file_name', '알 수 없음')}]"
    elif msg_type == "interactive":
        return "[카드 메시지]"
    else:
        return f"[{msg_type} 메시지]"


def group_messages_by_date(messages):
    """메시지를 날짜별로 그룹화"""
    date_groups = {}

    for msg in messages:
        # create_time은 Unix timestamp (밀리초 또는 초)
        create_time = msg.get("create_time", "0")
        try:
            ts = int(create_time)
            if ts > 1e12:  # 밀리초
                ts = ts / 1000
            dt = datetime.fromtimestamp(ts, tz=KST)
        except (ValueError, OSError):
            continue

        date_str = dt.strftime("%Y-%m-%d")
        if date_str not in date_groups:
            date_groups[date_str] = []

        sender = msg.get("sender", {})
        sender_name = sender.get("sender_id", {}).get("user_id", "알 수 없음")

        content = parse_message_content(msg)
        if not content or content.strip() == "":
            continue

        date_groups[date_str].append({
            "time": dt.strftime("%H:%M"),
            "sender": sender_name,
            "content": content,
            "msg_type": msg.get("msg_type", "unknown")
        })

    return date_groups


def generate_events(date_groups, start_evt_id=33):
    """날짜별 그룹화된 메시지를 이벤트 트래커 형식으로 변환"""
    events = []
    evt_num = start_evt_id

    for date_str in sorted(date_groups.keys()):
        msgs = date_groups[date_str]
        if len(msgs) == 0:
            continue

        # 텍스트 메시지만 필터
        text_msgs = [m for m in msgs if m["msg_type"] in ("text", "post")]
        if len(text_msgs) == 0:
            continue

        # 요약 생성 (처음 3개 메시지)
        preview_texts = [m["content"][:80] for m in text_msgs[:3]]
        summary = " | ".join(preview_texts)
        if len(summary) > 120:
            summary = summary[:117] + "..."

        # 상세 내용 (전체 대화)
        detail_lines = []
        for m in text_msgs:
            content_preview = m["content"]
            if len(content_preview) > 200:
                content_preview = content_preview[:197] + "..."
            detail_lines.append(f"[{m['time']}] {content_preview}")

        details = "\n".join(detail_lines)

        evt_id = f"EVT-{evt_num:03d}"
        events.append({
            "id": evt_id,
            "date": date_str,
            "category": "chat",
            "title": f"라크 시공 그룹 대화 — {date_str}",
            "summary": summary,
            "details": details,
            "decisions": [],
            "linkedEvents": [],
            "source": "Lark 시공그룹 채팅"
        })

        evt_num += 1

    return events


def main():
    parser = argparse.ArgumentParser(
        description="하이디라오 Lark 시공 그룹 채팅 수집기"
    )
    parser.add_argument("-a", "--app-id", required=True, help="Lark App ID")
    parser.add_argument("-s", "--app-secret", required=True, help="Lark App Secret")
    parser.add_argument("-d", "--domain", default=LARK_DOMAIN,
                        help=f"Lark API 도메인 (기본값: {LARK_DOMAIN})")
    parser.add_argument("--chat-id", help="특정 채팅 그룹 ID (생략 시 자동 검색)")
    parser.add_argument("--start-date", help="시작 날짜 (YYYY-MM-DD, 기본값: 2026-04-01)")
    parser.add_argument("--end-date", help="종료 날짜 (YYYY-MM-DD, 기본값: 오늘)")
    parser.add_argument("--start-evt-id", type=int, default=33,
                        help="시작 이벤트 번호 (기본값: 33)")
    parser.add_argument("-o", "--output", default="lark_chat_events.json",
                        help="출력 파일명 (기본값: lark_chat_events.json)")
    parser.add_argument("--list-only", action="store_true",
                        help="채팅 그룹 목록만 출력")

    args = parser.parse_args()

    # 1. 인증
    print("=" * 50)
    print("🔐 Lark API 인증 중...")
    token = get_tenant_token(args.app_id, args.app_secret, args.domain)
    if not token:
        print("\n💡 해결 방법:")
        print("   1. Lark 개발자 콘솔에서 App Secret 확인/재발급")
        print("   2. 앱에 im:chat:readonly, im:message:readonly 권한 확인")
        print("   3. 앱 봇이 시공 그룹에 추가되어 있는지 확인")
        sys.exit(1)

    # 2. 채팅 그룹 목록
    print("\n📋 채팅 그룹 조회 중...")
    chats = list_chats(token, args.domain)

    if args.list_only:
        print("\n=== 채팅 그룹 목록 ===")
        for chat in chats:
            print(f"  [{chat.get('chat_id')}] {chat.get('name', '(이름 없음)')}")
        sys.exit(0)

    # 3. 시공 그룹 찾기
    chat_id = args.chat_id
    if not chat_id:
        print("\n🔍 시공 그룹 검색 중...")
        matches = find_construction_group(chats)
        if not matches:
            print("\n💡 --chat-id 옵션으로 그룹 ID를 직접 지정할 수 있습니다.")
            sys.exit(1)
        chat_id = matches[0].get("chat_id")
        print(f"  ✅ 사용할 그룹: {matches[0].get('name')} ({chat_id})")

    # 4. 메시지 수집
    start_date = args.start_date or "2026-04-01"
    end_date = args.end_date or datetime.now(KST).strftime("%Y-%m-%d")

    start_ts = str(int(datetime.strptime(start_date, "%Y-%m-%d")
                       .replace(tzinfo=KST).timestamp()))
    end_ts = str(int(datetime.strptime(end_date, "%Y-%m-%d")
                     .replace(tzinfo=KST)
                     .replace(hour=23, minute=59, second=59).timestamp()))

    print(f"\n📨 메시지 수집 중 ({start_date} ~ {end_date})...")
    messages = get_messages(token, chat_id, start_ts, end_ts, args.domain)

    if not messages:
        print("⚠️  수집된 메시지가 없습니다.")
        sys.exit(0)

    # 5. 날짜별 그룹화
    print("\n📊 날짜별 그룹화 중...")
    date_groups = group_messages_by_date(messages)
    print(f"  📅 {len(date_groups)}일간의 대화 발견")

    # 6. 이벤트 생성
    print("\n🏗️ 이벤트 데이터 생성 중...")
    events = generate_events(date_groups, args.start_evt_id)
    print(f"  ✅ {len(events)}개 이벤트 생성")

    # 7. 저장
    output_path = os.path.join(os.path.dirname(__file__), args.output)
    output_data = {
        "project": "하이디라오 영등포점",
        "source": "Lark 시공그룹 채팅",
        "chat_id": chat_id,
        "period": f"{start_date} ~ {end_date}",
        "collected_at": datetime.now(KST).isoformat(),
        "total_messages": len(messages),
        "total_events": len(events),
        "events": events
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)

    print(f"\n💾 저장 완료: {output_path}")
    print(f"   총 메시지: {len(messages)}개")
    print(f"   생성 이벤트: {len(events)}개")
    print(f"   기간: {start_date} ~ {end_date}")

    # JS 코드 스니펫 출력
    print("\n" + "=" * 50)
    print("📋 이벤트 트래커에 추가하려면 다음 JSON 데이터를 사용하세요:")
    print("=" * 50)

    for evt in events[:3]:
        print(json.dumps(evt, ensure_ascii=False, indent=2))
    if len(events) > 3:
        print(f"\n... 외 {len(events) - 3}개 이벤트 (전체 내용은 {args.output} 참조)")


if __name__ == "__main__":
    main()
