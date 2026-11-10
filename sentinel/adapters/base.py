"""
The adapter contract. Every suite is written against `Target`, so the exact same
attacks run against the in-process reference apps (self-test + negative control)
and against a real backend over HTTP.

A Target also advertises `capabilities()`: some attacks need a gray-box hook
(disable a user, read a stored field, fetch the signing key, a DB probe). When a
capability is absent, the suite SKIPS those attacks with a clear reason instead
of failing — so a pure black-box run stays honest.

Two exceptions keep results honest in the other direction:

  Inconclusive   the check could not PROVE anything — the backend didn't answer,
                 a legitimate "control" request failed, a precondition (login,
                 a test hook) didn't hold. It is never reported as BLOCKED.
  NotApplicable  the control under test doesn't exist on this backend by design
                 (e.g. cookie flags on a token-only API). Reported as SKIPPED.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Inconclusive(Exception):
    """The check could not prove the attack was blocked (nor that it leaked)."""


class Unreachable(Inconclusive):
    """The backend did not answer at all (refused / reset / timed out)."""


class NotApplicable(Exception):
    """The control being tested does not exist on this backend by design."""


@dataclass
class Resp:
    status: int
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)
    set_cookies: list = field(default_factory=list)   # one entry per Set-Cookie header
    elapsed_s: float = 0.0

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300

    def header(self, name, default=None):
        """Case-insensitive header lookup (HTTP header names are case-insensitive)."""
        name = name.lower()
        for k, v in self.headers.items():
            if k.lower() == name:
                return v
        return default

    def cookies(self) -> list:
        """Every Set-Cookie value on this response."""
        if self.set_cookies:
            return list(self.set_cookies)
        one = self.header("set-cookie")
        return [one] if one else []


class Capability(str, Enum):
    TWO_ACCOUNTS   = "two_accounts"     # a second real user exists (IDOR/BOLA)
    USER_ADMIN     = "user_admin"       # can disable a user / read a user field
    SIGNING_KEY    = "signing_key"      # server public key available (JWKS) for confusion test
    OTHER_AUD_TOKEN= "other_aud_token"  # can mint a token (wrong audience / already expired)
    RESET_INTROSPECT = "reset_introspect"  # reset token observable in test mode
    DB_PROBE       = "db_probe"         # can ask whether an injected row exists
    OAUTH          = "oauth"            # OAuth2/PKCE endpoints present
    MEDIA_UPLOAD   = "media_upload"     # file upload endpoint present
    MFA            = "mfa"              # the seed accounts have a second factor
    CSRF           = "csrf"             # auth rides on an ambient credential (cookie)
    FRONTEND       = "frontend"         # a web front end is configured (its own port)


# Request shapes a bot uses to dodge a rate limiter. `Target.login(evasion=...)`
# takes one of these dicts; a correct limiter ignores all of it.
#   {"headers": {...}}   extra/spoofed request headers (client-IP, User-Agent…)
#   {"path": "<kind>"}   an equivalent spelling of the login route (see PATH_VARIANTS)
#   {"form": True}       form-encoded body instead of JSON
PATH_VARIANTS = ("trailing-slash", "upper", "double-slash", "matrix", "junk-query", "dot-segment")

# Pathological-but-bounded inputs for `Target.stress_input(kind)`. Each is ONE
# request; none is an exploit — they are the malformed/oversized shapes a parser
# must refuse cheaply instead of burning CPU, memory or file descriptors.
STRESS_KINDS = (
    "oversize",      # 1 MB string in a JSON field
    "deep-json",     # 5,000 levels of nesting
    "wide-json",     # 20,000 keys in one object
    "gzip-bomb",     # 16 MB of zeros gzip-compressed to a few KB
    "bad-encoding",  # Content-Encoding: br with a garbage body
    "bad-charset",   # a non-text codec named as the JSON charset
    "many-parts",    # multipart body with 2,000 tiny parts
    "long-accept",   # Accept header with 2,000 media ranges
)


class Target:
    """Abstract system under test. HttpTarget and the reference targets implement it.
    Unused operations may raise NotImplementedError; the suites guard with capabilities."""

    name: str = "target"

    def capabilities(self) -> set:
        return set()

    def reset(self) -> None:
        """Restore clean state before an attack. Reference targets are already
        fresh per attack (no-op); the HTTP target calls a test-reset endpoint if
        one is configured, so stateful attacks don't bleed into each other."""
        return None

    def begin_attack(self, attack_id: str) -> None:
        """Called by the runner before each attack (tracing / attribution)."""
        return None

    def evidence(self) -> str:
        """A short description of the last request(s), attached to a LEAK."""
        return ""

    # --- auth ---
    def login(self, username, password, source_ip="203.0.113.9", xff=None,
              otp_ok=True, prev_session=None, evasion=None) -> Resp: raise NotImplementedError
    def logout(self, token) -> Resp: raise NotImplementedError
    def refresh_token(self, rtok) -> Resp: raise NotImplementedError
    def register(self, username, password, requested_role=None, extra=None) -> Resp: raise NotImplementedError

    # --- protected resources ---
    def get_resource(self, token, owner_id) -> Resp: raise NotImplementedError
    def get_object(self, token, kind, obj_id) -> Resp: raise NotImplementedError
    def admin_users(self, token, spoof=None) -> Resp:
        """`spoof` is a dict of identity headers a client must never be able to
        assert for itself (X-Remote-User, X-Forwarded-User, …)."""
        raise NotImplementedError
    def admin_delete_user(self, token, target, method="DELETE") -> Resp: raise NotImplementedError

    # --- state-changing ---
    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False) -> Resp:
        raise NotImplementedError
    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False) -> Resp:
        raise NotImplementedError
    def change_email(self, token, new_email, reverified=False) -> Resp: raise NotImplementedError

    # --- media / upload ---
    def get_media(self, path) -> Resp: raise NotImplementedError
    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4") -> Resp:
        raise NotImplementedError
    def upload_bytes(self, token, filename, data, content_type) -> Resp: raise NotImplementedError

    # --- password reset ---
    def reset_request(self, email, host_header="app.example") -> Resp: raise NotImplementedError
    def reset_confirm(self, token, new_pw) -> Resp: raise NotImplementedError

    # --- oauth2 / pkce ---
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None) -> Resp:
        raise NotImplementedError
    def oauth_token(self, code, code_verifier, client_id, redirect_uri) -> Resp: raise NotImplementedError

    # --- misc ---
    def buggy_endpoint(self, payload) -> Resp: raise NotImplementedError

    # --- attack surface: what an anonymous visitor can see ---
    def fetch_path(self, where, path) -> Resp:
        """Anonymous GET of `path` on the "backend" or "frontend" origin. Text
        bodies come back under body["_text"]."""
        raise NotImplementedError
    def cors_probe(self, token, origin, preflight=False) -> Resp:
        """An authenticated API request that claims to come from the web page
        `origin` (or its CORS preflight). Only the response HEADERS matter."""
        raise NotImplementedError
    def frontend_assets(self) -> list:
        """[(path, text)]: the front-end page and the same-origin scripts it loads."""
        raise NotImplementedError

    # --- resilience ---
    def stress_input(self, kind) -> Resp:
        """Send ONE pathological-but-bounded request (see STRESS_KINDS) to an
        unauthenticated JSON endpoint and return how the backend answered."""
        raise NotImplementedError

    # --- gray-box hooks (guarded by capabilities) ---
    def issue_access_token(self, username, aud="api", ttl=None) -> str: raise NotImplementedError
    def set_enabled(self, username, enabled) -> None: raise NotImplementedError
    def user_field(self, username, field) -> object: raise NotImplementedError
    def public_key(self) -> bytes: raise NotImplementedError
    def injected_row_exists(self, marker) -> bool: raise NotImplementedError
