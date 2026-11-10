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
from sentinel.adapters.base import Resp
from sentinel.adapters.reference.secure_app import SecureApp, RSA_PUB, FRONTEND_HEADERS
from sentinel.adapters.reference.vulnerable_app import VulnerableApp
from sentinel.adapters.reference_target import MediaBackend

MODE = os.environ.get("DEMO_MODE", "secure")
SECURE = MODE != "vulnerable"

# request limits the SECURE build enforces before any parsing
MAX_JSON_BODY = 256 * 1024
MAX_UPLOAD_BODY = 32 * 1024 * 1024
MAX_HEADER_VALUE = 4096
MAX_JSON_KEYS = 1000
MAX_JSON_DEPTH = 32
MAX_PARTS = 100


def _nesting(raw: bytes) -> int:
    """Upper bound on the nesting depth of a JSON document, in one cheap pass."""
    depth = deepest = 0
    for b in raw:
        if b in (0x7B, 0x5B):          # { [
            depth += 1
            deepest = max(deepest, depth)
        elif b in (0x7D, 0x5D):        # } ]
            depth -= 1
    return deepest

IDENTITY_HEADERS = ("X-Remote-User", "X-Forwarded-User", "X-User", "X-Authenticated-User",
                    "X-Auth-Request-User", "X-Auth-Request-Email", "X-WEBAUTH-USER", "X-User-Id",
                    "X-Role", "X-Admin", "X-Is-Admin", "X-User-Role")


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


class Refuse(Exception):
    """Stop handling this request and answer with the given status."""
    def __init__(self, status, error):
        self.status, self.error = status, error


