#!/usr/bin/env python3
"""
campaign.py — a timed security campaign that "keeps trying" for a set duration
and then writes a Markdown report of strong vs. weak points, so you can fix
things before the next run.

It loops for --minutes, each pass running every suite (access_control,
media_injection, oct2026, nov2026, automation, resilience, surface) plus — against a live
HTTP target — a shuffled pass of the input fuzzer (scripts/fuzz.py). Across
passes a check is recorded as:

    LEAK          if it leaked in ANY pass
    BLOCKED       if it was proven blocked at least once and never leaked
    INCONCLUSIVE  if no pass could prove it either way
    SKIPPED       if it never ran

At the end it writes:

  reports/appsec-report-<timestamp>.md     human-readable report
  reports/appsec-report-<timestamp>.json   machine sidecar (used to diff next run)

The report has: score and executive summary, WEAK points (each with its fix),
checks that could not be proven and why, STRONG points, coverage gaps, fuzzer
signals to review, and a DIFF against the previous report.

Defensive use only, against a DISPOSABLE instance you own (it mutates state and
creates junk accounts). The scope guard in sentinel/safety.py applies.

Without `hooks.reset`, state from one pass (locked accounts, a throttled client
address) carries into the next: later passes will mostly be inconclusive. Either
expose a reset hook in the backend's test profile or give the limits time to
expire with --cooldown.

Usage:
    python scripts/campaign.py --target reference-vulnerable --minutes 0.2   # demo
    SENTINEL_CONFIG=config/target.videosanity.yaml \
        python scripts/campaign.py --target http --minutes 10 --cooldown 60

Exit code: 1 if anything leaked, 2 if nothing leaked but some checks were never
proven, 0 otherwise.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import glob
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # repo root
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))                   # scripts/ (for fuzz)

from sentinel import config as cfgmod
from sentinel import engine
from sentinel.safety import ScopeError
from sentinel.suites import BUILDERS
from sentinel.suites.common import Status, run_catalogue
from sentinel.suites.remediation import fix_for
import fuzz

HARD = ("AUTH BYPASS", "server error", "SQL-ERROR", "stack-trace")
THREAT_DOC = "docs/THREATS-2026-Q4.md"


def aggregate(counts: dict) -> str:
    """One status for a check across all passes (see module docstring)."""
    for s in (Status.LEAK, Status.ERROR, Status.BLOCKED, Status.INCONCLUSIVE):
        if counts.get(s.value):
            return s.value
    return Status.SKIPPED.value


def run_campaign(args):
    try:
        cfg = cfgmod.load(args.config)
        suites = [s for s in (args.suite or list(BUILDERS)) if s in BUILDERS]
        factory, attacks, notes = engine.prepare(args.target, cfg, suites)
    except (cfgmod.ConfigError, ScopeError) as e:
        print(e, file=sys.stderr)
        return 2
    for w in cfg.warnings + notes:
        print(f"note: {w}")

    do_fuzz = (not args.no_fuzz) and args.target == "http"
    corpus = [p for p in fuzz.build_corpus() if args.huge or p["id"] != fuzz.HUGE_ID]

    target = engine.target_label(args.target, cfg)
    print(f"campaign on {target} for {args.minutes} min "
          f"(suites: {', '.join(suites)}; fuzz: {do_fuzz})")

    checks = {}          # id -> {suite, category, desc, counts, detail}
    fuzz_hits = {}       # (target, field, payload_id) -> finding
    passes = 0
    deadline = time.monotonic() + args.minutes * 60

    while True:
        passes += 1
        for f in run_catalogue(factory, attacks):
            rec = checks.setdefault(f.id, {"suite": f.suite, "category": f.category,
                                           "desc": f.desc, "counts": {}, "detail": {}})
            rec["counts"][f.status.value] = rec["counts"].get(f.status.value, 0) + 1
            if f.detail:
                rec["detail"][f.status.value] = f.detail
        if do_fuzz:
            random.shuffle(corpus)
            plan = fuzz.build_plan(cfg, ["login", "register", "routes"], corpus[:args.fuzz_limit])
            found, _ = fuzz.sweep(cfg, plan, timeout=args.timeout)
            for fd in found:
                fuzz_hits[(fd["target"], fd["field"], fd["payload_id"])] = fd
        for rec in checks.values():
            rec["worst"] = aggregate(rec["counts"])
        tally = {}
        for rec in checks.values():
            tally[rec["worst"]] = tally.get(rec["worst"], 0) + 1
        print(f"  pass {passes}: " + ", ".join(f"{k.lower()}={v}" for k, v in sorted(tally.items()))
              + f", fuzz signals={len(fuzz_hits)}")
        if time.monotonic() + args.cooldown >= deadline:
            break
        if args.cooldown:
            time.sleep(args.cooldown)

    report_md, sidecar = build_report(target, suites, passes, args.minutes, checks, fuzz_hits,
                                      args.out_dir)
    os.makedirs(args.out_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(args.out_dir, f"appsec-report-{stamp}")
    with open(base + ".md", "w") as fh:
        fh.write(report_md)
    with open(base + ".json", "w") as fh:
        json.dump(sidecar, fh, indent=2)
    print(f"\nscore  : {sidecar['score']}/100\nreport : {base}.md\nsidecar: {base}.json")
    s = sidecar["summary"]
    if args.target == "reference-vulnerable":
        return 0 if s["leak"] and not (s["blocked"] or s["inconclusive"] or s["error"]) else 1
    return 1 if s["leak"] or s["error"] else 2 if s["inconclusive"] else 0


def _prev_sidecar(out_dir):
    files = sorted(glob.glob(os.path.join(out_dir, "appsec-report-*.json")))
    if not files:
        return None
    try:
        with open(files[-1]) as fh:
            return json.load(fh)
    except Exception:
        return None


def build_report(target, suites, passes, minutes, checks, fuzz_hits, out_dir):
    now = _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ids = lambda status: sorted(i for i, r in checks.items() if r["worst"] == status.value)
    strong, leaks, errors = ids(Status.BLOCKED), ids(Status.LEAK), ids(Status.ERROR)
    unproven, skipped = ids(Status.INCONCLUSIVE), ids(Status.SKIPPED)
    ran = len(checks) - len(skipped)
    score = round(100 * len(strong) / ran) if ran else 0
    if len(strong) < ran and score == 100:
        score = 99
    # proven at least once, but not in every pass: state bled between passes
    flaky = sorted(i for i in strong if checks[i]["counts"].get(Status.INCONCLUSIVE.value))

    fuzz_hard = [f for f in fuzz_hits.values() if any(k in s for s in f["signals"] for k in HARD)]
    fuzz_soft = [f for f in fuzz_hits.values() if f not in fuzz_hard]

    prev = _prev_sidecar(out_dir)
    diff = []
    if prev:
        prev_leaks, cur_leaks = set(prev.get("leak_ids", [])), set(leaks)
        resolved, newly = sorted(prev_leaks - cur_leaks), sorted(cur_leaks - prev_leaks)
        diff.append(f"Compared with the previous report ({prev.get('timestamp', '?')}, "
                    f"target `{prev.get('target', '?')}`):")
        diff.append(f"- Fixed since then: {', '.join(resolved) if resolved else 'none'}")
        diff.append(f"- New leaks since then: {', '.join(newly) if newly else 'none'}")
        diff.append(f"- Leaks: {len(prev_leaks)} → {len(cur_leaks)}")
        if "score" in prev:
            diff.append(f"- Score: {prev['score']} → {score}")
    else:
        diff.append("No previous report found — this is the baseline for future diffs.")

    L = ["# AppSec campaign report", "",
         f"- **Target:** `{target}`", f"- **When:** {now}",
         f"- **Duration:** {minutes} min, {passes} pass(es)",
         f"- **Suites:** {', '.join(suites)}",
         f"- **Score:** {score}/100 — share of the checks that ran which were *proven* blocked", "",
         "> Defensive, authorized testing against a disposable instance. "
         "Fuzzer signals are **leads for human review, not confirmed vulnerabilities**.", "",
         "## Executive summary", "", "| Outcome | Count |", "|---|---|",
         f"| ✅ Strong (proven blocked) | {len(strong)} |",
         f"| ❌ Weak (leaked) | {len(leaks)} |",
         f"| ? Not proven either way | {len(unproven)} |",
         f"| ! Check crashed | {len(errors)} |",
         f"| – Coverage gaps (skipped) | {len(skipped)} |",
         f"| 🔎 Fuzzer hard signals | {len(fuzz_hard)} |",
         f"| 🔎 Fuzzer other signals | {len(fuzz_soft)} |", ""]

    L += ["## ❌ Weak points — fix these first", ""]
    if not leaks and not errors and not fuzz_hard:
        L.append("None detected in this run. (Read the next two sections before celebrating: "
                 "an unproven or skipped check is not a pass.)")
    else:
        for i in leaks:
            r = checks[i]
            L.append(f"- **{i}** ({r['suite']} / {r['category']}) — {r['desc']}")
            if r["detail"].get("LEAK"):
                L.append(f"  - Seen: {r['detail']['LEAK']}")
            L.append(f"  - Fix: {fix_for(i, r['category'])}")
        for i in errors:
            L.append(f"- **{i}** — the check itself crashed: `{checks[i]['detail'].get('ERROR', '')}` "
                     f"(a harness or config problem; investigate).")
        for f in fuzz_hard:
            L.append(f"- **FUZZ {f['payload_id']}** on `{f['target']}.{f['field']}` "
                     f"(HTTP {f['status']}): {'; '.join(f['signals'])} — payload `{f['payload']}`")
    L.append("")

    L += ["## ? Not proven — the harness could not tell", ""]
    if unproven:
        L.append("These ran but proved nothing (a control request failed, the backend didn't "
                 "answer, …). They are **not** passes. The reason says what to fix in the config:")
        for i in unproven:
            L.append(f"- **{i}** — {checks[i]['desc']}  \n  _{checks[i]['detail'].get('INCONCLUSIVE', '')}_")
    else:
        L.append("None — every check that ran reached a verdict.")
    L.append("")
    if flaky:
        L += [f"**State bled between passes.** {len(flaky)} check(s) were proven in at least one "
              f"pass but inconclusive in others ({', '.join(flaky[:20])}"
              f"{'…' if len(flaky) > 20 else ''}). Locked accounts or a throttled client from an "
              f"earlier pass got in the way: expose `hooks.reset` in the backend's test profile, "
              f"or run with `--cooldown` longer than its lockout window.", ""]

    L += ["## ✅ Strong points — controls that held", ""]
    if strong:
        by_suite = {}
        for i in strong:
            by_suite.setdefault(checks[i]["suite"], []).append(i)
        for s in suites:
            if by_suite.get(s):
                L.append(f"- **{s}**: {', '.join(sorted(by_suite[s]))}")
    else:
        L.append("No check was proven blocked — likely a connectivity/config problem "
                 "(run `scripts/preflight.py`).")
    L.append("")

    L += ["## – Coverage gaps (skipped)", ""]
    if skipped:
        L.append("These did not run — a capability or feature isn't configured. Closing them widens coverage:")
        for i in skipped:
            L.append(f"- **{i}** — {checks[i]['desc']}  _({checks[i]['detail'].get('SKIPPED', '')})_")
    else:
        L.append("None — every check ran.")
    L.append("")

    if fuzz_soft:
        L += ["## 🔎 Fuzzer signals to review (reflection / encoding / hidden-instruction text)", ""]
        for f in sorted(fuzz_soft, key=lambda x: (x["target"], x["field"]))[:60]:
            L.append(f"- `{f['target']}.{f['field']}` {f['payload_id']} "
                     f"(HTTP {f['status']}): {'; '.join(f['signals'])}")
        L.append("")

    L += ["## Change since last run", ""] + diff + [""]

    L += ["## What to do next", "",
          "1. Fix the weak points above, highest blast radius first: anything under `authz`, "
          "`jwt`, `session`, `takeover` exposes other users' data directly.",
          "2. Turn every *not proven* line into a verdict — each one names the config key or "
          "hook that is missing.",
          "3. Re-run; the diff section tracks progress toward a clean, fully-proven run.", "",
          "## Threat mapping", "",
          f"Which October/November 2026 incident each check comes from, with sources and what "
          f"could not be verified: `{THREAT_DOC}`.", ""]

    sidecar = {
        "timestamp": now, "target": target, "minutes": minutes, "passes": passes, "score": score,
        "summary": {"blocked": len(strong), "leak": len(leaks), "inconclusive": len(unproven),
                    "error": len(errors), "skipped": len(skipped)},
        "leak_ids": leaks,
        "checks": {i: r["worst"] for i, r in checks.items()},
        "fuzz_hard": len(fuzz_hard), "fuzz_soft": len(fuzz_soft),
    }
    return "\n".join(L), sidecar


def main(argv=None):
    ap = argparse.ArgumentParser(description="timed security campaign + markdown report")
    ap.add_argument("--target", default="http", choices=list(engine.TARGETS))
    ap.add_argument("--config", help="YAML config (else $SENTINEL_CONFIG / defaults)")
    ap.add_argument("--minutes", type=float, default=10.0, help="how long to keep trying")
    ap.add_argument("--cooldown", type=float, default=0.0,
                    help="seconds to wait between passes (let lockouts/rate limits expire)")
    ap.add_argument("--suite", nargs="*", help="suites to run (default: all)")
    ap.add_argument("--no-fuzz", action="store_true", help="suites only, skip the fuzzer")
    ap.add_argument("--huge", action="store_true", help="include the 10 MB fuzz payload")
    ap.add_argument("--no-huge", action="store_true", help=argparse.SUPPRESS)   # old flag, now the default
    ap.add_argument("--fuzz-limit", type=int, default=30, help="fuzz payloads per pass")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--out-dir", default="reports", help="where to write the report")
    args = ap.parse_args(argv)
    sys.exit(run_campaign(args))


if __name__ == "__main__":
    main()
