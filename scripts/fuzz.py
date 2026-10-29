#!/usr/bin/env python3
"""
fuzz.py — a FAST, wide-net input fuzzer for auth / registration / route fields.

Where the access_control suite proves specific attacks are blocked (pass/fail),
this casts a wide net: it throws a big corpus of hostile inputs — SQLi, XSS,
HTML-entity / output-encoding cases, path traversal, command & template
injection, NoSQL, CRLF, and a deliberately brutal pile of VALIDATION / boundary
inputs (oversize, null bytes, unicode tricks, wrong types, control chars) — at
every field it can reach, hundreds of requests in seconds (no browser), and
inspects each RESPONSE for tell-tale signals:

  * payload reflected VERBATIM in the body        -> XSS / output-encoding risk
  * HTML entities double-encoded (&amp;#39;)       -> over/mis-encoding bug
  * SQL error strings / stack traces leaked        -> injection reached a parser
  * login returned a token on a WRONG password     -> auth bypass
  * HTTP 5xx                                        -> unhandled input (validation gap)
  * abnormal latency on time-based SQLi            -> blind injection

IMPORTANT — these are SIGNALS FOR A HUMAN TO REVIEW, not proven vulnerabilities.
A reflected payload in a JSON error echo is usually harmless; the same string
unescaped in an HTML page is not. The tool tells you WHERE to look, fast.

IMPORTANT — this is destructive-ish: fuzzing the registration endpoint creates
junk accounts, and some payloads are large. Point it ONLY at a DISPOSABLE test
instance.

Usage:
    SENTINEL_CONFIG=config/target.videosanity.yaml python scripts/fuzz.py
    python scripts/fuzz.py --config config/target.videosanity.yaml --targets login,register
    python scripts/fuzz.py --config ... --json report.json --limit 40
    python scripts/fuzz.py --config ... --dry-run     # show the plan, send nothing
"""
from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
import urllib.parse

# make `sentinel` importable whether run as `python scripts/fuzz.py` or `-m`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from sentinel import config as cfgmod
from sentinel.config import dotget


