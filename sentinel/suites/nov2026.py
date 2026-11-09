"""
nov2026 suite — controls behind the application-level flaws disclosed from
mid-October to early November 2026 that the earlier suites did not assert yet.

Every id, product and date below was read from the public CVE record or GitHub
advisory on 2026-11-09 (sources: docs/THREATS-2026-Q4.md). Each check asserts
the DEFENCE generically — none of them reproduces a product-specific exploit.

  NOV1   A zero-length HMAC key was accepted, so anyone could mint a "valid"
         HS256 token. → Authlib CVE-2026-114616 (22 Oct); PyJWT
         GHSA-pxh4-856f-4h89 (in the GitHub advisory DB 22 Oct).
  NOV2   Algorithm confusion: the server's PUBLIC key worked as an HMAC secret
         in another byte encoding than the guard expected.
         → Authlib CVE-2026-114615 (22 Oct).
  NOV3   Logout reported success but revoked nothing.
         → Django REST framework CVE-2026-114137 (21 Oct).
  NOV4   API/refresh tokens stayed valid after a password change.
         → wger CVE-2026-46437 (7 Oct).
  NOV5   A sign-in path ignored the "deactivated" flag, so disabled users
         (admins included) got sessions again. → Snipe-IT CVE-2026-116199 (25 Oct).
  NOV6   The password-reset flow issued a session before the MFA challenge.
         → SilverStripe MFA CVE-2026-55186 (3 Nov).
  NOV7   A second login path skipped MFA entirely.
         → SonicWall SonicOS SSLVPN CVE-2026-19868 (6 Nov; KEV the same day).
  NOV8   A password could be changed without the step-up / proof the UI asks for.
         → Nginx UI CVE-2026-84314 (12 Oct), Arcane CVE-2026-96627 (16 Oct).
  NOV9   Auth responses serialized restricted user fields.
         → Payload CMS CVE-2026-105853 (6 Oct).
  NOV10  Identity was taken from something the client can simply assert.
         → Ivanti Connect Secure CVE-2026-104935 (13 Oct; KEV), authentication
           bypass by spoofing (CWE-290), like BeyondTrust CVE-2026-102764.
  NOV11  A token endpoint issued a bearer token without a valid grant.
         → OAuthLib device flow CVE-2026-49272 (5 Nov).
  NOV12  A stolen authorization code could be redeemed by someone else.
         → Python Social Auth CVE-2026-115910 (26 Oct). We assert the PKCE half:
           the code is useless without the verifier of whoever requested it.
"""
from __future__ import annotations

import re

from ..adapters.base import Capability
from ..config import Config, dotget
from . import jwt_forge as jf
from .common import (Attack, Inconclusive, Leak, NotApplicable, MUTATES, STRONG_PW, authed,
                     denied, expect_ok, need_reset_token, need_token, reached, refused,
                     restore_password)
from .pkce import s256

# keys that must never appear in an auth response with a real value
_CREDENTIAL_KEY = re.compile(
    r"pass(word|wd)?(_?hash)?$|^pwd$|hash$|salt$|secret|totp|otp_?seed|private_?key|"
    r"api_?key|reset_?token|recovery_?code", re.I)

# headers a reverse proxy sets to say who the caller is — a client must not be
# able to assert them for itself
IDENTITY_HEADERS = ("X-Remote-User", "X-Forwarded-User", "X-User", "X-Authenticated-User",
                    "X-Auth-Request-User", "X-Auth-Request-Email", "X-WEBAUTH-USER")
PRIVILEGE_HEADERS = ({"X-Role": "admin"}, {"X-Admin": "true"}, {"X-Is-Admin": "1"},
                     {"X-User-Role": "admin"})
LOOPBACK_HEADERS = ({"X-Forwarded-For": "127.0.0.1"}, {"X-Real-IP": "127.0.0.1"},
                    {"Forwarded": "for=127.0.0.1"}, {"X-Forwarded-Host": "localhost"})


def _key_encodings(pem: bytes) -> list:
    """Every byte form in which a server might be holding its public key."""
    out = [pem, pem.strip(), pem.strip() + b"\n"]
    try:
        from cryptography.hazmat.primitives import serialization as s
        key = s.load_pem_public_key(pem)
        out.append(key.public_bytes(s.Encoding.DER, s.PublicFormat.SubjectPublicKeyInfo))
        pkcs1 = key.public_bytes(s.Encoding.PEM, s.PublicFormat.PKCS1)
        out += [pkcs1, pkcs1.strip()]
    except Exception:
        pass
    seen, uniq = set(), []
    for k in out:
        if k and k not in seen:
            seen.add(k); uniq.append(k)
    return uniq


