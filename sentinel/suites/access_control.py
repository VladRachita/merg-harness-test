"""
Access-control suite: 45 attacks across brute force, injection, output headers,
session/token spoofing, authorization, OAuth2/PKCE, account takeover, upload
abuse, credential-theft mitigations and information disclosure.

Every attack is written against the Target contract, so the same catalogue runs
against the reference apps and a real backend. Attacks that need a gray-box hook
declare `requires`; they're SKIPPED (not failed) when the hook isn't configured.

Every check follows the same shape (see suites/common.py):

    1. CONTROL  a legitimate request must succeed  -> else INCONCLUSIVE
    2. ATTACK   the hostile request must be refused -> else LEAK

so "blocked" always means "the door works AND it was shut on the attacker" —
never "the route was wrong", "the test account was locked" or "nothing answered".
"""
from __future__ import annotations

import time

from ..adapters.base import Capability
from ..config import Config
from .common import (Attack, Inconclusive, NotApplicable, PROBE, MUTATES, EXHAUSTS, OTP_LOCK,
                     LOCKS, FLOODS, STRONG_PW,
                     STACK_TRACE, authed, denied, expect_ok, need_reset_token, need_token, reached, refused,
                     restore_password, stable, throttled, unique)
from . import jwt_forge as jf
from .pkce import s256

TRAVERSALS = (
    "../../etc/passwd",
    "..%2f..%2fetc%2fpasswd",            # encoded separators
    "%2e%2e/%2e%2e/etc/passwd",          # encoded dots
    "....//....//etc/passwd",            # survives a naive single-pass "../" strip
    "..%252f..%252fetc%252fpasswd",      # double-encoded
)

SQLI_LOGINS = ("' OR '1'='1' --", "admin'--", "\" OR \"\"=\"")


