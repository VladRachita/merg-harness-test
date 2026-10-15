"""
appsec-sentinel CLI — point it at a backend (host/port/path via config or env)
and run the security suites. Returns a non-zero exit code if any attack gets
through, so it gates CI.

    python -m sentinel.cli run --target http --suite all
    python -m sentinel.cli run --target reference-secure       # self-test
    python -m sentinel.cli run --target reference-vulnerable    # negative control
"""
from __future__ import annotations

import argparse
import json
import sys

from . import config as cfgmod
from .suites import BUILDERS
from .suites.common import run_catalogue, Status


def _make_factory(name, cfg):
    """Return a zero-arg factory producing a Target. Reference targets get a FRESH
    instance per call (clean state per attack); the HTTP target is reused."""
    if name == "reference-secure":
        from .adapters.reference_target import ReferenceSecureTarget
        return ReferenceSecureTarget
    if name == "reference-vulnerable":
        from .adapters.reference_target import ReferenceVulnerableTarget
        return ReferenceVulnerableTarget
    if name == "http":
        from .adapters.http_target import HttpTarget
        inst = HttpTarget(cfg)
        return lambda: inst
    raise SystemExit(f"unknown target: {name}")


MARK = {Status.BLOCKED: "✓", Status.LEAK: "✗ LEAK", Status.SKIPPED: "– skip", Status.ERROR: "! err"}


def run(args):
    cfg = cfgmod.load(args.config)
    if args.suite and args.suite != ["all"]:
        cfg.suites = args.suite
    factory = _make_factory(args.target, cfg)
    sample = factory()

    if args.target == "http":
        print(f"target: {cfg.base_url}   (suites: {', '.join(cfg.suites)})")
    else:
        print(f"target: {sample.name}   (suites: {', '.join(cfg.suites)})")
    caps = ", ".join(sorted(c.value for c in sample.capabilities())) or "none"
    print(f"capabilities: {caps}\n")

    findings = []
    for suite in cfg.suites:
        builder = BUILDERS.get(suite)
        if not builder:
            print(f"  [skip] unknown suite '{suite}'"); continue
        findings += run_catalogue(factory, builder(cfg))

    # optional XSS suite (separate because it needs a browser)
    if "xss" in cfg.suites:
        findings += _run_xss(cfg, args.target)

    _print_report(findings)
    counts = _counts(findings)
    out = {"target": cfg.base_url if args.target == "http" else sample.name,
           "summary": counts,
           "findings": [vars(f) | {"status": f.status.value} for f in findings]}
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(out, fh, indent=2)
        print(f"\nJSON report written to {args.json}")

    leaks = counts[Status.LEAK.value]
    errs = counts[Status.ERROR.value]
    verdict_fail = (leaks > 0 and cfg.fail_on_leak) or errs > 0
    if args.target == "reference-vulnerable":
        # negative control: we EXPECT leaks; success means the suite caught them
        ok = leaks > 0
        print(f"\nNEGATIVE CONTROL: {leaks} leak(s) detected — "
              f"{'OK, suites have teeth ✅' if ok else 'BROKEN, no leaks seen ❌'}")
        return 0 if ok else 1
    print(f"\nRESULT: {'PASS ✅' if not verdict_fail else 'FAIL ❌'}  "
          f"(blocked={counts['BLOCKED']}, leaks={leaks}, skipped={counts['SKIPPED']}, errors={errs})")
    return 1 if verdict_fail else 0


def _run_xss(cfg, target_name):
    from .suites.common import Finding, Status
    try:
        from .suites import xss
    except Exception as e:
        return [Finding("XSS", "xss", "headless-browser XSS", Status.SKIPPED, f"playwright not available: {e}")]
    try:
        if target_name == "http":
            rc = xss.run_against_app(cfg.base_url, getattr(cfg, "xss_reflect_path", "/search?q={PAYLOAD}"))
        else:
            rc = xss.run_demo()
        st = Status.BLOCKED if rc == 0 else Status.LEAK
        return [Finding("XSS", "xss", "no injected payload executed in a real browser", st)]
    except Exception as e:
        return [Finding("XSS", "xss", "headless-browser XSS", Status.ERROR, repr(e))]


def _counts(findings):
    c = {s.value: 0 for s in Status}
    for f in findings:
        c[f.status.value] += 1
    return c


def _print_report(findings):
    cur = None
    for f in findings:
        if f.category != cur:
            cur = f.category
            print(f"  [{cur}]")
        extra = f"   ({f.detail})" if f.detail and f.status in (Status.SKIPPED, Status.ERROR) else ""
        print(f"     {MARK[f.status]:7} {f.id:5} {f.desc}{extra}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sentinel")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the security suites")
    r.add_argument("--target", default="reference-secure",
                   choices=["reference-secure", "reference-vulnerable", "http"])
    r.add_argument("--suite", nargs="*", help="suites to run (default from config); 'all' for every registered suite")
    r.add_argument("--config", help="path to a YAML config (else env vars / defaults)")
    r.add_argument("--json", help="write a JSON report to this path")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        if args.suite == ["all"]:
            cfg_suites = list(BUILDERS.keys())
            args.suite = cfg_suites
        sys.exit(run(args))


if __name__ == "__main__":
    main()
