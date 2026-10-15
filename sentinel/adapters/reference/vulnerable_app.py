#!/usr/bin/env python3
"""
vulnerable_app.py — the deliberately broken build (NEGATIVE CONTROL ONLY).
Every override is a labelled, textbook vulnerability so the harness can prove it
detects real breaks across every category. NEVER ship anything like this.
"""
import base64
import hashlib
import hmac
import json
import secrets
import time

import jwt

from .secure_app import SecureApp, Resp, s256, ISS, API_AUD


class VulnerableApp(SecureApp):

    # VULN: trusts the Host header when building reset links (poisoning).
    def reset_request(self, email, host_header="app.example"):
        user = next((u for u, d in self.users.items() if d["email"] == email), None)
        if not user:
            return Resp(404, {}, {"error": "no such user"})      # VULN: enumeration
        tok = secrets.token_urlsafe(24)
        self.reset_tokens[tok] = dict(user=user, exp=int(time.time()) + 999999, used=False)
        return Resp(200, {}, {"message": "sent",
                              "_link_for_test": f"https://{host_header}/reset?token={tok}"})

    # VULN: reset tokens never expire and can be reused; sessions survive.
    def reset_confirm(self, token, new_pw):
        rec = self.reset_tokens.get(token)
        if not rec:
            return Resp(400, {}, {"error": "invalid"})
        self.users[rec["user"]]["pw"] = new_pw                    # no single-use, no revoke
        return Resp(200, {}, {"status": "reset"})

    # VULN: no signature verification; trusts role + sub from the raw claim.
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

    # VULN: no rate limiting at all; MFA ignored; enumeration via messages.
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True,
              prev_session=None):
        key = self._norm(username)
        u = self.users.get(key)
        if not u:
            return Resp(404, {}, {"error": "unknown user"})       # VULN: enumeration
        if not hmac.compare_digest(self._hash(u["pw"]), self._hash(password or "")):
            return Resp(401, {}, {"error": "wrong password"})     # no counters
        tok = self._issue_access(key, u["role"], u["id"], u["mfa"])
        # VULN: session fixation — reuse the caller-supplied session if present.
        r = Resp(200, {}, {"access_token": tok, "sid": prev_session or tok[:16]})
        r.headers["Set-Cookie"] = "sid=static-123"                # VULN: no flags
        return r

    # VULN: logout does nothing (token stays valid).
    def logout(self, token):
        return Resp(200, {}, {"status": "logged out"})

    # VULN: refresh never rotates, no reuse detection.
    def refresh_token(self, rtok):
        rec = self.refresh.get(rtok)
        if not rec:
            return Resp(401, {}, {"error": "invalid"})
        return Resp(200, {}, {"access_token": self._issue_access(
            rec["user"], self.users[rec["user"]]["role"], self.users[rec["user"]]["id"], True),
            "refresh_token": rtok})

    # VULN: honours attacker-supplied role + privilege fields (mass assignment).
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

    def admin_users(self, token):
        return Resp(200, {}, {"pii": "ALL_USERS_PII"})

    # VULN: authz only checked for DELETE; other methods skip it.
    def admin_delete_user(self, token, target, method="DELETE"):
        if method != "DELETE":
            return Resp(200, {}, {"deleted": target})             # method confusion
        c = self._verify(token)
        if c and c["role"] == "admin":
            return Resp(200, {}, {"deleted": target})
        return Resp(403, {}, {"error": "admin only"})

    # VULN: no CSRF check, no step-up.
    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        return Resp(200, {}, {"status": "changed"})

    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        return Resp(200, {}, {"status": "done"})

    def change_email(self, token, new_email, reverified=False):
        return Resp(200, {}, {"status": "changed"})               # no re-verification

    # VULN: path traversal — serves whatever path is given.
    def get_media(self, path):
        return Resp(200, {}, {"bytes": 2048, "served": path})

    # VULN: fetches any URL (SSRF), no size/rate limits.
    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        return Resp(201, {}, {"stored": filename, "fetched": fetch_url})

    # VULN: no exact redirect match, PKCE optional, state optional, code replayable.
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        code = secrets.token_hex(8)
        self.oauth_codes[code] = dict(client=client_id, redirect_uri=redirect_uri,
                                      challenge=code_challenge, used=False)
        return Resp(200, {}, {"code": code, "state": state})

    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        rec = self.oauth_codes.get(code)
        if not rec:
            return Resp(400, {}, {"error": "invalid"})
        return Resp(200, {}, {"access_token": self._issue_access("alice", "user", 1, True)})

    # VULN: leaks a stack trace on error.
    def buggy_endpoint(self, payload):
        try:
            return Resp(200, {}, {"parsed": int(payload)})
        except Exception as e:
            return Resp(500, {}, {"trace": f"java.lang.NumberFormatException at "
                                           f"com.example.Parser.parse({payload})... {e}"})
