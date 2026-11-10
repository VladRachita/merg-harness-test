#!/usr/bin/env python3
"""
app_model.py — an HTTP-style model of an app's auth/access surface, in two
builds: SecureApp (correct) and VulnerableApp (deliberately broken, negative
control). The harness (verify_logic.py) drives both through an attack catalogue.

Defensive only: everything is in-process, no real service, no real secrets.
Mirrors the Kotlin deliverable's AuthSystemUnderTest contract.
"""
import base64
import hashlib
import hmac
import ipaddress
import json
import secrets
import time
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import jwt
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

# ---- key material (fresh per run) ------------------------------------------
_rsa = rsa.generate_private_key(public_exponent=65537, key_size=2048)
RSA_PRIV = _rsa.private_bytes(serialization.Encoding.PEM,
    serialization.PrivateFormat.PKCS8, serialization.NoEncryption())
RSA_PUB = _rsa.public_key().public_bytes(serialization.Encoding.PEM,
    serialization.PublicFormat.SubjectPublicKeyInfo)

ISS = "https://auth.example"
API_AUD = "api"
CONFIG_BASE_URL = "https://app.example"          # trusted base for links
MAX_PIXELS = 50_000_000
ACCESS_TTL = 900


def b64url(b):  # no padding
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def s256(verifier):
    return b64url(hashlib.sha256(verifier.encode()).digest())


@dataclass
class Resp:
    status: int
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)

    @property
    def ok(self):
        return 200 <= self.status < 300


FRONTEND_ORIGIN = "https://app.example"          # the one web origin allowed to call the API
COMMON_PASSWORDS = {"password", "password1", "12345678", "123456789", "1234567890", "qwerty123",
                    "qwertyuiop", "iloveyou", "11111111", "letmein123", "admin123", "welcome1"}

FRONTEND_PAGE = """<!doctype html><html><head><meta charset="utf-8"><title>App</title>
<script src="/assets/app.js" defer></script></head><body><div id="root"></div></body></html>"""
FRONTEND_JS = """const API = "/api"; export async function login(u, p) {
  return fetch(API + "/auth/login", {method: "POST", body: JSON.stringify({u, p})}); }"""
FRONTEND_HEADERS = {
    "Content-Security-Policy": "default-src 'self'; frame-ancestors 'none'; object-src 'none'",
    "X-Frame-Options": "DENY",
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "strict-origin-when-cross-origin",
}

SECURE_HEADERS = {
    "Content-Security-Policy": "default-src 'none'; frame-ancestors 'none'",
    "X-Content-Type-Options": "nosniff",
}


