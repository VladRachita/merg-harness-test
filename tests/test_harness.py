"""
Tests of the harness itself: the things that used to make a run say PASS while
testing nothing. Each test names the failure it guards against.
"""
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.request

import pytest

from sentinel import config as cfgmod
from sentinel import engine
from sentinel.adapters.base import Inconclusive, Resp, Unreachable
from sentinel.adapters.http_target import HttpTarget
from sentinel.adapters.reference.secure_app import SecureApp
from sentinel.adapters.reference_target import ReferenceSecureTarget
from sentinel.safety import Pacer, BudgetExceeded, ScopeError, check_scope, classify_host
from sentinel.suites import BUILDERS, automation
from sentinel.suites.common import (Status, denied, expect_ok, refused, run_catalogue,
                                    summarize, Finding)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALL = list(BUILDERS)


def _free_port():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _demo(mode):
    port = _free_port()
    proc = subprocess.Popen([sys.executable, os.path.join(ROOT, "demo_target", "server.py")],
                            env={**os.environ, "PORT": str(port), "DEMO_MODE": mode},
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for _ in range(100):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/health", timeout=1)
            return proc, port
        except Exception:
            time.sleep(0.1)
    proc.kill()
    raise RuntimeError("demo backend did not start")


@pytest.fixture(scope="module")
def secure_port():
    proc, port = _demo("secure")
    yield port
    proc.kill()


@pytest.fixture(scope="module")
def vulnerable_port():
    proc, port = _demo("vulnerable")
    yield port
    proc.kill()


def _cfg(port, hooks=True):
    cfg = cfgmod.load(os.path.join(ROOT, "config", "target.demo.yaml"))
    cfgmod.retarget(cfg, host="127.0.0.1", port=port)
    if not hooks:                       # a true black-box run: no test profile at all
        cfg.hooks = {"reset": None, "user_admin": None, "db_probe": None,
                     "reset_introspect": False, "other_aud_token": None}
        cfg.jwks_url = None
    return cfg


def _by_status(findings):
    out = {}
    for f in findings:
        out.setdefault(f.status.value, []).append(f"{f.id}: {f.detail}")
    return out


# ---------------------------------------------------------------------------
#  the whole catalogue over a real socket
# ---------------------------------------------------------------------------
def test_http_secure_backend_all_blocked(secure_port):
    cfg = _cfg(secure_port)
    findings, s = engine.execute("http", cfg, ALL)
    assert set(_by_status(findings)) == {"BLOCKED"}, _by_status(findings)
    assert s["score"] == 100 and engine.exit_code("http", cfg, findings) == 0


def test_http_vulnerable_backend_all_leak(vulnerable_port):
    cfg = _cfg(vulnerable_port)
    findings, s = engine.execute("http", cfg, ALL)
    assert set(_by_status(findings)) == {"LEAK"}, _by_status(findings)
    assert engine.exit_code("http", cfg, findings) == 1
    leak = next(f for f in findings if f.id == "AZ1")
    assert "/admin/users" in leak.detail and "200" in leak.detail      # evidence trail


def test_dead_backend_is_never_a_pass():
    """Was: 39 checks reported 'blocked' with nothing listening."""
    cfg = _cfg(_free_port())
    cfg.timeout_s = 2
    findings, s = engine.execute("http", cfg, ALL)
    assert set(_by_status(findings)) == {"INCONCLUSIVE"}, _by_status(findings)
    assert s["verdict"] == "INCOMPLETE" and s["score"] == 0
    assert engine.exit_code("http", cfg, findings) == 2


def test_blackbox_secure_backend_reports_no_false_leak(secure_port):
    """Was: with no reset hook the first lockout test locked the seed account,
    after which secure controls 'leaked' and everything else 'passed' blindly."""
    findings, s = engine.execute("http", _cfg(secure_port, hooks=False), ALL)
    got = _by_status(findings)
    assert "LEAK" not in got and "ERROR" not in got, got
    assert len(got["BLOCKED"]) >= 65
    assert len(got.get("INCONCLUSIVE", [])) <= 3, got.get("INCONCLUSIVE")


def test_blackbox_vulnerable_backend_reports_no_false_block(vulnerable_port):
    findings, _ = engine.execute("http", _cfg(vulnerable_port, hooks=False), ALL)
    got = _by_status(findings)
    assert "BLOCKED" not in got and "ERROR" not in got, got
    assert len(got["LEAK"]) >= 65


def test_wrong_route_is_inconclusive_not_blocked(secure_port):
    """Was: a mistyped route 404'd and counted as 'attack blocked'."""
    cfg = _cfg(secure_port)
    cfg.endpoints["resource"] = "GET /no/such/route/{owner_id}"
    findings, _ = engine.execute("http", cfg, ["access_control"])
    st = {f.id: f.status for f in findings}
    assert st["AZ2"] == Status.INCONCLUSIVE and st["SES2"] == Status.INCONCLUSIVE
    assert Status.LEAK not in st.values()


def test_wrong_credentials_are_inconclusive_not_blocked(secure_port):
    cfg = _cfg(secure_port)
    cfg.users["user"] = dict(cfg.users["user"], password="not-the-password")
    findings, _ = engine.execute("http", cfg, ["access_control"])
    st = {f.id: f for f in findings}
    assert st["AZ1"].status == Status.INCONCLUSIVE and "could not log in" in st["AZ1"].detail


def test_failing_reset_hook_is_reported(secure_port):
    cfg = _cfg(secure_port)
    cfg.hooks["reset"] = "POST /test/no-such-reset"
    findings, _ = engine.execute("http", cfg, ["nov2026"])
    assert all(f.status == Status.INCONCLUSIVE and "hooks.reset" in f.detail for f in findings)


# ---------------------------------------------------------------------------
#  what goes on the wire
# ---------------------------------------------------------------------------
def _capture(n, drive):
    """Run `drive(cfg)` against a socket that records n request heads."""
    seen = []
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0)); srv.listen(8)

    def loop():
        for _ in range(n):
            c, _a = srv.accept()
            seen.append(c.recv(65536).decode(errors="replace"))
            c.sendall(b"HTTP/1.1 200 OK\r\nSet-Cookie: sid=abc; Path=/\r\n"
                      b"Content-Type: application/json\r\nContent-Length: 2\r\n"
                      b"Connection: close\r\n\r\n{}")
            c.close()
    t = threading.Thread(target=loop, daemon=True); t.start()
    cfg = cfgmod.Config(); cfg.host = "127.0.0.1"; cfg.port = srv.getsockname()[1]
    drive(cfg); t.join(5); srv.close()
    return seen


