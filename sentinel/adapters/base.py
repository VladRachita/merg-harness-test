"""
The adapter contract. Every suite is written against `Target`, so the exact same
attacks run against the in-process reference apps (self-test + negative control)
and against a real backend over HTTP.

A Target also advertises `capabilities()`: some attacks need a gray-box hook
(disable a user, read a stored field, fetch the signing key, a DB probe). When a
capability is absent, the suite SKIPS those attacks with a clear reason instead
of failing — so a pure black-box run stays honest.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass
class Resp:
    status: int
    headers: dict = field(default_factory=dict)
    body: dict = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        return 200 <= self.status < 300


class Capability(str, Enum):
    TWO_ACCOUNTS   = "two_accounts"     # a second real user exists (IDOR/BOLA)
    USER_ADMIN     = "user_admin"       # can disable a user / read a user field
    SIGNING_KEY    = "signing_key"      # server public key available (JWKS) for confusion test
    OTHER_AUD_TOKEN= "other_aud_token"  # can mint a wrong-audience token (substitution test)
    RESET_INTROSPECT = "reset_introspect"  # reset token observable in test mode
    DB_PROBE       = "db_probe"         # can ask whether an injected row exists
    OAUTH          = "oauth"            # OAuth2/PKCE endpoints present
    MEDIA_UPLOAD   = "media_upload"     # file upload endpoint present


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

    # --- auth ---
    def login(self, username, password, source_ip="203.0.113.9", xff=None,
              otp_ok=True, prev_session=None) -> Resp: raise NotImplementedError
    def logout(self, token) -> Resp: raise NotImplementedError
    def refresh_token(self, rtok) -> Resp: raise NotImplementedError
    def register(self, username, password, requested_role=None, extra=None) -> Resp: raise NotImplementedError

    # --- protected resources ---
    def get_resource(self, token, owner_id) -> Resp: raise NotImplementedError
    def get_object(self, token, kind, obj_id) -> Resp: raise NotImplementedError
    def admin_users(self, token) -> Resp: raise NotImplementedError
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

    # --- gray-box hooks (guarded by capabilities) ---
    def issue_access_token(self, username, aud="api") -> str: raise NotImplementedError
    def set_enabled(self, username, enabled) -> None: raise NotImplementedError
    def user_field(self, username, field) -> object: raise NotImplementedError
    def public_key(self) -> bytes: raise NotImplementedError
    def injected_row_exists(self, marker) -> bool: raise NotImplementedError