class SecureApp:
    ACCOUNT_LIMIT = 5
    IP_LIMIT = 10
    OTP_LIMIT = 5
    UPLOAD_LIMIT = 5
    REGISTER_LIMIT = 12      # sign-ups per client before throttling (bot sign-up waves)
    MIN_PASSWORD = 8
    RESET_GUESS_LIMIT = 10   # wrong reset tokens per client before throttling (token cracking)

    def __init__(self):
        now = int(time.time())
        self.users = {
            "alice": dict(id=1, pw="alice-pw", role="user", enabled=True,
                          mfa=True, verified=True, balance=0, email="alice@x.com"),
            "bob":   dict(id=2, pw="bob-pw", role="user", enabled=True,
                          mfa=True, verified=True, balance=0, email="bob@x.com"),
            "admin": dict(id=3, pw="admin-pw", role="admin", enabled=True,
                          mfa=True, verified=True, balance=0, email="admin@x.com"),
        }
        self.resources = {1: "alice-private", 2: "bob-private"}
        self.videos = {101: 1, 102: 2}            # id -> owner_id
        self.media = {"intro.mp4": b"\x00\x00\x00\x18ftyp"}  # allow-listed ids
        self.account_fails = {}
        self.ip_fails = {}
        self.otp_fails = {}
        self.upload_counts = {}
        self.register_count = 0
        self.reset_guess_fails = 0
        self.revoked_jti = set()
        self.user_jtis = {}                        # username -> set(jti)
        self.refresh = {}                          # token -> dict(family, used, user)
        self.reset_tokens = {}                     # token -> dict(user, exp, used)
        self.oauth_clients = {
            "public-app": dict(redirect_uris={"https://app.example/cb"}, public=True),
            "other-app":  dict(redirect_uris={"https://other.example/cb"}, public=True),
        }
        self.oauth_codes = {}                      # code -> dict(...)

    # ---- helpers -----------------------------------------------------------
    def _hash(self, pw): return hashlib.sha256(("s4lt::" + pw).encode()).hexdigest()

    def _norm(self, username): return (username or "").strip().lower()

    def _issue_access(self, username, role, uid, mfa, aud=API_AUD, ttl=ACCESS_TTL):
        now = int(time.time()); jti = secrets.token_hex(8)
        self.user_jtis.setdefault(username, set()).add(jti)
        return jwt.encode({"sub": username, "uid": uid, "role": role, "mfa": mfa,
                           "iss": ISS, "aud": aud, "jti": jti,
                           "iat": now, "exp": now + ttl}, RSA_PRIV, algorithm="RS256")

    def _verify(self, token):
        try:
            c = jwt.decode(token, RSA_PUB, algorithms=["RS256"], audience=API_AUD,
                           issuer=ISS, options={"require": ["exp", "sub", "jti", "aud", "iss"]})
        except Exception:
            return None
        if c["jti"] in self.revoked_jti:
            return None
        u = self.users.get(c["sub"])
        if not u or not u["enabled"]:
            return None
        return {**c, "role": u["role"]}            # role re-read from store

    def _resp(self, status, body=None):
        return Resp(status, dict(SECURE_HEADERS), body or {})

    # ---- auth --------------------------------------------------------------
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True,
              prev_session=None, evasion=None):
        # `xff` and `evasion` (spoofed headers, alternate route spellings, a
        # form-encoded body) are deliberately IGNORED: limits key on the real
        # peer address and the normalized account, nothing the client controls.
        key = self._norm(username)
        # rate limiting: per-account (normalized) AND per real source IP
        if self.ip_fails.get(source_ip, 0) >= self.IP_LIMIT:
            return self._resp(429, {"error": "too many requests"})
        if self.account_fails.get(key, 0) >= self.ACCOUNT_LIMIT:
            return self._resp(429, {"error": "locked"})
        u = self.users.get(key)
        ok = bool(u) and u["enabled"] and hmac.compare_digest(
            self._hash(u["pw"]), self._hash(password or ""))
        if ok and u["mfa"] and not otp_ok:
            self.otp_fails[key] = self.otp_fails.get(key, 0) + 1
            if self.otp_fails[key] >= self.OTP_LIMIT:
                return self._resp(429, {"error": "otp locked"})
            return self._resp(401, {"error": "otp required"})   # uniform-ish
        if not ok:
            self.account_fails[key] = self.account_fails.get(key, 0) + 1
            self.ip_fails[source_ip] = self.ip_fails.get(source_ip, 0) + 1
            return self._resp(401, {"error": "invalid credentials"})  # no enumeration
        self.account_fails[key] = 0
        tok = self._issue_access(key, u["role"], u["id"], u["mfa"])
        rtok = secrets.token_hex(16)
        self.refresh[rtok] = dict(family=secrets.token_hex(4), used=False, user=key)
        r = self._resp(200, {"access_token": tok, "refresh_token": rtok, "sid": tok[:16]})
        # session FIXATION defence: a brand-new session, never the caller's prior one
        r.headers["Set-Cookie"] = f"sid={secrets.token_hex(8)}; HttpOnly; Secure; SameSite=Lax; Path=/"
        return r

    def _kill_refresh(self, username):
        """Revoke every refresh token of a user (logout / password change / reset)."""
        for rec in self.refresh.values():
            if rec["user"] == username:
                rec["used"] = True

    def logout(self, token):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        self.revoked_jti.add(c["jti"])
        self._kill_refresh(c["sub"])              # logout ends the refresh family too
        return self._resp(200, {"status": "logged out"})

    def refresh_token(self, rtok):
        rec = self.refresh.get(rtok)
        if not rec:
            return self._resp(401, {"error": "invalid"})
        if rec["used"]:
            # REUSE DETECTED -> kill the whole family's sessions
            for t, r in self.refresh.items():
                if r["family"] == rec["family"]:
                    r["used"] = True
            for jti in list(self.user_jtis.get(rec["user"], [])):
                self.revoked_jti.add(jti)
            return self._resp(401, {"error": "reuse detected; family revoked"})
        rec["used"] = True
        u = self.users[rec["user"]]
        new = secrets.token_hex(16)
        self.refresh[new] = dict(family=rec["family"], used=False, user=rec["user"])
        tok = self._issue_access(rec["user"], u["role"], u["id"], u["mfa"])
        return self._resp(200, {"access_token": tok, "refresh_token": new})

    def register(self, username, password, requested_role=None, extra=None):
        key = self._norm(username)
        if self.register_count >= self.REGISTER_LIMIT:
            return self._resp(429, {"error": "too many sign-ups"})
        # password policy: long enough, and not one of the passwords every
        # credential-stuffing list starts with
        pw = password if isinstance(password, str) else ""
        if len(pw) < self.MIN_PASSWORD or pw.lower() in COMMON_PASSWORDS or pw.lower() == key:
            return self._resp(400, {"error": "password too weak"})
        self.register_count += 1
        if key in self.users:
            return self._resp(409, {"error": "exists"})
        # role + privilege fields are SERVER-assigned; attacker input ignored
        self.users[key] = dict(id=max(u["id"] for u in self.users.values()) + 1,
                               pw=password, role="user", enabled=True, mfa=False,
                               verified=False, balance=0, email=f"{key}@x.com")
        return self._resp(201, {"role": "user",
                                "verified": False, "balance": 0})

    # ---- protected resources ----------------------------------------------
    def get_resource(self, token, owner_id):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if c["role"] != "admin" and c["uid"] != owner_id:
            return self._resp(403, {"error": "forbidden"})
        return self._resp(200, {"secret": self.resources.get(owner_id)})

    def get_object(self, token, kind, obj_id):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        owner = self.videos.get(obj_id) if kind == "video" else None
        if owner is None:
            return self._resp(404)
        if c["role"] != "admin" and c["uid"] != owner:
            return self._resp(403, {"error": "forbidden"})
        return self._resp(200, {"video": obj_id, "owner": owner})

    def admin_users(self, token, spoof=None):
        # identity comes ONLY from the verified token; `spoof` (X-Remote-User,
        # X-Forwarded-User, …) is client-controlled and ignored
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if c["role"] != "admin":
            return self._resp(403, {"error": "admin only"})
        return self._resp(200, {"pii": "ALL_USERS_PII"})

    def admin_delete_user(self, token, target, method="DELETE"):
        # function-level authz enforced for EVERY method (no method confusion)
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if c["role"] != "admin":
            return self._resp(403, {"error": "admin only"})
        return self._resp(200, {"deleted": target})

    # ---- state-changing (CSRF + step-up) -----------------------------------
    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if cross_site or not csrf_ok:
            return self._resp(403, {"error": "csrf"})
        if not reauthed:
            return self._resp(401, {"error": "re-authentication required"})
        self.users[c["sub"]]["pw"] = new
        for jti in list(self.user_jtis.get(c["sub"], [])):
            self.revoked_jti.add(jti)                 # kill all sessions
        self._kill_refresh(c["sub"])                  # ...and refresh tokens
        return self._resp(200, {"status": "changed"})

    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if cross_site or not csrf_ok:
            return self._resp(403, {"error": "csrf"})
        if not c.get("mfa"):
            return self._resp(403, {"error": "mfa required"})
        if not reauthed:
            return self._resp(401, {"error": "step-up required"})
        return self._resp(200, {"status": "done"})

    def change_email(self, token, new_email, reverified=False):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        if not reverified:
            return self._resp(401, {"error": "verify new email first"})
        self.users[c["sub"]]["email"] = new_email
        return self._resp(200, {"status": "email pending verification"})

    # ---- media / upload ----------------------------------------------------
    def get_media(self, path):
        # path traversal defence: allow-list, reject separators / traversal
        if "/" in path or "\\" in path or ".." in path or path not in self.media:
            return self._resp(404, {"error": "not found"})
        r = self._resp(200, {"bytes": len(self.media[path])})
        r.headers["Content-Type"] = "video/mp4"
        r.headers["Content-Disposition"] = "attachment"
        return r

    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        c = self._verify(token)
        if not c:
            return self._resp(401)
        # validate first: a refused request never reaches storage or the quota
        if fetch_url and self._is_internal(fetch_url):
            return self._resp(400, {"error": "ssrf blocked"})     # SSRF defence
        if width and height and width * height > MAX_PIXELS:
            return self._resp(400, {"error": "image too large"})  # pixel-flood
        self.upload_counts[c["sub"]] = self.upload_counts.get(c["sub"], 0) + 1
        if self.upload_counts[c["sub"]] > self.UPLOAD_LIMIT:
            return self._resp(429, {"error": "upload rate limit"})
        r = self._resp(201, {"stored": filename})
        # uploads are served as downloads, never inline HTML/SVG
        r.headers["Content-Disposition"] = "attachment"
        r.headers["X-Content-Type-Options"] = "nosniff"
        return r

    def _is_internal(self, url):
        """SSRF defence: only plain http(s) to a PUBLIC address is fetchable.
        The host is parsed the way the fetcher will parse it (so `user@host`,
        `#@`, and the decimal / hex / octal / short / IPv6-mapped spellings of an
        internal address are all seen for what they are), then range-checked.
        A real implementation must also resolve DNS and re-check the resolved IP
        on every redirect hop — this model has no network to resolve against, so
        it refuses names it cannot prove public."""
        try:
            u = urlsplit(url.strip())
        except ValueError:
            return True
        if u.scheme not in ("http", "https") or not u.hostname:
            return True
        host = u.hostname.lower().rstrip(".")
        ip = self._parse_ip(host)
        if ip is not None:
            mapped = getattr(ip, "ipv4_mapped", None)
            ip = mapped or ip
            return not ip.is_global
        if host == "localhost" or "." not in host:
            return True
        return host.endswith((".localhost", ".local", ".internal", ".lan", ".home.arpa"))

    @staticmethod
    def _parse_ip(host):
        try:
            return ipaddress.ip_address(host)
        except ValueError:
            pass
        # inet_aton-style IPv4: 2130706433, 0x7f000001, 017700000001, 127.1 …
        parts = host.split(".")
        if not 1 <= len(parts) <= 4:
            return None
        try:
            nums = [int(p, 16) if p.lower().startswith("0x") else
                    int(p, 8) if len(p) > 1 and p.startswith("0") else int(p) for p in parts]
        except ValueError:
            return None
        if any(n < 0 for n in nums) or any(n > 255 for n in nums[:-1]):
            return None
        tail_bytes = 5 - len(nums)
        if nums[-1] >= 256 ** tail_bytes:
            return None
        value = nums[-1]
        for i, n in enumerate(nums[:-1]):
            value += n << (8 * (3 - i))
        return ipaddress.ip_address(value)

    # ---- password reset ----------------------------------------------------
    def reset_request(self, email, host_header="app.example"):
        # uniform response regardless of whether the email exists (no enumeration)
        user = next((u for u, d in self.users.items() if d["email"] == email), None)
        link = None
        if user:
            tok = secrets.token_urlsafe(24)
            self.reset_tokens[tok] = dict(user=user, exp=int(time.time()) + 900, used=False)
            # link built from TRUSTED config, never the Host header
            link = f"{CONFIG_BASE_URL}/reset?token={tok}"
        return Resp(200, dict(SECURE_HEADERS),
                    {"message": "If the account exists, an email was sent.",
                     "_link_for_test": link})

    def reset_confirm(self, token, new_pw):
        if self.reset_guess_fails >= self.RESET_GUESS_LIMIT:
            return self._resp(429, {"error": "too many attempts"})   # token guessing
        rec = self.reset_tokens.get(token)
        if not rec or rec["used"] or rec["exp"] < int(time.time()):
            self.reset_guess_fails += 1
            return self._resp(400, {"error": "invalid or expired"})
        rec["used"] = True
        self.users[rec["user"]]["pw"] = new_pw
        for jti in list(self.user_jtis.get(rec["user"], [])):
            self.revoked_jti.add(jti)                 # reset kills sessions
        self._kill_refresh(rec["user"])
        # NO session is issued here: the user signs in again and passes MFA
        return self._resp(200, {"status": "reset"})

    # ---- OAuth2 / PKCE -----------------------------------------------------
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        cl = self.oauth_clients.get(client_id)
        if not cl:
            return self._resp(400, {"error": "unknown client"})
        if redirect_uri not in cl["redirect_uris"]:          # exact match only
            return self._resp(400, {"error": "bad redirect_uri"})
        if cl["public"] and not code_challenge:              # PKCE mandatory
            return self._resp(400, {"error": "pkce required"})
        if not state:                                        # CSRF on callback
            return self._resp(400, {"error": "state required"})
        code = secrets.token_hex(8)
        self.oauth_codes[code] = dict(client=client_id, redirect_uri=redirect_uri,
                                      challenge=code_challenge, used=False)
        return self._resp(200, {"code": code, "state": state})

    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        rec = self.oauth_codes.get(code)
        if not rec or rec["used"]:
            return self._resp(400, {"error": "invalid code"})
        if rec["client"] != client_id or rec["redirect_uri"] != redirect_uri:
            return self._resp(400, {"error": "client/redirect mismatch"})
        if rec["challenge"] and s256(code_verifier or "") != rec["challenge"]:
            return self._resp(400, {"error": "pkce verify failed"})
        rec["used"] = True                                    # single-use
        return self._resp(200, {"access_token": self._issue_access(
            "alice", "user", 1, True)})

    # ---- error handling ----------------------------------------------------
    def buggy_endpoint(self, payload):
        try:
            return self._resp(200, {"parsed": int(payload)})
        except Exception:
            return self._resp(400, {"error": "bad request"})   # no stack trace

    # ---- attack surface -----------------------------------------------------
    def fetch_path(self, where, path):
        """Only the app itself is served: no dotfiles, no backups, no debug or
        management endpoints, on either origin."""
        if where == "frontend" and path in ("/", "/index.html"):
            return Resp(200, dict(FRONTEND_HEADERS), {"_text": FRONTEND_PAGE})
        if where == "frontend" and path == "/assets/app.js":
            return Resp(200, dict(FRONTEND_HEADERS), {"_text": FRONTEND_JS})
        return self._resp(404, {"error": "not found"})

    def frontend_assets(self):
        return [("/", FRONTEND_PAGE), ("/assets/app.js", FRONTEND_JS)]   # no secrets shipped

    def cors_probe(self, token, origin, preflight=False):
        """Cross-origin access is granted to ONE configured origin, never to
        whatever Origin the request names (and never to "null")."""
        r = self._resp(204 if preflight else 200)
        if origin == FRONTEND_ORIGIN:
            r.headers.update({"Access-Control-Allow-Origin": origin,
                              "Access-Control-Allow-Credentials": "true", "Vary": "Origin"})
        return r

    # ---- resilience --------------------------------------------------------
    def stress_input(self, kind):
        """Pathological input is refused CHEAPLY, before any expensive parsing:
        size and shape limits answer 4xx, they never crash or stall the worker."""
        status = {
            "oversize": 413,        # body larger than the endpoint's limit
            "deep-json": 400,       # nesting depth limit
            "wide-json": 400,       # key-count limit
            "gzip-bomb": 415,       # compressed request bodies are not accepted
            "bad-encoding": 415,
            "bad-charset": 415,     # only utf-8 JSON
            "many-parts": 400,      # part-count limit
            "long-accept": 431,     # header size limit
        }.get(kind)
        if status is None:
            raise ValueError(f"unknown stress kind: {kind}")
        return self._resp(status, {"error": "request refused"})
