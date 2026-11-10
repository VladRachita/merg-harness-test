"""
Configuration: the input parameters that point the harness at a backend.

Precedence (low -> high): built-in defaults  <  YAML file  <  environment vars.
The two parameters you emphasised — port and base path — are SENTINEL_PORT and
SENTINEL_BASE_PATH (or target.port / target.base_path in YAML).

Env var names: SENTINEL_<UPPER_DOTTED_KEY>, dots -> underscores.
  target.scheme        -> SENTINEL_SCHEME
  target.host          -> SENTINEL_HOST
  target.port          -> SENTINEL_PORT
  target.base_path     -> SENTINEL_BASE_PATH
  target.verify_tls    -> SENTINEL_VERIFY_TLS
  endpoints.login      -> SENTINEL_ENDPOINT_LOGIN
  fields.username      -> SENTINEL_FIELD_USERNAME
  jwks_url             -> SENTINEL_JWKS_URL
  safety.allowed_hosts -> SENTINEL_ALLOWED_HOSTS   (comma list)

A config that can't be read is an ERROR, never a silent fall-back to defaults:
testing localhost with demo credentials while believing you tested your app is
the worst possible outcome for a security harness.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from urllib.parse import urlsplit

try:
    import yaml  # optional; env-only config works without it
except Exception:  # pragma: no cover
    yaml = None


class ConfigError(Exception):
    """The configuration is missing or malformed."""


DEFAULT_ENDPOINTS = {
    "login":           "POST /auth/login",
    "logout":          "POST /auth/logout",
    "refresh":         "POST /auth/refresh",
    "register":        "POST /auth/register",
    "admin_users":     "GET /admin/users",
    "admin_delete":    "DELETE /admin/users/{target}",
    "resource":        "GET /resources/{owner_id}",
    "object":          "GET /{kind}s/{id}",
    "change_password": "POST /account/password",
    "sensitive":       "POST /account/payout",
    "change_email":    "POST /account/email",
    "media":           "GET /media/{path}",
    "upload":          "POST /upload",
    "reset_request":   "POST /auth/reset/request",
    "reset_confirm":   "POST /auth/reset/confirm",
    "oauth_authorize": "GET /oauth/authorize",
    "oauth_token":     "POST /oauth/token",
    "buggy":           "GET /debug/parse",
}

DEFAULT_FIELDS = {
    "username": "username", "password": "password", "otp": "otp",
    "email": "email", "token": "token", "new_password": "newPassword",
    # request details that used to need a code edit (# ADAPT) in http_target.py
    "old_password": "old",        # current-password field on change-password
    "role": "role",               # privilege field tried by mass-assignment checks
    "upload_file": "file",        # multipart field name for uploads
    "fetch_url": "fetchUrl",      # "import from URL" field (SSRF checks)
}

# How your backend signals things the suites need to express. Each is a header
# ("Name: value") — set one to "" to stop sending it.
DEFAULT_SIGNALS = {
    "client_ip_header": "X-Forwarded-For",            # header your proxy uses for the client IP
    "csrf_header": "X-CSRF-Token: test-csrf-token",   # what a legitimate same-site write carries
    "cross_site_origin": "https://evil.example",      # Origin sent by the CSRF attack
    "step_up_header": "X-Step-Up: reauthed",          # proof of a fresh re-authentication
    "email_verified_header": "X-Email-Verified: true",  # proof the new e-mail was verified
}

# The web front end, if the project has one on its own port. With a port set,
# the `surface` suite also checks the front end (headers, exposed files, secrets
# shipped in its JavaScript). `api_path` is the prefix under which the front end
# proxies the API (e.g. "/api") — set it to run the API attacks THROUGH the
# front-end port, the way a browser reaches them.
DEFAULT_FRONTEND = {
    "scheme": "http",
    "host": None,          # defaults to target.host
    "port": None,          # no port = no front end configured
    "api_path": None,
}

DEFAULT_SAFETY = {
    # Hosts that are loopback, private, single-label (docker service names) or
    # on a reserved test TLD are always allowed. Anything else — i.e. anything
    # that could be a real, public system — must be listed here explicitly.
    "allowed_hosts": [],
    "max_rps": 0,          # global request pacing; 0 = unpaced
    "max_requests": 0,     # hard budget for one run; 0 = unlimited
    # tag every request with X-Sentinel-Run / X-Sentinel-Check so the traffic is
    # attributable in the backend's logs (which check sent what)
    "tag_requests": True,
}

# How hard the brute-force / bot checks push. Raise these if your limits are
# looser than the reference app's (lock after 5 failures, throttle an IP after 10).
DEFAULT_LIMITS = {
    "lockout_attempts": 6,   # wrong passwords against ONE account
    "spray_attempts": 13,    # failed logins across many accounts from one client
    "burst": 15,             # sign-ups / token guesses in a row
}

DEFAULT_LOAD = {
    "burst_requests": 60,  # size of the concurrent burst (resilience suite)
    "concurrency": 12,
    "p95_ms": 2000,        # acceptable 95th-percentile latency under that burst
    "max_latency_ms": 5000,  # longest ONE pathological request may tie up the server
}

_TOP_LEVEL_KEYS = {
    "target", "frontend", "endpoints", "fields", "signals", "users", "oauth", "hooks", "safety",
    "load", "limits", "bola_object", "token_json_path", "refresh_json_path", "auth_header", "jwks_url",
    "jwt_iss", "jwt_aud", "features", "suites", "fail_on_leak", "fail_on_inconclusive",
    "session_cookie", "throttle_statuses", "media_sample", "xss_reflect_path",
    "stress_endpoint",
}
_TARGET_KEYS = ("scheme", "host", "port", "base_path", "verify_tls", "timeout_s")
_DICT_SECTIONS = ("frontend", "endpoints", "fields", "signals", "users", "oauth", "hooks", "safety",
                  "load", "limits", "bola_object")
_SCALARS = ("token_json_path", "refresh_json_path", "auth_header", "jwks_url", "jwt_iss",
            "jwt_aud", "features", "suites", "fail_on_leak", "fail_on_inconclusive",
            "session_cookie", "throttle_statuses", "media_sample", "xss_reflect_path",
            "stress_endpoint")


@dataclass
class Config:
    # --- target location (the "input parameters") ---
    scheme: str = "http"
    host: str = "localhost"
    port: int = 8080
    base_path: str = ""              # e.g. "/api/v1"
    verify_tls: bool = True
    timeout_s: float = 10.0
    frontend: dict = field(default_factory=lambda: dict(DEFAULT_FRONTEND))
    # set when API traffic is routed through the front-end port: where the
    # backend itself still is (for exposed-file probes and test hooks)
    backend_origin: str | None = None

    # --- how to talk to it ---
    # "METHOD /path" is relative to scheme://host:port/base_path. A project that
    # spans several internal ports can give an absolute URL for any endpoint or
    # hook instead:  login: "POST http://auth:9000/login"
    endpoints: dict = field(default_factory=lambda: dict(DEFAULT_ENDPOINTS))
    fields: dict = field(default_factory=lambda: dict(DEFAULT_FIELDS))
    signals: dict = field(default_factory=lambda: dict(DEFAULT_SIGNALS))
    # dot-path into the login JSON response that holds the access token
    token_json_path: str = "access_token"
    refresh_json_path: str = "refresh_token"
    auth_header: str = "Authorization: Bearer {token}"
    session_cookie: str = "sid"      # name of the session cookie, if the app sets one
    # where to fetch the signing key for the RS256->HS256 confusion test (optional)
    jwks_url: str | None = None
    # expected issuer/audience, so forged tokens match what the backend looks for
    jwt_iss: str = "https://auth.example"
    jwt_aud: str = "api"
    # statuses that mean "rate-limited / locked out" (add 423 if your API uses it)
    throttle_statuses: list = field(default_factory=lambda: [429])

    # --- seed accounts the backend already has (for IDOR/BOLA/login tests) ---
    # role -> {username, password, id, email}
    users: dict = field(default_factory=lambda: {
        "user":   {"username": "alice", "password": "alice-pw", "id": 1, "email": "alice@x.com"},
        "user2":  {"username": "bob",   "password": "bob-pw",   "id": 2, "email": "bob@x.com"},
        "admin":  {"username": "admin", "password": "admin-pw", "id": 3, "email": "admin@x.com"},
    })
    # an object that belongs to `owner` and must NOT be readable by `user` (BOLA)
    bola_object: dict = field(default_factory=lambda: {"kind": "video", "id": 102, "owner": "user2"})
    # a media path that legitimately exists — the positive control for traversal checks
    media_sample: str | None = "intro.mp4"
    # endpoint that receives the pathological inputs of the resilience suite
    stress_endpoint: str = "register"

    # --- OAuth2 client details, if the backend exposes OAuth endpoints ---
    oauth: dict = field(default_factory=lambda: {
        "client_id": "public-app",
        "redirect_uri": "https://app.example/cb",
        "other_client_id": "other-app",
        "other_redirect_uri": "https://other.example/cb",
    })

    # --- gray-box test hooks the backend may expose in a test profile ---
    # Set these only when the backend offers them; otherwise the dependent
    # attacks are reported SKIPPED with guidance.
    hooks: dict = field(default_factory=lambda: {
        "reset": None,            # e.g. "POST /test/reset" — clean state before each attack
        "user_admin": None,       # e.g. "POST /test/users/{username}"
        "db_probe": None,         # e.g. "GET /test/injected?marker={marker}"
        "reset_introspect": False,# True if reset_request returns the token in test mode
        "other_aud_token": None,  # e.g. "GET /test/token?aud={aud}&username={username}&ttl={ttl}"
    })

    # --- optional backend features; attacks for a disabled feature are SKIPPED ---
    #   oauth         OAuth2/PKCE endpoints exist
    #   media_upload  an upload endpoint exists
    #   mfa           the seed accounts have a second factor (OTP)
    #   csrf          auth rides on a cookie, so cross-site requests are a threat
    features: list = field(default_factory=lambda: ["oauth", "media_upload", "mfa", "csrf"])

    # --- which suites to run ---
    suites: list = field(default_factory=lambda: ["access_control", "media_injection"])
    # fail the run (exit 1) if any attack is not blocked
    fail_on_leak: bool = True
    # fail the run (exit 2) if any check could not be proven either way
    fail_on_inconclusive: bool = True

    safety: dict = field(default_factory=lambda: dict(DEFAULT_SAFETY))
    load: dict = field(default_factory=lambda: dict(DEFAULT_LOAD))
    limits: dict = field(default_factory=lambda: dict(DEFAULT_LIMITS))
    xss_reflect_path: str = "/search?q={PAYLOAD}"

    # problems noticed while loading (unknown keys, …) — the CLI prints them
    warnings: list = field(default_factory=list)
    source: str | None = None        # the YAML file this came from, if any

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}{self.base_path}".rstrip("/")

    @property
    def origin(self) -> str:
        """scheme://host:port of the API target, without the base path."""
        return f"{self.scheme}://{self.host}:{self.port}"

    @property
    def frontend_origin(self) -> str | None:
        """scheme://host:port of the front end, or None when none is configured."""
        fe = self.frontend
        if not fe.get("port"):
            return None
        return f"{fe.get('scheme') or 'http'}://{fe.get('host') or self.host}:{fe['port']}"

    def origin_of(self, where: str) -> str | None:
        if where == "frontend":
            return self.frontend_origin
        return self.backend_origin or self.origin

    def url_for(self, path: str) -> str:
        """Absolute URL for an endpoint/hook path. Absolute URLs pass through, so
        one project can reach several internal services/ports."""
        if path.startswith(("http://", "https://")):
            return path
        return f"{self.base_url}{path}"

    def spec(self, name: str):
        """('METHOD', '/path') for a configured endpoint."""
        return split_spec(self.endpoints[name], f"endpoints.{name}")

    def hosts(self) -> set:
        """Every host this config can send traffic to (for the scope guard)."""
        out = {self.host}
        specs = list(self.endpoints.values())
        specs += [v for v in self.hooks.values() if isinstance(v, str)]
        for s in specs:
            path = s.split(" ", 1)[-1]
            if path.startswith(("http://", "https://")):
                out.add(urlsplit(path).hostname or "")
        if self.jwks_url:
            out.add(urlsplit(self.jwks_url).hostname or "")
        for origin in (self.frontend_origin, self.backend_origin):
            if origin:
                out.add(urlsplit(origin).hostname or "")
        return {h for h in out if h}


