"""
The web UI: point the harness at a backend port, start a run, watch it live.

    python -m sentinel.ui                 # http://127.0.0.1:8090
    python -m sentinel.cli ui --port 8090

Standard library only (no extra dependencies), one page, polled JSON.

This page can launch attacks, so it is locked down the way the harness asks the
apps it tests to be:
  * it binds to loopback unless told otherwise (in Docker: publish the port on
    127.0.0.1 only);
  * every /api call needs the per-process token embedded in the page, sent in a
    custom header — a hostile web page open in the same browser can neither read
    the token (same-origin policy) nor send that header cross-site (CSRF);
  * the Host header must be a name the UI is served under (DNS-rebinding guard);
  * it can only load configs from the config/ directory, and every run still
    goes through the scope guard (sentinel/safety.py): internal targets only,
    unless a host is allow-listed in the config.
"""
from __future__ import annotations

import datetime as _dt
import glob
import json
import os
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from .. import config as cfgmod
from .. import engine
from ..adapters.base import Unreachable
from ..safety import ScopeError
from ..suites import BUILDERS, SUITE_INFO
from ..suites.common import run_catalogue, summarize

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CONFIG_DIR = os.path.join(ROOT, "config")
PAGE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
MAX_BODY = 64 * 1024
HISTORY = 12


def _now():
    return _dt.datetime.now().astimezone().isoformat(timespec="seconds")


def list_configs() -> list:
    return sorted(os.path.relpath(p, ROOT).replace(os.sep, "/")
                  for p in glob.glob(os.path.join(CONFIG_DIR, "*.y*ml")))


class BadRequest(Exception):
    pass


def build_config(req: dict):
    """A Config from the form: a config file (optional) + host/port overrides."""
    mode = req.get("mode") or "http"
    if mode not in engine.TARGETS:
        raise BadRequest(f"unknown mode: {mode}")
    name = (req.get("config") or "").strip()
    if name and name not in list_configs():
        raise BadRequest("config must be one of the files in config/")
    try:
        cfg = cfgmod.load(os.path.join(ROOT, name)) if name else cfgmod.load(None)
        if mode == "http":
            port = req.get("port")
            cfgmod.retarget(cfg, host=req.get("host"), port=port if port not in ("", None) else None,
                            scheme=req.get("scheme"),
                            base_path=req.get("base_path") if "base_path" in req else None)
        cfgmod.validate(cfg)
    except cfgmod.ConfigError as e:
        raise BadRequest(str(e))
    suites = [s for s in (req.get("suites") or []) if s in BUILDERS] or list(BUILDERS)
    return mode, cfg, suites


class Runs:
    """The single current run, plus a short history. All access under one lock."""

    def __init__(self):
        self.lock = threading.Lock()
        self.run = None
        self.history = []
        self._stop = threading.Event()
        self._thread = None

    def snapshot(self):
        with self.lock:
            return (json.loads(json.dumps(self.run)) if self.run else None), list(self.history)

    def start(self, req: dict):
        mode, cfg, suites = build_config(req)
        with self.lock:
            if self.run and self.run["status"] == "running":
                raise BadRequest("a run is already in progress")
        try:
            factory, attacks, notes = engine.prepare(mode, cfg, suites)
        except ScopeError as e:
            raise BadRequest(str(e))
        if not attacks:
            raise BadRequest("no checks selected")
        run = {
            "id": secrets.token_hex(4), "status": "running", "mode": mode,
            "target": engine.target_label(mode, cfg), "config": req.get("config") or "",
            "suites": suites, "started": _now(), "finished": None, "t0": time.time(),
            "elapsed": 0.0, "total": len(attacks), "done": 0, "current": None,
            "findings": [], "summary": summarize([]), "notes": notes + list(cfg.warnings),
            "error": None, "requests": 0,
        }
        self._stop.clear()
        with self.lock:
            self.run = run
        self._thread = threading.Thread(target=self._work, args=(run, mode, cfg, suites,
                                                                  factory, attacks), daemon=True)
        self._thread.start()
        return run["id"]

    def stop(self):
        self._stop.set()

    def _work(self, run, mode, cfg, suites, factory, attacks):
        done = []

        def on_start(atk):
            with self.lock:
                run["current"] = {"id": atk.id, "desc": atk.desc, "suite": atk.suite}

        def on_result(f):
            done.append(f)
            with self.lock:
                run["findings"].append(engine.finding_dict(f))
                run["done"] = len(done)
                run["summary"] = summarize(done)
                run["elapsed"] = round(time.time() - run["t0"], 1)
                run["requests"] = getattr(factory(), "requests_sent", 0) if mode == "http" else 0

        status, error = "done", None
        try:
            findings = run_catalogue(factory, attacks, on_start=on_start, on_result=on_result,
                                     should_stop=self._stop.is_set)
            if self._stop.is_set():
                status = "stopped"
        except Exception as e:                      # the runner itself failed
            findings, status, error = done, "error", repr(e)
        with self.lock:
            run.update(status=status, error=error, current=None, finished=_now(),
                       elapsed=round(time.time() - run["t0"], 1), summary=summarize(findings),
                       report=engine.report(mode, cfg, suites, findings),
                       exit_code=engine.exit_code(mode, cfg, findings))
            s = run["summary"]
            self.history.insert(0, {"id": run["id"], "when": run["finished"], "target": run["target"],
                                    "mode": mode, "status": status, "score": s["score"],
                                    "verdict": s["verdict"], "counts": s["counts"],
                                    "coverage": s["coverage"]})
            del self.history[HISTORY:]


