"""
oct2026 suite — checks modelled on the app-level techniques seen in the
October 2026 wave of incidents. Each check asserts the app BLOCKS the technique
(defensive); it is written against the Target contract, capability-gated, and
validated against the reference secure/vulnerable apps like every other suite.

Threat mapping (what real attackers did -> what we test):

  OCT1  OAuth "state" / auth-code reused as a magic-link / verification token to
        sign in or self-verify as another user.
        → Better Auth CVE-2026-110862 (a.k.a. CVE-2026-114607), Snipe-IT
          CVE-2026-116199 (OAuth callback bypass).
  OCT2  A social/OAuth or self-service flow yields a falsely e-mail-verified
        account / lets e-mail change without re-verification (account takeover).
        → Better Auth "falsely email-verified account".
  OCT3  Unauthenticated password-reset endpoint abused: injection input and
        token replay. → Metabase CVE-2026-72898 (unauth SQLi in reset endpoint
        → admin takeover).
  OCT4  A protected / privileged operation reachable with NO or a forged token.
        → BeyondTrust Remote Support CVE-2026-102764 (unauth file operations).
  OCT5  Media import/"fetch by URL" pointed at loopback / cloud-metadata / RFC1918
        (SSRF → internal token theft). → Plex CVE-2026-96652 (SSRF in the player
        timeline endpoint; loopback request gets the owner's admin token).
  OCT6  Hostile / container-confused / undecodable media accepted into the
        transcode pipeline. → Plex CVE-2026-96654/55/56 (crafted media writes a
        library into the Codecs dir, loaded without signature checks → RCE).
  OCT7  Function-level authz bypassed by HTTP verb tampering on an edge API.
        → ASEC "outer contact point collapsed" edge-API theme; SiteGuard WAF
          command-injection class.
  OCT8  BOLA — one user reads another user's object by id (the single most
        exploited API weakness reported through 2026).
  OCT9  Mass assignment — client injects privilege fields (role/verified/balance).

Sources are listed in the module docstring of scripts/campaign.py and in the
report it generates.
"""
from __future__ import annotations

from ..adapters.base import Capability
from ..config import Config
from .common import Attack
from .pkce import s256


def _token(t, user):
    return t.login(user["username"], user["password"]).body.get("access_token", "")


def _reset_token(resp):
    b = resp.body
    for k in ("_link_for_test", "link", "reset_link"):
        if b.get(k):
            return str(b[k]).split("token=")[-1]
    return b.get("token") or b.get("reset_token")


# internal / sensitive hosts an SSRF would target (Plex chain hit loopback:32400)
SSRF_URLS = [
    "http://169.254.169.254/latest/meta-data/",   # cloud metadata
    "http://127.0.0.1:32400/",                     # loopback (Plex agent port)
    "http://localhost/admin",
    "http://10.0.0.1/",
    "http://[::1]/",
    "http://metadata.google.internal/",
]


