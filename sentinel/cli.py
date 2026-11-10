"""
appsec-sentinel CLI — point it at a backend (host/port/path via config or env)
and run the security suites.

    python -m sentinel.cli run --target http --suite all
    python -m sentinel.cli run --target http --host my-api --port 8080
    python -m sentinel.cli run --target reference-secure       # self-test
    python -m sentinel.cli run --target reference-vulnerable    # negative control
    python -m sentinel.cli list                                 # every check, by suite
    python -m sentinel.cli ui                                   # the web UI (port 8090)

Exit codes (gate CI on them):
    0  every check that ran was proven blocked
    1  at least one attack got through, or a check crashed
    2  nothing leaked, but the run proved less than it should have: some checks
       were inconclusive, the config was unusable, or the target is out of scope
"""
from __future__ import annotations

import argparse
import json
import sys

from . import config as cfgmod
from . import engine
from .safety import ScopeError
from .suites import BUILDERS, SUITE_INFO
from .suites.common import Status, summarize

MARK = {Status.BLOCKED: "✓", Status.LEAK: "✗ LEAK", Status.SKIPPED: "– skip",
        Status.INCONCLUSIVE: "? n/a", Status.ERROR: "! err"}
VERDICT = {"PASS": "PASS ✅", "FAIL": "FAIL ❌", "INCOMPLETE": "INCOMPLETE ⚠️  (unproven checks)",
           "EMPTY": "EMPTY ⚠️  (nothing ran)"}


def load_config(args):
    cfg = cfgmod.load(args.config)
    cfgmod.retarget(cfg, host=getattr(args, "host", None), port=getattr(args, "port", None),
                    scheme=getattr(args, "scheme", None),
                    base_path=getattr(args, "base_path", None),
                    frontend_host=getattr(args, "frontend_host", None),
                    frontend_port=getattr(args, "frontend_port", None),
                    frontend_api_path=getattr(args, "frontend_api_path", None))
    cfgmod.validate(cfg)
    if getattr(args, "via_frontend", False):
        cfgmod.route_via_frontend(cfg)
    return cfg


def run(args):
    try:
        cfg = load_config(args)
    except cfgmod.ConfigError as e:
        print(f"config error: {e}", file=sys.stderr)
        return 2
    for w in cfg.warnings:
        print(f"warning: {w}", file=sys.stderr)

    suites = engine.resolve_suites(cfg, args.suite)
    for s in suites:
        if s not in BUILDERS and s != "xss":
            print(f"warning: unknown suite '{s}' skipped (known: {', '.join(BUILDERS)}, xss)",
                  file=sys.stderr)
    known_flows = [k for k, _, _ in engine.FLOWS]
    for fl in args.flow or []:
        if fl not in known_flows:
            print(f"unknown flow '{fl}' (known: {', '.join(known_flows)})", file=sys.stderr)
            return 2
    if args.flow and not args.suite:
        suites = list(BUILDERS)                  # a flow cuts across every suite
    try:
        factory, attacks, notes = engine.prepare(args.target, cfg, suites, args.flow or None)
    except ScopeError as e:
        print(str(e), file=sys.stderr)
        return 2
    for n in notes:
        print(f"note: {n}")

    print(f"target: {engine.target_label(args.target, cfg)}   (suites: {', '.join(suites)})")
    if args.target == "http" and cfg.frontend_origin:
        print(f"front end: {cfg.frontend_origin}"
              + ("   (API traffic is routed through it)" if cfg.backend_origin else ""))
    if args.flow:
        print(f"flows: {', '.join(args.flow)}")
    caps = ", ".join(sorted(c.value for c in factory().capabilities())) or "none"
    print(f"capabilities: {caps}\n")

    from .suites.common import run_catalogue
    findings = run_catalogue(factory, attacks)

    # optional XSS suite (separate because it needs a browser)
    if "xss" in suites:
        findings += _run_xss(cfg, args.target)

    _print_report(findings)
    s = summarize(findings)
    c = s["counts"]
    if args.json:
        with open(args.json, "w") as fh:
            json.dump(engine.report(args.target, cfg, suites, findings), fh, indent=2)
        print(f"\nJSON report written to {args.json}")

    code = engine.exit_code(args.target, cfg, findings)
    if args.target == "reference-vulnerable":
        # negative control: EVERY check must leak, or that check has no teeth
        toothless = [f.id for f in findings if f.status not in (Status.LEAK, Status.SKIPPED)]
        print(f"\nNEGATIVE CONTROL: {c['LEAK']} of {s['ran']} checks caught the broken build — "
              + ("OK, every check has teeth ✅" if code == 0 else
                 f"BROKEN ❌ no leak reported by: {', '.join(toothless) or 'any check'}"))
        return code
    print(f"\nRESULT: {VERDICT[s['verdict']]}   score {s['score']}/100   "
          f"(blocked={c['BLOCKED']}, leaks={c['LEAK']}, inconclusive={c['INCONCLUSIVE']}, "
          f"skipped={c['SKIPPED']}, errors={c['ERROR']}; coverage {s['coverage']}%)")
    if c["INCONCLUSIVE"]:
        print("        inconclusive = the check could not prove the control works "
              "(see the reason next to each '?'); it is not a pass.")
    flows = engine.flow_summary(findings)
    if len(flows) > 1:
        print("        by flow: " + "  ".join(f"{f['label']} {f['counts']['BLOCKED']}/{f['ran']}"
                                             for f in flows if f["ran"]))
    return code