# ─────────────────────────────────────────────────────────────────────────────
#  PAYLOAD CORPUS
#  Each payload: id, category, value, and optional flags:
#    json_value  -> send this Python object as the field value (type confusion)
#    time_based  -> expect a latency spike if the injection lands
# ─────────────────────────────────────────────────────────────────────────────
def build_corpus() -> list[dict]:
    P: list[dict] = []

    def add(cat, value, pid=None, **flags):
        P.append({"id": pid or f"{cat}{len([x for x in P if x['category']==cat])+1}",
                  "category": cat, "value": value, **flags})

    # ---- SQL injection ----
    for v in ["' OR '1'='1' --", "' OR 1=1--", "admin'--", "admin' #",
              "' UNION SELECT NULL,NULL,NULL--", "\" OR \"\"=\"",
              "') OR ('1'='1", "'; DROP TABLE users;--", "1 OR 1=1",
              "' OR 'x'='x", "\\'", "'||'", "'=='"]:
        add("sqli", v)
    add("sqli", "' OR SLEEP(5)--", pid="sqli-time1", time_based=True)
    add("sqli", "'; WAITFOR DELAY '0:0:5'--", pid="sqli-time2", time_based=True)
    add("sqli", "' OR pg_sleep(5)--", pid="sqli-time3", time_based=True)

    # ---- XSS / HTML-injection vectors ----
    for v in ["<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
              "\"><script>alert(1)</script>", "<svg onload=alert(1)>",
              "javascript:alert(1)", "'\"><svg/onload=confirm(1)>",
              "<body onload=alert(1)>", "</title><script>alert(1)</script>",
              "{{constructor.constructor('alert(1)')()}}"]:
        add("xss", v)

    # ---- HTML-entity / output-encoding cases (the Ana's fade & cut! family) ----
    add("encoding", "Ana's fade & cut! weekend!", pid="enc-raw")
    add("encoding", "Ana&#39;s fade &amp; cut! weekend!", pid="enc-preencoded")
    add("encoding", "Ana&amp;#39;s fade &amp;amp; cut!", pid="enc-doubled")
    add("encoding", "<>&\"'`", pid="enc-metachars")
    add("encoding", "&#60;&#62;&#38;&#34;&#39;", pid="enc-numeric")
    add("encoding", "café résumé naïve — “smart” ‘quotes’ …", pid="enc-unicode-punct")
    add("encoding", "100% & <free> \"today\"", pid="enc-mixed")

    # ---- path traversal / LFI ----
    for v in ["../../../../etc/passwd", "..%2f..%2f..%2fetc%2fpasswd",
              "....//....//etc/passwd", "/etc/passwd%00.png",
              "..\\..\\..\\windows\\win.ini", "file:///etc/passwd"]:
        add("traversal", v)

    # ---- command injection ----
    for v in ["; id", "| whoami", "`id`", "$(id)", "& dir", "\n/bin/sh", "; sleep 5"]:
        add("cmdi", v)

    # ---- template / expression injection (SSTI) ----
    for v in ["${7*7}", "{{7*7}}", "#{7*7}", "<%= 7*7 %>", "${{7*7}}", "@(7*7)"]:
        add("ssti", v)

    # ---- NoSQL / LDAP / header injection ----
    add("nosql", {"$gt": ""}, pid="nosql-gt", json_value=True)
    add("nosql", {"$ne": None}, pid="nosql-ne", json_value=True)
    add("nosql", "' || '1'=='1", pid="nosql-js")
    add("ldap", "*)(uid=*))(|(uid=*", pid="ldap1")
    add("crlf", "x\r\nSet-Cookie: pwn=1", pid="crlf-setcookie")
    add("crlf", "x\r\nX-Injected: 1", pid="crlf-header")

    # ---- VALIDATION / boundary — the "roughest" pile ----
    add("validation", "", pid="val-empty")
    add("validation", "   ", pid="val-whitespace")
    add("validation", "A" * 100000, pid="val-oversize-100k")
    add("validation", "A" * 10_000_000, pid="val-oversize-10m")   # DoS-ish; drop with --no-huge
    add("validation", "a\x00b", pid="val-nullbyte")
    add("validation", "line1\r\nline2\tcol", pid="val-controlchars")
    add("validation", "%s%s%s%n%x", pid="val-formatstring")
    add("validation", "-1", pid="val-negative")
    add("validation", "99999999999999999999999999", pid="val-bignum")
    add("validation", "0x1F600", pid="val-hex")
    add("validation", "NaN", pid="val-nan")
    add("validation", "null", pid="val-null-literal")
    add("validation", "undefined", pid="val-undefined")
    add("validation", "true", pid="val-bool-literal")
    add("validation", "  surrounded  ", pid="val-trim")
    add("validation", "ＡＤＭＩＮ", pid="val-fullwidth")          # homoglyph admin
    add("validation", "a‮b‭c", pid="val-bidi")          # RTL/LTR override
    add("validation", "👨‍👩‍👧‍👦🏴‍☠️", pid="val-emoji-zwj")        # grapheme clusters
    add("validation", "𝕒𝕕𝕞𝕚𝕟", pid="val-mathalnum")             # 4-byte UTF-8
    add("validation", "é́́́", pid="val-combining")  # combining overflow
    add("validation", "a" * 64 + "@" + "b" * 255 + ".com", pid="val-long-email")
    add("validation", "not-an-email", pid="val-bad-email")
    add("validation", "a@b@c.com", pid="val-double-at")
    add("validation", "SELECT", pid="val-keyword")
    add("validation", "{\"nested\":{\"a\":1}}", pid="val-json-string")
    # type confusion — send a non-string where a string is expected
    add("validation", ["a", "b"], pid="val-type-array", json_value=True)
    add("validation", {"k": "v"}, pid="val-type-object", json_value=True)
    add("validation", 123456, pid="val-type-int", json_value=True)
    add("validation", True, pid="val-type-bool", json_value=True)
    add("validation", None, pid="val-type-null", json_value=True)

    return P


