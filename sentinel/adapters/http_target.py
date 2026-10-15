"""
HttpTarget — the real adapter. Turns the abstract Target operations into HTTP
calls against the configured backend (host/port/base_path/endpoints). This is
the class you point at your other project.

Every method is a thin, documented mapping. Backends differ, so the places most
likely to need tweaking (field names, how a token is returned, how CSRF/step-up
are signalled) are read from config or marked with  # ADAPT.
"""
from __future__ import annotations

import requests

from .base import Target, Resp, Capability
from ..config import Config, dotget


class HttpTarget(Target):
    name = "http"

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._client = requests.Session()
        self._client.verify = cfg.verify_tls

    # ---- capabilities derived from config -------------------------------
    def capabilities(self):
        caps = set()
        if "user2" in self.cfg.users:
            caps.add(Capability.TWO_ACCOUNTS)
        if "oauth" in self.cfg.features:
            caps.add(Capability.OAUTH)
        if "media_upload" in self.cfg.features:
            caps.add(Capability.MEDIA_UPLOAD)
        if self.cfg.jwks_url:
            caps.add(Capability.SIGNING_KEY)
        h = self.cfg.hooks
        if h.get("user_admin"):
            caps.add(Capability.USER_ADMIN)
        if h.get("db_probe"):
            caps.add(Capability.DB_PROBE)
        if h.get("reset_introspect"):
            caps.add(Capability.RESET_INTROSPECT)
        if h.get("other_aud_token"):
            caps.add(Capability.OTHER_AUD_TOKEN)
        return caps

    def reset(self):
        ep = self.cfg.hooks.get("reset")
        if ep:
            method, path = ep.split(" ", 1)
            self._call(method.upper(), path)

    # ---- request plumbing ------------------------------------------------
    def _spec(self, name):
        method, path = self.cfg.endpoints[name].split(" ", 1)
        return method.upper(), path

    def _url(self, path):  # path already formatted
        return f"{self.cfg.base_url}{path}"

    def _auth(self, token):
        name, _, tmpl = self.cfg.auth_header.partition(": ")
        return {name: tmpl.format(token=token)}

    def _call(self, method, path, *, headers=None, json=None, data=None, files=None, raw_path=False):
        url = self._url(path) if not raw_path else f"{self.cfg.base_url}{path}"
        try:
            r = self._client.request(method, url, headers=headers or {}, json=json,
                                     data=data, files=files, timeout=self.cfg.timeout_s,
                                     allow_redirects=False)
        except Exception as e:
            return Resp(0, {}, {"error": f"transport: {e}"})
        try:
            body = r.json()
            if not isinstance(body, dict):
                body = {"_raw": body}
        except Exception:
            body = {"_text": r.text[:2000]}
        return Resp(r.status_code, dict(r.headers), body)

    # ---- auth ------------------------------------------------------------
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True, prev_session=None):
        m, p = self._spec("login")
        f = self.cfg.fields
        payload = {f["username"]: username, f["password"]: password,
                   f["otp"]: ("000000" if otp_ok else "bad-otp")}
        headers = {"X-Forwarded-For": xff or source_ip}      # ADAPT: your real client-IP header
        if prev_session:
            headers["Cookie"] = f"sid={prev_session}"
        r = self._call(m, p, headers=headers, json=payload)
        # normalize: lift the token into a stable key the suites use
        tok = dotget(r.body, self.cfg.token_json_path)
        ref = dotget(r.body, self.cfg.refresh_json_path)
        if tok and "access_token" not in r.body:
            r.body["access_token"] = tok
        if ref and "refresh_token" not in r.body:
            r.body["refresh_token"] = ref
        # expose a session id if the server sets one, for the fixation check
        sc = r.headers.get("set-cookie", "")
        if "sid=" in sc:
            r.body.setdefault("sid", sc.split("sid=")[1].split(";")[0])
        return r

    def logout(self, token):
        m, p = self._spec("logout"); return self._call(m, p, headers=self._auth(token))

    def refresh_token(self, rtok):
        m, p = self._spec("refresh")
        return self._call(m, p, json={self.cfg.fields["token"]: rtok})

    def register(self, username, password, requested_role=None, extra=None):
        m, p = self._spec("register")
        f = self.cfg.fields
        body = {f["username"]: username, f["password"]: password}
        if requested_role is not None:
            body["role"] = requested_role
        if extra:
            body.update(extra)
        return self._call(m, p, json=body)

    # ---- resources -------------------------------------------------------
    def get_resource(self, token, owner_id):
        m, p = self._spec("resource")
        return self._call(m, p.format(owner_id=owner_id), headers=self._auth(token))

    def get_object(self, token, kind, obj_id):
        m, p = self._spec("object")
        return self._call(m, p.format(kind=kind, id=obj_id), headers=self._auth(token))

    def admin_users(self, token):
        m, p = self._spec("admin_users"); return self._call(m, p, headers=self._auth(token))

    def admin_delete_user(self, token, target, method="DELETE"):
        _, p = self._spec("admin_delete")
        return self._call(method, p.format(target=target), headers=self._auth(token))

    # ---- state-changing --------------------------------------------------
    def _mutate_headers(self, token, reauthed, csrf_ok, cross_site):
        h = dict(self._auth(token))
        if cross_site:
            h["Origin"] = "https://evil.example"            # ADAPT to your CSRF signal
        elif csrf_ok:
            h["X-CSRF-Token"] = "test-csrf-token"
        if reauthed:
            h["X-Step-Up"] = "reauthed"                     # ADAPT to your step-up signal
        return h

    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        m, p = self._spec("change_password")
        return self._call(m, p, headers=self._mutate_headers(token, reauthed, csrf_ok, cross_site),
                          json={"old": old, self.cfg.fields["new_password"]: new})

    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        m, p = self._spec("sensitive")
        return self._call(m, p, headers=self._mutate_headers(token, reauthed, csrf_ok, cross_site),
                          json={"amount": 1})

    def change_email(self, token, new_email, reverified=False):
        m, p = self._spec("change_email")
        h = self._auth(token)
        if reverified:
            h["X-Email-Verified"] = "true"                  # ADAPT
        return self._call(m, p, headers=h, json={self.cfg.fields["email"]: new_email})

    # ---- media -----------------------------------------------------------
    def get_media(self, path):
        _, p = self._spec("media")
        # keep traversal sequences intact (do not url-encode the slashes)
        full = p.replace("{path}", path)
        return self._call("GET", full, raw_path=True)

    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        m, p = self._spec("upload")
        body = {"filename": filename}
        if fetch_url is not None:
            body["fetchUrl"] = fetch_url                    # ADAPT: your "import from URL" field
        if width is not None:
            body["width"] = width; body["height"] = height
        return self._call(m, p, headers=self._auth(token), json=body)

    def upload_bytes(self, token, filename, data, content_type):
        m, p = self._spec("upload")
        files = {"file": (filename, data, content_type)}    # ADAPT: your multipart field name
        return self._call(m, p, headers=self._auth(token), files=files)

    # ---- reset -----------------------------------------------------------
    def reset_request(self, email, host_header="app.example"):
        m, p = self._spec("reset_request")
        r = self._call(m, p, headers={"Host": host_header}, json={self.cfg.fields["email"]: email})
        # in a test profile the backend may echo the link/token for introspection
        return r

    def reset_confirm(self, token, new_pw):
        m, p = self._spec("reset_confirm")
        return self._call(m, p, json={self.cfg.fields["token"]: token,
                                      self.cfg.fields["new_password"]: new_pw})

    # ---- oauth -----------------------------------------------------------
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        m, p = self._spec("oauth_authorize")
        q = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri}
        if code_challenge is not None:
            q["code_challenge"] = code_challenge; q["code_challenge_method"] = "S256"
        if state is not None:
            q["state"] = state
        qs = "&".join(f"{k}={v}" for k, v in q.items())
        return self._call(m, f"{p}?{qs}", raw_path=True)

    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        m, p = self._spec("oauth_token")
        return self._call(m, p, data={"grant_type": "authorization_code", "code": code,
                                      "code_verifier": code_verifier or "", "client_id": client_id,
                                      "redirect_uri": redirect_uri})

    # ---- misc ------------------------------------------------------------
    def buggy_endpoint(self, payload):
        m, p = self._spec("buggy")
        return self._call(m, f"{p}?value={payload}", raw_path=True)

    # ---- gray-box hooks (only called when the capability is present) -----
    def issue_access_token(self, username, aud="api"):
        ep = self.cfg.hooks["other_aud_token"]
        method, path = ep.split(" ", 1)
        r = self._call(method.upper(), path.format(aud=aud, username=username))
        return dotget(r.body, self.cfg.token_json_path) or r.body.get("access_token", "")

    def set_enabled(self, username, enabled):
        ep = self.cfg.hooks["user_admin"]
        method, path = ep.split(" ", 1)
        self._call(method.upper(), path.format(username=username),
                   json={"enabled": bool(enabled)})

    def user_field(self, username, field):
        ep = self.cfg.hooks.get("user_admin")
        if not ep:
            return None
        _, path = ep.split(" ", 1)
        r = self._call("GET", path.format(username=username))
        return r.body.get(field)

    def public_key(self):
        # fetch JWKS and build a PEM public key for the RS256->HS256 confusion test
        try:
            r = self._client.get(self.cfg.jwks_url, timeout=self.cfg.timeout_s)
            jwk = r.json()["keys"][0]
            return _jwk_to_pem(jwk)
        except Exception:
            return b""

    def injected_row_exists(self, marker):
        ep = self.cfg.hooks["db_probe"]
        method, path = ep.split(" ", 1)
        r = self._call(method.upper(), path.format(marker=marker))
        return bool(r.ok and (r.body.get("exists") or r.body.get("_raw")))


def _jwk_to_pem(jwk) -> bytes:
    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    def dec(v):
        return int.from_bytes(base64.urlsafe_b64decode(v + "=" * (-len(v) % 4)), "big")

    pub = rsa.RSAPublicNumbers(dec(jwk["e"]), dec(jwk["n"])).public_key()
    return pub.public_bytes(serialization.Encoding.PEM,
                            serialization.PublicFormat.SubjectPublicKeyInfo)
