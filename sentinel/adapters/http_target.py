"""
HttpTarget — the real adapter. Turns the abstract Target operations into HTTP
calls against the configured backend (host/port/base_path/endpoints). This is
the class you point at your other project.

Every method is a thin, documented mapping. Backends differ, so everything that
varies — routes, field names, how a token is returned, how CSRF / step-up / the
client IP are signalled — is read from config (`endpoints`, `fields`,
`signals`); nothing here should need editing per project.

Three properties keep results trustworthy:
  * a request that gets NO answer raises `Unreachable` — it is never mistaken
    for "the attack was refused";
  * no cookie jar: each request carries only what the check put on it, so an
    "unauthenticated" attack is really unauthenticated;
  * paths can be sent verbatim (`raw=True`), so `../` reaches the server instead
    of being tidied away by the HTTP client.
"""
from __future__ import annotations

import collections
import gzip
import http.cookiejar
import os
import re
import secrets
import time
from urllib.parse import quote, urlencode, urljoin, urlsplit, urlunsplit, parse_qs

import requests

from .base import Target, Resp, Capability, Inconclusive, Unreachable
from ..config import Config, dotget, split_spec
from ..safety import Pacer

VERSION = "2"
ASSET_CAP = 2_000_000          # bytes of one front-end script scanned for secrets
MAX_SCRIPTS = 15
_SCRIPT_SRC = re.compile(r"<script[^>]+src=[\"']([^\"']+)[\"']", re.I)


def _variant(url: str, kind: str) -> str:
    """An equivalent spelling of a URL's path, as a bot would try to get past a
    limiter that keys on the literal route."""
    u = urlsplit(url)
    path, query = u.path, u.query
    if kind == "trailing-slash":
        path = path.rstrip("/") + "/"
    elif kind == "upper":
        path = path.upper()
    elif kind == "double-slash":
        path = "/" + path
    elif kind == "matrix":
        path = path + ";sentinel=1"
    elif kind == "junk-query":
        query = (query + "&" if query else "") + "sentinel=1"
    elif kind == "dot-segment":
        head, _, tail = path.rpartition("/")
        path = f"{head}/./{tail}"
    else:
        raise ValueError(f"unknown path variant: {kind}")
    return urlunsplit((u.scheme, u.netloc, path, query, u.fragment))