# ─────────────────────────────────────────────────────────────────────────────
#  RESPONSE SIGNAL DETECTION
# ─────────────────────────────────────────────────────────────────────────────
SQL_ERRORS = re.compile(
    r"SQL syntax|SQLITE_ERROR|sqlite3\.|psycopg2|PG::|ORA-\d{3,}|ODBC|"
    r"mysql_fetch|MySqlException|SQLSTATE|unclosed quotation|"
    r"quoted string not properly terminated|PDOException|SQLException|"
    r"near \".*\": syntax error|column .* does not exist|"
    r"you have an error in your sql", re.I)

STACK_TRACES = re.compile(
    r"Traceback \(most recent call last\)|at [\w.$]+\([\w.]+\.java:\d+\)|"
    r'File "[^"]*", line \d+|\.rb:\d+:in |goroutine \d+ |'
    r"System\.\w+Exception|org\.springframework|werkzeug|"
    r"<b>(Warning|Fatal error|Notice)</b>|panic:|NullPointerException", re.I)


def classify_reflection(sent: str, body: str):
    """Return how the payload came back: raw / escaped / double-encoded / decoded / None."""
    if not isinstance(sent, str) or not sent or len(sent) > 4096:
        return None  # skip giant/non-string payloads for reflection scan
    if sent in body:
        return "raw"
    esc = html.escape(sent, quote=True)
    if esc != sent and esc in body:
        return "escaped"
    if html.escape(esc, quote=True) in body:
        return "double-encoded"
    dec = html.unescape(sent)
    if dec != sent and dec in body:
        return "decoded"
    return None


def analyze(sent, resp_status, body_text, content_type, elapsed, baseline, flags):
    """Return a list of signal strings for one response."""
    sigs = []
    if resp_status == 0:
        return ["transport-error: " + body_text[:80]]
    if resp_status >= 500:
        sigs.append(f"HTTP {resp_status} (server error — input not handled)")
    if SQL_ERRORS.search(body_text):
        sigs.append("SQL-ERROR string leaked in body")
    if STACK_TRACES.search(body_text):
        sigs.append("stack-trace / exception leaked in body")
    refl = classify_reflection(sent, body_text)
    if refl == "raw":
        htmlish = "html" in content_type.lower() or "<" in sent
        sigs.append("payload REFLECTED RAW" + (" in HTML response (XSS risk)" if htmlish else ""))
    elif refl == "double-encoded":
        sigs.append("payload DOUBLE-ENCODED in body (encoding bug)")
    elif refl == "decoded":
        sigs.append("HTML entities DECODED by server (may re-introduce markup)")
    if flags.get("time_based") and baseline is not None and elapsed > baseline + 4.0:
        sigs.append(f"LATENCY spike {elapsed:.1f}s (blind/time-based injection?)")
    return sigs


# ─────────────────────────────────────────────────────────────────────────────
#  REQUEST PLUMBING
# ─────────────────────────────────────────────────────────────────────────────
class Fuzzer:
    def __init__(self, cfg, session, timeout):
        self.cfg = cfg
        self.s = session
        self.timeout = timeout
        self.baseline = None

    def _spec(self, name):
        method, path = self.cfg.endpoints[name].split(" ", 1)
        return method.upper(), path

    def _send(self, method, path, *, json_body=None, raw_path=False):
        url = f"{self.cfg.base_url}{path}"
        t0 = time.monotonic()
        try:
            r = self.s.request(method, url, json=json_body, timeout=self.timeout,
                               allow_redirects=False)
            elapsed = time.monotonic() - t0
            ctype = r.headers.get("content-type", "")
            return r.status_code, r.text, ctype, elapsed
        except Exception as e:
            return 0, f"{type(e).__name__}: {e}", "", time.monotonic() - t0

    def measure_baseline(self):
        """A couple of benign requests to learn normal latency (for time-based)."""
        m, p = self._spec("login")
        f = self.cfg.fields
        payload = {f["username"]: "baseline-user", f["password"]: "baseline-pw"}
        times = []
        for _ in range(3):
            _, _, _, el = self._send(m, p, json_body=payload)
            times.append(el)
        self.baseline = min(times) if times else None
        return self.baseline