def build(cfg: Config) -> list[Attack]:
    U = cfg.users
    user, user2, admin = U["user"], U.get("user2"), U["admin"]
    oc = cfg.oauth
    A: list[Attack] = []

    def add(id, cat, desc, check, requires=None):
        A.append(Attack(id, cat, desc, check, set(requires or [])))

    # ---- OCT1: OAuth state/code can't be redeemed as a reset/verification token
    def oauth_token_confusion(t):
        r = t.oauth_authorize(oc["client_id"], oc["redirect_uri"], s256("v"), "state-abc123")
        candidates = [r.body.get("state") or "state-abc123", r.body.get("code") or ""]
        # none of these OAuth artefacts may act as a password-reset token
        return all(not t.reset_confirm(tok, "attacker-pw").ok for tok in candidates if tok)
    add("OCT1", "oauth-confusion",
        "OAuth state/code is not accepted as a reset/verification token "
        "(Better Auth CVE-2026-110862)", oauth_token_confusion, [Capability.OAUTH])

    # ---- OCT2: no falsely-verified takeover; email change needs re-verification
    add("OCT2", "takeover",
        "email change requires re-verification (no falsely-verified takeover; "
        "Better Auth)",
        lambda t: not t.change_email(_token(t, user), "attacker@evil.example",
                                     reverified=False).ok)

    # ---- OCT3a: reset endpoint survives injection input (no 500 / no leak)
    def reset_injection_safe(t):
        r = t.reset_request("' OR '1'='1' --@x.com")
        body = str(r.body).lower()
        return r.status != 500 and "trace" not in body and "sql" not in body
    add("OCT3a", "injection",
        "password-reset endpoint doesn't 500 or leak on injection input "
        "(Metabase CVE-2026-72898)", reset_injection_safe)

    # ---- OCT3b: reset token is single-use (no replay to takeover)
    def reset_single_use(t):
        tok = _reset_token(t.reset_request(user["email"]))
        if not tok:
            return False
        t.reset_confirm(tok, "new-1")
        return not t.reset_confirm(tok, "new-2").ok
    add("OCT3b", "takeover",
        "password-reset token is single-use (no replay; Metabase)",
        reset_single_use, [Capability.RESET_INTROSPECT])

    # ---- OCT4: privileged/admin operation denied with NO or forged token
    def unauth_privileged(t):
        for tok in ("", "garbage", "a.b.c"):
            if t.admin_users(tok).ok:
                return False
            if t.get_resource(tok, user["id"]).ok:
                return False
        return True
    add("OCT4", "authz",
        "privileged operation refused without a valid token "
        "(BeyondTrust CVE-2026-102764)", unauth_privileged)

    # ---- OCT5: media import/fetch can't reach loopback/metadata/RFC1918 (SSRF)
    def media_ssrf(t):
        tok = _token(t, user)
        return all(not t.upload(tok, fetch_url=u).ok for u in SSRF_URLS)
    add("OCT5", "ssrf",
        "media 'fetch by URL' blocks loopback / cloud-metadata / internal hosts "
        "(Plex CVE-2026-96652)", media_ssrf, [Capability.MEDIA_UPLOAD])

    # ---- OCT6: hostile / confused / undecodable media rejected pre-processing
    def media_parser_confusion(t):
        tok = _token(t, user)
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 48
        cases = [
            ("evil.mp4", png, "video/mp4"),                               # ext/content mismatch
            ("trunc.mp4", b"\x00\x00\x00\x18ftyp" + b"\x00" * 4, "video/mp4"),  # truncated
            ("x.mp4", b"not a media file at all", "video/mp4"),           # garbage
        ]
        return all(not t.upload_bytes(tok, n, d, c).ok for n, d, c in cases)
    add("OCT6", "media",
        "container-confused / undecodable media rejected before transcode "
        "(Plex CVE-2026-96654/55/56)", media_parser_confusion, [Capability.MEDIA_UPLOAD])

    # ---- OCT7: verb tampering can't bypass function-level authz on an edge API
    add("OCT7", "authz",
        "function-level authz holds across HTTP methods (verb tampering; edge API)",
        lambda t: not t.admin_delete_user(_token(t, user),
                                          (user2["username"] if user2 else "x"),
                                          method="PUT").ok)

    # ---- OCT8: BOLA — one user can't read another user's object
    add("OCT8", "authz",
        "BOLA: a user cannot read another user's object by id",
        lambda t: not t.get_object(_token(t, user), "video", 102).ok,
        [Capability.TWO_ACCOUNTS])

    # ---- OCT9: mass assignment of privilege fields is ignored
    def mass_assign(t):
        t.register("oct_mallory", "pw", requested_role="admin",
                   extra={"role": "admin", "isVerified": True, "balance": 10 ** 9})
        return t.user_field("oct_mallory", "role") == "user"
    add("OCT9", "authz",
        "mass assignment of role/privilege fields ignored", mass_assign,
        [Capability.USER_ADMIN])

    return A