class HttpTarget(Target):
    name = "http"

    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._client = requests.Session()
        self._client.verify = cfg.verify_tls
        # never persist cookies between requests (see module docstring)
        self._client.cookies.set_policy(http.cookiejar.DefaultCookiePolicy(allowed_domains=[]))
        self.run_id = secrets.token_hex(4)
        # identify our traffic, so it is attributable in the backend's logs
        self._client.headers["User-Agent"] = (
            f"appsec-sentinel/{VERSION} (authorized security test; run {self.run_id})")
        self._attack = ""
        self._trace = collections.deque(maxlen=4)
        self._pacer = Pacer(cfg.safety.get("max_rps"), cfg.safety.get("max_requests"))
        self.requests_sent = 0

    # ---- capabilities derived from config -------------------------------
    def capabilities(self):
        caps = set()
        feats = set(self.cfg.features)
        if "user2" in self.cfg.users:
            caps.add(Capability.TWO_ACCOUNTS)
        for name, cap in (("oauth", Capability.OAUTH), ("media_upload", Capability.MEDIA_UPLOAD),
                          ("mfa", Capability.MFA), ("csrf", Capability.CSRF)):
            if name in feats:
                caps.add(cap)
        if self.cfg.jwks_url:
            caps.add(Capability.SIGNING_KEY)
        if self.cfg.frontend_origin:
            caps.add(Capability.FRONTEND)
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

    def begin_attack(self, attack_id):
        self._attack = attack_id
        self._trace.clear()

    def evidence(self):
        return "; ".join(self._trace)

    def reset(self):
        if self.cfg.hooks.get("reset"):
            r = self._hook("reset")
            if not r.ok:
                raise Inconclusive(f"hooks.reset failed (HTTP {r.status}) — state would bleed "
                                   f"between attacks")

    # ---- request plumbing ------------------------------------------------
    def _auth(self, token):
        if not token:
            return {}                       # truly unauthenticated: no header at all
        name, _, tmpl = self.cfg.auth_header.partition(": ")
        return {name: tmpl.format(token=token)}

    def _signal(self, key):
        """A configured 'Name: value' signal header as a dict ({} when unset)."""
        raw = self.cfg.signals.get(key) or ""
        name, sep, value = raw.partition(":")
        return {name.strip(): value.strip()} if sep and name.strip() else {}

    def _call(self, method, path, *, headers=None, json=None, data=None, files=None,
              raw=False, variant=None, timeout=None, text_cap=2000):
        url = self.cfg.url_for(path)
        if variant:
            url, raw = _variant(url, variant), True
        hdrs = dict(headers or {})
        if self.cfg.safety.get("tag_requests", True):
            hdrs.setdefault("X-Sentinel-Run", self.run_id)
            if self._attack:
                hdrs.setdefault("X-Sentinel-Check", self._attack)
        self._pacer.tick()
        self.requests_sent += 1
        shown = urlsplit(url).path or "/"
        if urlsplit(url).netloc != urlsplit(self.cfg.base_url).netloc:
            shown = f"{urlsplit(url).netloc}{shown}"         # another origin (front end, hook)
        t0 = time.monotonic()
        try:
            req = requests.Request(method, self.cfg.base_url + "/" if raw else url,
                                   headers=hdrs, json=json, data=data, files=files)
            prepped = self._client.prepare_request(req)
            if raw:
                # send the path exactly as written: the client must not collapse
                # "../", "//" or "/./" before the server sees them
                u = urlsplit(url)
                safe = quote(u.path, safe="/%;:@&=+$,.~-_!*'()")
                prepped.url = urlunsplit((u.scheme, u.netloc, safe, u.query, ""))
            env = self._client.merge_environment_settings(prepped.url, {}, None, None, None)
            r = self._client.send(prepped, timeout=timeout or self.cfg.timeout_s,
                                  allow_redirects=False, **env)
        except requests.RequestException as e:
            self._trace.append(f"{method} {shown} → no response")
            raise Unreachable(f"{method} {shown}: no response from {urlsplit(url).netloc} "
                              f"({type(e).__name__})") from None
        elapsed = time.monotonic() - t0
        try:
            body = r.json()
            if not isinstance(body, dict):
                body = {"_raw": body}
        except Exception:
            body = {"_text": r.text[:text_cap]}
        try:
            cookies = list(r.raw.headers.getlist("Set-Cookie"))
        except Exception:
            cookies = []
        self._trace.append(f"{method} {shown} → {r.status_code}")
        return Resp(r.status_code, dict(r.headers), body, cookies, elapsed)

    def _endpoint(self, name, **kw):
        m, p = self.cfg.spec(name)
        return self._call(m, p, **kw)

    def _hook(self, name, json=None, method=None, **params):
        m, p = split_spec(self.cfg.hooks[name], f"hooks.{name}")
        p = p.format(**{k: quote(str(v), safe="") for k, v in params.items()})
        return self._call(method or m, p, json=json)

    # ---- auth ------------------------------------------------------------
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True,
              prev_session=None, evasion=None):
        m, p = self.cfg.spec("login")
        f = self.cfg.fields
        payload = {f["username"]: username, f["password"]: password}
        if f.get("otp"):
            payload[f["otp"]] = "000000" if otp_ok else "bad-otp"
        headers = {}
        ip_header = self.cfg.signals.get("client_ip_header")
        if ip_header:
            headers[ip_header] = xff or source_ip
        if prev_session:
            headers["Cookie"] = f"{self.cfg.session_cookie}={prev_session}"
        ev = evasion or {}
        headers.update(ev.get("headers") or {})
        if ev.get("form"):
            r = self._call(m, p, headers=headers, data=payload, variant=ev.get("path"))
        else:
            r = self._call(m, p, headers=headers, json=payload, variant=ev.get("path"))
        # normalize: lift the token into a stable key the suites use
        tok = dotget(r.body, self.cfg.token_json_path)
        ref = dotget(r.body, self.cfg.refresh_json_path)
        if tok and "access_token" not in r.body:
            r.body["access_token"] = tok
        if ref and "refresh_token" not in r.body:
            r.body["refresh_token"] = ref
        # expose the session id if the server sets one (fixation / cookie-auth)
        prefix = f"{self.cfg.session_cookie}="
        for c in r.cookies():
            if c.strip().startswith(prefix):
                sid = c.strip()[len(prefix):].split(";")[0]
                r.body["sid"] = sid
                if r.ok and "access_token" not in r.body and \
                        self.cfg.auth_header.lower().startswith("cookie"):
                    r.body["access_token"] = sid      # cookie-session backends
        return r

    def logout(self, token):
        return self._endpoint("logout", headers=self._auth(token))

    def refresh_token(self, rtok):
        return self._endpoint("refresh", json={self.cfg.fields["token"]: rtok})

    def register(self, username, password, requested_role=None, extra=None):
        f = self.cfg.fields
        body = {f["username"]: username, f["password"]: password}
        if f.get("email") and f["email"] not in body:
            body[f["email"]] = username if "@" in str(username) else f"{username}@sentinel.test"
        if extra:
            body.update(extra)
        if requested_role is not None:
            body[f.get("role") or "role"] = requested_role
        return self._endpoint("register", json=body)

    # ---- resources -------------------------------------------------------
    def get_resource(self, token, owner_id):
        m, p = self.cfg.spec("resource")
        return self._call(m, p.format(owner_id=owner_id), headers=self._auth(token))

    def get_object(self, token, kind, obj_id):
        m, p = self.cfg.spec("object")
        return self._call(m, p.format(kind=kind, id=obj_id), headers=self._auth(token))

    def admin_users(self, token, spoof=None):
        return self._endpoint("admin_users", headers={**self._auth(token), **(spoof or {})})

    def admin_delete_user(self, token, target, method="DELETE"):
        _, p = self.cfg.spec("admin_delete")
        return self._call(method, p.format(target=quote(str(target), safe="")),
                          headers=self._auth(token))

    # ---- state-changing --------------------------------------------------
    def _mutate_headers(self, token, reauthed, csrf_ok, cross_site):
        h = dict(self._auth(token))
        if cross_site:
            h["Origin"] = self.cfg.signals.get("cross_site_origin") or "https://evil.example"
            h["Sec-Fetch-Site"] = "cross-site"
        elif csrf_ok:
            h.update(self._signal("csrf_header"))
        if reauthed:
            h.update(self._signal("step_up_header"))
        return h

    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        f = self.cfg.fields
        return self._endpoint("change_password",
                              headers=self._mutate_headers(token, reauthed, csrf_ok, cross_site),
                              json={f.get("old_password") or "old": old, f["new_password"]: new})

    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        return self._endpoint("sensitive",
                              headers=self._mutate_headers(token, reauthed, csrf_ok, cross_site),
                              json={"amount": 1})

    def change_email(self, token, new_email, reverified=False):
        h = self._auth(token)
        if reverified:
            h.update(self._signal("email_verified_header"))
        return self._endpoint("change_email", headers=h, json={self.cfg.fields["email"]: new_email})

    # ---- media -----------------------------------------------------------
    def get_media(self, path):
        _, p = self.cfg.spec("media")
        # verbatim: traversal sequences must reach the server intact
        return self._call("GET", p.replace("{path}", path), raw=True)

    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        body = {"filename": filename}
        if fetch_url is not None:
            body[self.cfg.fields.get("fetch_url") or "fetchUrl"] = fetch_url
        if width is not None:
            body["width"] = width; body["height"] = height
        return self._endpoint("upload", headers=self._auth(token), json=body)

    def upload_bytes(self, token, filename, data, content_type):
        field = self.cfg.fields.get("upload_file") or "file"
        return self._endpoint("upload", headers=self._auth(token),
                              files={field: (filename, data, content_type)})

    # ---- reset -----------------------------------------------------------
    def reset_request(self, email, host_header="app.example"):
        # only override Host when a check is deliberately spoofing it
        headers = {} if host_header == "app.example" else {"Host": host_header}
        return self._endpoint("reset_request", headers=headers,
                              json={self.cfg.fields["email"]: email})

    def reset_confirm(self, token, new_pw):
        f = self.cfg.fields
        return self._endpoint("reset_confirm", json={f["token"]: token, f["new_password"]: new_pw})

    # ---- oauth -----------------------------------------------------------
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        m, p = self.cfg.spec("oauth_authorize")
        q = {"response_type": "code", "client_id": client_id, "redirect_uri": redirect_uri}
        if code_challenge is not None:
            q["code_challenge"] = code_challenge; q["code_challenge_method"] = "S256"
        if state is not None:
            q["state"] = state
        r = self._call(m, f"{p}?{urlencode(q)}")
        # Real authorization servers answer with a redirect. A redirect that
        # delivers a code to the requested redirect_uri IS a successful grant.
        if 300 <= r.status < 400:
            loc = r.header("location") or ""
            parts = urlsplit(loc)
            got = {**parse_qs(parts.fragment), **parse_qs(parts.query)}
            if "code" in got and loc.startswith(redirect_uri):
                return Resp(200, r.headers, {"code": got["code"][0],
                                             "state": (got.get("state") or [None])[0]},
                            r.set_cookies, r.elapsed_s)
            if "error" in got:
                return Resp(400, r.headers, {"error": got["error"][0]}, r.set_cookies, r.elapsed_s)
        return r

    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        return self._endpoint("oauth_token", data={
            "grant_type": "authorization_code", "code": code,
            "code_verifier": code_verifier or "", "client_id": client_id,
            "redirect_uri": redirect_uri})

    # ---- misc ------------------------------------------------------------
    def buggy_endpoint(self, payload):
        m, p = self.cfg.spec("buggy")
        return self._call(m, f"{p}?value={quote(str(payload), safe='')}")

    # ---- attack surface --------------------------------------------------
    def fetch_path(self, where, path):
        origin = self.cfg.origin_of(where)
        if not origin:
            raise Inconclusive(f"no {where} origin configured (set frontend.port)")
        return self._call("GET", origin + path, raw=True)

    def cors_probe(self, token, origin, preflight=False):
        m, p = self.cfg.spec("resource")
        path = p.format(owner_id=self.cfg.users["user"]["id"])
        if preflight:
            return self._call("OPTIONS", path, headers={
                "Origin": origin, "Access-Control-Request-Method": m,
                "Access-Control-Request-Headers": "authorization, content-type"})
        return self._call(m, path, headers={**self._auth(token), "Origin": origin})

    def frontend_assets(self):
        origin = self.cfg.frontend_origin
        if not origin:
            raise Inconclusive("no front end configured (set frontend.port)")
        page = self._call("GET", origin + "/", text_cap=ASSET_CAP)
        html = page.body.get("_text") or ""
        out = [("/", html)]
        for src in _SCRIPT_SRC.findall(html)[:MAX_SCRIPTS]:
            url = urljoin(origin + "/", src)
            if urlsplit(url).netloc != urlsplit(origin).netloc:
                continue                            # a third-party CDN: not ours to scan
            r = self._call("GET", url, text_cap=ASSET_CAP)
            if r.ok and r.body.get("_text"):
                out.append((urlsplit(url).path, r.body["_text"]))
        return out

    # ---- resilience ------------------------------------------------------
    def stress_input(self, kind):
        m, p = self.cfg.spec(self.cfg.stress_endpoint)
        f = self.cfg.fields
        J = {"Content-Type": "application/json"}
        base = '"%s":"sentinel-stress","%s":"Stress-Passw0rd!"' % (f["username"], f["password"])
        timeout = max(float(self.cfg.timeout_s), 20.0)
        if kind == "oversize":
            body = '{%s,"padding":"%s"}' % (base, "A" * 1_000_000)
            return self._call(m, p, headers=J, data=body, timeout=timeout)
        if kind == "deep-json":
            depth = 5000
            body = '{%s,"nest":%s1%s}' % (base, '{"a":' * depth, "}" * depth)
            return self._call(m, p, headers=J, data=body, timeout=timeout)
        if kind == "wide-json":
            body = "{%s,%s}" % (base, ",".join(f'"k{i}":{i}' for i in range(20000)))
            return self._call(m, p, headers=J, data=body, timeout=timeout)
        if kind == "gzip-bomb":
            body = gzip.compress(b"\0" * (16 * 1024 * 1024))
            return self._call(m, p, headers={**J, "Content-Encoding": "gzip"}, data=body,
                              timeout=timeout)
        if kind == "bad-encoding":
            return self._call(m, p, headers={**J, "Content-Encoding": "br"},
                              data=os.urandom(512), timeout=timeout)
        if kind == "bad-charset":
            return self._call(m, p, headers={"Content-Type": "application/json; charset=bz2_codec"},
                              data=("{%s}" % base).encode(), timeout=timeout)
        if kind == "many-parts":
            b = "sentinelboundary"
            parts = "".join(f'--{b}\r\nContent-Disposition: form-data; name="f{i}"\r\n\r\nx\r\n'
                            for i in range(2000))
            return self._call(m, p, data=(parts + f"--{b}--\r\n").encode(), timeout=timeout,
                              headers={"Content-Type": f"multipart/form-data; boundary={b}"})
        if kind == "long-accept":
            accept = ",".join(f"a{i}/b{i};q=0.{i % 9 + 1}" for i in range(2000))
            return self._call(m, p, headers={**J, "Accept": accept}, data=("{%s}" % base),
                              timeout=timeout)
        raise ValueError(f"unknown stress kind: {kind}")

    # ---- gray-box hooks (only called when the capability is present) -----
    def issue_access_token(self, username, aud="api", ttl=None):
        r = self._hook("other_aud_token", aud=aud, username=username,
                       ttl="" if ttl is None else ttl)
        tok = dotget(r.body, self.cfg.token_json_path) or r.body.get("access_token")
        if not tok:
            raise Inconclusive(f"hooks.other_aud_token returned no token (HTTP {r.status})")
        return tok

    def set_enabled(self, username, enabled):
        r = self._hook("user_admin", json={"enabled": bool(enabled)}, username=username)
        if not r.ok:
            raise Inconclusive(f"hooks.user_admin could not update '{username}' (HTTP {r.status})")

    def user_field(self, username, field):
        if not self.cfg.hooks.get("user_admin"):
            return None
        r = self._hook("user_admin", method="GET", username=username)
        if r.status == 404:
            return None
        if not r.ok:
            raise Inconclusive(f"hooks.user_admin could not read '{username}' (HTTP {r.status})")
        return r.body.get(field)

    def public_key(self):
        # fetch JWKS and build a PEM public key for the RS256->HS256 confusion test
        try:
            self._pacer.tick()
            r = self._client.get(self.cfg.jwks_url, timeout=self.cfg.timeout_s)
            keys = [k for k in r.json()["keys"] if k.get("kty") == "RSA"]
            return _jwk_to_pem(keys[0])
        except Exception as e:
            raise Inconclusive(f"could not fetch an RSA key from jwks_url "
                               f"({type(e).__name__}) — cannot run the confusion test") from None

    def injected_row_exists(self, marker):
        r = self._hook("db_probe", marker=marker)
        if not r.ok:
            raise Inconclusive(f"hooks.db_probe failed (HTTP {r.status})")
        return bool(r.body.get("exists") or r.body.get("_raw"))


def _jwk_to_pem(jwk) -> bytes:
    import base64
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization

    def dec(v):
        return int.from_bytes(base64.urlsafe_b64decode(v + "=" * (-len(v) % 4)), "big")

    pub = rsa.RSAPublicNumbers(dec(jwk["e"]), dec(jwk["n"])).public_key()
    return pub.public_bytes(serialization.Encoding.PEM,
                            serialization.PublicFormat.SubjectPublicKeyInfo)