def test_traversal_reaches_the_server_verbatim():
    """Was: the HTTP client collapsed /media/../../etc/passwd to /etc/passwd."""
    seen = _capture(3, lambda cfg: [HttpTarget(cfg).get_media(p) for p in
                                    ("../../etc/passwd", "....//....//etc/passwd",
                                     "..%2f..%2fetc%2fpasswd")])
    lines = [s.split("\r\n")[0] for s in seen]
    assert lines[0] == "GET /media/../../etc/passwd HTTP/1.1"
    assert lines[1] == "GET /media/....//....//etc/passwd HTTP/1.1"
    assert lines[2].lower() == "get /media/..%2f..%2fetc%2fpasswd http/1.1"


def test_no_cookie_bleed_and_unauthenticated_means_no_header():
    """Was: one shared cookie jar replayed the login cookie on every later request."""
    def drive(cfg):
        t = HttpTarget(cfg)
        r = t.login("alice", "alice-pw")
        assert r.body.get("sid") == "abc"          # Set-Cookie is found whatever its case
        t.admin_users("")
        t.get_resource("tok-1", 1)
    seen = _capture(3, drive)
    assert "cookie:" not in seen[1].lower() and "authorization:" not in seen[1].lower()
    assert "authorization: bearer tok-1" in seen[2].lower() and "cookie:" not in seen[2].lower()
    assert "x-sentinel-run:" in seen[0].lower() and "appsec-sentinel" in seen[0].lower()