def split_spec(spec, where="endpoint"):
    try:
        method, path = str(spec).split(" ", 1)
    except ValueError:
        raise ConfigError(f"{where}: expected 'METHOD /path', got {spec!r}")
    path = path.strip()
    if not path.startswith(("/", "http://", "https://")):
        raise ConfigError(f"{where}: path must start with '/' or be an absolute URL, got {spec!r}")
    return method.upper(), path


def _coerce(default, raw):
    if isinstance(default, bool):
        return str(raw).strip().lower() in ("1", "true", "yes", "on")
    if isinstance(default, int) and not isinstance(default, bool):
        return int(raw)
    if isinstance(default, float):
        return float(raw)
    return raw


def load(path: str | None = None) -> Config:
    cfg = Config()
    # 1) YAML file
    path = path or os.environ.get("SENTINEL_CONFIG")
    if path:
        if not os.path.exists(path):
            raise ConfigError(f"config file not found: {path}")
        if yaml is None:
            raise ConfigError("PyYAML not installed but a config file was given")
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            raise ConfigError(f"{path}: top level must be a mapping")
        cfg.source = path
        for k in sorted(set(data) - _TOP_LEVEL_KEYS):
            cfg.warnings.append(f"{path}: unknown key '{k}' ignored (typo?)")
        t = data.get("target") or {}
        for k in sorted(set(t) - set(_TARGET_KEYS)):
            cfg.warnings.append(f"{path}: unknown key 'target.{k}' ignored (typo?)")
        for k in _TARGET_KEYS:
            if k in t:
                setattr(cfg, k, t[k])
        for section in _DICT_SECTIONS:
            if section in data:
                if not isinstance(data[section], dict):
                    raise ConfigError(f"{path}: '{section}' must be a mapping")
                getattr(cfg, section).update(data[section])
        for k in _SCALARS:
            if k in data:
                setattr(cfg, k, data[k])

    # 2) environment overrides
    env = os.environ
    simple = {
        "SENTINEL_SCHEME": "scheme", "SENTINEL_HOST": "host", "SENTINEL_PORT": "port",
        "SENTINEL_BASE_PATH": "base_path", "SENTINEL_VERIFY_TLS": "verify_tls",
        "SENTINEL_TIMEOUT_S": "timeout_s", "SENTINEL_JWKS_URL": "jwks_url",
        "SENTINEL_TOKEN_JSON_PATH": "token_json_path",
        "SENTINEL_AUTH_HEADER": "auth_header",
        "SENTINEL_JWT_ISS": "jwt_iss", "SENTINEL_JWT_AUD": "jwt_aud",
    }
    where = {a: _coerce(getattr(cfg, a), env[ev]) for ev, a in simple.items()
             if ev in env and a in ("scheme", "host", "port", "base_path")}
    retarget(cfg, frontend_host=env.get("SENTINEL_FRONTEND_HOST"),
             frontend_port=env.get("SENTINEL_FRONTEND_PORT"),
             frontend_scheme=env.get("SENTINEL_FRONTEND_SCHEME"), **where)
    for ev, attr in simple.items():
        if ev in env and attr not in where:
            setattr(cfg, attr, _coerce(getattr(cfg, attr), env[ev]))
    for ev, val in env.items():
        if ev.startswith("SENTINEL_ENDPOINT_"):
            cfg.endpoints[ev[len("SENTINEL_ENDPOINT_"):].lower()] = val
        elif ev.startswith("SENTINEL_FIELD_"):
            cfg.fields[ev[len("SENTINEL_FIELD_"):].lower()] = val
    if "SENTINEL_SUITES" in env:
        cfg.suites = [s.strip() for s in env["SENTINEL_SUITES"].split(",") if s.strip()]
    if "SENTINEL_FEATURES" in env:
        cfg.features = [s.strip() for s in env["SENTINEL_FEATURES"].split(",") if s.strip()]
    if "SENTINEL_ALLOWED_HOSTS" in env:
        cfg.safety["allowed_hosts"] = [s.strip() for s in env["SENTINEL_ALLOWED_HOSTS"].split(",")
                                       if s.strip()]
    validate(cfg)
    return cfg


