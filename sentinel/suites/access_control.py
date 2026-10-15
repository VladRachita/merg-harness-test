"""
Access-control suite: 40+ attacks across brute force, injection, output headers,
session/token spoofing, authorization, OAuth2/PKCE, account takeover, upload
abuse, credential-theft mitigations and information disclosure.

Every attack is written against the Target contract, so the same catalogue runs
against the reference apps and a real backend. Attacks that need a gray-box hook
declare `requires`; they're SKIPPED (not failed) when the hook isn't configured.
"""
from __future__ import annotations

import hashlib
import time

from ..adapters.base import Capability
from ..config import Config
from .common import Attack
from . import jwt_forge as jf


def _token(t, user):   # a genuine low-priv access token
    return t.login(user["username"], user["password"]).body.get("access_token", "")


def _reset_token(resp):
    """Pull a reset token out of a reset_request response, however it's exposed."""
    b = resp.body
    for k in ("_link_for_test", "link", "reset_link"):
        if b.get(k):
            return str(b[k]).split("token=")[-1]
    return b.get("token") or b.get("reset_token")


def build(cfg: Config) -> list[Attack]:
    U = cfg.users
    user, user2, admin = U["user"], U.get("user2"), U["admin"]
    ISS, AUD = cfg.jwt_iss, cfg.jwt_aud
    oc = cfg.oauth
    A: list[Attack] = []

    def add(id, cat, desc, check, requires=None):
        A.append(Attack(id, cat, desc, check, set(requires or [])))

    # ---- 1. brute force & credential --------------------------------------
    def bf_lockout(t):
        for _ in range(6):
            t.login(user["username"], "wrong-pw")
        return t.login(user["username"], user["password"]).status == 429
    add("BF1", "brute-force", "lockout holds even with the correct password", bf_lockout)

    def bf_spray(t):
        hits = [t.login(f"user{i}", "Password1", source_ip="9.9.9.9").status for i in range(13)]
        return 429 in hits
    add("BF2", "brute-force", "password spraying throttled per source IP", bf_spray)

    def bf_norm(t):
        for v in (user["username"], user["username"].upper(), f" {user['username']} "):
            for _ in range(3):
                t.login(v, "wrong-pw")
        return t.login(user["username"], user["password"]).status == 429
    add("BF3", "brute-force", "lockout counter shared across username casing/space", bf_norm)

    def bf_xff(t):
        for i in range(13):
            t.login(user["username"], "wrong-pw", source_ip="7.7.7.7", xff=f"1.2.3.{i}")
        return t.login(user["username"], "wrong-pw", source_ip="7.7.7.7").status == 429
    add("BF4", "brute-force", "spoofed X-Forwarded-For can't bypass the IP limit", bf_xff)

    def bf_otp(t):
        for _ in range(6):
            t.login(user["username"], user["password"], otp_ok=False)
        return t.login(user["username"], user["password"], otp_ok=False).status == 429
    add("BF5", "brute-force", "OTP / second-factor attempts rate-limited", bf_otp)

    def bf_enum(t):
        r1 = t.login("definitely-no-such-user", "x")
        r2 = t.login(user["username"], "wrong-pw")
        return r1.status == r2.status and r1.body.get("error") == r2.body.get("error")
    add("BF6", "brute-force", "login gives no user-enumeration signal", bf_enum)

    # ---- 2. injection ------------------------------------------------------
    add("INJ1", "injection", "SQLi in username does not authenticate",
        lambda t: not t.login("' OR '1'='1' --", "x").ok)
    add("INJ5", "injection", "path traversal in media path rejected",
        lambda t: not t.get_media("../../etc/passwd").ok)
    add("INJ6", "injection", "SSRF to cloud-metadata IP blocked",
        lambda t: not t.upload(_token(t, user), fetch_url="http://169.254.169.254/latest/meta-data/").ok,
        [Capability.MEDIA_UPLOAD])

    # ---- 3. output / headers ----------------------------------------------
    add("OUT1", "output", "X-Content-Type-Options: nosniff present",
        lambda t: _h(t.buggy_endpoint("1"), "x-content-type-options") == "nosniff")
    add("OUT3", "output", "Content-Security-Policy present",
        lambda t: _h(t.buggy_endpoint("1"), "content-security-policy") is not None)
    add("OUT5", "output", "uploads served as attachments, never inline",
        lambda t: _h(t.upload(_token(t, user), filename="evil.svg"), "content-disposition") == "attachment",
        [Capability.MEDIA_UPLOAD])

    # ---- 4. session & token ------------------------------------------------
    add("C1", "jwt", "alg:none admin token rejected",
        lambda t: not t.admin_users(jf.forge({"alg": "none"}, jf.admin_claims(user["username"], user["id"], ISS, AUD))).ok)
    add("C2", "jwt", "RS256->HS256 confusion (HMAC w/ public key) rejected",
        lambda t: not t.admin_users(jf.forge({"alg": "HS256"},
            jf.admin_claims(user["username"], user["id"], ISS, AUD), t.public_key())).ok,
        [Capability.SIGNING_KEY])
    add("C3", "jwt", "token signed with attacker secret rejected",
        lambda t: not t.admin_users(jf.forge({"alg": "HS256"},
            jf.admin_claims(user["username"], user["id"], ISS, AUD), b"attacker-secret")).ok)
    add("C5", "jwt", "expired token rejected",
        lambda t: not t.get_resource(jf.forge({"alg": "none"},
            jf.expired_claims(user["username"], user["id"], ISS, AUD)), user["id"]).ok)

    def fixation(t):
        return t.login(user["username"], user["password"], prev_session="attacker-chosen-id").body.get("sid") != "attacker-chosen-id"
    add("SES1", "session", "session id rotates on login (no fixation)", fixation)

    def logout_revoke(t):
        tok = _token(t, user); t.logout(tok)
        return not t.get_resource(tok, user["id"]).ok
    add("SES2", "session", "token revoked after logout", logout_revoke)

    def pwchange_revoke(t):
        tok = _token(t, user)
        t.change_password(tok, user["password"], "new-pw-123", reauthed=True)
        return not t.get_resource(tok, user["id"]).ok
    add("SES3", "session", "tokens revoked after password change", pwchange_revoke)

    def refresh_reuse(t):
        rt = t.login(user["username"], user["password"]).body.get("refresh_token")
        if not rt:
            return False
        t.refresh_token(rt)
        return not t.refresh_token(rt).ok
    add("SES4", "session", "refresh-token reuse detected, family killed", refresh_reuse)

    def cookie_flags(t):
        sc = _h(t.login(user["username"], user["password"]), "set-cookie") or ""
        return all(f.lower() in sc.lower() for f in ("HttpOnly", "Secure", "SameSite"))
    add("SES5", "session", "session cookie sets HttpOnly/Secure/SameSite", cookie_flags)

    add("SES6", "session", "cross-site state change rejected (CSRF)",
        lambda t: not t.change_password(_token(t, user), user["password"], "x", reauthed=True, cross_site=True).ok)

    def token_substitution(t):
        other = t.issue_access_token(user["username"], aud="client")
        return not t.admin_users(other).ok and not t.get_resource(other, user["id"]).ok
    add("SES7", "session", "wrong-audience token rejected (no substitution)",
        token_substitution, [Capability.OTHER_AUD_TOKEN])

    # ---- 5. authorization --------------------------------------------------
    add("AZ1", "authz", "user token on admin endpoint forbidden",
        lambda t: not t.admin_users(_token(t, user)).ok)
    add("AZ2", "authz", "IDOR: user reads another user's resource",
        lambda t: not t.get_resource(_token(t, user), user2["id"]).ok, [Capability.TWO_ACCOUNTS])
    add("AZ3", "authz", "BOLA: user reads another user's object",
        lambda t: not t.get_object(_token(t, user), "video", 102).ok, [Capability.TWO_ACCOUNTS])
    add("AZ4", "authz", "function-level authz holds across HTTP methods",
        lambda t: not t.admin_delete_user(_token(t, user), user2["username"] if user2 else "x", method="PUT").ok)

    def massassign(t):
        t.register("mallory", "pw", requested_role="admin",
                   extra={"isVerified": True, "balance": 999999, "role": "admin"})
        return t.user_field("mallory", "role") == "user"
    add("AZ5", "authz", "mass assignment of role/privilege ignored", massassign, [Capability.USER_ADMIN])

    def disabled(t):
        tok = _token(t, user); t.set_enabled(user["username"], False)
        return not t.get_resource(tok, user["id"]).ok
    add("AZ6", "authz", "token for a disabled account rejected", disabled, [Capability.USER_ADMIN])

    # ---- 6. oauth2 / pkce --------------------------------------------------
    from .pkce import s256
    add("OA1", "oauth", "PKCE mandatory for public clients",
        lambda t: not t.oauth_authorize(oc["client_id"], oc["redirect_uri"], code_challenge=None, state="s").ok,
        [Capability.OAUTH])
    add("OA3", "oauth", "redirect_uri must exactly match a registered one",
        lambda t: not t.oauth_authorize(oc["client_id"], "https://attacker.example/cb", s256("v"), "s").ok,
        [Capability.OAUTH])
    add("OA4", "oauth", "state required (callback CSRF)",
        lambda t: not t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256("v"), None).ok,
        [Capability.OAUTH])

    def code_replay(t):
        r = t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256("verifier-xyz"), "s")
        if not r.ok:
            return False
        code = r.body.get("code")
        t.oauth_token(code, "verifier-xyz", oc["client_id"], oc["redirect_uri"])
        return not t.oauth_token(code, "verifier-xyz", oc["client_id"], oc["redirect_uri"]).ok
    add("OA2", "oauth", "authorization code is single-use", code_replay, [Capability.OAUTH])

    def code_wrong_client(t):
        r = t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256("verifier-xyz"), "s")
        code = r.body.get("code")
        return not t.oauth_token(code, "verifier-xyz", oc["other_client_id"], oc["other_redirect_uri"]).ok
    add("OA5", "oauth", "code bound to its client", code_wrong_client, [Capability.OAUTH])

    # ---- 7. account takeover ----------------------------------------------
    def reset_single_use(t):
        tok = _reset_token(t.reset_request(user["email"]))
        if not tok:
            return False
        t.reset_confirm(tok, "new-1")
        return not t.reset_confirm(tok, "new-2").ok
    add("AT1", "takeover", "password-reset token is single-use", reset_single_use, [Capability.RESET_INTROSPECT])

    def reset_revokes(t):
        sess = _token(t, user)
        tok = _reset_token(t.reset_request(user["email"]))
        if not tok:
            return False
        t.reset_confirm(tok, "new-abc")
        return not t.get_resource(sess, user["id"]).ok
    add("AT3", "takeover", "password reset invalidates existing sessions", reset_revokes,
        [Capability.RESET_INTROSPECT])

    add("AT4", "takeover", "email change requires re-verification",
        lambda t: not t.change_email(_token(t, user), "attacker@evil.com", reverified=False).ok)

    # ---- 8. upload abuse ---------------------------------------------------
    add("UP2", "upload", "pixel-flood / oversized image rejected",
        lambda t: not t.upload(_token(t, user), width=60000, height=60000).ok, [Capability.MEDIA_UPLOAD])

    def upload_rate(t):
        tok = _token(t, user)
        hits = [t.upload(tok, filename=f"{i}.mp4").status for i in range(9)]
        return 429 in hits
    add("UP3", "upload", "upload endpoint rate-limited", upload_rate, [Capability.MEDIA_UPLOAD])

    # ---- 9. credential-theft mitigations ----------------------------------
    add("CT1", "cred-theft", "sensitive action requires step-up re-auth",
        lambda t: not t.sensitive_action(_token(t, user), reauthed=False).ok)

    def short_ttl(t):
        tok = t.login(user["username"], user["password"]).body.get("access_token")
        c = jf.payload_unverified(tok or "")
        return bool(c) and (c.get("exp", 0) - c.get("iat", 0)) <= 3600
    add("CT3", "cred-theft", "access tokens are short-lived (<=1h)", short_ttl)

    # ---- 10. information disclosure ---------------------------------------
    add("ID1", "info-leak", "errors don't leak stack traces",
        lambda t: "trace" not in str(t.buggy_endpoint("not-an-int").body).lower())
    def reset_uniform(t):
        r1 = t.reset_request(user["email"]); r2 = t.reset_request("ghost-nobody@x.com")
        return r1.status == r2.status and r1.body.get("message") == r2.body.get("message")
    add("ID2", "info-leak", "reset-request response uniform (no enumeration)", reset_uniform)
    def host_injection(t):
        link = t.reset_request(user["email"], host_header="attacker.com").body.get("_link_for_test", "")
        return bool(link) and "attacker.com" not in link
    add("ID3", "info-leak", "reset link ignores a spoofed Host header", host_injection,
        [Capability.RESET_INTROSPECT])

    return A


def _h(resp, name):
    for k, v in resp.headers.items():
        if k.lower() == name:
            return v
    return None