# fields that must be plain strings — a secure build rejects a JSON object,
# array or number here instead of passing it on to code that assumes a string
STRING_FIELDS = ("username", "password", "otp", "email", "token", "newPassword", "old", "role",
                 "code", "code_verifier", "client_id", "redirect_uri", "filename", "fetchUrl")


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    disable_nagle_algorithm = True     # answer in one segment, no 40 ms delayed-ACK stall
    wbufsize = 64 * 1024

    def log_message(self, *a):
        pass  # quiet

    # --- helpers ---
    def _limit(self, status, error):
        """A request-shape limit. The SECURE build refuses cheaply (4xx); the
        VULNERABLE build has no limits, so the input reaches code that dies."""
        raise Refuse(status if SECURE else 500,
                     error if SECURE else f"unhandled exception while parsing request ({error})")

    def _body(self):
        """Read and parse the request body, enforcing size/shape limits first."""
        n = int(self.headers.get("Content-Length", 0) or 0)
        ctype = self.headers.get("Content-Type", "")
        is_json = ctype.startswith("application/json")
        is_multipart = ctype.startswith("multipart/")
        raw = self.rfile.read(n) if n else b""           # always drain, then decide
        if any(len(v) > MAX_HEADER_VALUE for v in self.headers.values()):
            self._limit(431, "request header too large")
        if n > (MAX_UPLOAD_BODY if is_multipart else MAX_JSON_BODY):
            self._limit(413, "request body too large")
        if self.headers.get("Content-Encoding", "identity").lower() != "identity":
            self._limit(415, "compressed request bodies are not accepted")
        if "charset=" in ctype.lower() and "utf-8" not in ctype.lower():
            self._limit(415, "unsupported charset")
        if is_multipart:
            boundary = ctype.split("boundary=")[-1].encode()
            if raw.count(b"--" + boundary) > MAX_PARTS:
                self._limit(400, "too many multipart parts")
            return {}, raw
        if raw and is_json:
            if _nesting(raw) > MAX_JSON_DEPTH:           # checked BEFORE parsing
                self._limit(400, "JSON nested too deeply")
            try:
                data = json.loads(raw)
            except (ValueError, RecursionError):
                self._limit(400, "malformed JSON")
            if not isinstance(data, dict):
                self._limit(400, "JSON body must be an object")
            if len(data) > MAX_JSON_KEYS:
                self._limit(400, "too many fields")
            for k in STRING_FIELDS:                      # type confusion ({"$ne": null}, [..])
                if k in data and data[k] is not None and not isinstance(data[k], str):
                    self._limit(400, f"'{k}' must be a string")
            return data, raw
        if raw and "application/x-www-form-urlencoded" in ctype:
            return {k: v[0] for k, v in parse_qs(raw.decode(errors="replace")).items()}, raw
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

    def _send_text(self, resp, ctype):
        """A non-JSON response (the demo front end, served on the same port)."""
        payload = str(resp.body.get("_text", "")).encode()
        self.send_response(resp.status)
        for k, v in resp.headers.items():
            self.send_header(k, v)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _static(self, path):
        """The front end and anything else an anonymous visitor may fetch. The
        app decides what exists: the secure build serves its page and script and
        nothing more; the vulnerable build also hands out dotfiles and dumps."""
        app = STATE.app
        if path == "/assets/app.js":
            js = dict(app.frontend_assets()).get(path, "")
            return self._send_text(Resp(200, dict(FRONTEND_HEADERS) if SECURE else {},
                                        {"_text": js}), "text/javascript; charset=utf-8")
        r = app.fetch_path("frontend", path)
        if "_text" in r.body:
            html = path in ("/", "/index.html")
            return self._send_text(r, "text/html; charset=utf-8" if html else "text/plain; charset=utf-8")
        return None

    def do_OPTIONS(self):
        # CORS preflight: the app decides which Origin (if any) is allowed
        self._dispatch(lambda: self._send(STATE.app.cors_probe(
            "", self.headers.get("Origin", ""), preflight=True)))

    def _send_raw(self, status, body):
        # the secure build sets its security headers on EVERY response, errors included
        headers = {"X-Content-Type-Options": "nosniff",
                   "Content-Security-Policy": "default-src 'none'"} if SECURE else {}
        self._send(Resp(status, headers, body))

    def _token(self):
        h = self.headers.get("Authorization", "")
        return h[7:] if h.startswith("Bearer ") else ""

    def _ip(self):
        # SECURE: trust the real connection IP, NOT X-Forwarded-For
        return self.client_address[0]

    def _spoof(self):
        return {h: self.headers[h] for h in IDENTITY_HEADERS if h in self.headers}

    def _multipart_file(self, raw):
        # minimal multipart parse: find filename and the file bytes
        try:
            boundary = self.headers["Content-Type"].split("boundary=")[1].encode()
            for p in raw.split(b"--" + boundary):
                if b"filename=" in p:
                    head, _, data = p.partition(b"\r\n\r\n")
                    fn = head.split(b'filename="')[1].split(b'"')[0].decode()
                    return fn, data.rstrip(b"\r\n")
        except Exception:
            pass
        return None, None

    def _dispatch(self, handler):
        try:
            return handler()
        except Refuse as r:
            return self._send_raw(r.status, {"error": r.error})
        except (ValueError, KeyError):
            return self._send_raw(400, {"error": "bad request"})
        except Exception as e:
            # anything unexpected: a generic 500 (the secure build never echoes the
            # exception; the vulnerable one does) — and the connection stays usable
            return self._send_raw(500, {"error": "internal error"} if SECURE else
                                  {"trace": f"{type(e).__name__}: {e}"})

    # --- routing ---
    def do_GET(self):
        self._dispatch(self._get)

    def do_POST(self):
        self._dispatch(self._post)

    def do_PUT(self):      # for the method-confusion authz test (AZ4)
        self._dispatch(lambda: self._admin_user_method("PUT"))

    def do_PATCH(self):
        self._dispatch(lambda: self._admin_user_method("PATCH"))

    def do_DELETE(self):
        self._dispatch(lambda: self._admin_user_method("DELETE"))

    def _admin_user_method(self, method):
        self._body()
        p = urlparse(self.path).path
        if p.startswith("/admin/users/"):
            return self._send(STATE.app.admin_delete_user(self._token(), p.rsplit("/", 1)[1],
                                                          method=method))
        return self._send_raw(404, {"error": "not found"})

    def _get(self):
        u = urlparse(self.path)
        p, q = u.path, parse_qs(u.query)
        app = STATE.app
        if any(len(v) > MAX_HEADER_VALUE for v in self.headers.values()):
            self._limit(431, "request header too large")
        if p == "/health":
            return self._send_raw(200, {"ok": True, "mode": MODE})
        if p == "/jwks.json":
            return self._send_raw(200, _jwks())
        if p == "/admin/users":
            return self._send(app.admin_users(self._token(), self._spoof()))
        if p.startswith("/resources/"):
            r = app.get_resource(self._token(), int(p.rsplit("/", 1)[1]))
            if self.headers.get("Origin"):          # a browser on another origin is asking
                r.headers.update({k: v for k, v in app.cors_probe(
                    self._token(), self.headers["Origin"]).headers.items()
                    if k.lower().startswith("access-control-") or k == "Vary"})
            return self._send(r)
        if p.startswith("/videos/"):
            return self._send(app.get_object(self._token(), "video", int(p.rsplit("/", 1)[1])))
        if p.startswith("/media/"):
            return self._send(app.get_media(p[len("/media/"):]))
        if p == "/debug/parse":
            return self._send(app.buggy_endpoint(q.get("value", [""])[0]))
        if p == "/oauth/authorize":
            return self._send(app.oauth_authorize(
                q.get("client_id", [""])[0], q.get("redirect_uri", [""])[0],
                q.get("code_challenge", [None])[0], q.get("state", [None])[0]))
        # ---- test profile (a real backend exposes these only in a test build) ----
        if p.startswith("/test/users/"):
            u2 = app.users.get(p.split("/test/users/")[1])
            if u2 is None:
                return self._send_raw(404, {"error": "no such user"})
            return self._send_raw(200, {k: u2.get(k) for k in
                                        ("role", "verified", "balance", "enabled", "email")})
        if p == "/test/token":
            uname = q.get("username", ["alice"])[0]; aud = q.get("aud", ["api"])[0]
            ttl = q.get("ttl", [""])[0]
            uu = app.users[uname]
            kw = {"ttl": int(ttl)} if ttl.lstrip("-").isdigit() else {}
            tok = app._issue_access(uname, uu["role"], uu["id"], uu["mfa"], aud=aud, **kw)
            return self._send_raw(200, {"access_token": tok})
        if p == "/test/injected":
            return self._send_raw(200, {"exists": STATE.media.injected_row_exists(q.get("marker", [""])[0])})
        if self._static(p) is None:
            return self._send_raw(404, {"error": "not found"})
        return None

    def _post(self):
        p = urlparse(self.path).path
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
            if not body.get("username") or not body.get("password"):
                return self._send_raw(400, {"error": "username and password are required"})
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
                if SECURE and not app._verify(self._token()):
                    return self._send_raw(401, {"error": "authentication required"})
                fn, data = self._multipart_file(raw)
                return self._send(STATE.media.upload_bytes(fn or "f", data or b"", ctype))
            return self._send(app.upload(self._token(), body.get("fetchUrl"),
                                         body.get("width"), body.get("height"),
                                         body.get("filename", "v.mp4")))
        if p == "/auth/reset/request":
            return self._send(app.reset_request(body.get("email", ""),
                                                self.headers.get("Host", "app.example")))
        if p == "/auth/reset/confirm":
            return self._send(app.reset_confirm(body.get("token", ""), body.get("newPassword", "")))
        if p == "/oauth/token":
            return self._send(app.oauth_token(body.get("code", ""), body.get("code_verifier"),
                                              body.get("client_id", ""), body.get("redirect_uri", "")))
        if p.startswith("/test/users/"):            # POST /test/users/{username} sets enabled
            uname = p.split("/test/users/")[1]
            if uname not in app.users:
                return self._send_raw(404, {"error": "no such user"})
            app.users[uname]["enabled"] = bool(body.get("enabled"))
            return self._send_raw(200, {"username": uname, "enabled": body.get("enabled")})
        return self._send_raw(404, {"error": "not found"})


class Server(ThreadingHTTPServer):
    daemon_threads = True
    request_queue_size = 128          # room for a burst of concurrent connections


def main():
    port = int(os.environ.get("PORT", "8080"))
    srv = Server(("0.0.0.0", port), Handler)
    print(f"demo backend ({'SECURE' if SECURE else 'VULNERABLE'}) listening on :{port}", flush=True)
    srv.serve_forever()


if __name__ == "__main__":
    main()