def build(cfg: Config) -> list[Attack]:
    U = cfg.users
    user, user2, admin = U["user"], U.get("user2"), U["admin"]
    # Lockout tests each burn an account. Give them different ones, so that on
    # a backend with no reset hook one test doesn't lock the other out of its
    # control login.  users.lockout (optional) keeps `user` usable afterwards.
    victim = U.get("lockout") or user
    victim2 = user2 or victim
    ISS, AUD = cfg.jwt_iss, cfg.jwt_aud
    oc = cfg.oauth
    bola = cfg.bola_object
    L = cfg.limits
    A: list[Attack] = []

    def add(id, cat, desc, check, requires=None, stage=PROBE):
        A.append(Attack(id, cat, desc, check, set(requires or []), stage))

    def admin_works(t):
        """Control for every admin-endpoint attack: a real admin gets in."""
        expect_ok(t.admin_users(need_token(t, admin)),
                  "the real admin listing users (genuine token)")

    # ---- 1. brute force & credential --------------------------------------
    def bf_lockout(t):
        need_token(t, victim)                               # the right password works first
        for _ in range(L["lockout_attempts"]):
            t.login(victim["username"], "wrong-pw")
        return denied(t.login(victim["username"], victim["password"]),
                      "correct-password login after repeated failures")
    add("BF1", "brute-force", "lockout holds even with the correct password", bf_lockout,
        stage=LOCKS)

    def bf_spray(t):
        hits = [reached(t.login(unique("spray"), "Password1", source_ip="9.9.9.9"))
                for _ in range(L["spray_attempts"])]
        return any(throttled(r, cfg) for r in hits)
    add("BF2", "brute-force", "password spraying throttled per source IP", bf_spray,
        stage=FLOODS)

    def bf_norm(t):
        need_token(t, victim2)
        name = victim2["username"]
        per = max(1, L["lockout_attempts"] // 2)
        for v in (name, name.upper(), f" {name} "):
            for _ in range(per):
                t.login(v, "wrong-pw")
        return denied(t.login(name, victim2["password"]),
                      "correct-password login after failures spread across spellings")
    add("BF3", "brute-force", "lockout counter shared across username casing/space", bf_norm,
        stage=LOCKS)

    def bf_xff(t):
        # distinct unknown accounts, so only the per-CLIENT limit can stop this —
        # and every attempt claims a different address in the client-IP header
        hits = [reached(t.login(unique("xff"), "wrong-pw", source_ip="7.7.7.7",
                                xff=f"198.51.100.{i + 1}"))
                for i in range(L["spray_attempts"])]
        return any(throttled(r, cfg) for r in hits)
    add("BF4", "brute-force", "spoofed X-Forwarded-For can't bypass the IP limit", bf_xff,
        stage=FLOODS)

    def bf_otp(t):
        need_token(t, victim)
        for _ in range(L["lockout_attempts"]):
            t.login(victim["username"], victim["password"], otp_ok=False)
        return throttled(reached(t.login(victim["username"], victim["password"], otp_ok=False)), cfg)
    add("BF5", "brute-force", "OTP / second-factor attempts rate-limited", bf_otp,
        [Capability.MFA], stage=OTP_LOCK)

    def bf_enum(t):
        r1 = reached(t.login(unique("no-such-user"), "x"))
        r2 = reached(t.login(user["username"], "wrong-pw"))
        if throttled(r1, cfg) or throttled(r2, cfg):
            raise Inconclusive("login is rate-limited right now — responses can't be compared")
        if r2.ok:
            raise Inconclusive("a wrong password was accepted for the seed user")
        return r1.status == r2.status and stable(r1.body) == stable(r2.body)
    add("BF6", "brute-force", "login gives no user-enumeration signal", bf_enum)

    # ---- 2. injection ------------------------------------------------------
    def sqli_login(t):
        need_token(t, user)                                 # the login route works
        return all(denied(t.login(p, "x"), "SQL-injection login") for p in SQLI_LOGINS)
    add("INJ1", "injection", "SQLi in username does not authenticate", sqli_login)

    def traversal(t):
        if cfg.media_sample:
            expect_ok(t.get_media(cfg.media_sample),
                      f"fetching the known media file '{cfg.media_sample}' (media_sample)")
        return all(denied(t.get_media(p), "path traversal") for p in TRAVERSALS)
    add("INJ5", "injection", "path traversal in media path rejected (5 encodings)", traversal)

    def ssrf(t):
        tok = authed(t, user)
        expect_ok(t.upload(tok), "a plain upload")
        return denied(t.upload(tok, fetch_url="http://169.254.169.254/latest/meta-data/"),
                      "import-by-URL to the cloud-metadata address")
    add("INJ6", "injection", "SSRF to cloud-metadata IP blocked", ssrf, [Capability.MEDIA_UPLOAD])

    # ---- 3. output / headers ----------------------------------------------
    add("OUT1", "output", "X-Content-Type-Options: nosniff present",
        lambda t: (reached(t.buggy_endpoint("1")).header("x-content-type-options") or "")
        .strip().lower() == "nosniff")
    add("OUT3", "output", "Content-Security-Policy present",
        lambda t: bool(reached(t.buggy_endpoint("1")).header("content-security-policy")))

    def attachment(t):
        r = expect_ok(t.upload(authed(t, user), filename="evil.svg"), "an upload")
        return (r.header("content-disposition") or "").strip().lower().startswith("attachment")
    add("OUT5", "output", "uploads served as attachments, never inline", attachment,
        [Capability.MEDIA_UPLOAD])

    # ---- 4. session & token ------------------------------------------------
    def forged(make, what):
        def check(t):
            admin_works(t)
            for tok in make(t):
                if not denied(t.admin_users(tok), what):
                    return False
            return True
        return check

    claims = lambda: jf.admin_claims(user["username"], user["id"], ISS, AUD)
    add("C1", "jwt", "alg:none admin token rejected (none/None/NONE/nOnE)",
        forged(lambda t: [jf.forge({"alg": a, "typ": "JWT"}, claims())
                          for a in ("none", "None", "NONE", "nOnE")], "unsigned (alg:none) token"))
    add("C2", "jwt", "RS256->HS256 confusion (HMAC w/ public key) rejected",
        forged(lambda t: [jf.forge({"alg": "HS256", "typ": "JWT"}, claims(), t.public_key())],
               "token HMAC-signed with the server's public key"),
        [Capability.SIGNING_KEY])
    add("C3", "jwt", "token signed with attacker secret rejected",
        forged(lambda t: [jf.forge({"alg": "HS256", "typ": "JWT"}, claims(), b"attacker-secret")],
               "token signed with an attacker-chosen secret"))

    def expired(t):
        good = t.issue_access_token(user["username"], aud=AUD)
        expect_ok(t.get_resource(good, user["id"]), "a freshly minted token reading own resource")
        old = t.issue_access_token(user["username"], aud=AUD, ttl=-60)
        exp = jf.payload_unverified(old).get("exp")
        if not exp or exp > time.time():
            raise Inconclusive("hooks.other_aud_token ignored the ttl — add '&ttl={ttl}' to the "
                               "hook so it can mint an already-expired token")
        return denied(t.get_resource(old, user["id"]), "validly-signed but expired token")
    add("C5", "jwt", "expired (but validly signed) token rejected", expired,
        [Capability.OTHER_AUD_TOKEN])

    def fixation(t):
        r = reached(t.login(user["username"], user["password"], prev_session="attacker-chosen-id"))
        if not r.body.get("access_token"):
            raise Inconclusive(f"could not log in as '{user['username']}' (HTTP {r.status})")
        if not r.body.get("sid"):
            raise NotApplicable("login issues no session id/cookie (token-only API)")
        return r.body["sid"] != "attacker-chosen-id"
    add("SES1", "session", "session id rotates on login (no fixation)", fixation)

    def logout_revoke(t):
        tok = authed(t, user)
        expect_ok(t.logout(tok), "logout")
        return denied(t.get_resource(tok, user["id"]), "token reuse after logout")
    add("SES2", "session", "token revoked after logout", logout_revoke)

    def pwchange_revoke(t):
        tok = authed(t, user)
        try:
            expect_ok(t.change_password(tok, user["password"], STRONG_PW, reauthed=True),
                      "a legitimate password change (with step-up)")
            return denied(t.get_resource(tok, user["id"]), "old token after password change")
        finally:
            restore_password(t, user, STRONG_PW)
    add("SES3", "session", "tokens revoked after password change", pwchange_revoke, stage=MUTATES)

    def refresh_reuse(t):
        r = reached(t.login(user["username"], user["password"]))
        if not r.body.get("access_token"):
            raise Inconclusive(f"could not log in as '{user['username']}' (HTTP {r.status})")
        rt = r.body.get("refresh_token")
        if not rt:
            raise NotApplicable("login returns no refresh token (check refresh_json_path)")
        expect_ok(t.refresh_token(rt), "the first use of a refresh token")
        return denied(t.refresh_token(rt), "second use of the same refresh token")
    add("SES4", "session", "refresh-token reuse detected, family killed", refresh_reuse)

    def cookie_flags(t):
        r = reached(t.login(user["username"], user["password"]))
        if not r.ok:
            raise Inconclusive(f"could not log in as '{user['username']}' (HTTP {r.status})")
        cookies = r.cookies()
        if not cookies:
            raise NotApplicable("login sets no cookie (token-only API)")
        session = [c for c in cookies if c.strip().startswith(cfg.session_cookie + "=")] or cookies
        return all(all(flag in c.lower() for flag in ("httponly", "secure", "samesite"))
                   for c in session)
    add("SES5", "session", "session cookie sets HttpOnly/Secure/SameSite", cookie_flags)

    def csrf(t):
        tok = authed(t, user)
        try:
            return refused(t.change_password(tok, user["password"], STRONG_PW, reauthed=True,
                                             cross_site=True), "cross-site password change")
        finally:
            restore_password(t, user, STRONG_PW)
    add("SES6", "session", "cross-site state change rejected (CSRF)", csrf,
        [Capability.CSRF], stage=MUTATES)

    def token_substitution(t):
        good = t.issue_access_token(user["username"], aud=AUD)
        expect_ok(t.get_resource(good, user["id"]), "a correctly-addressed minted token")
        other = t.issue_access_token(user["username"], aud="sentinel-other-audience")
        return denied(t.get_resource(other, user["id"]), "token minted for another audience")
    add("SES7", "session", "wrong-audience token rejected (no substitution)",
        token_substitution, [Capability.OTHER_AUD_TOKEN])

    # ---- 5. authorization --------------------------------------------------
    def user_on_admin(t):
        admin_works(t)
        return denied(t.admin_users(authed(t, user)), "ordinary user on the admin endpoint")
    add("AZ1", "authz", "user token on admin endpoint forbidden", user_on_admin)

    def idor(t):
        tok = authed(t, user)                               # control: own resource readable
        return denied(t.get_resource(tok, user2["id"]), "reading another user's resource")
    add("AZ2", "authz", "IDOR: user reads another user's resource", idor, [Capability.TWO_ACCOUNTS])

    def bola_check(t):
        owner = U.get(bola.get("owner", "user2"))
        if not owner:
            raise Inconclusive(f"bola_object.owner '{bola.get('owner')}' is not a configured user")
        expect_ok(t.get_object(need_token(t, owner), bola["kind"], bola["id"]),
                  f"the owner reading their own {bola['kind']} {bola['id']} (bola_object)")
        return denied(t.get_object(authed(t, user), bola["kind"], bola["id"]),
                      "reading another user's object by id")
    add("AZ3", "authz", "BOLA: user reads another user's object", bola_check,
        [Capability.TWO_ACCOUNTS])

    def verb_tampering(t):
        tok = authed(t, user)
        target = user2["username"] if user2 else "x"
        # the canonical verb must be refused with a real 401/403 (proves the route)
        if not refused(t.admin_delete_user(tok, target, method="DELETE"),
                       "ordinary user calling the admin delete route"):
            return False
        return all(denied(t.admin_delete_user(tok, target, method=m), f"{m} on the admin route")
                   for m in ("PUT", "POST", "PATCH"))
    add("AZ4", "authz", "function-level authz holds across HTTP methods", verb_tampering,
        stage=MUTATES)

    PRIV = {"isVerified": True, "is_admin": True, "balance": 999999, "role": "admin"}

    def massassign(t):
        base, evil = unique("control"), unique("mallory")
        expect_ok(t.register(base, STRONG_PW), "registering an ordinary control account")
        r = reached(t.register(evil, STRONG_PW, requested_role="admin", extra=dict(PRIV)))
        if denied(r, "registration carrying privilege fields"):
            return True                                     # refused outright
        return all(t.user_field(evil, f) == t.user_field(base, f)
                   for f in ("role", "verified", "balance"))
    add("AZ5", "authz", "mass assignment of role/privilege ignored", massassign,
        [Capability.USER_ADMIN], stage=MUTATES)

    def disabled(t):
        tok = authed(t, user)
        t.set_enabled(user["username"], False)
        try:
            return denied(t.get_resource(tok, user["id"]), "token of a disabled account")
        finally:
            t.set_enabled(user["username"], True)
    add("AZ6", "authz", "token for a disabled account rejected", disabled,
        [Capability.USER_ADMIN], stage=MUTATES)

    def selfreg_admin(t):
        admin_works(t)
        name = unique("mallory")
        r = reached(t.register(name, STRONG_PW, requested_role="admin", extra=dict(PRIV)))
        if denied(r, "registration carrying privilege fields"):
            return True
        tok = reached(t.login(name, STRONG_PW)).body.get("access_token")
        if not tok:
            raise Inconclusive("the account was created but cannot sign in yet (e-mail "
                               "verification?) — its privileges can't be observed black-box; "
                               "AZ5 covers this with hooks.user_admin")
        return denied(t.admin_users(tok), "self-registered 'admin' on the admin endpoint")
    add("AZ7", "authz", "self-registration with role=admin gains no admin access (black-box)",
        selfreg_admin, stage=MUTATES)

    # ---- 6. oauth2 / pkce --------------------------------------------------
    VERIFIER = "verifier-xyz-" + "0" * 32                   # RFC 7636: 43..128 chars

    def grant(t):
        r = expect_ok(t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256(VERIFIER),
                                        "state-1"), "a fully valid authorization request")
        if not r.body.get("code"):
            raise Inconclusive("the authorization response carries no code")
        return r.body["code"]

    def pkce_required(t):
        grant(t)
        return denied(t.oauth_authorize(oc["client_id"], oc["redirect_uri"], None, "s"),
                      "authorization request without PKCE")
    add("OA1", "oauth", "PKCE mandatory for public clients", pkce_required, [Capability.OAUTH])

    def redirect_exact(t):
        grant(t)
        for uri in ("https://attacker.example/cb", oc["redirect_uri"] + ".attacker.example",
                    oc["redirect_uri"] + "/../../attacker"):
            if not denied(t.oauth_authorize(oc["client_id"], uri, s256(VERIFIER), "s"),
                          "authorization request with an unregistered redirect_uri"):
                return False
        return True
    add("OA3", "oauth", "redirect_uri must exactly match a registered one", redirect_exact,
        [Capability.OAUTH])

    def state_required(t):
        grant(t)
        return denied(t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256(VERIFIER), None),
                      "authorization request without state")
    add("OA4", "oauth", "state required (callback CSRF)", state_required, [Capability.OAUTH])

    def code_replay(t):
        code = grant(t)
        expect_ok(t.oauth_token(code, VERIFIER, oc["client_id"], oc["redirect_uri"]),
                  "the first exchange of an authorization code")
        return denied(t.oauth_token(code, VERIFIER, oc["client_id"], oc["redirect_uri"]),
                      "second exchange of the same code")
    add("OA2", "oauth", "authorization code is single-use", code_replay, [Capability.OAUTH])

    def code_wrong_client(t):
        code = grant(t)
        return denied(t.oauth_token(code, VERIFIER, oc["other_client_id"], oc["other_redirect_uri"]),
                      "code exchanged by a different client")
    add("OA5", "oauth", "code bound to its client", code_wrong_client, [Capability.OAUTH])

    # ---- 7. account takeover ----------------------------------------------
    def reset_single_use(t):
        tok = need_reset_token(t, user)
        try:
            expect_ok(t.reset_confirm(tok, STRONG_PW), "the first use of a reset token")
            return denied(t.reset_confirm(tok, STRONG_PW + "2"), "second use of the reset token")
        finally:
            restore_password(t, user, STRONG_PW + "2", STRONG_PW)
    add("AT1", "takeover", "password-reset token is single-use", reset_single_use,
        [Capability.RESET_INTROSPECT], stage=MUTATES)

    def reset_revokes(t):
        sess = authed(t, user)
        tok = need_reset_token(t, user)
        try:
            expect_ok(t.reset_confirm(tok, STRONG_PW), "a password reset")
            return denied(t.get_resource(sess, user["id"]), "pre-reset session after the reset")
        finally:
            restore_password(t, user, STRONG_PW)
    add("AT3", "takeover", "password reset invalidates existing sessions", reset_revokes,
        [Capability.RESET_INTROSPECT], stage=MUTATES)

    add("AT4", "takeover", "email change requires re-verification",
        email_change_check(cfg, "attacker@evil.example"), stage=MUTATES)

    # ---- 8. upload abuse ---------------------------------------------------
    def pixel_flood(t):
        tok = authed(t, user)
        expect_ok(t.upload(tok), "a plain upload")
        return denied(t.upload(tok, width=60000, height=60000), "3.6-gigapixel image")
    add("UP2", "upload", "pixel-flood / oversized image rejected", pixel_flood,
        [Capability.MEDIA_UPLOAD])

    def upload_rate(t):
        tok = authed(t, user)
        expect_ok(t.upload(tok, filename="0.mp4"), "a plain upload")
        return any(throttled(reached(t.upload(tok, filename=f"{i}.mp4")), cfg) for i in range(1, 9))
    add("UP3", "upload", "upload endpoint rate-limited", upload_rate, [Capability.MEDIA_UPLOAD],
        stage=EXHAUSTS)

    # ---- 9. credential-theft mitigations ----------------------------------
    add("CT1", "cred-theft", "sensitive action requires step-up re-auth",
        lambda t: refused(t.sensitive_action(authed(t, user), reauthed=False),
                          "sensitive action without step-up"))

    def short_ttl(t):
        c = jf.payload_unverified(need_token(t, user))
        if not c or "exp" not in c:
            raise NotApplicable("the access token is opaque (not a JWT with exp) — its lifetime "
                                "can't be read from outside")
        return c["exp"] - c.get("iat", int(time.time())) <= 3600
    add("CT3", "cred-theft", "access tokens are short-lived (<=1h)", short_ttl)

    # ---- 10. information disclosure ---------------------------------------
    def no_trace(t):
        r = reached(t.buggy_endpoint("not-an-int"))
        return not STACK_TRACE.search(str(r.body))
    add("ID1", "info-leak", "errors don't leak stack traces", no_trace)

    def reset_uniform(t):
        r1 = expect_ok(t.reset_request(user["email"]), "a reset request for a real account")
        r2 = reached(t.reset_request(f"{unique('ghost')}@nobody.example"))
        return r1.status == r2.status and stable(r1.body) == stable(r2.body)
    add("ID2", "info-leak", "reset-request response uniform (no enumeration)", reset_uniform)

    def host_injection(t):
        need_reset_token(t, user)                           # the link is observable at all
        r = reached(t.reset_request(user["email"], host_header="attacker.example"))
        if not r.ok:
            return denied(r, "reset request with a spoofed Host")   # unknown Host refused
        link = str(r.body.get("_link_for_test") or r.body.get("link") or r.body.get("reset_link") or "")
        if not link:
            raise Inconclusive("the reset link was not echoed for the spoofed-Host request")
        return "attacker.example" not in link
    add("ID3", "info-leak", "reset link ignores a spoofed Host header", host_injection,
        [Capability.RESET_INTROSPECT])

    return A


def email_change_check(cfg: Config, new_email: str):
    """Shared by AT4 and OCT2. A well-built backend may ACCEPT the request and
    hold the change pending verification, so a 2xx alone is not a leak: with the
    user_admin hook we look at what was actually stored."""
    user = cfg.users["user"]

    def check(t):
        tok = authed(t, user)
        r = t.change_email(tok, new_email, reverified=False)
        if refused(r, "e-mail change without re-verification"):
            return True
        if Capability.USER_ADMIN not in t.capabilities():
            raise Inconclusive(
                f"the server accepted the request (HTTP {r.status}) — 'pending verification' "
                f"and 'changed immediately' look the same from outside; configure "
                f"hooks.user_admin so the stored address can be checked")
        try:
            stored = t.user_field(user["username"], "email")
            if stored is None:
                raise Inconclusive("hooks.user_admin does not expose the stored 'email'")
            return stored != new_email
        finally:
            try:
                t.change_email(tok, user.get("email", ""), reverified=True)
            except Exception:
                pass
    return check
