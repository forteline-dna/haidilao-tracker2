#!/usr/bin/env python3
"""
Lark OAuth 로그인 & 채팅 데이터 수집 통합 스크립트
- 자체 OAuth 서버로 User Access Token 발급
- 시공 그룹 채팅 메시지 수집
"""

import http.server
import json
import sys
import webbrowser
import threading
import time
from urllib.request import Request, urlopen
from urllib.parse import urlencode, urlparse, parse_qs

APP_ID = "cli_a97aa70eeca15e15"
APP_SECRET = "l37gyqepLXhdTjLW7L9UngWh5jV6jtQw"
DOMAIN = "https://open.larksuite.com"
REDIRECT_URI = "http://localhost:9876/callback"
PORT = 9876

# 결과 저장
auth_result = {"code": None, "token": None, "error": None}


class OAuthHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/callback":
            params = parse_qs(parsed.query)
            if "code" in params:
                auth_result["code"] = params["code"][0]
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write("✅ 인증 성공! 이 창을 닫아도 됩니다.".encode("utf-8"))
            else:
                error = params.get("error", ["unknown"])[0]
                error_desc = params.get("error_description", [""])[0]
                auth_result["error"] = f"{error}: {error_desc}"
                self.send_response(400)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.end_headers()
                self.wfile.write(f"❌ 인증 실패: {error} - {error_desc}".encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format, *args):
        pass  # 로그 억제


def get_user_token(code):
    """Authorization Code → User Access Token"""
    url = f"{DOMAIN}/open-apis/authen/v1/oidc/access_token"
    data = json.dumps({
        "grant_type": "authorization_code",
        "code": code
    }).encode("utf-8")

    # 먼저 app_access_token 발급
    app_token_url = f"{DOMAIN}/open-apis/auth/v3/app_access_token/internal"
    app_data = json.dumps({
        "app_id": APP_ID,
        "app_secret": APP_SECRET
    }).encode("utf-8")
    req0 = Request(app_token_url, data=app_data,
                   headers={"Content-Type": "application/json"})
    with urlopen(req0, timeout=15) as resp:
        app_token = json.loads(resp.read().decode())["app_access_token"]

    req = Request(url, data=data, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {app_token}"
    })
    try:
        with urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        return result
    except Exception as e:
        if hasattr(e, 'read'):
            print(f"토큰 교환 오류 본문: {e.read().decode()}")
        raise


def main():
    print("=" * 50)
    print("🔐 Lark OAuth 인증 시작")
    print("=" * 50)

    # 1. 로컬 서버 시작
    server = http.server.HTTPServer(("localhost", PORT), OAuthHandler)
    server_thread = threading.Thread(target=server.serve_forever, daemon=True)
    server_thread.start()
    print(f"✅ 로컬 인증 서버 시작 (포트 {PORT})")

    # 2. Lark 인증 페이지 열기
    auth_params = urlencode({
        "app_id": APP_ID,
        "redirect_uri": REDIRECT_URI,
        "state": "lark_chat_auth"
    })
    auth_url = f"{DOMAIN}/open-apis/authen/v1/authorize?{auth_params}"

    print(f"\n📱 브라우저에서 Lark 로그인 페이지를 엽니다...")
    print(f"🔗 {auth_url}\n")
    webbrowser.open(auth_url)

    # 3. 콜백 대기 (최대 120초)
    print("⏳ 로그인 대기 중... (최대 120초)")
    for i in range(120):
        if auth_result["code"] or auth_result["error"]:
            break
        time.sleep(1)
        if (i + 1) % 10 == 0:
            print(f"  ... {i + 1}초 경과")

    server.shutdown()

    if auth_result["error"]:
        print(f"\n❌ 인증 실패: {auth_result['error']}")
        sys.exit(1)

    if not auth_result["code"]:
        print("\n❌ 타임아웃: 120초 내 로그인하지 않았습니다.")
        sys.exit(1)

    code = auth_result["code"]
    print(f"\n✅ Authorization Code 수신!")

    # 4. User Access Token 발급
    print("\n🔄 User Access Token 발급 중...")
    try:
        token_result = get_user_token(code)
        if token_result.get("code") == 0:
            token_data = token_result.get("data", {})
            user_token = token_data.get("access_token")
            print(f"✅ User Access Token 발급 성공!")
            print(f"   만료: {token_data.get('expires_in', 0)}초")

            # 5. 채팅 목록 조회
            # 토큰 먼저 저장
            with open("lark_user_token.txt", "w") as f:
                f.write(user_token)
            print(f"💾 토큰 저장: lark_user_token.txt")

            print("\n📋 채팅 그룹 조회 중...")
            params = urlencode({"page_size": 100})
            url = f"{DOMAIN}/open-apis/im/v1/chats?{params}"
            req = Request(url, headers={
                "Authorization": f"Bearer {user_token}",
                "Content-Type": "application/json"
            })
            try:
                with urlopen(req, timeout=15) as resp:
                    chats_result = json.loads(resp.read().decode())
            except Exception as e:
                if hasattr(e, 'read'):
                    err_body = e.read().decode()
                    print(f"❌ 채팅 조회 오류: {err_body}")
                    chats_result = json.loads(err_body)
                else:
                    raise

            if chats_result.get("code") == 0:
                items = chats_result.get("data", {}).get("items", [])
                print(f"✅ {len(items)}개 채팅 그룹 발견\n")
                for chat in items:
                    name = chat.get("name", "(이름 없음)")
                    chat_id = chat.get("chat_id", "")
                    print(f"  [{chat_id}] {name}")

                # 결과 저장
                output = {
                    "user_access_token": user_token,
                    "expires_in": token_data.get("expires_in"),
                    "chats": items
                }
                with open("lark_auth_result.json", "w", encoding="utf-8") as f:
                    json.dump(output, f, ensure_ascii=False, indent=2)
                print(f"\n💾 결과 저장: lark_auth_result.json")
            else:
                print(f"❌ 채팅 조회 실패: {chats_result.get('msg')}")
                print(json.dumps(chats_result, ensure_ascii=False, indent=2))
        else:
            print(f"❌ 토큰 발급 실패: {token_result.get('msg')}")
            print(json.dumps(token_result, ensure_ascii=False, indent=2))
    except Exception as e:
        print(f"❌ 오류: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