# ─────────────────────────────────────────────────────────────────────────────
#  TASK BUILDERS — what gets fuzzed
# ─────────────────────────────────────────────────────────────────────────────
def login_tasks(cfg, payload):
    """Fuzz each login field; use a WRONG password so a 2xx/token = auth bypass."""
    f = cfg.fields
    base = {f["username"]: "nonexistent-user", f["password"]: "wrong-password-xyz"}
    if "otp" in f:
        base[f["otp"]] = "000000"
    tasks = []
    for field in [k for k in ("username", "password", "otp") if k in f]:
        body = dict(base)
        body[f[field]] = payload["value"]
        tasks.append(("login", field, body, False))
    return tasks


def register_tasks(cfg, payload):
    f = cfg.fields
    base = {f["username"]: f"fuzz_{int(time.time()*1000)%100000}",
            f["password"]: "Fuzz-Passw0rd!", f.get("email", "email"): "fuzz@example.test"}
    tasks = []
    for field in [k for k in ("username", "password", "email") if k in f]:
        body = dict(base)
        body[f[field]] = payload["value"]
        tasks.append(("register", field, body, False))
    # privilege / mass-assignment style extras
    tasks.append(("register", "role", dict(base, role=payload["value"]), False))
    return tasks


def route_tasks(cfg, payload):
    """Inject into path params and the buggy query param."""
    if not isinstance(payload["value"], str):
        return []  # structural payloads make no sense in a URL
    enc = urllib.parse.quote(payload["value"], safe="")
    tasks = []
    simple = {
        "resource": ("owner_id", False),
        "object": ("id", False),
        "media": ("path", True),     # keep traversal slashes
    }
    for name, (param, keep_slashes) in simple.items():
        if name not in cfg.endpoints:
            continue
        method, path = cfg.endpoints[name].split(" ", 1)
        val = payload["value"] if keep_slashes else enc
        # substitute the chosen param; fill any other params with a benign 1
        filled = path
        for m in re.findall(r"\{(\w+)\}", path):
            filled = filled.replace("{" + m + "}", val if m == param else "1")
        tasks.append((name, f"path:{param}", ("GET", filled), True))
    if "buggy" in cfg.endpoints:
        method, path = cfg.endpoints["buggy"].split(" ", 1)
        tasks.append(("buggy", "query:value", (method.upper(), f"{path}?value={enc}"), True))
    return tasks


