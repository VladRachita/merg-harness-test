"""Suite primitives: an Attack, a Finding, a capability-aware runner, and the
helpers that keep a verdict honest.

The rule every check follows:

    BLOCKED       proven — a legitimate request worked AND the attack was refused
    LEAK          the attack was accepted
    INCONCLUSIVE  nothing was proven (backend silent, control failed, 5xx, …)
    SKIPPED       a capability isn't configured, or the control doesn't apply
    ERROR         the check itself crashed

"The server said no" is not enough to claim BLOCKED: a wrong route (404), a
locked-out test account (429) or a dead container (connection refused) all say
no. So checks first run a positive CONTROL with `expect_ok(...)` / `need_token`
and only then judge the attack with `denied(...)`.
"""
from __future__ import annotations

import re
import secrets
from dataclasses import dataclass, field
from enum import Enum

from ..adapters.base import Inconclusive, NotApplicable, Unreachable  # noqa: F401  (re-exported)


class Status(str, Enum):
    BLOCKED = "BLOCKED"            # the attack was correctly denied (good)
    LEAK = "LEAK"                  # the attack got through (bad)
    SKIPPED = "SKIPPED"            # capability not configured / control not applicable
    INCONCLUSIVE = "INCONCLUSIVE"  # could not be proven either way — NOT a pass
    ERROR = "ERROR"                # the check itself crashed


class Leak(Exception):
    """Raised by a check to report a LEAK with a specific explanation (a check
    may equally just return False)."""


# Run order. Without a reset hook, state bleeds between attacks on a live
# backend, so each check is placed after everything it could poison.
PROBE = 0       # read-only / self-contained
MUTATES = 10    # changes account state (password, email, sessions)
EXHAUSTS = 20   # uses up a per-user quota (uploads, sign-ups, token guesses)
OTP_LOCK = 25   # burns second-factor attempts (the account can still sign in)
LOCKS = 30      # locks an account out
FLOODS = 40     # trips the per-client limit: every later login from here is throttled
STRESS = 50     # pathological input and the load burst (needs no login)


@dataclass
class Attack:
    id: str
    category: str
    desc: str
    check: object                     # (target) -> bool ; True == safe/blocked
    requires: set = field(default_factory=set)
    stage: int = PROBE
    suite: str = ""                   # filled in by collect()
    flow: str = ""                    # the product flow it attacks (suites/flows.py)


@dataclass
class Finding:
    id: str
    category: str
    desc: str
    status: Status
    detail: str = ""
    suite: str = ""
    flow: str = ""


# ---------------------------------------------------------------------------
#  verdict helpers
# ---------------------------------------------------------------------------
def reached(resp, what="request"):
    """The backend answered. (Transport failures normally raise Unreachable in
    the adapter already; this also covers adapters that return status 0.)"""
    if resp.status == 0:
        raise Unreachable(f"{what}: no response from the backend "
                          f"({resp.body.get('error', 'transport error')})")
    return resp


def expect_ok(resp, what):
    """Positive control: a LEGITIMATE request must succeed, otherwise a later
    refusal proves nothing (wrong route? bad credentials? locked out?)."""
    reached(resp, what)
    if not resp.ok:
        raise Inconclusive(f"control failed — {what} returned HTTP {resp.status}; "
                           f"the attack result would be meaningless")
    return resp


def denied(resp, what="attack request"):
    """True when the server cleanly refused; False when it accepted (a leak).
    A 5xx is neither: the attack wasn't refused, the server fell over."""
    reached(resp, what)
    if resp.ok:
        return False
    if resp.status >= 500 and resp.status not in (501, 505):
        raise Inconclusive(f"{what} returned HTTP {resp.status} — a server error, "
                           f"not a clean refusal (investigate)")
    return True