def retarget(cfg: Config, host=None, port=None, scheme=None, base_path=None,
             frontend_host=None, frontend_port=None, frontend_scheme=None,
             frontend_api_path=None) -> Config:
    """Point a loaded config at another host/port/scheme/base path (and front
    end). A `jwks_url` that lived on the old address follows the target, so
    "same app, other port" needs exactly one change."""
    if frontend_host not in (None, ""):
        cfg.frontend["host"] = str(frontend_host).strip()
    if frontend_port is not None:                      # "" clears it
        cfg.frontend["port"] = frontend_port if frontend_port != "" else None
    if frontend_scheme not in (None, ""):
        cfg.frontend["scheme"] = frontend_scheme
    if frontend_api_path is not None:
        cfg.frontend["api_path"] = str(frontend_api_path).strip() or None
    old_origin = f"{cfg.scheme}://{cfg.host}:{cfg.port}"
    if host not in (None, ""):
        cfg.host = str(host).strip()
    if port not in (None, ""):
        cfg.port = port
    if scheme not in (None, ""):
        cfg.scheme = scheme
    if base_path is not None:
        cfg.base_path = str(base_path).strip()
    new_origin = f"{cfg.scheme}://{cfg.host}:{cfg.port}"
    if cfg.jwks_url and cfg.jwks_url.startswith(old_origin + "/"):
        cfg.jwks_url = new_origin + cfg.jwks_url[len(old_origin):]
    return cfg