# ─────────────────────────────────────────────────────────────────────────────
#  MAIN
# ─────────────────────────────────────────────────────────────────────────────
def main(argv=None):
    ap = argparse.ArgumentParser(description="fast wide-net input fuzzer")
    ap.add_argument("--config", help="YAML config (else $SENTINEL_CONFIG / defaults)")
    ap.add_argument("--targets", default="login,register,routes",
                    help="comma list: login, register, routes")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--limit", type=int, help="use only the first N payloads (quick run)")
    ap.add_argument("--no-huge", action="store_true",
                    help="drop the 10MB oversize payload (recommended for slow links)")
    ap.add_argument("--delay", type=float, default=0.0, help="seconds between requests")
    ap.add_argument("--json", help="write a JSON report here")
    ap.add_argument("--dry-run", action="store_true", help="print the plan and send nothing")
    args = ap.parse_args(argv)

    cfg = cfgmod.load(args.config)
    targets = [t.strip() for t in args.targets.split(",") if t.strip()]
    corpus = build_corpus()
    if args.no_huge:
        corpus = [p for p in corpus if p["id"] != "val-oversize-10m"]
    if args.limit:
        corpus = corpus[:args.limit]

    builders = {"login": login_tasks, "register": register_tasks, "routes": route_tasks}

    # build the full plan so we can show counts up front
    plan = []  # (target, field, payload, kind, request)
    for payload in corpus:
        for tgt in targets:
            b = builders.get(tgt)
            if not b:
                continue
            for item in b(cfg, payload):
                plan.append((tgt, payload, item))

    print(f"target     : {cfg.base_url}")
    print(f"corpus     : {len(corpus)} payloads across "
          f"{len(set(p['category'] for p in corpus))} categories")
    print(f"targets    : {', '.join(targets)}")
    print(f"total reqs : {len(plan)}")
    if args.dry_run:
        cats = {}
        for p in corpus:
            cats[p["category"]] = cats.get(p["category"], 0) + 1
        print("\npayloads by category:")
        for c, n in sorted(cats.items()):
            print(f"   {c:12} {n}")
        print("\n(dry run — nothing sent)")
        return 0

    print("WARNING: this mutates state (creates junk accounts). Disposable instance only.\n")

    s = requests.Session()
    s.verify = cfg.verify_tls
    fz = Fuzzer(cfg, s, args.timeout)
    if any(p.get("time_based") for p in corpus):
        fz.measure_baseline()

    findings = []
    sent_count = 0
    for tgt, payload, item in plan:
        # item is (name, field, request, raw_path) where request is body-dict or (method,path)
        name, field, req, is_route = item
        if is_route:
            method, path = req
            status, body, ctype, elapsed = fz._send(method, path, raw_path=True)
        else:
            m, p = fz._spec(name)
            body_dict = req
            status, body, ctype, elapsed = fz._send(m, p, json_body=body_dict)
        sent_count += 1

        # auth-bypass: a login/register field payload that yields a token on bad creds
        extra = []
        if name == "login" and 200 <= status < 300:
            try:
                jb = json.loads(body)
                if isinstance(jb, dict) and (dotget(jb, cfg.token_json_path) or jb.get("access_token")):
                    extra.append("AUTH BYPASS: token returned on wrong password")
            except Exception:
                pass

        sigs = analyze(payload["value"], status, body, ctype, elapsed, fz.baseline, payload) + extra
        if sigs:
            findings.append({
                "target": name, "field": field, "payload_id": payload["id"],
                "category": payload["category"],
                "payload": (payload["value"] if isinstance(payload["value"], str)
                            else json.dumps(payload["value"]))[:120],
                "status": status, "elapsed_s": round(elapsed, 2), "signals": sigs,
            })
        if args.delay:
            time.sleep(args.delay)

    # ---- report ----
    print(f"sent {sent_count} requests; {len(findings)} with signals worth a look:\n")
    by_target = {}
    for fdg in findings:
        by_target.setdefault(fdg["target"], []).append(fdg)
    for tgt in sorted(by_target):
        print(f"[{tgt}]")
        for fdg in by_target[tgt]:
            print(f"   {fdg['payload_id']:20} {fdg['field']:14} HTTP {fdg['status']:<4} "
                  f"{fdg['category']:11} {fdg['payload'][:46]!r}")
            for sig in fdg["signals"]:
                print(f"       → {sig}")
        print()

    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"target": cfg.base_url, "requests": sent_count,
                       "findings": findings}, fh, indent=2)
        print(f"JSON report written to {args.json}")

    print("\nNOTE: signals are leads for a human to verify, not confirmed vulns.")
    # non-zero if we saw a hard signal (auth bypass / 5xx / sql error / stack trace)
    hard = any(any(k in s for s in f["signals"]
                   for k in ("AUTH BYPASS", "server error", "SQL-ERROR", "stack-trace"))
               for f in findings)
    return 1 if hard else 0


if __name__ == "__main__":
    sys.exit(main())
