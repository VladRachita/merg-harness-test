"""
oct2026 suite — checks modelled on application-level techniques that were being
exploited in October 2026. Each check asserts the app BLOCKS the technique
(defensive); it is written against the Target contract, capability-gated, and
validated against the reference secure/vulnerable apps like every other suite.

Threat mapping (what attackers did -> the control we assert). CVE ids, products
and dates were checked against the public CVE records and CISA's Known Exploited
Vulnerabilities (KEV) catalogue on 2026-11-09; see docs/THREATS-2026-Q4.md for
the sources and for what could NOT be verified.

  OCT1  An OAuth sign-in `state` value was accepted as a magic-link token, giving
        a session as an existing user. → Better Auth, CVE-2026-114607 /
        CVE-2026-110862 (GHSA-965c-763c-88jm; CVEs published 14 & 22 Oct 2026).
        Control: verification tokens are bound to their purpose.
  OCT2  The same flaw produced a falsely e-mail-verified account.
        Control: an e-mail address never takes effect before it is verified.
  OCT3  Unauthenticated SQL injection in a password-reset endpoint → admin.
        → Metabase CVE-2026-72898. NOTE: disclosed Aug 2026 (KEV 11 Aug), kept
        here because the class stayed in active use. Controls: the reset
        endpoint treats input as data (OCT3a); reset tokens are single-use (OCT3b).
  OCT4  A privileged operation was reachable by a caller that never proved who
        it was (origin of a message was not validated, CWE-290).
        → BeyondTrust Remote Support CVE-2026-102764 (15 Oct; KEV 16 Oct).
  OCT5  A "fetch this URL" feature reached internal addresses (SSRF).
        → Plex Media Server CVE-2026-96652 (/player/timeline) and
          CVE-2026-96655 (transcode); KEV 20 Oct 2026.
  OCT6  A crafted or disguised upload was accepted and written to disk.
        → unrestricted-upload class: Adobe Commerce CVE-2026-48356 (KEV 27 Oct),
          Cisco Secure Email Gateway CVE-2026-76519 (KEV 14 Oct).
  OCT7  Function-level authorization skipped for some HTTP verbs on an exposed
        API (the "outer contact point" theme of AhnLab ASEC's October report —
        secondary source).
  OCT8  BOLA — one caller reads or changes another's object by id.
        → e.g. Authlib CVE-2026-116672 (27 Oct): any registration token could
          read/modify another OAuth client.
  OCT9  Mass assignment — the client supplies its own privilege fields.

OCT2/3b/7/8/9 reuse the access_control implementations (AT4/AT1/AZ4/AZ3/AZ5) so
there is exactly one definition of each control.
"""
from __future__ import annotations

from ..adapters.base import Capability
from ..config import Config
from . import access_control
from .common import (Attack, Inconclusive, Leak, MUTATES, SQL_ERRORS, STACK_TRACE, STRONG_PW,
                     authed, denied, expect_ok, need_token, reached, refused, restore_password,
                     strings, throttled)
from .media_injection import valid_upload
from .pkce import s256

# Internal / sensitive destinations an SSRF would aim for, in every spelling a
# naive block-list misses.
SSRF_URLS = [
    "http://169.254.169.254/latest/meta-data/",   # cloud metadata
    "http://127.0.0.1:32400/",                     # loopback service port
    "http://localhost/admin",
    "http://10.0.0.1/",                            # RFC 1918
    "http://192.168.0.1/",
    "http://[::1]/",                               # IPv6 loopback
    "http://metadata.google.internal/",
    "http://0.0.0.0/",
    "http://2130706433/",                          # 127.0.0.1 as one decimal integer
    "http://0x7f000001/",                          # ...as hex
    "http://017700000001/",                        # ...as octal
    "http://127.1/",                               # ...short form
    "http://[::ffff:169.254.169.254]/",            # IPv4-mapped IPv6
    "http://public.example@127.0.0.1/",            # userinfo confusion
    "file:///etc/passwd",                          # non-http schemes
    "gopher://127.0.0.1:6379/_",
]