def route_via_frontend(cfg: Config) -> Config:
    """Send the API traffic through the FRONT-END port (its reverse proxy), the
    way a browser reaches the API. Test hooks and exposed-file probes keep going
    to the backend directly."""
    if not cfg.frontend_origin:
        raise ConfigError("frontend.port is not set — nothing to route through")
    backend_base = cfg.base_url
    cfg.backend_origin = cfg.origin
    for name, spec in list(cfg.hooks.items()):
        if isinstance(spec, str) and spec:
            method, path = split_spec(spec, f"hooks.{name}")
            if not path.startswith(("http://", "https://")):
                cfg.hooks[name] = f"{method} {backend_base}{path}"
    fe = cfg.frontend
    cfg.scheme, cfg.host, cfg.port = fe.get("scheme") or "http", fe.get("host") or cfg.host, fe["port"]
    cfg.base_path = fe.get("api_path") or ""
    validate(cfg)
    return cfg


KNOWN_FEATURES = ("oauth", "media_upload", "mfa", "csrf")


def apply_overrides(cfg: Config, ov: dict) -> Config:
    """Apply flow settings a person typed into the web UI (routes, field names,
    test accounts). Only known keys are accepted and everything is re-validated,
    so the form cannot smuggle in arbitrary configuration."""
    ov = ov if isinstance(ov, dict) else {}
    for name, spec in (ov.get("endpoints") or {}).items():
        if name in DEFAULT_ENDPOINTS and isinstance(spec, str) and spec.strip():
            cfg.endpoints[name] = spec.strip()
    for name, val in (ov.get("fields") or {}).items():
        if name in DEFAULT_FIELDS and isinstance(val, str):
            cfg.fields[name] = val.strip()
    for role, u in (ov.get("users") or {}).items():
        if role not in ("user", "user2", "admin", "lockout") or not isinstance(u, dict):
            continue
        cur = dict(cfg.users.get(role) or {})
        for k in ("username", "password", "email"):
            if isinstance(u.get(k), str) and u[k] != "":
                cur[k] = u[k]
        if u.get("id") not in (None, ""):
            raw = str(u["id"]).strip()
            cur["id"] = int(raw) if raw.lstrip("-").isdigit() else raw
        if cur:
            cfg.users[role] = cur
    for k in ("token_json_path", "refresh_json_path", "auth_header"):
        if isinstance(ov.get(k), str) and ov[k].strip():
            setattr(cfg, k, ov[k].strip())
    if isinstance(ov.get("media_upload"), bool):
        feats = [f for f in cfg.features if f != "media_upload"]
        cfg.features = feats + (["media_upload"] if ov["media_upload"] else [])
    validate(cfg)
    return cfg


