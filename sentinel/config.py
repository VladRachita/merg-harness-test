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
  auth.token_json_path -> SENTINEL_AUTH_TOKEN_JSON_PATH
  jwks_url             -> SENTINEL_JWKS_URL
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field

try:
    import yaml  # optional; env-only config works without it
except Exception:  # pragma: no cover
    yaml = None


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
}


@dataclass
class Config:
    # --- target location (the "input parameters") ---
    scheme: str = "http"
    host: str = "localhost"
    port: int = 8080
    base_path: str = ""              # e.g. "/api/v1"
    verify_tls: bool = True
    timeout_s: float = 10.0

    # --- how to talk to it ---
    endpoints: dict = field(default_factory=lambda: dict(DEFAULT_ENDPOINTS))
    fields: dict = field(default_factory=lambda: dict(DEFAULT_FIELDS))
    # dot-path into the login JSON response that holds the access token
    token_json_path: str = "access_token"
    refresh_json_path: str = "refresh_token"
    auth_header: str = "Authorization: Bearer {token}"
    # where to fetch the signing key for the RS256->HS256 confusion test (optional)
    jwks_url: str | None = None
    # expected issuer/audience, so forged tokens match what the backend looks for
    jwt_iss: str = "https://auth.example"
    jwt_aud: str = "api"

    # --- seed accounts the backend already has (for IDOR/BOLA/login tests) ---
    # role -> {username, password, id, email}
    users: dict = field(default_factory=lambda: {
        "user":   {"username": "alice", "password": "alice-pw", "id": 1, "email": "alice@x.com"},
        "user2":  {"username": "bob",   "password": "bob-pw",   "id": 2, "email": "bob@x.com"},
        "admin":  {"username": "admin", "password": "admin-pw", "id": 3, "email": "admin@x.com"},
    })

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
        "user_admin": None,       # e.g. "POST /test/users/{username}/enabled"
        "db_probe": None,         # e.g. "GET /test/injected?marker={marker}"
        "reset_introspect": False,# True if reset_request returns the token in test mode
        "other_aud_token": None,  # e.g. "POST /test/token?aud={aud}"
    })

    # --- optional backend features; attacks for a disabled feature are SKIPPED ---
    features: list = field(default_factory=lambda: ["oauth", "media_upload"])

    # --- which suites to run ---
    suites: list = field(default_factory=lambda: ["access_control", "media_injection"])
    # fail the run (non-zero exit) if any attack is not blocked
    fail_on_leak: bool = True

    @property
    def base_url(self) -> str:
        return f"{self.scheme}://{self.host}:{self.port}{self.base_path}".rstrip("/")


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
    data = {}
    path = path or os.environ.get("SENTINEL_CONFIG")
    if path and os.path.exists(path):
        if yaml is None:
            raise RuntimeError("PyYAML not installed but a config file was given")
        with open(path) as f:
            data = yaml.safe_load(f) or {}
        t = data.get("target", {})
        for k in ("scheme", "host", "port", "base_path", "verify_tls", "timeout_s"):
            if k in t:
                setattr(cfg, k, t[k])
        for section in ("endpoints", "fields", "users", "oauth", "hooks"):
            if section in data and isinstance(data[section], dict):
                getattr(cfg, section).update(data[section])
        for k in ("token_json_path", "refresh_json_path", "auth_header", "jwks_url",
                  "suites", "fail_on_leak"):
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
    for ev, attr in simple.items():
        if ev in env:
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
    return cfg


def dotget(obj, path, default=None):
    """Extract a value by dot path from a nested dict, e.g. 'data.token'."""
    cur = obj
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        else:
            return default
    return cur
