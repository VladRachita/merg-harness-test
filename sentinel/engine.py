"""One place that knows how to turn (target name, config, suites) into a run.
Shared by the CLI, the campaign runner and the web UI so they cannot drift."""
from __future__ import annotations

import datetime as _dt

from . import config as cfgmod
from .safety import check_scope
from .suites import BUILDERS
from .suites.common import Status, collect, run_catalogue, summarize
from .suites.remediation import fix_for

TARGETS = ("http", "reference-secure", "reference-vulnerable")


def make_factory(name, cfg):
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
    raise ValueError(f"unknown target: {name}")


def resolve_suites(cfg, requested=None) -> list:
    """Suite names to run: explicit list, 'all', or the config's default."""
    if not requested:
        names = list(cfg.suites)
    elif list(requested) == ["all"]:
        names = list(BUILDERS)
    else:
        names = list(requested)
    return list(dict.fromkeys(names))


def target_label(target, cfg) -> str:
    return cfg.base_url if target == "http" else target


def prepare(target, cfg, suites):
    """Scope-check the target and build (factory, attacks, notes).
    Raises safety.ScopeError when an HTTP target is outside the allowed scope."""
    notes = check_scope(cfg) if target == "http" else []
    known = [s for s in suites if s in BUILDERS]
    return make_factory(target, cfg), collect(BUILDERS, known, cfg), notes


def execute(target, cfg, suites, **hooks):
    """Run the suites; return (findings, summary)."""
    factory, attacks, _ = prepare(target, cfg, suites)
    findings = run_catalogue(factory, attacks, **hooks)
    return findings, summarize(findings)


def finding_dict(f) -> dict:
    d = {"id": f.id, "suite": f.suite, "category": f.category, "desc": f.desc,
         "status": f.status.value, "detail": f.detail}
    if f.status == Status.LEAK:
        d["fix"] = fix_for(f.id, f.category)
    return d


def report(target, cfg, suites, findings) -> dict:
    """The machine-readable report (CLI --json, UI download, campaign sidecar)."""
    return {
        "target": target_label(target, cfg),
        "mode": target,
        "generated": _dt.datetime.now().astimezone().isoformat(timespec="seconds"),
        "suites": list(suites),
        "summary": summarize(findings),
        "findings": [finding_dict(f) for f in findings],
    }


def exit_code(target, cfg, findings) -> int:
    """0 clean · 1 a leak or crashed check · 2 nothing leaked but something is unproven.
    For the negative control the meaning flips: 0 only if EVERY check that ran leaked."""
    s = summarize(findings)
    c = s["counts"]
    if target == "reference-vulnerable":
        return 0 if c["LEAK"] and c["LEAK"] == s["ran"] else 1
    if (c["LEAK"] and cfg.fail_on_leak) or c["ERROR"]:
        return 1
    if (c["INCONCLUSIVE"] and cfg.fail_on_inconclusive) or not s["ran"]:
        return 2
    return 0


__all__ = ["TARGETS", "BUILDERS", "cfgmod", "make_factory", "resolve_suites", "target_label",
           "prepare", "execute", "finding_dict", "report", "exit_code"]