def need_token(t, user, **login_kw):
    """Log in as a seed user and return the access token, or stop the check:
    an attack sent with no token is refused for the wrong reason."""
    r = reached(t.login(user["username"], user["password"], **login_kw), "login")
    tok = r.body.get("access_token")
    if not tok:
        raise Inconclusive(
            f"could not log in as '{user['username']}' (HTTP {r.status}) — check the login "
            f"route, field names, credentials and token_json_path; or the account/IP is "
            f"locked out by an earlier check (configure hooks.reset)")
    return tok


def refused(resp, what="attack request"):
    """`denied`, for a route no legitimate request has proven to exist: a 404
    there more likely means "wrong path in the config" than "attack blocked"."""
    if reached(resp, what).status == 404:
        raise Inconclusive(f"{what} returned HTTP 404 — route missing or mis-mapped in the "
                           f"config? (a refusal would be 401/403/4xx)")
    return denied(resp, what)


def authed(t, user):
    """A token that is PROVEN to work: the user can read their own resource with
    it. Without this, a wrong `auth_header` makes every authenticated attack
    look "blocked" (the server just never saw a valid session)."""
    tok = need_token(t, user)
    expect_ok(t.get_resource(tok, user["id"]),
              f"'{user['username']}' reading their own resource with a fresh token")
    return tok


def throttled(resp, cfg) -> bool:
    return resp.status in cfg.throttle_statuses


STRONG_PW = "Sentinel-Pw-7!x"          # passes typical password policies

SQL_ERRORS = re.compile(
    r"SQL syntax|SQLITE_ERROR|sqlite3\.|psycopg2|PG::|ORA-\d{3,}|ODBC|mysql_fetch|MySqlException|"
    r"SQLSTATE|unclosed quotation|quoted string not properly terminated|PDOException|"
    r"SQLException|near \".*\": syntax error|syntax error at or near|"
    r"column .* does not exist|you have an error in your sql", re.I)
STACK_TRACE = re.compile(
    r"\"trace\"|'trace'|Traceback \(most recent call last\)|\bat [\w.$]+\([\w.]+\.java:\d+\)|"
    r"java\.lang\.\w+Exception|File \"[^\"]*\", line \d+|\.rb:\d+:in |goroutine \d+ |"
    r"System\.\w+Exception|org\.springframework\.|NullPointerException|panic:", re.I)
_TEST_ONLY = {"_link_for_test", "link", "reset_link", "token", "reset_token"}
_VOLATILE = {"timestamp", "time", "path", "instance", "requestid", "request_id", "traceid",
             "trace_id", "correlationid", "nonce"}


def stable(body: dict) -> dict:
    """A response body minus fields that legitimately differ between two calls
    (timestamps, request ids, test-profile echoes) — for uniformity checks."""
    return {k: v for k, v in (body or {}).items()
            if k not in _TEST_ONLY and k.lower() not in _VOLATILE}


