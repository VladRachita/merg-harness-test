#!/usr/bin/env python3
"""
campaign.py — a timed security campaign that "keeps trying" for a set duration
and then writes a Markdown report of strong vs. weak points, so you can fix
things before the next run.

It loops for --minutes, each pass running the configured suites (access_control,
media_injection, oct2026) plus — against a live HTTP target — a shuffled pass of
the input fuzzer (scripts/fuzz.py). Across passes it keeps the WORST outcome seen
per check (a check that ever leaks is recorded as a leak) and de-duplicates the
fuzzer's signals. At the end it writes:

  reports/appsec-report-<timestamp>.md     human-readable report
  reports/appsec-report-<timestamp>.json   machine sidecar (used to diff next run)

The report has: an executive summary, STRONG points (what held), WEAK points
(leaks + hard fuzzer signals, each mapped to its October-2026 technique and a
fix), COVERAGE GAPS (skipped checks + why), fuzzer signals to review, a DIFF vs.
the previous report, recommendations, and sources.

Defensive use only, against a DISPOSABLE instance (it mutates state / creates
junk accounts).

Usage:
    python scripts/campaign.py --target reference-vulnerable --minutes 1   # demo
    SENTINEL_CONFIG=config/target.videosanity.yaml \
        python scripts/campaign.py --target http --minutes 10
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
from sentinel.suites import BUILDERS
from sentinel.suites.common import run_catalogue, Status
import fuzz


# severity order for "worst outcome across passes"
SEV = {Status.BLOCKED.value: 0, Status.SKIPPED.value: 1,
       Status.ERROR.value: 2, Status.LEAK.value: 3}

# October-2026 technique + fix hint, keyed by check id
TECH = {
    "OCT1": ("OAuth state/token-type confusion — Better Auth CVE-2026-110862",
             "Namespace verification tokens; never accept an OAuth state value as a magic-link/reset token."),
    "OCT2": ("Falsely-verified account / email takeover — Better Auth",
             "Require fresh proof-of-control (verification/step-up) before an email change or OAuth account link takes effect."),
    "OCT3a": ("Reset-endpoint injection — Metabase CVE-2026-72898",
              "Parameterize all queries on the unauthenticated reset endpoint; return generic errors, never SQL/stack detail."),
    "OCT3b": ("Reset-token replay — Metabase",
              "Make reset tokens single-use and short-lived; invalidate on use and rotate sessions."),
    "OCT4": ("Unauthenticated privileged operation — BeyondTrust CVE-2026-102764",
             "Enforce authz on every privileged route server-side; reject missing/forged tokens before any work."),
    "OCT5": ("SSRF via media fetch — Plex CVE-2026-96652",
             "Block loopback/link-local/RFC1918/metadata targets; resolve-then-validate the IP before fetching."),
    "OCT6": ("Malicious-media transcode RCE — Plex CVE-2026-96654/55/56",
             "Validate magic bytes + re-decode before accepting; never load codecs/plugins from upload-controlled paths."),
    "OCT7": ("Verb tampering on an edge API — ASEC edge-API theme",
             "Apply the same function-level authz to every HTTP method; don't special-case verbs."),
    "OCT8": ("BOLA — the most-exploited API weakness of 2026",
             "Check object ownership on every access by id; never trust client-supplied ids."),
    "OCT9": ("Mass assignment",
             "Server-assign role/verified/balance; bind only an explicit allow-list of client fields."),
}

SOURCES = [
    "Microsoft — Storm-0940 / ConnectWise AI-driven supply-chain campaign",
    "Metabase unauthenticated SQLi in password reset — CVE-2026-72898 (Wiz, Horizon3, CISA KEV)",
    "Plex Media Server unauth RCE chain — CVE-2026-96652/96654/96655/96656 (Censys, CISA KEV)",
    "Better Auth OAuth state reused as magic-link token — CVE-2026-110862",
    "BeyondTrust Remote Support auth bypass — CVE-2026-102764 (Rapid7, CISA KEV)",
    "AhnLab ASEC — October 2026 breaches via externally-exposed web services / backend APIs",
    "Akamai State of the Internet 2026 — injection + BOLA + SSRF remain top app/API techniques",
]


def make_factory(name, cfg):
    if name == "reference-secure":
        from sentinel.adapters.reference_target import ReferenceSecureTarget
        return ReferenceSecureTarget
    if name == "reference-vulnerable":
        from sentinel.adapters.reference_target import ReferenceVulnerableTarget
        return ReferenceVulnerableTarget
    if name == "http":
        from sentinel.adapters.http_target import HttpTarget
        inst = HttpTarget(cfg)
        return lambda: inst
    raise SystemExit(f"unknown target: {name}")


def worse(a, b):
    """Return the higher-severity of two status values."""
    if a is None:
        return b
    return a if SEV[a] >= SEV[b] else b


def run_campaign(args):
    cfg = cfgmod.load(args.config)
    suites = args.suite if args.suite else (cfg.suites + ["oct2026"])
    suites = [s for s in dict.fromkeys(suites) if s in BUILDERS]  # dedupe, keep known
    factory = make_factory(args.target, cfg)

    do_fuzz = (not args.no_fuzz) and args.target == "http"
    corpus = fuzz.build_corpus()
    if args.no_huge:
        corpus = [p for p in corpus if p["id"] != "val-oversize-10m"]

    target_label = cfg.base_url if args.target == "http" else args.target
    print(f"campaign on {target_label} for {args.minutes} min "
          f"(suites: {', '.join(suites)}; fuzz: {do_fuzz})")

    checks = {}          # id -> {category, desc, worst, detail, counts}
    fuzz_hits = {}       # (target, field, payload_id) -> finding
    passes = 0
    deadline = time.monotonic() + args.minutes * 60

    while True:
        passes += 1
        for suite in suites:
            for f in run_catalogue(factory, BUILDERS[suite](cfg)):
                rec = checks.setdefault(f.id, {"category": f.category, "desc": f.desc,
                                               "worst": None, "detail": "", "counts": {}})
                rec["counts"][f.status.value] = rec["counts"].get(f.status.value, 0) + 1
                rec["worst"] = worse(rec["worst"], f.status.value)
                if f.detail:
                    rec["detail"] = f.detail
        if do_fuzz:
            random.shuffle(corpus)
            plan = fuzz.build_plan(cfg, ["login", "register", "routes"],
                                   corpus[:args.fuzz_limit])
            found, _ = fuzz.sweep(cfg, plan, timeout=args.timeout)
            for fd in found:
                fuzz_hits[(fd["target"], fd["field"], fd["payload_id"])] = fd
        print(f"  pass {passes} done ({len(checks)} checks seen, "
              f"{len(fuzz_hits)} fuzz signals)")
        if time.monotonic() >= deadline:
            break

    report_md, sidecar = build_report(target_label, suites, passes, args.minutes,
                                      checks, fuzz_hits, args.out_dir)
    os.makedirs(args.out_dir, exist_ok=True)
    stamp = _dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    base = os.path.join(args.out_dir, f"appsec-report-{stamp}")
    with open(base + ".md", "w") as fh:
        fh.write(report_md)
    with open(base + ".json", "w") as fh:
        json.dump(sidecar, fh, indent=2)
    print(f"\nreport : {base}.md\nsidecar: {base}.json")
    leaks = [i for i, r in checks.items() if r["worst"] == Status.LEAK.value]
    return 1 if leaks else 0


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
    strong = sorted(i for i, r in checks.items() if r["worst"] == Status.BLOCKED.value)
    leaks = sorted(i for i, r in checks.items() if r["worst"] == Status.LEAK.value)
    errors = sorted(i for i, r in checks.items() if r["worst"] == Status.ERROR.value)
    skipped = sorted(i for i, r in checks.items() if r["worst"] == Status.SKIPPED.value)

    HARD = ("AUTH BYPASS", "server error", "SQL-ERROR", "stack-trace")
    fuzz_hard = [f for f in fuzz_hits.values() if any(k in s for s in f["signals"] for k in HARD)]
    fuzz_soft = [f for f in fuzz_hits.values() if f not in fuzz_hard]

    # diff vs previous run
    prev = _prev_sidecar(out_dir)
    diff_lines = []
    if prev:
        prev_leaks = set(prev.get("leak_ids", []))
        cur_leaks = set(leaks)
        resolved = sorted(prev_leaks - cur_leaks)
        newly = sorted(cur_leaks - prev_leaks)
        diff_lines.append(f"Compared with previous report ({prev.get('timestamp', '?')}):")
        diff_lines.append(f"- Resolved since then: {', '.join(resolved) if resolved else 'none'}")
        diff_lines.append(f"- New leaks since then: {', '.join(newly) if newly else 'none'}")
        diff_lines.append(f"- Leak count: {len(prev_leaks)} → {len(cur_leaks)}")
    else:
        diff_lines.append("No previous report found — this is the baseline for future diffs.")

    L = []
    L.append(f"# AppSec campaign report")
    L.append("")
    L.append(f"- **Target:** `{target}`")
    L.append(f"- **When:** {now}")
    L.append(f"- **Duration:** {minutes} min, {passes} pass(es)")
    L.append(f"- **Suites:** {', '.join(suites)}")
    L.append("")
    L.append("> Defensive, authorized testing against a disposable instance. "
             "Fuzzer signals are **leads for human review, not confirmed vulnerabilities**.")
    L.append("")

    L.append("## Executive summary")
    L.append("")
    L.append("| Outcome | Count |")
    L.append("|---|---|")
    L.append(f"| ✅ Strong (blocked) | {len(strong)} |")
    L.append(f"| ❌ Weak (leaked) | {len(leaks)} |")
    L.append(f"| ! Errors | {len(errors)} |")
    L.append(f"| – Coverage gaps (skipped) | {len(skipped)} |")
    L.append(f"| 🔎 Fuzzer hard signals | {len(fuzz_hard)} |")
    L.append(f"| 🔎 Fuzzer other signals | {len(fuzz_soft)} |")
    L.append("")

    L.append("## ❌ Weak points — fix these first")
    L.append("")
    if not leaks and not errors and not fuzz_hard:
        L.append("None detected in this run. 🎉 (Verify coverage gaps below aren't hiding untested areas.)")
    else:
        for i in leaks:
            r = checks[i]
            tech, fix = TECH.get(i, (r["desc"], "See the check description; enforce the control server-side."))
            L.append(f"- **{i}** ({r['category']}) — {r['desc']}")
            L.append(f"  - Technique: {tech}")
            L.append(f"  - Fix: {fix}")
        for i in errors:
            L.append(f"- **{i}** — check errored repeatedly: `{checks[i]['detail']}` (investigate target/config).")
        for f in fuzz_hard:
            L.append(f"- **FUZZ {f['payload_id']}** on `{f['target']}.{f['field']}` "
                     f"(HTTP {f['status']}): {'; '.join(f['signals'])} — payload `{f['payload']}`")
    L.append("")

    L.append("## ✅ Strong points — controls that held")
    L.append("")
    if strong:
        by_cat = {}
        for i in strong:
            by_cat.setdefault(checks[i]["category"], []).append(i)
        for cat in sorted(by_cat):
            L.append(f"- **{cat}**: {', '.join(sorted(by_cat[cat]))}")
    else:
        L.append("No checks passed cleanly — likely a connectivity/config problem (run the preflight).")
    L.append("")

    L.append("## – Coverage gaps (skipped)")
    L.append("")
    if skipped:
        L.append("These did not run — usually a missing capability/route. Closing them widens coverage:")
        for i in skipped:
            L.append(f"- **{i}** — {checks[i]['desc']}  _({checks[i]['detail']})_")
    else:
        L.append("None — every applicable check ran.")
    L.append("")

    if fuzz_soft:
        L.append("## 🔎 Fuzzer signals to review (reflection / encoding)")
        L.append("")
        for f in sorted(fuzz_soft, key=lambda x: (x["target"], x["field"]))[:60]:
            L.append(f"- `{f['target']}.{f['field']}` {f['payload_id']} "
                     f"(HTTP {f['status']}): {'; '.join(f['signals'])}")
        L.append("")

    L.append("## Change since last run")
    L.append("")
    L.extend(diff_lines)
    L.append("")

    L.append("## Recommendations (October-2026 threat-informed)")
    L.append("")
    L.append("- The month's breaches mostly used *old* methods at scale (AI-driven credential "
             "guessing, stolen/trusted access, unpatched edge APIs). Prioritise: rate-limiting & "
             "lockout (BF checks), killing auth bypass (OCT4) and BOLA/mass-assignment (OCT8/9).")
    L.append("- Treat every weak point above as reachable from the internet by an automated agent "
             "running 24/7 — assume it *will* be found.")
    L.append("- Re-run this campaign after each fix; the diff section tracks progress toward a clean run.")
    L.append("")

    L.append("## Sources")
    L.append("")
    for s in SOURCES:
        L.append(f"- {s}")
    L.append("")

    sidecar = {
        "timestamp": now, "target": target, "minutes": minutes, "passes": passes,
        "summary": {"blocked": len(strong), "leak": len(leaks),
                    "error": len(errors), "skipped": len(skipped)},
        "leak_ids": leaks,
        "checks": {i: r["worst"] for i, r in checks.items()},
        "fuzz_hard": len(fuzz_hard), "fuzz_soft": len(fuzz_soft),
    }
    return "\n".join(L), sidecar


def main(argv=None):
    ap = argparse.ArgumentParser(description="timed security campaign + markdown report")
    ap.add_argument("--target", default="http",
                    choices=["reference-secure", "reference-vulnerable", "http"])
    ap.add_argument("--config", help="YAML config (else $SENTINEL_CONFIG / defaults)")
    ap.add_argument("--minutes", type=float, default=10.0, help="how long to keep trying")
    ap.add_argument("--suite", nargs="*", help="suites to run (default: config + oct2026)")
    ap.add_argument("--no-fuzz", action="store_true", help="suites only, skip the fuzzer")
    ap.add_argument("--no-huge", action="store_true", help="drop the 10MB fuzz payload")
    ap.add_argument("--fuzz-limit", type=int, default=30, help="fuzz payloads per pass")
    ap.add_argument("--timeout", type=float, default=15.0)
    ap.add_argument("--out-dir", default="reports", help="where to write the report")
    args = ap.parse_args(argv)
    sys.exit(run_campaign(args))


if __name__ == "__main__":
    main()