def preflight(req: dict) -> dict:
    """Is something listening, and do the configured credentials log in?"""
    mode, cfg, _ = build_config(req)
    if mode != "http":
        return {"ok": True, "lines": [["ok", "Built-in reference app — nothing to connect to."]]}
    lines = []
    try:
        factory, _, notes = engine.prepare(mode, cfg, [])
    except ScopeError as e:
        return {"ok": False, "lines": [["fail", str(e).split("\n")[0]]]}
    lines += [["note", n] for n in notes]
    t = factory()
    try:
        r = t._call("GET", "/")
        lines.append(["ok", f"{cfg.base_url} answered (HTTP {r.status})"])
    except Unreachable as e:
        return {"ok": False, "lines": lines + [["fail", f"Nothing answered at {cfg.base_url} — "
                f"is the backend up, on this network, and is the port right? ({e})"]]}
    ok = True
    try:
        u = cfg.users["user"]
        r = t.login(u["username"], u["password"])
        if r.body.get("access_token"):
            lines.append(["ok", f"Login as '{u['username']}' returned a token"])
            own = t.get_resource(r.body["access_token"], u["id"])
            if own.ok:
                lines.append(["ok", "That token can read the user's own resource"])
            else:
                ok = False
                lines.append(["fail", f"…but reading the user's own resource returned HTTP "
                              f"{own.status}: check endpoints.resource and auth_header"])
        else:
            ok = False
            lines.append(["fail", f"Login as '{u['username']}' gave no token (HTTP {r.status}): "
                          f"check endpoints.login, fields, users and token_json_path"])
    except Unreachable as e:
        ok = False
        lines.append(["fail", str(e)])
    return {"ok": ok, "lines": lines}


