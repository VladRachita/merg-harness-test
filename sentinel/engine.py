"""One place that knows how to turn (target name, config, suites) into a run.
Shared by the CLI, the campaign runner and the web UI so they cannot drift."""
from __future__ import annotations

import datetime as _dt

from . import config as cfgmod
from .adapters.base import Inconclusive
from .safety import check_scope
from .suites import BUILDERS
from .suites.common import STRONG_PW, Status, collect, run_catalogue, summarize, unique
from .suites.flows import FLOWS, FLOW_LABEL
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


def prepare(target, cfg, suites, flows=None):
    """Scope-check the target and build (factory, attacks, notes). `flows`
    keeps only the checks of those product flows (login, registration, upload…).
    Raises safety.ScopeError when an HTTP target is outside the allowed scope."""
    notes = check_scope(cfg) if target == "http" else []
    known = [s for s in suites if s in BUILDERS]
    return make_factory(target, cfg), collect(BUILDERS, known, cfg, flows), notes


def execute(target, cfg, suites, flows=None, **hooks):
    """Run the suites; return (findings, summary)."""
    factory, attacks, _ = prepare(target, cfg, suites, flows)
    findings = run_catalogue(factory, attacks, **hooks)
    return findings, summarize(findings)


def flow_summary(findings) -> list:
    """Score per product flow, in display order (flows with no check are left out)."""
    out = []
    for key, label, _ in FLOWS:
        part = [f for f in findings if f.flow == key]
        if part:
            s = summarize(part)
            out.append({"flow": key, "label": label, "counts": s["counts"], "ran": s["ran"],
                        "total": s["total"], "score": s["score"], "verdict": s["verdict"]})
    return out


def _excerpt(resp, limit=220) -> str:
    """A short, secret-free view of a response body for the 'try the flows' panel."""
    import json as _json
    import re as _re

    def mask(o):
        if isinstance(o, dict):
            return {k: ("•••" if _re.search(r"token|secret|password|passwd|sid|cookie|key", str(k), _re.I)
                        and isinstance(v, (str, int)) and v else mask(v)) for k, v in o.items()}
        if isinstance(o, list):
            return [mask(v) for v in o[:5]]
        return o
    text = _json.dumps(mask(resp.body), ensure_ascii=False)
    return text if len(text) <= limit else text[:limit] + "…"


def try_flows(cfg) -> list:
    """Perform each product flow ONCE, legitimately — reach the backend and the
    front end, log in, read the user's own data, sign up, upload — and report
    which ones the harness can do with this configuration. A flow that cannot be
    done legitimately cannot be attacked meaningfully (its checks would be
    inconclusive), so this is what to get green before a run.

    Side effects: one junk account and up to two small uploads."""
    from .adapters.http_target import HttpTarget
    check_scope(cfg)
    t = HttpTarget(cfg)
    t.begin_attack("try-flows")
    steps, state = [], {}

    def step(key, label, fn, needs=None):
        if needs and not state.get(needs):
            steps.append({"key": key, "label": label, "state": "skip",
                          "text": f"skipped — needs a working {needs}"})
            return
        try:
            ok, text = fn()
        except Inconclusive as e:               # includes "no response"
            ok, text = False, str(e)
        except Exception as e:
            ok, text = False, f"{type(e).__name__}: {e}"
        state[key] = ok
        steps.append({"key": key, "label": label, "state": "ok" if ok else "fail", "text": text})

    user, admin = cfg.users["user"], cfg.users["admin"]

    step("backend", "Backend reachable",
         lambda: (True, f"{cfg.base_url} answered (HTTP {t._call('GET', '/').status})"))

    if cfg.hooks.get("reset"):
        def reset():
            t.reset()                       # raises Inconclusive when the hook fails
            return True, "the backend's test-reset hook answered — starting from clean state"
        step("reset", "Test reset hook", reset, needs="backend")

    if cfg.frontend_origin:
        def frontend():
            r = t.fetch_path("frontend", "/")
            return r.ok, f"{cfg.frontend_origin} answered HTTP {r.status}" + \
                ("" if r.ok else " — is this the front-end port?")
        step("frontend", "Front end reachable", frontend)

    def login():
        r = t.login(user["username"], user["password"])
        state["token"] = r.body.get("access_token")
        if state["token"]:
            return True, f"signed in as '{user['username']}' (HTTP {r.status}); token found"
        return False, (f"HTTP {r.status} and no token at '{cfg.token_json_path}'. Check the login "
                       f"route, the field names, the test user and the token path. "
                       f"Response: {_excerpt(r)}")
    step("login", "Login", login, needs="backend")

    def own_data():
        r = t.get_resource(state["token"], user["id"])
        return r.ok, (f"the token reads the user's own data (HTTP {r.status})" if r.ok else
                      f"HTTP {r.status} reading the user's own data. Check the 'own data' route, "
                      f"the user id and the auth header. Response: {_excerpt(r)}")
    step("own_data", "Read own data", own_data, needs="login")

    def registration():
        name = unique("try")
        r = t.register(name, STRONG_PW)
        return r.ok, (f"created the test account '{name}' (HTTP {r.status})" if r.ok else
                      f"HTTP {r.status}. Check the registration route and field names (sign-up "
                      f"may also need a CAPTCHA or invite). Response: {_excerpt(r)}")
    step("registration", "Registration", registration, needs="backend")

    if "media_upload" in cfg.features:
        def upload_file():
            from .suites.media_injection import samples
            m, data = samples(lambda m: m["expect"] == "control")[0]
            r = t.upload_bytes(state["token"], m["file"], data, m["content_type"])
            return r.ok, (f"uploaded a small valid {m['type']} file (HTTP {r.status})" if r.ok else
                          f"HTTP {r.status} uploading a valid {m['type']} file. Check the upload "
                          f"route and the file field name. Response: {_excerpt(r)}")
        step("upload", "Upload a file", upload_file, needs="login")

        def upload_request():
            r = t.upload(state["token"])
            return r.ok, (f"the JSON upload request was accepted (HTTP {r.status})" if r.ok else
                          f"HTTP {r.status}. If the app has no import-by-URL / JSON upload "
                          f"request, the SSRF and pixel-flood checks will be inconclusive. "
                          f"Response: {_excerpt(r)}")
        step("upload_request", "Upload request (import by URL)", upload_request, needs="login")

    def admin_login():
        r = t.login(admin["username"], admin["password"])
        tok = r.body.get("access_token")
        if not tok:
            return False, (f"HTTP {r.status} and no token for the admin test account "
                           f"'{admin['username']}'. Response: {_excerpt(r)}")
        a = t.admin_users(tok)
        return a.ok, (f"signed in as '{admin['username']}' and the admin route answered "
                      f"(HTTP {a.status})" if a.ok else
                      f"signed in, but the admin route returned HTTP {a.status} — check the "
                      f"admin route. Response: {_excerpt(a)}")
    step("admin", "Admin login", admin_login, needs="backend")
    return steps


def finding_dict(f) -> dict:
    d = {"id": f.id, "suite": f.suite, "flow": f.flow, "flow_label": FLOW_LABEL.get(f.flow, ""),
         "category": f.category, "desc": f.desc, "status": f.status.value, "detail": f.detail}
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
        "flows": flow_summary(findings),
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


__all__ = ["TARGETS", "BUILDERS", "FLOWS", "cfgmod", "make_factory", "resolve_suites",
           "target_label", "prepare", "execute", "flow_summary", "try_flows", "finding_dict",
           "report", "exit_code"]
