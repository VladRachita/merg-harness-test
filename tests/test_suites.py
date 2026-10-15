"""
pytest entry points — run the suites against the in-process reference targets.
Lets you gate CI with `pytest` instead of (or alongside) the CLI.

    pytest -q                      # self-test + negative control

To run against a live backend from pytest, set SENTINEL_CONFIG and target=http
in your own test (see the CLI for the pattern).
"""
import pytest

from sentinel import config as cfgmod
from sentinel.suites import BUILDERS
from sentinel.suites.common import run_catalogue, Status
from sentinel.adapters.reference_target import ReferenceSecureTarget, ReferenceVulnerableTarget


def _run(factory):
    cfg = cfgmod.Config()
    findings = []
    for name, build in BUILDERS.items():
        findings += run_catalogue(factory, build(cfg))
    return findings


def test_secure_blocks_everything():
    findings = _run(ReferenceSecureTarget)
    leaks = [f for f in findings if f.status == Status.LEAK]
    errors = [f for f in findings if f.status == Status.ERROR]
    assert not leaks, "unblocked attacks: " + ", ".join(f.id for f in leaks)
    assert not errors, "errored attacks: " + ", ".join(f"{f.id}:{f.detail}" for f in errors)
    assert sum(1 for f in findings if f.status == Status.BLOCKED) >= 40


def test_negative_control_has_teeth():
    findings = _run(ReferenceVulnerableTarget)
    leaks = [f for f in findings if f.status == Status.LEAK]
    assert len(leaks) >= 10, "the broken build should be broken on many attacks"


@pytest.mark.parametrize("suite", list(BUILDERS.keys()))
def test_suite_runs(suite):
    cfg = cfgmod.Config()
    findings = run_catalogue(ReferenceSecureTarget, BUILDERS[suite](cfg))
    assert findings, f"suite {suite} produced no findings"
