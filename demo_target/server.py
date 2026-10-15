#!/usr/bin/env python3
"""
Demo backend — re-exposes the in-process reference app over HTTP so you can see
the exact "point the harness at a backend by host/port" workflow, and so the
HTTP adapter is exercised against a real socket. It also serves a test profile
(reset, user-admin, token-mint, JWKS, injected-row probe) that the harness uses.

DEMO_MODE=secure (default) or vulnerable.  Listens on PORT (default 8080).

This is NOT your backend — it's a stand-in with the same contract, so you can
run `docker compose up` and watch a green run before pointing config at your app.
"""
import base64
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from sentinel.adapters.reference.secure_app import SecureApp, RSA_PUB
from sentinel.adapters.reference.vulnerable_app import VulnerableApp
from sentinel.adapters.reference_target import MediaBackend, _magic, _decodes

MODE = os.environ.get("DEMO_MODE", "secure")
SECURE = MODE != "vulnerable"


class State:
    def __init__(self):
        self.app = (SecureApp if SECURE else VulnerableApp)()
        self.media = MediaBackend(secure=SECURE)


STATE = State()


def reset_state():
    global STATE
    STATE = State()


def _jwks():
    # expose the demo's RSA public key as a JWKS for the confusion test
    from cryptography.hazmat.primitives.serialization import load_pem_public_key
    pub = load_pem_public_key(RSA_PUB)
    nums = pub.public_numbers()
    def b64(i):
        b = i.to_bytes((i.bit_length() + 7) // 8, "big")
        return base64.urlsafe_b64encode(b).rstrip(b"=").decode()
    return {"keys": [{"kty": "RSA", "use": "sig", "alg": "RS256",
                      "n": b64(nums.n), "e": b64(nums.e)}]}


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass  # quiet

    # --- helpers ---
    def _body(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(n) if n else b""
        ctype = self.headers.get("Content-Type", "")
        if raw and ctype.startswith("application/json"):
            try:
                return json.loads(raw), raw
            except Exception:
                return {}, raw
        if raw and "application/x-www-form-urlencoded" in ctype:
            return {k: v[0] for k, v in parse_qs(raw.decode()).items()}, raw
        return {}, raw

    def _send(self, resp):
        payload = json.dumps(resp.body).encode()
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _token(self):
        h = self.headers.get("Authorization", "")
        return h[7:] if h.startswith("Bearer ") else ""

    def _ip(self):
        # SECURE: trust the real connection IP, NOT X-Forwarded-For
        return self.client_address[0]

    def _multipart_file(self, raw):
        # minimal multipart parse: find filename and the file bytes
        try:
            boundary = self.headers["Content-Type"].split("boundary=")[1].encode()
            parts = raw.split(b"--" + boundary)
            for p in parts:
                if b"filename=" in p:
                    head, _, data = p.partition(b"\r\n\r\n")
                    fn = head.split(b'filename="')[1].split(b'"')[0].decode()
                    return fn, data.rstrip(b"\r\n")
        except Exception:
            pass
        return None, None

    # --- routing ---
    def do_GET(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        app = STATE.app
        if p == "/health":
            return self._send_raw(200, {"ok": True})
        if p == "/jwks.json":
            return self._send_raw(200, _jwks())
        if p == "/admin/users":
            return self._send(app.admin_users(self._token()))
        if p.startswith("/resources/"):
            return self._send(app.get_resource(self._token(), int(p.rsplit("/", 1)[1])))
        if p.startswith("/videos/"):
            return self._send(app.get_object(self._token(), "video", int(p.rsplit("/", 1)[1])))
        if p.startswith("/media/"):
            return self._send(app.get_media(p[len("/media/"):]))
        if p == "/debug/parse":
            return self._send(app.buggy_endpoint(q.get("value", [""])[0]))
        if p.startswith("/test/users/"):
            uname = p.split("/test/users/")[1]
            u2 = app.users.get(uname, {})
            return self._send_raw(200, {k: u2.get(k) for k in ("role", "verified", "balance", "enabled")})
        if p == "/test/token":
            uname = q.get("username", ["alice"])[0]; aud = q.get("aud", ["api"])[0]
            uu = app.users[uname]
            tok = app._issue_access(uname, uu["role"], uu["id"], uu["mfa"], aud=aud)
            return self._send_raw(200, {"access_token": tok})
        if p == "/test/injected":
            return self._send_raw(200, {"exists": STATE.media.injected_row_exists(q.get("marker", [""])[0])})
        return self._send_raw(404, {"error": "not found"})

    def do_POST(self):
        u = urlparse(self.path)
        p = u.path
        body, raw = self._body()
        app = STATE.app
        if p == "/test/reset":
            reset_state()
            return self._send_raw(200, {"reset": True})
        if p == "/auth/login":
            otp_ok = body.get("otp") == "000000"
            cookie = self.headers.get("Cookie", "")
            prev = cookie.split("sid=")[1].split(";")[0] if "sid=" in cookie else None
            return self._send(app.login(body.get("username", ""), body.get("password", ""),
                                        source_ip=self._ip(), xff=self.headers.get("X-Forwarded-For"),
                                        otp_ok=otp_ok, prev_session=prev))
        if p == "/auth/logout":
            return self._send(app.logout(self._token()))
        if p == "/auth/refresh":
            return self._send(app.refresh_token(body.get("token", "")))
        if p == "/auth/register":
            extra = {k: v for k, v in body.items() if k not in ("username", "password", "role")}
            return self._send(app.register(body.get("username", ""), body.get("password", ""),
                                           body.get("role"), extra))
        if p == "/account/password":
            return self._send(app.change_password(self._token(), body.get("old", ""),
                body.get("newPassword", ""), reauthed=self.headers.get("X-Step-Up") == "reauthed",
                csrf_ok=bool(self.headers.get("X-CSRF-Token")),
                cross_site=self.headers.get("Origin", "").endswith("evil.example")))
        if p == "/account/payout":
            return self._send(app.sensitive_action(self._token(),
                reauthed=self.headers.get("X-Step-Up") == "reauthed",
                csrf_ok=bool(self.headers.get("X-CSRF-Token")),
                cross_site=self.headers.get("Origin", "").endswith("evil.example")))
        if p == "/account/email":
            return self._send(app.change_email(self._token(), body.get("email", ""),
                reverified=self.headers.get("X-Email-Verified") == "true"))
        if p == "/upload":
            ctype = self.headers.get("Content-Type", "")
            if ctype.startswith("multipart/"):
                fn, data = self._multipart_file(raw)
                return self._send(STATE.media.upload_bytes(fn or "f", data or b"", ctype))
            return self._send(app.upload(self._token(), body.get("fetchUrl"),
                                         body.get("width"), body.get("height"),
                                         body.get("filename", "v.mp4")))
        if p == "/auth/reset/request":
            r = app.reset_request(body.get("email", ""), self.headers.get("Host", "app.example"))
            return self._send(r)
        if p == "/auth/reset/confirm":
            return self._send(app.reset_confirm(body.get("token", ""), body.get("newPassword", "")))
        if p == "/oauth/token":
            return self._send(app.oauth_token(body.get("code", ""), body.get("code_verifier"),
                                              body.get("client_id", ""), body.get("redirect_uri", "")))
        if p.startswith("/test/users/"):            # POST /test/users/{username} sets enabled
            uname = p.split("/test/users/")[1]
            if uname in app.users:
                app.users[uname]["enabled"] = bool(body.get("enabled"))
            return self._send_raw(200, {"username": uname, "enabled": body.get("enabled")})
        return self._send_raw(404, {"error": "not found"})

    def do_PUT(self):      # for the method-confusion authz test (AZ4)
        p = urlparse(self.path).path
        if p.startswith("/admin/users/"):
            return self._send(STATE.app.admin_delete_user(self._token(), p.rsplit("/", 1)[1], method="PUT"))
        return self._send_raw(404, {"error": "not found"})

    def do_DELETE(self):
        p = urlparse(self.path).path
        if p.startswith("/admin/users/"):
            return self._send(STATE.app.admin_delete_user(self._token(), p.rsplit("/", 1)[1], method="DELETE"))
        return self._send_raw(404, {"error": "not found"})

    def do_GET_oauth(self):
        pass

    def _send_raw(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        # secure headers on every response
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'")
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


# oauth/authorize is a GET with query params -> handle in do_GET
_orig_do_get = Handler.do_GET
def _do_get(self):
    u = urlparse(self.path)
    if u.path == "/oauth/authorize":
        q = parse_qs(u.query)
        r = STATE.app.oauth_authorize(q.get("client_id", [""])[0], q.get("redirect_uri", [""])[0],
                                      q.get("code_challenge", [None])[0], q.get("state", [None])[0])
        return self._send(r)
    return _orig_do_get(self)
Handler.do_GET = _do_get


def main():
    port = int(os.environ.get("PORT", "8080"))
    srv = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"demo backend ({'SECURE' if SECURE else 'VULNERABLE'}) listening on :{port}")
    srv.serve_forever()


if __name__ == "__main__":
    main()