def _run_xss(cfg, target_name):
    from .suites.common import Finding
    try:
        from .suites import xss
    except Exception as e:
        return [Finding("XSS", "xss", "headless-browser XSS", Status.SKIPPED,
                        f"playwright not available: {e}")]
    try:
        if target_name == "http":
            rc = xss.run_against_app(cfg.base_url, cfg.xss_reflect_path)
        else:
            rc = xss.run_demo()
        st = Status.BLOCKED if rc == 0 else Status.LEAK
        return [Finding("XSS", "xss", "no injected payload executed in a real browser", st)]
    except Exception as e:
        return [Finding("XSS", "xss", "headless-browser XSS", Status.ERROR, repr(e))]


def _print_report(findings):
    cur = None
    for f in findings:
        if f.category != cur:
            cur = f.category
            print(f"  [{cur}]")
        print(f"     {MARK[f.status]:7} {f.id:6} {f.desc}")
        if f.detail and f.status != Status.BLOCKED:
            print(f"             ↳ {f.detail}")


def list_checks(args):
    cfg = cfgmod.Config()
    total = 0
    for name, build in BUILDERS.items():
        attacks = build(cfg)
        total += len(attacks)
        print(f"\n{name} — {SUITE_INFO.get(name, '')} ({len(attacks)})")
        for a in attacks:
            needs = f"   [needs: {', '.join(sorted(c.value for c in a.requires))}]" if a.requires else ""
            print(f"  {a.id:6} {a.desc}{needs}")
    print(f"\n{total} checks in {len(BUILDERS)} suites (+ optional 'xss', which needs a browser)")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="sentinel", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run", help="run the security suites")
    r.add_argument("--target", default="reference-secure", choices=list(engine.TARGETS))
    r.add_argument("--suite", nargs="*", help="suites to run (default from config); 'all' for every registered suite")
    r.add_argument("--config", help="path to a YAML config (else $SENTINEL_CONFIG / defaults)")
    r.add_argument("--host", help="override target.host (e.g. a docker service name)")
    r.add_argument("--port", type=int, help="override target.port")
    r.add_argument("--base-path", dest="base_path", help="override target.base_path, e.g. /api/v1")
    r.add_argument("--scheme", choices=["http", "https"], help="override target.scheme")
    r.add_argument("--frontend-port", dest="frontend_port", type=int,
                   help="port of the web front end (enables the front-end checks)")
    r.add_argument("--frontend-host", dest="frontend_host", help="front-end host (default: --host)")
    r.add_argument("--frontend-api-path", dest="frontend_api_path",
                   help="prefix under which the front end proxies the API, e.g. /api")
    r.add_argument("--via-frontend", dest="via_frontend", action="store_true",
                   help="send the API attacks through the front-end port, as a browser would")
    r.add_argument("--flow", nargs="*", help="only these product flows: "
                   + ", ".join(k for k, _, _ in engine.FLOWS))
    r.add_argument("--json", help="write a JSON report to this path")
    sub.add_parser("list", help="list every check")
    u = sub.add_parser("ui", help="start the web UI")
    u.add_argument("--listen", default="127.0.0.1", help="address to bind (default 127.0.0.1)")
    u.add_argument("--port", type=int, default=8090, help="UI port (default 8090)")
    u.add_argument("--config", help="default config to preselect")
    args = ap.parse_args(argv)
    if args.cmd == "run":
        sys.exit(run(args))
    if args.cmd == "list":
        sys.exit(list_checks(args))
    if args.cmd == "ui":
        from .ui.server import serve
        sys.exit(serve(args.listen, args.port, args.config))


if __name__ == "__main__":
    main()