def strings(obj):
    """Every string value nested anywhere in a parsed body."""
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for k, v in obj.items():
            yield str(k)
            yield from strings(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from strings(v)


def body_contains(body, needle: str) -> bool:
    return any(needle in s for s in strings(body))


def reset_token_from(resp):
    """Pull a reset token out of a reset_request response, however it's exposed."""
    b = resp.body
    for k in ("_link_for_test", "link", "reset_link"):
        if b.get(k):
            return str(b[k]).split("token=")[-1]
    return b.get("token") or b.get("reset_token")


def need_reset_token(t, user):
    r = expect_ok(t.reset_request(user["email"]), "password-reset request for a real account")
    tok = reset_token_from(r)
    if not tok:
        raise Inconclusive("the reset response carries no token/link — hooks.reset_introspect "
                           "is set but the backend's test profile doesn't echo it")
    return tok


def restore_password(t, user, *current):
    """Best effort: put a seed user's password back after a check changed it, so
    later checks (on a backend with no reset hook) can still sign in."""
    for pw in current:
        try:
            tok = t.login(user["username"], pw).body.get("access_token")
            if tok:
                t.change_password(tok, pw, user["password"], reauthed=True)
                return
        except Exception:
            pass


def unique(prefix="sentinel") -> str:
    """A name that can't collide with an earlier run's leftovers."""
    return f"{prefix}-{secrets.token_hex(4)}"


# ---------------------------------------------------------------------------
#  runner
# ---------------------------------------------------------------------------
def run_catalogue(factory, attacks: list[Attack], *, on_start=None, on_result=None,
                  should_stop=None) -> list[Finding]:
    """`factory` returns a Target. A FRESH target is used per attack so stateful
    effects (lockout counters, revoked tokens, disabled users) don't bleed between
    attacks. For a live HTTP backend the factory reuses one client, so attacks run
    in stage order (read-only → mutating → lockout) and each one re-proves its own
    preconditions. Findings come back in catalogue order.

    Optional hooks let a caller watch a run live (the web UI does):
      on_start(attack)     just before an attack runs
      on_result(finding)   as soon as its verdict is known
      should_stop()        polled between attacks; True ends the run early"""
    caps = set(factory().capabilities())
    results: dict[int, Finding] = {}
    for i in sorted(range(len(attacks)), key=lambda i: attacks[i].stage):
        atk = attacks[i]

        def done(status, detail=""):
            results[i] = Finding(atk.id, atk.category, atk.desc, status, detail, atk.suite,
                                 atk.flow)
            if on_result:
                on_result(results[i])

        if should_stop and should_stop():
            done(Status.SKIPPED, "run stopped before this check")
            continue
        missing = set(atk.requires) - caps
        if missing:
            done(Status.SKIPPED, "needs capability: " + ", ".join(sorted(m.value for m in missing)))
            continue
        if on_start:
            on_start(atk)
        try:
            t = factory()
            t.begin_attack(atk.id)
            t.reset()
            if bool(atk.check(t)):
                done(Status.BLOCKED)
            else:
                done(Status.LEAK, t.evidence())
        except Leak as e:
            done(Status.LEAK, str(e))
        except NotApplicable as e:
            done(Status.SKIPPED, f"not applicable: {e}")
        except Inconclusive as e:
            done(Status.INCONCLUSIVE, str(e))
        except Exception as e:
            done(Status.ERROR, repr(e))
    return [results[i] for i in range(len(attacks))]


def summarize(findings) -> dict:
    """Counts, score and verdict — one definition shared by the CLI, the JSON
    report, the campaign runner and the web UI.

      score     % of the checks that RAN which were proven blocked. A check that
                leaked, errored or stayed inconclusive counts against it, because
                none of those is evidence the control works.
      coverage  % of the catalogue that ran at all (the rest was skipped).
      verdict   FAIL        at least one leak or crashed check
                INCOMPLETE  no leak, but some checks proved nothing
                PASS        every check that ran was proven blocked
                EMPTY       nothing ran"""
    counts = {s.value: 0 for s in Status}
    for f in findings:
        counts[f.status.value] += 1
    total = len(findings)
    ran = total - counts["SKIPPED"]
    score = round(100 * counts["BLOCKED"] / ran) if ran else 0
    if counts["BLOCKED"] < ran and score == 100:
        score = 99                      # never round an imperfect run up to 100
    coverage = round(100 * ran / total) if total else 0
    if not ran:
        verdict = "EMPTY"
    elif counts["LEAK"] or counts["ERROR"]:
        verdict = "FAIL"
    elif counts["INCONCLUSIVE"]:
        verdict = "INCOMPLETE"
    else:
        verdict = "PASS"
    return {"counts": counts, "total": total, "ran": ran, "score": score,
            "coverage": coverage, "verdict": verdict}


def collect(builders: dict, suites: list, cfg, flows=None) -> list[Attack]:
    """All attacks of the named suites as ONE catalogue, so stage ordering holds
    across suites (a lockout test in one suite can't starve the next suite).
    `flows` (optional) keeps only the checks of those product flows."""
    from .flows import flow_of
    out: list[Attack] = []
    for s in suites:
        if s in builders:
            for a in builders[s](cfg):
                a.suite, a.flow = s, flow_of(a.id)
                if flows is None or a.flow in flows:
                    out.append(a)
    return out
