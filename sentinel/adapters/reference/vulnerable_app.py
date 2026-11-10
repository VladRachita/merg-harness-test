#!/usr/bin/env python3
"""
vulnerable_app.py — the deliberately broken build (NEGATIVE CONTROL ONLY).
Every override is a labelled, textbook vulnerability so the harness can prove it
detects real breaks across every category. NEVER ship anything like this.

The rule this file exists to enforce: EVERY check in EVERY suite must report a
LEAK against this build. A check that still says "blocked" here has no teeth —
it could not detect the flaw it claims to test (tests/test_suites.py asserts it).
"""
import base64
import hmac
import json
import secrets
import threading
import time

from .secure_app import SecureApp, Resp, API_AUD


class VulnerableApp(SecureApp):

    def __init__(self):
        super().__init__()
        self._in_flight = 0
        self._flight_lock = threading.Lock()

    # VULN: access tokens live for 30 days (a stolen token is good for a month).
    def _issue_access(self, username, role, uid, mfa, aud=API_AUD, ttl=30 * 24 * 3600):
        return super()._issue_access(username, role, uid, mfa, aud=aud, ttl=ttl)

    # VULN: trusts the Host header when building reset links (poisoning).
    def reset_request(self, email, host_header="app.example"):
        # VULN: the e-mail is concatenated into a query — a quote breaks it and
        # the driver error is returned verbatim.
        if "'" in (email or ""):
            return Resp(500, {}, {"error": "SQLSTATE[42601]: syntax error at or near \"'\" in "
                                           f"SELECT id FROM users WHERE email = '{email}'"})
        user = next((u for u, d in self.users.items() if d["email"] == email), None)
        if not user:
            return Resp(404, {}, {"error": "no such user"})      # VULN: enumeration
        tok = secrets.token_urlsafe(24)
        self.reset_tokens[tok] = dict(user=user, exp=int(time.time()) + 999999, used=False)
        return Resp(200, {}, {"message": "sent",
                              "_link_for_test": f"https://{host_header}/reset?token={tok}"})

    # VULN: reset tokens never expire and can be reused; sessions survive; no
    # guess limit; and the reset hands back a full session (skipping MFA).
    def reset_confirm(self, token, new_pw):
        rec = self.reset_tokens.get(token)
        if not rec:
            return Resp(400, {}, {"error": "invalid"})
        self.users[rec["user"]]["pw"] = new_pw                    # no single-use, no revoke
        u = self.users[rec["user"]]
        return Resp(200, {}, {"status": "reset",
                              "access_token": self._issue_access(rec["user"], u["role"], u["id"], True)})

    # VULN: no signature verification; trusts role + sub from the raw claim;
    # never looks at exp, aud, revocation or whether the account is enabled.
    def _verify(self, token):
        try:
            payload = token.split(".")[1]
            payload += "=" * (-len(payload) % 4)
            c = json.loads(base64.urlsafe_b64decode(payload))
        except Exception:
            return None
        return {"sub": c.get("sub", "?"), "uid": c.get("uid", -1),
                "role": c.get("role", "user"), "jti": c.get("jti", ""),
                "mfa": c.get("mfa", True)}

    # VULN: no rate limiting at all; MFA ignored; enumeration via messages;
    # disabled accounts can still sign in; SQL injection in the username.
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True,
              prev_session=None, evasion=None):
        key = self._norm(username)
        u = self.users.get(key)
        if "' or " in key or key.endswith("'--"):
            # VULN: username concatenated into the query -> auth bypass as row 1
            key, u = "alice", self.users["alice"]
        elif not u:
            return Resp(404, {}, {"error": "unknown user"})       # VULN: enumeration
        elif not hmac.compare_digest(self._hash(u["pw"]), self._hash(password or "")):
            return Resp(401, {}, {"error": "wrong password"})     # no counters
        tok = self._issue_access(key, u["role"], u["id"], u["mfa"])
        rtok = secrets.token_hex(16)
        self.refresh[rtok] = dict(family=secrets.token_hex(4), used=False, user=key)
        # VULN: session fixation — reuse the caller-supplied session if present.
        # VULN: the whole user row (password hash included) is serialized back.
        r = Resp(200, {}, {"access_token": tok, "refresh_token": rtok,
                           "sid": prev_session or tok[:16],
                           "user": {"username": key, "role": u["role"],
                                    "password_hash": self._hash(u["pw"])}})
        r.headers["Set-Cookie"] = f"sid={prev_session or 'static-123'}"   # VULN: no flags
        return r

    # VULN: logout does nothing (access AND refresh tokens stay valid).
    def logout(self, token):
        return Resp(200, {}, {"status": "logged out"})

    # VULN: refresh never rotates, no reuse detection, never revoked.
    def refresh_token(self, rtok):
        rec = self.refresh.get(rtok)
        if not rec:
            return Resp(401, {}, {"error": "invalid"})
        return Resp(200, {}, {"access_token": self._issue_access(
            rec["user"], self.users[rec["user"]]["role"], self.users[rec["user"]]["id"], True),
            "refresh_token": rtok})

    # VULN: honours attacker-supplied role + privilege fields (mass assignment);
    # unlimited sign-ups; any password is accepted ("123456" included).
    def register(self, username, password, requested_role=None, extra=None):
        key = self._norm(username)
        if key in self.users:
            return Resp(409, {}, {"error": "exists"})
        e = extra or {}
        self.users[key] = dict(id=99, pw=password, role=requested_role or e.get("role", "user"),
                               enabled=True, mfa=False,
                               verified=e.get("isVerified", False),
                               balance=e.get("balance", 0), email=f"{key}@x.com")
        return Resp(201, {}, {"role": self.users[key]["role"],
                              "verified": self.users[key]["verified"],
                              "balance": self.users[key]["balance"]})

    # VULN: no ownership/role checks anywhere.
    def get_resource(self, token, owner_id):
        return Resp(200, {}, {"secret": self.resources.get(owner_id)})

    def get_object(self, token, kind, obj_id):
        return Resp(200, {}, {"video": obj_id, "owner": self.videos.get(obj_id)})

    # VULN: no token needed, and a client-supplied identity header is believed.
    def admin_users(self, token, spoof=None):
        return Resp(200, {}, {"pii": "ALL_USERS_PII",
                              "as": (spoof or {}).get("X-Remote-User", "anonymous")})

    # VULN: authz only checked for DELETE; other methods skip it.
    def admin_delete_user(self, token, target, method="DELETE"):
        if method != "DELETE":
            return Resp(200, {}, {"deleted": target})             # method confusion
        c = self._verify(token)
        if c and c["role"] == "admin":
            return Resp(200, {}, {"deleted": target})
        return Resp(403, {}, {"error": "admin only"})

    # VULN: no CSRF check, no step-up, sessions and refresh tokens survive.
    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        c = self._verify(token)
        if c and c["sub"] in self.users:
            self.users[c["sub"]]["pw"] = new
        return Resp(200, {}, {"status": "changed"})

    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        return Resp(200, {}, {"status": "done"})

    # VULN: the new address takes effect immediately — no re-verification.
    def change_email(self, token, new_email, reverified=False):
        c = self._verify(token)
        if c and c["sub"] in self.users:
            self.users[c["sub"]]["email"] = new_email
        return Resp(200, {}, {"status": "changed"})

    # VULN: path traversal — serves whatever path is given.
    def get_media(self, path):
        return Resp(200, {}, {"bytes": 2048, "served": path})

    # VULN: fetches any URL (SSRF), no size/rate limits.
    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        return Resp(201, {}, {"stored": filename, "fetched": fetch_url})

    # VULN: no exact redirect match, PKCE optional, state optional, code replayable,
    # and the OAuth state/code land in the SAME token table as reset tokens.
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        code = secrets.token_hex(8)
        self.oauth_codes[code] = dict(client=client_id, redirect_uri=redirect_uri,
                                      challenge=code_challenge, used=False)
        for artefact in (code, state):
            if artefact:                                          # VULN: token-type confusion
                self.reset_tokens[artefact] = dict(user="alice", exp=int(time.time()) + 999999,
                                                   used=False)
        return Resp(200, {}, {"code": code, "state": state})

    # VULN: any code (even an unknown or empty one) and any verifier get a token.
    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        return Resp(200, {}, {"access_token": self._issue_access("alice", "user", 1, True)})

    # VULN: leaks a stack trace on error; and a tiny unguarded worker pool that
    # collapses into 500s the moment a few requests overlap.
    def buggy_endpoint(self, payload):
        with self._flight_lock:
            self._in_flight += 1
            crowded = self._in_flight > 3
        try:
            time.sleep(0.02)
            if crowded:
                return Resp(500, {}, {"error": "pool exhausted: no worker available"})
            return Resp(200, {}, {"parsed": int(payload)})
        except Exception as e:
            return Resp(500, {}, {"trace": f"java.lang.NumberFormatException at "
                                           f"com.example.Parser.parse({payload})... {e}"})
        finally:
            with self._flight_lock:
                self._in_flight -= 1

    # VULN: the web root is the project directory — dotfiles, the git repo and
    # the framework's management endpoints are all served to anyone.
    EXPOSED = {
        "/.env": "APP_ENV=production\nDB_PASSWORD=hunter2-example\nJWT_SECRET=example-not-a-real-secret\n",
        "/.git/config": "[core]\n\trepositoryformatversion = 0\n[remote \"origin\"]\n\turl = git@example:app.git\n",
        "/.git/HEAD": "ref: refs/heads/main\n",
        "/actuator/env": '{"activeProfiles": ["prod"], "propertySources": [{"name": "systemEnvironment"}]}',
        "/backup.sql": "-- dump\nCREATE TABLE users (id int, password_hash text);\n",
    }

    def fetch_path(self, where, path):
        if path in self.EXPOSED:
            return Resp(200, {}, {"_text": self.EXPOSED[path]})
        if where == "frontend" and path in ("/", "/index.html"):
            return Resp(200, {}, {"_text": self._page()})        # VULN: no security headers
        return Resp(404, {}, {"error": "not found"})

    @staticmethod
    def _page():
        return ('<!doctype html><html><head><title>App</title>'
                '<script src="/assets/app.js"></script></head><body></body></html>')

    # VULN: server-side credentials compiled into the browser bundle. (The key
    # id is AWS's published documentation example, not a real credential.)
    def frontend_assets(self):
        js = ('const cfg = {awsAccessKeyId: "AKIAIOSFODNN7EXAMPLE", '
              'client_secret: "example-client-secret-0123456789"};')
        return [("/", self._page()), ("/assets/app.js", js)]

    # VULN: CORS reflects whatever Origin asks, with credentials allowed.
    def cors_probe(self, token, origin, preflight=False):
        return Resp(204 if preflight else 200,
                    {"Access-Control-Allow-Origin": origin,
                     "Access-Control-Allow-Credentials": "true"}, {})

    # VULN: no size/shape limits — pathological input reaches the parser and
    # the request dies with an unhandled error.
    def stress_input(self, kind):
        return Resp(500, {}, {"error": f"unhandled exception while parsing request ({kind})"})
