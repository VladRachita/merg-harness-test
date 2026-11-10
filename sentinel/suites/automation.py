"""
automation suite — does the backend hold up against BOTS and scripted agents?

A person types a password a few times. A bot — or an AI agent told to "get in" —
tries thousands of things per minute and, crucially, changes how each request
LOOKS so a naive rate limiter sees thousands of different "clients". This suite
asserts the limits survive that, using OWASP's Automated Threat (OAT) taxonomy:

  BOT1  OAT-008 credential stuffing   the per-client login limit can't be dodged
                                      by rotating client-IP headers
        → Echo (Go) CVE-2026-118653 (28 Oct 2026): the default rate limiter
          keyed on the client-supplied X-Forwarded-For.
  BOT2  OAT-008                       ...nor by rotating User-Agent / device ids
  BOT3  OAT-008                       ...nor by an equivalent spelling of the route
        → cf. Vikunja CVE-2026-91972: a second set of auth routes had no limit.
  BOT4  OAT-008                       ...nor by switching the body encoding
  BOT5  OAT-019 account creation      a burst of sign-ups is throttled (spam accounts)
  BOT6  OAT-002 token cracking        guessing reset tokens is throttled

(Single-account brute force, spraying and OTP guessing — OAT-007 — are BF1–BF5
in access_control; upload flooding is UP3.)

How the evasion checks work, and why they don't flood the target: the limiter is
tripped ONCE with ordinary failed logins (that it trips at all is the control),
then each evasion gets a single attempt. A throttle answer means the limiter saw
through it; an ordinary "wrong password" answer means the request was counted
as a brand-new client — the limit is bypassed. ~40 requests per check.
"""
from __future__ import annotations

import secrets

from ..adapters.base import PATH_VARIANTS
from ..config import Config
from .common import (Attack, EXHAUSTS, FLOODS, Inconclusive, Leak, STRONG_PW, reached, refused,
                     throttled, unique)

CLIENT_IP_HEADERS = ("X-Forwarded-For", "X-Real-IP", "X-Client-IP", "True-Client-IP",
                     "CF-Connecting-IP", "X-Originating-IP", "X-Cluster-Client-IP",
                     "Fastly-Client-IP")
USER_AGENTS = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/141.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 19_0 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148",
    "okhttp/5.1.0",
)


def build(cfg: Config) -> list[Attack]:
    L = cfg.limits
    A: list[Attack] = []
    seen = {"baseline": None}          # status of an ordinary failed login, once observed
    SRC = "198.51.100.77"              # the one client all of this comes from

    def add(id, desc, check, stage=FLOODS):
        A.append(Attack(id, "bots", desc, check, set(), stage))

    def trip_limiter(t):
        """Fail logins on distinct unknown accounts until the per-client limit
        trips. No trip => there is no limiter to evade, which is the finding."""
        tries = L["spray_attempts"] * 2
        for _ in range(tries):
            r = reached(t.login(unique("bot"), "wrong-pw", source_ip=SRC))
            if throttled(r, cfg):
                return
            if r.ok:
                raise Inconclusive("a login for a made-up account succeeded — cannot test limits")
            seen["baseline"] = r.status
        raise Leak(f"{tries} failed logins in a row from one client and none was throttled — "
                   f"unlimited guessing (statuses seen: {seen['baseline']})")

    def evades(t, evasion):
        """True if a request dressed up with `evasion` gets past the tripped limiter."""
        r = reached(t.login(unique("bot"), "wrong-pw", source_ip=SRC, evasion=evasion))
        if throttled(r, cfg):
            return False
        if r.ok:
            return True
        # an ordinary failure => it was processed as a fresh client (bypass).
        # anything else (404/405/400/415…) => this spelling isn't served at all.
        return r.status == (seen["baseline"] or 401)

    def evasion_check(variants):
        def check(t):
            trip_limiter(t)
            for label, ev in variants():
                if evades(t, ev):
                    raise Leak(f"the login limit was bypassed by {label}")
            return True
        return check

    def ip():
        return f"203.0.113.{secrets.randbelow(250) + 1}"

    add("BOT1", "login limit survives client-IP header rotation — 10 headers "
        "(OAT-008; Echo CVE-2026-118653)", evasion_check(lambda: (
            [(f"a spoofed {h} header", {"headers": {h: ip()}}) for h in CLIENT_IP_HEADERS]
            + [("a spoofed Forwarded header", {"headers": {"Forwarded": f"for={ip()}"}}),
               ("claiming to be localhost (X-Forwarded-For: 127.0.0.1)",
                {"headers": {"X-Forwarded-For": "127.0.0.1"}})])))

    add("BOT2", "login limit survives User-Agent / device-id rotation (OAT-008)",
        evasion_check(lambda: (
            [(f"a different User-Agent ({ua.split('/')[0]}…)", {"headers": {"User-Agent": ua}})
             for ua in USER_AGENTS]
            + [("a fresh X-Device-Id", {"headers": {"X-Device-Id": secrets.token_hex(8)}}),
               ("a fresh device cookie", {"headers": {"Cookie": f"device={secrets.token_hex(8)}"}})])))

    add("BOT3", "login limit survives alternate spellings of the route (OAT-008; "
        "cf. Vikunja CVE-2026-91972)", evasion_check(lambda: (
            [(f"the '{v}' spelling of the login path", {"path": v}) for v in PATH_VARIANTS])))

    add("BOT4", "login limit survives a body-encoding / method-override switch (OAT-008)",
        evasion_check(lambda: [
            ("a form-encoded body", {"form": True}),
            ("an X-HTTP-Method-Override header", {"headers": {"X-HTTP-Method-Override": "PUT"}}),
        ]))

    def signup_burst(t):
        n = L["burst"]
        first = reached(t.register(unique("bot"), STRONG_PW))
        if throttled(first, cfg):
            return True
        if not first.ok:
            raise Inconclusive(f"a plain sign-up was refused (HTTP {first.status}) — sign-up may "
                               f"need a CAPTCHA/invite, so a burst can't be tested this way")
        for _ in range(n - 1):
            if throttled(reached(t.register(unique("bot"), STRONG_PW)), cfg):
                return True
        raise Leak(f"{n} accounts were created back-to-back from one client; none was throttled")
    add("BOT5", "burst of sign-ups is throttled (OAT-019 account creation / spam accounts)",
        signup_burst, EXHAUSTS)

    def reset_token_guessing(t):
        n = L["burst"]
        if not refused(t.reset_confirm(secrets.token_urlsafe(24), STRONG_PW),
                       "a made-up reset token"):
            raise Leak("a random string was accepted as a password-reset token")
        for _ in range(n - 1):
            r = reached(t.reset_confirm(secrets.token_urlsafe(24), STRONG_PW))
            if throttled(r, cfg):
                return True
            if r.ok:
                raise Leak("a random string was accepted as a password-reset token")
        raise Leak(f"{n} wrong reset tokens in a row from one client; none was throttled")
    add("BOT6", "reset-token guessing is throttled (OAT-002 token cracking)",
        reset_token_guessing, EXHAUSTS)

    return A
