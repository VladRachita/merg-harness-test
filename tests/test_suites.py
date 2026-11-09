"""
pytest entry points — run the suites against the in-process reference targets.
Lets you gate CI with `pytest` instead of (or alongside) the CLI.

    pytest -q                      # self-test + negative control + harness tests

The two invariants that keep the suites honest:
  * the SECURE reference build: every check is BLOCKED (no false alarms);
  * the VULNERABLE reference build: every check LEAKS (no check without teeth).
"""
import pytest

from sentinel import config as cfgmod
from sentinel.suites import BUILDERS, SUITE_INFO
from sentinel.suites.common import Status, collect, run_catalogue, summarize
from sentinel.suites.remediation import FIX, fix_for
from sentinel.adapters.reference_target import ReferenceSecureTarget, ReferenceVulnerableTarget


def _run(factory):
    cfg = cfgmod.Config()
    return run_catalogue(factory, collect(BUILDERS, list(BUILDERS), cfg))


@pytest.fixture(scope="module")
def secure():
    return _run(ReferenceSecureTarget)


@pytest.fixture(scope="module")
def vulnerable():
    return _run(ReferenceVulnerableTarget)


def _not(findings, status):
    return [f"{f.id}={f.status.value} ({f.detail})" for f in findings if f.status != status]


def test_secure_blocks_everything(secure):
    assert not _not(secure, Status.BLOCKED), "the secure build must pass every check"
    s = summarize(secure)
    assert s["verdict"] == "PASS" and s["score"] == 100 and s["coverage"] == 100
    assert len(secure) >= 80


def test_negative_control_every_check_has_teeth(vulnerable):
    """A check that does not LEAK on the broken build cannot detect its own flaw."""
    assert not _not(vulnerable, Status.LEAK)
    s = summarize(vulnerable)
    assert s["verdict"] == "FAIL" and s["score"] == 0


def test_leaks_explain_themselves(vulnerable):
    """The custom LEAK messages name what was seen (in-process there is no HTTP trace)."""
    detail = {f.id: f.detail for f in vulnerable}
    assert "password_hash" in detail["NOV9"]
    assert "X-Remote-User" in detail["NOV10"]
    assert "169.254.169.254" in detail["OCT5"]
    assert "server error" in detail["RES9"]


@pytest.mark.parametrize("suite", list(BUILDERS.keys()))
def test_suite_runs(suite):
    cfg = cfgmod.Config()
    attacks = BUILDERS[suite](cfg)
    assert attacks, f"suite {suite} produced no attacks"
    assert suite in SUITE_INFO


def test_check_ids_unique_and_documented():
    cfg = cfgmod.Config()
    attacks = collect(BUILDERS, list(BUILDERS), cfg)
    ids = [a.id for a in attacks]
    assert len(ids) == len(set(ids)), "duplicate check ids"
    assert all(a.suite for a in attacks)
    generic = fix_for("no-such-id")
    missing = [a.id for a in attacks if a.id not in FIX and fix_for(a.id, a.category) == generic]
    assert not missing, f"checks without a remediation hint: {missing}"


def test_findings_keep_catalogue_order_despite_staged_execution(secure):
    cfg = cfgmod.Config()
    assert [f.id for f in secure] == [a.id for a in collect(BUILDERS, list(BUILDERS), cfg)]