def to_dict(cfg: Config) -> dict:
    """A complete, standalone YAML-able form of a config (what the UI saves)."""
    return {
        "target": {"scheme": cfg.scheme, "host": cfg.host, "port": cfg.port,
                   "base_path": cfg.base_path, "verify_tls": cfg.verify_tls,
                   "timeout_s": cfg.timeout_s},
        "frontend": dict(cfg.frontend),
        "endpoints": dict(cfg.endpoints), "fields": dict(cfg.fields),
        "signals": dict(cfg.signals),
        "token_json_path": cfg.token_json_path, "refresh_json_path": cfg.refresh_json_path,
        "auth_header": cfg.auth_header, "session_cookie": cfg.session_cookie,
        "throttle_statuses": list(cfg.throttle_statuses),
        "jwks_url": cfg.jwks_url, "jwt_iss": cfg.jwt_iss, "jwt_aud": cfg.jwt_aud,
        "users": {k: dict(v) for k, v in cfg.users.items()},
        "bola_object": dict(cfg.bola_object), "media_sample": cfg.media_sample,
        "stress_endpoint": cfg.stress_endpoint, "oauth": dict(cfg.oauth),
        "features": list(cfg.features), "hooks": dict(cfg.hooks),
        "limits": dict(cfg.limits), "load": dict(cfg.load), "safety": dict(cfg.safety),
        "suites": list(cfg.suites), "fail_on_leak": cfg.fail_on_leak,
        "fail_on_inconclusive": cfg.fail_on_inconclusive,
    }


