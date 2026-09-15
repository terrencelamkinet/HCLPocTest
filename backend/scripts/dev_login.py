#!/usr/bin/env python3
"""Dev login — get JWT token instantly via dev-login endpoint.
Usage: python3 dev_login.py [email] [password]
       python3 dev_login.py --browser [email] [password]
"""
import sys, json, asyncio, time

API = "http://localhost:5173"

async def get_token(email: str, password: str) -> str:
    import httpx
    async with httpx.AsyncClient() as c:
        r = await c.post(f"{API}/api/v1/auth/dev-login",
            json={"email": email, "password": password})
        if r.status_code == 200:
            return r.json()["access_token"]

        print("dev-login unavailable, falling back to MFA flow...", file=sys.stderr)
        r = await c.post(f"{API}/api/v1/auth/login",
            json={"email": email, "password": password})
        if r.status_code != 200:
            print(f"Login failed: {r.text}", file=sys.stderr); sys.exit(1)
        body = r.json()
        if not body.get("mfa_required"):
            return body["access_token"]

        import redis.asyncio as aioredis
        for _ in range(5):
            try:
                red = aioredis.from_url("redis://127.0.0.1:6379/0")
                otp = await red.get(f"otp:{email}")
                await red.aclose()
                if otp:
                    otp_str = otp.decode(); break
            except:
                pass
            await asyncio.sleep(0.5)
        else:
            print("Could not get OTP from Redis", file=sys.stderr); sys.exit(1)

        r = await c.post(f"{API}/api/v1/auth/verify-mfa",
            json={"email": email, "otp_code": otp_str})
        if r.status_code != 200:
            print(f"MFA verify failed: {r.text}", file=sys.stderr); sys.exit(1)
        return r.json()["access_token"]


if __name__ == "__main__":
    browser_mode = "--browser" in sys.argv
    args = [a for a in sys.argv[1:] if a != "--browser"]
    email = args[0] if len(args) > 0 else "test@test.com"
    pw = args[1] if len(args) > 1 else "test123"
    token = asyncio.run(get_token(email, pw))

    if browser_mode:
        now_ms = int(time.time() * 1000)
        js = f"""(() => {{
  const key = 'nexus_crm_auth';
  localStorage.setItem(key, JSON.stringify({{
    access_token: '{token}',
    refresh_token: '',
    email: '{email}',
    expires: {now_ms + 1439 * 60 * 1000},
    refresh_expires: {now_ms + 22 * 60 * 60 * 1000}
  }}));
  location.reload();
}})();"""
        print(js)
    else:
        print(token)