def _credential_keys(obj, path=""):
    if isinstance(obj, dict):
        for k, v in obj.items():
            here = f"{path}.{k}" if path else str(k)
            if _CREDENTIAL_KEY.search(str(k)) and isinstance(v, (str, dict, list)) and v:
                yield here
            yield from _credential_keys(v, here)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            yield from _credential_keys(v, f"{path}[{i}]")


def build(cfg: Config) -> list[Attack]:
    U = cfg.users
    user, admin = U["user"], U["admin"]
    ISS, AUD = cfg.jwt_iss, cfg.jwt_aud
    oc = cfg.oauth
    A: list[Attack] = []

    def add(id, cat, desc, check, requires=None, stage=0):
        A.append(Attack(id, cat, desc, check, set(requires or []), stage))

    def admin_works(t):
        expect_ok(t.admin_users(need_token(t, admin)), "the real admin listing users")

    claims = lambda: jf.admin_claims(user["username"], user["id"], ISS, AUD)

    # ---- NOV1 / NOV2: forged tokens ---------------------------------------
    def empty_key(t):
        admin_works(t)
        for alg in ("HS256", "HS384", "HS512"):
            if not denied(t.admin_users(jf.forge({"alg": alg, "typ": "JWT"}, claims(), b"")),
                          f"{alg} token signed with an empty key"):
                raise Leak(f"an {alg} token signed with a ZERO-LENGTH key was accepted")
        return True
    add("NOV1", "jwt", "token signed with an empty HMAC key rejected (Authlib CVE-2026-114616)",
        empty_key)

    def confusion_encodings(t):
        admin_works(t)
        for key in _key_encodings(t.public_key()):
            for alg in ("HS256", "HS384", "HS512"):
                if not denied(t.admin_users(jf.forge({"alg": alg, "typ": "JWT"}, claims(), key)),
                              "token HMAC-signed with the public key"):
                    raise Leak(f"{alg} with the server's public key as the secret was accepted")
        return True
    add("NOV2", "jwt",
        "algorithm confusion rejected for every public-key encoding (Authlib CVE-2026-114615)",
        confusion_encodings, [Capability.SIGNING_KEY])

    # ---- NOV3 / NOV4: refresh tokens die with the session ------------------
    def session_with_refresh(t):
        r = reached(t.login(user["username"], user["password"]))
        tok, rt = r.body.get("access_token"), r.body.get("refresh_token")
        if not tok:
            raise Inconclusive(f"could not log in as '{user['username']}' (HTTP {r.status})")
        if not rt:
            raise NotApplicable("login returns no refresh token (check refresh_json_path)")
        return tok, rt

    def refresh_works(t):
        _, rt = session_with_refresh(t)
        expect_ok(t.refresh_token(rt), "refreshing an untouched session")

    def refresh_after_logout(t):
        refresh_works(t)
        tok, rt = session_with_refresh(t)
        expect_ok(t.logout(tok), "logout")
        return denied(t.refresh_token(rt), "refresh token after logout")
    add("NOV3", "session", "refresh token dies at logout (DRF CVE-2026-114137)",
        refresh_after_logout)

    def refresh_after_pwchange(t):
        refresh_works(t)
        tok, rt = session_with_refresh(t)
        try:
            expect_ok(t.change_password(tok, user["password"], STRONG_PW, reauthed=True),
                      "a legitimate password change (with step-up)")
            return denied(t.refresh_token(rt), "refresh token after a password change")
        finally:
            restore_password(t, user, STRONG_PW)
    add("NOV4", "session", "refresh token dies on password change (wger CVE-2026-46437)",
        refresh_after_pwchange, stage=MUTATES)

    # ---- NOV5: a disabled account gets no NEW session ----------------------
    def disabled_login(t):
        need_token(t, user)
        t.set_enabled(user["username"], False)
        try:
            r = reached(t.login(user["username"], user["password"]))
            if r.body.get("access_token"):
                raise Leak("a deactivated account signed in and received a token")
            return denied(r, "login of a deactivated account")
        finally:
            t.set_enabled(user["username"], True)
    add("NOV5", "authz", "deactivated account cannot start a new session (Snipe-IT CVE-2026-116199)",
        disabled_login, [Capability.USER_ADMIN], stage=MUTATES)

    # ---- NOV6 / NOV7: MFA cannot be side-stepped ---------------------------
    def reset_gives_no_session(t):
        tok = need_reset_token(t, user)
        try:
            r = expect_ok(t.reset_confirm(tok, STRONG_PW), "a password reset")
            if dotget(r.body, cfg.token_json_path) or r.body.get("access_token") \
                    or dotget(r.body, cfg.refresh_json_path) or r.body.get("refresh_token"):
                raise Leak("the reset response contains a token — a session before the MFA step")
            if any(c.strip().startswith(cfg.session_cookie + "=") for c in r.cookies()):
                raise Leak("the reset response sets the session cookie — a session before MFA")
            return True
        finally:
            restore_password(t, user, STRONG_PW)
    add("NOV6", "takeover", "password reset does not hand out a session (SilverStripe MFA "
        "CVE-2026-55186)", reset_gives_no_session,
        [Capability.RESET_INTROSPECT, Capability.MFA], stage=MUTATES)

    def mfa_enforced(t):
        need_token(t, user)
        r = reached(t.login(user["username"], user["password"], otp_ok=False))
        if r.body.get("access_token"):
            raise Leak("the right password with a WRONG second factor produced a token")
        return denied(r, "login with a wrong second factor")
    add("NOV7", "mfa", "second factor enforced at login (SonicWall CVE-2026-19868)",
        mfa_enforced, [Capability.MFA])

    # ---- NOV8: password change needs step-up -------------------------------
    def pwchange_needs_stepup(t):
        tok = authed(t, user)
        try:
            return refused(t.change_password(tok, user["password"], STRONG_PW, reauthed=False),
                           "password change without step-up")
        finally:
            restore_password(t, user, STRONG_PW)
    add("NOV8", "takeover", "password change requires step-up (Nginx UI CVE-2026-84314)",
        pwchange_needs_stepup, stage=MUTATES)

    # ---- NOV9: auth responses carry no credential material -----------------
    def no_credential_fields(t):
        r = reached(t.login(user["username"], user["password"]))
        if not r.body.get("access_token"):
            raise Inconclusive(f"could not log in as '{user['username']}' (HTTP {r.status})")
        found = list(_credential_keys(r.body))
        rt = r.body.get("refresh_token")
        if rt:
            found += [f"refresh:{k}" for k in _credential_keys(reached(t.refresh_token(rt)).body)]
        if found:
            raise Leak("auth response exposes credential fields: " + ", ".join(sorted(set(found))[:6]))
        return True
    add("NOV9", "info-leak", "login/refresh responses expose no credential fields "
        "(Payload CVE-2026-105853)", no_credential_fields)

    # ---- NOV10: identity can't be asserted by the client -------------------
    def spoofed_identity(t):
        admin_works(t)
        who = admin["username"]
        attempts = [({h: who}, "") for h in IDENTITY_HEADERS]
        attempts += [({"X-User-Id": str(admin["id"])}, "")]
        attempts += [(h, "") for h in LOOPBACK_HEADERS]
        low = authed(t, user)
        attempts += [(h, low) for h in PRIVILEGE_HEADERS]
        attempts += [({h: who}, low) for h in IDENTITY_HEADERS[:3]]
        for headers, tok in attempts:
            name = next(iter(headers))
            if not denied(t.admin_users(tok, spoof=headers), f"admin endpoint with spoofed {name}"):
                raise Leak(f"the admin endpoint trusted a client-supplied '{name}' header"
                           + (" on top of an ordinary user's token" if tok else " with no token"))
        return True
    add("NOV10", "authz", "client-supplied identity/loopback headers are not trusted "
        "(Ivanti CVE-2026-104935)", spoofed_identity)

    # ---- NOV11 / NOV12: the token endpoint ---------------------------------
    VERIFIER = "verifier-xyz-" + "0" * 32

    def grant(t):
        r = expect_ok(t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256(VERIFIER),
                                        "state-1"), "a fully valid authorization request")
        if not r.body.get("code"):
            raise Inconclusive("the authorization response carries no code")
        return r.body["code"]

    def exchange_works(t):
        expect_ok(t.oauth_token(grant(t), VERIFIER, oc["client_id"], oc["redirect_uri"]),
                  "a legitimate code exchange")

    def no_grant_no_token(t):
        exchange_works(t)
        for code in ("", "0" * 16, "undefined"):
            if not denied(t.oauth_token(code, VERIFIER, oc["client_id"], oc["redirect_uri"]),
                          f"token request with code {code!r}"):
                raise Leak(f"a token was issued for the unknown code {code!r}")
        return True
    add("NOV11", "oauth", "token endpoint issues nothing without a valid grant "
        "(OAuthLib CVE-2026-49272)", no_grant_no_token, [Capability.OAUTH])

    def stolen_code(t):
        exchange_works(t)
        for verifier in ("attacker-verifier-" + "1" * 32, ""):
            code = grant(t)
            if not denied(t.oauth_token(code, verifier, oc["client_id"], oc["redirect_uri"]),
                          "code exchange with the wrong PKCE verifier"):
                raise Leak("an authorization code was redeemed "
                           + ("without any" if not verifier else "with the wrong") + " PKCE verifier")
        return True
    add("NOV12", "oauth", "authorization code is useless without its PKCE verifier "
        "(stolen-code class, Python Social Auth CVE-2026-115910)", stolen_code, [Capability.OAUTH])

    return A