def test_path_variants_and_evasion_headers():
    def drive(cfg):
        t = HttpTarget(cfg)
        for v in ("trailing-slash", "upper", "double-slash", "dot-segment", "matrix", "junk-query"):
            t.login("u", "p", evasion={"path": v})
        t.login("u", "p", evasion={"headers": {"X-Forwarded-For": "1.2.3.4"}, "form": True})
    seen = _capture(7, drive)
    targets = [s.split(" ")[1] for s in seen]
    assert targets[:6] == ["/auth/login/", "/AUTH/LOGIN", "//auth/login", "/auth/./login",
                           "/auth/login;sentinel=1", "/auth/login?sentinel=1"]
    assert "x-forwarded-for: 1.2.3.4" in seen[6].lower()
    assert "application/x-www-form-urlencoded" in seen[6].lower()


# ---------------------------------------------------------------------------
#  verdict helpers
# ---------------------------------------------------------------------------
def test_verdict_helpers():
    assert denied(Resp(403)) and denied(Resp(404)) and denied(Resp(302)) and denied(Resp(501))
    assert not denied(Resp(200)) and not denied(Resp(204))
    with pytest.raises(Inconclusive):
        denied(Resp(500))                           # a crash is not a refusal
    with pytest.raises(Unreachable):
        denied(Resp(0, {}, {"error": "boom"}))      # silence is not a refusal
    with pytest.raises(Inconclusive):
        refused(Resp(404))                          # unproven route
    assert refused(Resp(401))
    with pytest.raises(Inconclusive):
        expect_ok(Resp(404), "control")
    assert Resp(200, {"SET-COOKIE": "a=b"}).header("set-cookie") == "a=b"


def test_score_counts_unproven_checks_against_you():
    mk = lambda st, n: [Finding(f"{st.value}{i}", "c", "d", st) for i in range(n)]
    s = summarize(mk(Status.BLOCKED, 8) + mk(Status.INCONCLUSIVE, 2) + mk(Status.SKIPPED, 10))
    assert (s["score"], s["coverage"], s["verdict"]) == (80, 50, "INCOMPLETE")
    assert summarize(mk(Status.BLOCKED, 199) + mk(Status.LEAK, 1))["score"] == 99   # never rounds up to 100
    assert summarize(mk(Status.BLOCKED, 3) + mk(Status.LEAK, 1))["verdict"] == "FAIL"
    assert summarize(mk(Status.SKIPPED, 3))["verdict"] == "EMPTY"
    assert summarize(mk(Status.BLOCKED, 3))["verdict"] == "PASS"


# ---------------------------------------------------------------------------
#  bot-evasion checks: each one catches exactly its own bypass
# ---------------------------------------------------------------------------
class NaiveLimiterApp(SecureApp):
    """Secure in every way except that the per-client login limit is keyed on
    something the client controls (`weakness`)."""
    weakness = None

    def login(self, username, password, source_ip="203.0.113.9", xff=None, otp_ok=True,
              prev_session=None, evasion=None):
        ev = evasion or {}
        h = ev.get("headers") or {}
        ip_headers = set(automation.CLIENT_IP_HEADERS) | {"Forwarded"}
        if self.weakness == "ip-header" and ip_headers & set(h):
            source_ip = next(v for k, v in h.items() if k in ip_headers)
        if self.weakness == "fingerprint" and {"User-Agent", "X-Device-Id", "Cookie"} & set(h):
            source_ip += "|" + json.dumps(h, sort_keys=True)
        if self.weakness == "route" and ev.get("path"):
            source_ip += "|" + ev["path"]
        if self.weakness == "encoding" and (ev.get("form") or "X-HTTP-Method-Override" in h):
            source_ip += "|alt"
        return super().login(username, password, source_ip, xff, otp_ok, prev_session)


@pytest.mark.parametrize("weakness,caught_by", [
    ("ip-header", "BOT1"), ("fingerprint", "BOT2"), ("route", "BOT3"), ("encoding", "BOT4")])
def test_each_evasion_check_catches_its_own_bypass(weakness, caught_by):
    app_cls = type("App", (NaiveLimiterApp,), {"weakness": weakness})
    target = type("T", (ReferenceSecureTarget,), {"app_cls": app_cls})
    findings = run_catalogue(target, automation.build(cfgmod.Config()))
    st = {f.id: f for f in findings}
    assert st[caught_by].status == Status.LEAK and "bypassed" in st[caught_by].detail
    others = {i for i in ("BOT1", "BOT2", "BOT3", "BOT4") if i != caught_by}
    assert all(st[i].status == Status.BLOCKED for i in others), {i: st[i].status for i in others}


# ---------------------------------------------------------------------------
#  config
# ---------------------------------------------------------------------------
def _yaml(tmp_path, text):
    p = tmp_path / "t.yaml"
    p.write_text(text)
    return str(p)


def test_yaml_features_and_jwt_claims_are_loaded(tmp_path):
    """Was: features / jwt_iss / jwt_aud in the YAML were silently ignored."""
    cfg = cfgmod.load(_yaml(tmp_path, "features: [media_upload]\njwt_iss: https://real\n"
                                      "jwt_aud: real-aud\nthrottle_statuses: [429, 423]\n"))
    assert cfg.features == ["media_upload"] and cfg.jwt_iss == "https://real"
    assert cfg.jwt_aud == "real-aud" and cfg.throttle_statuses == [429, 423]
    caps = {c.value for c in HttpTarget(cfg).capabilities()}
    assert "oauth" not in caps and "mfa" not in caps and "media_upload" in caps


def test_missing_or_broken_config_is_an_error(tmp_path):
    """Was: a typo in the config path silently tested localhost with demo defaults."""
    with pytest.raises(cfgmod.ConfigError):
        cfgmod.load(str(tmp_path / "nope.yaml"))
    with pytest.raises(cfgmod.ConfigError):
        cfgmod.load(_yaml(tmp_path, "endpoints:\n  login: 'auth/login'\n"))
    with pytest.raises(cfgmod.ConfigError):
        cfgmod.load(_yaml(tmp_path, "target:\n  port: 99999\n"))


def test_unknown_keys_warn(tmp_path):
    cfg = cfgmod.load(_yaml(tmp_path, "endpoint:\n  login: 'POST /x'\ntarget:\n  prot: 1\n"))
    assert any("'endpoint'" in w for w in cfg.warnings)
    assert any("target.prot" in w for w in cfg.warnings)


def test_retarget_moves_jwks_and_absolute_endpoints_pass_through(tmp_path):
    cfg = cfgmod.load(_yaml(tmp_path, "target: {host: app, port: 8080}\n"
                                      "jwks_url: http://app:8080/jwks.json\n"
                                      "endpoints:\n  login: 'POST http://auth:9000/login'\n"))
    cfgmod.retarget(cfg, port=9090)
    assert cfg.jwks_url == "http://app:9090/jwks.json"
    assert cfg.url_for("/x") == "http://app:9090/x"
    assert cfg.url_for(cfg.spec("login")[1]) == "http://auth:9000/login"
    assert cfg.hosts() == {"app", "auth"}


def test_shipped_configs_load():
    for name in ("target.demo.yaml", "target.example.yaml", "target.videosanity.yaml"):
        cfg = cfgmod.load(os.path.join(ROOT, "config", name))
        assert not cfg.warnings, (name, cfg.warnings)


# ---------------------------------------------------------------------------
#  safety rails
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "10.1.2.3", "192.168.1.5", "172.20.0.4",
                                  "::1", "demo-target", "videosanity-videosanity-app-1",
                                  "host.docker.internal", "api.staging.test", "svc.cluster.local",
                                  "169.254.169.254"])