def defaults(config_hint=None) -> dict:
    configs = list_configs()
    chosen = config_hint if config_hint in configs else ""
    if not chosen:
        env = os.environ.get("SENTINEL_CONFIG", "")
        rel = os.path.relpath(os.path.abspath(env), ROOT).replace(os.sep, "/") if env else ""
        chosen = rel if rel in configs else ""
    out = {"configs": configs, "config": chosen, "targets": list(engine.TARGETS),
           "suites": [], "config_targets": {}}
    base = cfgmod.Config()
    for name, build in BUILDERS.items():
        out["suites"].append({"name": name, "info": SUITE_INFO.get(name, ""),
                              "count": len(build(base))})
    for c in [""] + configs:
        try:
            cfg = cfgmod.load(os.path.join(ROOT, c)) if c else cfgmod.load(None)
            out["config_targets"][c] = {"host": cfg.host, "port": cfg.port, "scheme": cfg.scheme,
                                        "base_path": cfg.base_path}
            if not c and os.environ.get("SENTINEL_UI_DEFAULT_HOST") and "SENTINEL_HOST" not in os.environ:
                # in a container "localhost" is the harness itself; prefill the
                # address of the machine running docker instead
                out["config_targets"][c]["host"] = os.environ["SENTINEL_UI_DEFAULT_HOST"]
        except cfgmod.ConfigError as e:
            out["config_targets"][c] = {"error": str(e)}
    return out


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "sentinel-ui"

    def log_message(self, *a):
        pass

    # ---- plumbing ----------------------------------------------------------
    def _send(self, status, body, ctype="application/json", extra=None):
        data = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("Content-Security-Policy",
                         "default-src 'none'; script-src 'self'; style-src 'self'; "
                         "connect-src 'self'; img-src 'self' data:; base-uri 'none'; "
                         "form-action 'none'; frame-ancestors 'none'")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(data)

    def _host_ok(self):
        host = (self.headers.get("Host") or "").rsplit(":", 1)[0].strip("[]").lower()
        return host in self.server.allowed_hosts

    def _authorized(self):
        return secrets.compare_digest(self.headers.get("X-Sentinel-Token", ""), self.server.token)

    def _json(self):
        n = int(self.headers.get("Content-Length", 0) or 0)
        if n > MAX_BODY:
            raise BadRequest("request too large")
        if not (self.headers.get("Content-Type") or "").startswith("application/json"):
            raise BadRequest("JSON body required")
        try:
            data = json.loads(self.rfile.read(n) or b"{}")
        except ValueError:
            raise BadRequest("malformed JSON")
        if not isinstance(data, dict):
            raise BadRequest("JSON object required")
        return data

    # ---- routes ------------------------------------------------------------
    def do_GET(self):
        if not self._host_ok():
            return self._send(421, {"error": "unknown Host"})
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            with open(PAGE, "rb") as fh:
                html = fh.read().replace(b"__SENTINEL_TOKEN__", self.server.token.encode())
            return self._send(200, html, "text/html; charset=utf-8")
        if path in ("/app.js", "/app.css"):
            ctype = "text/javascript" if path.endswith(".js") else "text/css"
            with open(os.path.join(os.path.dirname(PAGE), path.lstrip("/")), "rb") as fh:
                return self._send(200, fh.read(), ctype + "; charset=utf-8")
        if path == "/healthz":
            return self._send(200, {"ok": True})
        if not path.startswith("/api/"):
            return self._send(404, {"error": "not found"})
        if not self._authorized():
            return self._send(403, {"error": "missing or wrong token — reload the page"})
        runs = self.server.runs
        if path == "/api/state":
            run, history = runs.snapshot()
            if run:
                run.pop("report", None); run.pop("t0", None)
            return self._send(200, {"run": run, "history": history})
        if path == "/api/defaults":
            return self._send(200, defaults(self.server.config_hint))
        if path == "/api/report":
            run, _ = runs.snapshot()
            if not run or not run.get("report"):
                return self._send(404, {"error": "no finished run yet"})
            name = f"sentinel-report-{run['id']}.json"
            return self._send(200, json.dumps(run["report"], indent=2).encode(), "application/json",
                              {"Content-Disposition": f'attachment; filename="{name}"'})
        return self._send(404, {"error": "not found"})

    def do_POST(self):
        if not self._host_ok():
            return self._send(421, {"error": "unknown Host"})
        if not self._authorized():
            return self._send(403, {"error": "missing or wrong token — reload the page"})
        runs = self.server.runs
        try:
            if self.path == "/api/run":
                return self._send(200, {"ok": True, "id": runs.start(self._json())})
            if self.path == "/api/stop":
                runs.stop()
                return self._send(200, {"ok": True})
            if self.path == "/api/preflight":
                return self._send(200, preflight(self._json()))
        except BadRequest as e:
            return self._send(400, {"error": str(e)})
        return self._send(404, {"error": "not found"})


class Server(ThreadingHTTPServer):
    daemon_threads = True


def make_server(listen="127.0.0.1", port=8090, config_hint=None, allowed_hosts=None):
    srv = Server((listen, port), Handler)
    srv.token = secrets.token_urlsafe(24)
    srv.runs = Runs()
    srv.config_hint = config_hint
    names = {"localhost", "127.0.0.1", "::1", listen.lower()}
    extra = allowed_hosts or os.environ.get("SENTINEL_UI_HOSTS", "")
    names |= {h.strip().lower() for h in (extra.split(",") if isinstance(extra, str) else extra)
              if h.strip()}
    srv.allowed_hosts = names - {"0.0.0.0", "::"}
    return srv


def serve(listen="127.0.0.1", port=8090, config_hint=None):
    srv = make_server(listen, port, config_hint)
    shown = "localhost" if listen in ("127.0.0.1", "0.0.0.0", "::") else listen
    print(f"appsec-sentinel UI on http://{shown}:{srv.server_address[1]}  (bound to {listen})",
          flush=True)
    if listen not in ("127.0.0.1", "::1", "localhost"):
        print("  note: bound beyond loopback — publish this port on 127.0.0.1 only; anyone who "
              "can open the page can start a run.", flush=True)
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0
