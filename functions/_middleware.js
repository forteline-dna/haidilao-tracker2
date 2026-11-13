// 사이트 전체 비밀번호 잠금 (Cloudflare Pages Functions)
// 비밀번호는 Cloudflare 환경변수 SITE_PASSWORD 에 저장 (코드에 넣지 않음)
const COOKIE = "hdl_auth";
const MAX_AGE = 60 * 60 * 24 * 180; // 180일 동안 로그인 유지

async function tokenFor(pw) {
  const buf = await crypto.subtle.digest("SHA-256", new TextEncoder().encode("hdl:" + pw));
  return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function loginPage(error) {
  return new Response(
    `<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>하이디라오 영등포</title>
<style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#f4f4f5;font-family:-apple-system,system-ui,sans-serif}
form{background:#fff;padding:32px 24px;border-radius:16px;box-shadow:0 4px 20px rgba(0,0,0,.08);width:min(320px,calc(100vw - 32px));box-sizing:border-box;text-align:center}
h1{font-size:18px;margin:0 0 20px}
input{width:100%;box-sizing:border-box;font-size:20px;padding:12px;border:1px solid #d4d4d8;border-radius:10px;text-align:center;letter-spacing:4px}
button{margin-top:12px;width:100%;padding:12px;font-size:16px;border:0;border-radius:10px;background:#b91c1c;color:#fff}
p{color:#b91c1c;font-size:14px;margin:12px 0 0}
</style></head><body>
<form method="POST" action="/__login">
<h1>하이디라오 영등포</h1>
<input type="password" name="password" inputmode="numeric" autocomplete="current-password" placeholder="비밀번호" autofocus required>
<button type="submit">들어가기</button>
${error ? "<p>비밀번호가 틀렸습니다</p>" : ""}
</form></body></html>`,
    { status: 401, headers: { "Content-Type": "text/html; charset=utf-8", "Cache-Control": "no-store" } }
  );
}

export async function onRequest({ request, next, env }) {
  const url = new URL(request.url);
  const expected = await tokenFor(env.SITE_PASSWORD || "");

  if (url.pathname === "/__login" && request.method === "POST") {
    const form = await request.formData();
    if (env.SITE_PASSWORD && form.get("password") === env.SITE_PASSWORD) {
      return new Response(null, {
        status: 303,
        headers: {
          Location: "/",
          "Set-Cookie": `${COOKIE}=${expected}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
        },
      });
    }
    await new Promise((r) => setTimeout(r, 1500)); // 무차별 대입 지연
    return loginPage(true);
  }

  const cookie = request.headers.get("Cookie") || "";
  const ok = env.SITE_PASSWORD && cookie.split(/;\s*/).includes(`${COOKIE}=${expected}`);
  if (!ok) return loginPage(false);

  const res = await next();
  const out = new Response(res.body, res);
  out.headers.set("Cache-Control", "private, no-store");
  return out;
}