def validate(cfg: Config) -> None:
    """Fail fast on a config that cannot work, instead of mid-run."""
    fe = cfg.frontend
    if fe.get("port") not in (None, ""):
        try:
            fe["port"] = int(fe["port"])
        except (TypeError, ValueError):
            raise ConfigError(f"frontend.port must be a number, got {fe['port']!r}")
        if not 0 < fe["port"] < 65536:
            raise ConfigError(f"frontend.port out of range: {fe['port']}")
    else:
        fe["port"] = None
    if (fe.get("scheme") or "http") not in ("http", "https"):
        raise ConfigError(f"frontend.scheme must be http or https, got {fe.get('scheme')!r}")
    if fe.get("host") and any(c in str(fe["host"]) for c in "/@ ?#"):
        raise ConfigError(f"frontend.host must be a bare hostname or IP, got {fe['host']!r}")
    if fe.get("api_path") and not str(fe["api_path"]).startswith("/"):
        raise ConfigError(f"frontend.api_path must start with '/', got {fe['api_path']!r}")
    try:
        cfg.port = int(cfg.port)
    except (TypeError, ValueError):
        raise ConfigError(f"target.port must be a number, got {cfg.port!r}")
    if not 0 < cfg.port < 65536:
        raise ConfigError(f"target.port out of range: {cfg.port}")
    if cfg.scheme not in ("http", "https"):
        raise ConfigError(f"target.scheme must be http or https, got {cfg.scheme!r}")
    if not cfg.host or any(c in str(cfg.host) for c in "/@ ?#"):
        raise ConfigError(f"target.host must be a bare hostname or IP, got {cfg.host!r}")
    if cfg.base_path and not str(cfg.base_path).startswith("/"):
        raise ConfigError(f"target.base_path must start with '/', got {cfg.base_path!r}")
    for name, spec in cfg.endpoints.items():
        split_spec(spec, f"endpoints.{name}")
    for name, spec in cfg.hooks.items():
        if isinstance(spec, str) and spec:
            split_spec(spec, f"hooks.{name}")
    for role in ("user", "admin"):
        if role not in cfg.users:
            raise ConfigError(f"users.{role} is required")
    for role, u in cfg.users.items():
        for k in ("username", "password", "id"):
            if not isinstance(u, dict) or k not in u:
                raise ConfigError(f"users.{role} needs '{k}'")
    for k in ("features", "suites", "throttle_statuses"):
        if not isinstance(getattr(cfg, k), list):
            raise ConfigError(f"'{k}' must be a list")


def dotget(obj, path, default=None):
    """Extract a value by dot path from a nested dict, e.g. 'data.token'."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur
