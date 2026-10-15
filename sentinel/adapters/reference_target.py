"""
Reference targets — wrap the proven in-process SecureApp / VulnerableApp (auth &
access-control) plus a small MediaBackend (upload injection) behind the Target
contract. Used for: (a) a self-test that passes with no backend, proving the
suites and runner work; (b) a negative control that gets broken, proving the
suites detect real flaws.
"""
from __future__ import annotations

import re
import subprocess
import tempfile

from .base import Target, Resp, Capability
from .reference.secure_app import SecureApp, RSA_PUB
from .reference.vulnerable_app import VulnerableApp

_PROBE = re.compile(rb"SQLiPROBE_[A-Za-z0-9]+::[^\x00\"']*")


def _magic(data: bytes):
    if data[:8] == b"\x89PNG\r\n\x1a\n":
        return "png"
    if data[:3] == b"\xff\xd8\xff":
        return "jpg"
    if data[4:8] == b"ftyp":
        return "mp4"
    return None


def _decodes(data: bytes, ext: str) -> bool:
    """Fully decode with ffmpeg (decode-to-null) — rejects truncated / structurally
    broken files that merely carry the right magic bytes or a valid header. This
    mirrors a real pipeline that re-encodes rather than trusting ffprobe's header."""
    try:
        with tempfile.NamedTemporaryFile(suffix=f".{ext}", delete=True) as f:
            f.write(data); f.flush()
            r = subprocess.run(["ffmpeg", "-v", "error", "-i", f.name, "-f", "null", "-"],
                               capture_output=True, text=True)
            # ffmpeg returns non-zero AND/OR writes to stderr on a broken stream
            return r.returncode == 0 and r.stderr.strip() == ""
    except Exception:
        return False


class MediaBackend:
    """Minimal media-upload backend. secure=True validates by magic bytes and
    stores metadata inertly; secure=False concatenates it (injection)."""

    def __init__(self, secure: bool):
        self.secure = secure
        self.audit: list[str] = []   # rows an injection would create

    def upload_bytes(self, filename: str, data: bytes, content_type: str) -> Resp:
        ext = filename.rsplit(".", 1)[-1].lower()
        norm = {"jpeg": "jpg"}.get(ext, ext)
        probe = _PROBE.search(data)
        meta = probe.group().decode("latin1") if probe else ""
        if self.secure:
            magic = _magic(data)
            if magic is None:
                return Resp(400, {}, {"error": "unrecognized media"})
            if magic != norm:
                return Resp(400, {}, {"error": f"content/ext mismatch {magic}!={norm}"})
            if not _decodes(data, norm):
                return Resp(400, {}, {"error": "undecodable / truncated media"})
            # metadata stored as bound data; never concatenated into a query
            return Resp(201, {"Content-Disposition": "attachment",
                              "X-Content-Type-Options": "nosniff"}, {"stored": filename})
        # vulnerable: metadata concatenated -> a stacked INSERT fires
        if "INSERT INTO audit" in meta:
            self.audit.append(meta)
        return Resp(201, {}, {"stored": filename})

    def injected_row_exists(self, marker: str) -> bool:
        return any(marker in a for a in self.audit)


class _BaseReferenceTarget(Target):
    app_cls = SecureApp
    secure = True

    def __init__(self):
        self.app = self.app_cls()
        self.media = MediaBackend(secure=self.secure)

    def capabilities(self):
        return {Capability.TWO_ACCOUNTS, Capability.USER_ADMIN, Capability.SIGNING_KEY,
                Capability.OTHER_AUD_TOKEN, Capability.RESET_INTROSPECT, Capability.DB_PROBE,
                Capability.OAUTH, Capability.MEDIA_UPLOAD}

    @staticmethod
    def _wrap(r) -> Resp:
        return Resp(r.status, dict(r.headers), dict(r.body))

    # --- auth ---
    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True, prev_session=None):
        return self._wrap(self.app.login(username, password, source_ip, xff, otp_ok, prev_session))
    def logout(self, token): return self._wrap(self.app.logout(token))
    def refresh_token(self, rtok): return self._wrap(self.app.refresh_token(rtok))
    def register(self, username, password, requested_role=None, extra=None):
        return self._wrap(self.app.register(username, password, requested_role, extra))

    # --- resources ---
    def get_resource(self, token, owner_id): return self._wrap(self.app.get_resource(token, owner_id))
    def get_object(self, token, kind, obj_id): return self._wrap(self.app.get_object(token, kind, obj_id))
    def admin_users(self, token): return self._wrap(self.app.admin_users(token))
    def admin_delete_user(self, token, target, method="DELETE"):
        return self._wrap(self.app.admin_delete_user(token, target, method))

    # --- state-changing ---
    def change_password(self, token, old, new, reauthed=False, csrf_ok=True, cross_site=False):
        return self._wrap(self.app.change_password(token, old, new, reauthed, csrf_ok, cross_site))
    def sensitive_action(self, token, reauthed=False, csrf_ok=True, cross_site=False):
        return self._wrap(self.app.sensitive_action(token, reauthed, csrf_ok, cross_site))
    def change_email(self, token, new_email, reverified=False):
        return self._wrap(self.app.change_email(token, new_email, reverified))

    # --- media ---
    def get_media(self, path): return self._wrap(self.app.get_media(path))
    def upload(self, token, fetch_url=None, width=None, height=None, filename="v.mp4"):
        return self._wrap(self.app.upload(token, fetch_url, width, height, filename))
    def upload_bytes(self, token, filename, data, content_type):
        return self.media.upload_bytes(filename, data, content_type)

    # --- reset ---
    def reset_request(self, email, host_header="app.example"):
        return self._wrap(self.app.reset_request(email, host_header))
    def reset_confirm(self, token, new_pw): return self._wrap(self.app.reset_confirm(token, new_pw))

    # --- oauth ---
    def oauth_authorize(self, client_id, redirect_uri, code_challenge=None, state=None):
        return self._wrap(self.app.oauth_authorize(client_id, redirect_uri, code_challenge, state))
    def oauth_token(self, code, code_verifier, client_id, redirect_uri):
        return self._wrap(self.app.oauth_token(code, code_verifier, client_id, redirect_uri))

    # --- misc ---
    def buggy_endpoint(self, payload): return self._wrap(self.app.buggy_endpoint(payload))

    # --- gray-box hooks ---
    def issue_access_token(self, username, aud="api"):
        u = self.app.users[username]
        return self.app._issue_access(username, u["role"], u["id"], u["mfa"], aud=aud)
    def set_enabled(self, username, enabled): self.app.users[username]["enabled"] = enabled
    def user_field(self, username, field): return self.app.users.get(username, {}).get(field)
    def public_key(self): return RSA_PUB
    def injected_row_exists(self, marker): return self.media.injected_row_exists(marker)


class ReferenceSecureTarget(_BaseReferenceTarget):
    name = "reference-secure"
    app_cls = SecureApp
    secure = True


class ReferenceVulnerableTarget(_BaseReferenceTarget):
    name = "reference-vulnerable"
    app_cls = VulnerableApp
    secure = False