def build(cfg: Config) -> list[Attack]:
    U = cfg.users
    user, admin = U["user"], U["admin"]
    oc = cfg.oauth
    ac = {a.id: a for a in access_control.build(cfg)}
    A: list[Attack] = []

    def add(id, cat, desc, check, requires=None, stage=0):
        A.append(Attack(id, cat, desc, check, set(requires or []), stage))

    def same_as(id, other, cat, desc):
        o = ac[other]
        add(id, cat, desc, o.check, o.requires, o.stage)

    # ---- OCT1: OAuth state/code can't be redeemed as a reset/verification token
    def oauth_token_confusion(t):
        state = "state-" + "abc123" * 4
        r = expect_ok(t.oauth_authorize(oc["client_id"], oc["redirect_uri"],
                                        s256("verifier-" + "0" * 40), state),
                      "a fully valid authorization request")
        try:
            for name, artefact in (("state", r.body.get("state") or state),
                                   ("code", r.body.get("code"))):
                if artefact and not refused(t.reset_confirm(artefact, STRONG_PW),
                                            f"OAuth {name} offered as a reset token"):
                    raise Leak(f"the OAuth {name} value was accepted as a password-reset token")
            return True
        finally:
            restore_password(t, user, STRONG_PW)
    add("OCT1", "oauth-confusion",
        "OAuth state/code is not accepted as a reset/verification token "
        "(Better Auth CVE-2026-114607)", oauth_token_confusion, [Capability.OAUTH], MUTATES)

    # ---- OCT2: no falsely-verified takeover; email change needs re-verification
    add("OCT2", "takeover",
        "e-mail change takes effect only after re-verification (Better Auth CVE-2026-114607)",
        access_control.email_change_check(cfg, "attacker@evil.example"), stage=MUTATES)

    # ---- OCT3a: reset endpoint survives injection input (no 5xx / no leak)
    def reset_injection_safe(t):
        expect_ok(t.reset_request(user["email"]), "a reset request for a real account")
        for probe in ("' OR '1'='1' --@x.com", "x@x.com' AND 1=CAST((SELECT 1) AS int)--",
                      "x@x.com\"; --"):
            r = reached(t.reset_request(probe))
            text = " ".join(strings(r.body))
            if r.status >= 500:
                raise Leak(f"HTTP {r.status} on a quote in the e-mail field — input reached a parser")
            if SQL_ERRORS.search(text) or STACK_TRACE.search(str(r.body)):
                raise Leak("a database/stack error is echoed from the reset endpoint")
        return True
    add("OCT3a", "injection",
        "password-reset endpoint treats hostile input as data — no 5xx, no SQL error "
        "(Metabase CVE-2026-72898)", reset_injection_safe)

    # ---- OCT3b: reset token is single-use (no replay to takeover)
    same_as("OCT3b", "AT1", "takeover",
            "password-reset token is single-use (no replay; Metabase CVE-2026-72898)")

    # ---- OCT4: privileged/admin operation denied without a proven identity
    def unauth_privileged(t):
        expect_ok(t.admin_users(need_token(t, admin)), "the real admin listing users")
        authed(t, user)                                     # the resource route works
        for tok in ("", "garbage", "a.b.c", "null", "undefined"):
            if not denied(t.admin_users(tok), f"admin endpoint with token {tok!r}"):
                raise Leak(f"the admin endpoint answered with token {tok!r}")
            if not denied(t.get_resource(tok, user["id"]), f"user resource with token {tok!r}"):
                raise Leak(f"a private resource was served with token {tok!r}")
        return True
    add("OCT4", "authz",
        "privileged operation refused without a valid token (BeyondTrust CVE-2026-102764)",
        unauth_privileged)

    # ---- OCT5: media import/fetch can't reach loopback/metadata/RFC1918 (SSRF)
    def media_ssrf(t):
        tok = authed(t, user)
        expect_ok(t.upload(tok), "a plain upload")
        for i, url in enumerate(SSRF_URLS):
            r = reached(t.upload(tok, fetch_url=url))
            if throttled(r, cfg):
                raise Inconclusive(f"rate-limited after {i} of {len(SSRF_URLS)} destinations — "
                                   f"the SSRF filter was not exercised on the rest")
            if not denied(r, f"import-by-URL to {url}"):
                raise Leak(f"the server agreed to fetch {url}")
        return True
    add("OCT5", "ssrf",
        f"'fetch by URL' refuses {len(SSRF_URLS)} internal destinations incl. decimal/hex/"
        "IPv6-mapped spellings (Plex CVE-2026-96652/96655)", media_ssrf, [Capability.MEDIA_UPLOAD])

    # ---- OCT6: hostile / confused / undecodable media rejected pre-processing
    def media_parser_confusion(t):
        tok = authed(t, user)
        valid_upload(t, tok)
        png = b"\x89PNG\r\n\x1a\n" + b"\x00" * 48
        cases = [
            ("evil.mp4", png, "video/mp4", "a PNG renamed .mp4"),
            ("trunc.mp4", b"\x00\x00\x00\x18ftyp" + b"\x00" * 4, "video/mp4", "a truncated MP4"),
            ("x.mp4", b"not a media file at all", "video/mp4", "plain text named .mp4"),
            ("shell.php.mp4", b"<?php echo 1; ?>", "video/mp4", "a script with a media suffix"),
        ]
        for name, data, ctype, what in cases:
            r = reached(t.upload_bytes(tok, name, data, ctype))
            if r.ok:
                raise Leak(f"{what} ('{name}') was accepted")
            if r.status >= 500:
                raise Leak(f"{what} ('{name}') crashed the upload pipeline (HTTP {r.status})")
        return True
    add("OCT6", "media",
        "disguised / undecodable uploads rejected before storage "
        "(unrestricted-upload class: Adobe Commerce CVE-2026-48356)",
        media_parser_confusion, [Capability.MEDIA_UPLOAD])

    # ---- OCT7..9: one definition each, shared with access_control
    same_as("OCT7", "AZ4", "authz",
            "function-level authz holds across HTTP methods (verb tampering on an exposed API)")
    same_as("OCT8", "AZ3", "authz",
            "BOLA: a user cannot read another user's object by id (cf. Authlib CVE-2026-116672)")
    same_as("OCT9", "AZ5", "authz", "mass assignment of role/privilege fields ignored")

    return A