def test_internal_hosts_are_in_scope(host):
    assert classify_host(host, resolve=False)[0] == "internal"


@pytest.mark.parametrize("host", ["example.com", "8.8.8.8", "api.mycompany.io", "2001:4860:4860::8888"])
def test_public_hosts_need_an_allow_list_entry(host):
    assert classify_host(host, resolve=False)[0] == "public"
    cfg = cfgmod.Config(); cfg.host = host
    with pytest.raises(ScopeError):
        check_scope(cfg, resolve=False)
    cfg.safety["allowed_hosts"] = [host]
    assert check_scope(cfg, resolve=False)          # allowed, with a note


def test_scope_covers_absolute_endpoints_and_wildcards():
    cfg = cfgmod.Config()
    cfg.endpoints["login"] = "POST https://auth.mycompany.io/login"
    with pytest.raises(ScopeError):
        check_scope(cfg, resolve=False)
    cfg.safety["allowed_hosts"] = ["*.mycompany.io"]
    check_scope(cfg, resolve=False)


def test_request_budget():
    p = Pacer(max_requests=2)
    p.tick(); p.tick()
    with pytest.raises(BudgetExceeded):
        p.tick()


# ---------------------------------------------------------------------------
#  web UI
# ---------------------------------------------------------------------------
@pytest.fixture()
def ui():
    from sentinel.ui.server import make_server
    srv = make_server("127.0.0.1", 0)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    yield srv
    srv.shutdown()


def _ui(srv, path, body=None, token=True, host=None):
    req = urllib.request.Request(f"http://127.0.0.1:{srv.server_address[1]}{path}",
                                 data=None if body is None else json.dumps(body).encode())
    if token:
        req.add_header("X-Sentinel-Token", srv.token)
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if host:
        req.add_header("Host", host)
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def test_ui_api_is_locked_down(ui):
    assert _ui(ui, "/api/state", token=False)[0] == 403                 # no token
    assert _ui(ui, "/api/run", {"mode": "reference-secure"}, token=False)[0] == 403
    assert _ui(ui, "/api/state", host="evil.example")[0] == 421         # DNS rebinding
    code, body = _ui(ui, "/api/run", {"mode": "http", "host": "example.com", "port": 443})
    assert code == 400 and "outside the allowed scope" in body["error"]
    code, body = _ui(ui, "/api/run", {"mode": "http", "config": "../../etc/passwd"})
    assert code == 400 and "config/" in body["error"]
    assert _ui(ui, "/api/run", {"mode": "http", "host": "a b", "port": 1})[0] == 400


def test_ui_page_has_no_inline_script_and_carries_the_token(ui):
    with urllib.request.urlopen(f"http://127.0.0.1:{ui.server_address[1]}/") as r:
        html = r.read().decode()
        csp = r.headers["Content-Security-Policy"]
    assert ui.token in html and "__SENTINEL_TOKEN__" not in html
    assert "script-src 'self'" in csp and "unsafe-inline" not in csp
    assert "<script>" not in html and "onclick=" not in html


def test_ui_runs_and_scores_live(ui):
    code, defaults = _ui(ui, "/api/defaults")
    assert code == 200 and {s["name"] for s in defaults["suites"]} == set(BUILDERS)
    assert "config/target.demo.yaml" in defaults["configs"]
    code, body = _ui(ui, "/api/run", {"mode": "reference-secure", "suites": ["nov2026", "automation"]})
    assert code == 200, body
    assert _ui(ui, "/api/run", {"mode": "reference-secure"})[0] in (200, 400)   # 400 while busy
    for _ in range(200):
        run = _ui(ui, "/api/state")[1]["run"]
        if run["status"] != "running":
            break
        time.sleep(0.1)
    code, state = _ui(ui, "/api/state")
    history = state["history"]
    first = history[-1]
    assert first["score"] == 100 and first["verdict"] == "PASS"
    assert first["counts"]["BLOCKED"] == 18
