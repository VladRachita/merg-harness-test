"""
surface suite — what an anonymous visitor (or their scanner) can see and reach
before attacking anything: the first ten minutes of every real intrusion.

  SUR1  backend     no dotfiles, repositories, dumps or management endpoints served
  SUR2  backend     CORS does not hand credentialed access to any web page that asks
  FE1   front end   no dotfiles, repositories or dumps served            [frontend]
  FE2   front end   a Content-Security-Policy is sent                    [frontend]
  FE3   front end   the page cannot be framed (clickjacking)             [frontend]
  FE4   front end   X-Content-Type-Options: nosniff                      [frontend]
  FE5   front end   no server-side secrets shipped in the page or its JS [frontend]

The FE checks need a front-end port (`frontend.port` in the config, the
"Front-end port" field in the UI, or --frontend-port); without one they are
skipped. They look at what the front end SERVES. They do not click through the
app in a browser — that is the optional `xss` suite.

Exposed-file hits are confirmed by content, not by status: a single-page app
answers 200 with its index.html for ANY path, so "/.env returned 200" alone
means nothing; "/.env returned KEY=value lines" does.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from ..adapters.base import Capability
from ..config import Config
from .common import (Attack, Inconclusive, Leak, authed, expect_ok, reached, strings)

# (path, what a real hit looks like, what it is)
SENSITIVE = [
    ("/.env", r"(?m)^\s*[A-Z][A-Z0-9_]{2,}\s*=\s*\S", "environment file"),
    ("/.env.local", r"(?m)^\s*[A-Z][A-Z0-9_]{2,}\s*=\s*\S", "environment file"),
    ("/.env.production", r"(?m)^\s*[A-Z][A-Z0-9_]{2,}\s*=\s*\S", "environment file"),
    ("/.git/config", r"\[core\]", "git repository"),
    ("/.git/HEAD", r"^ref: refs/", "git repository"),
    ("/.aws/credentials", r"aws_access_key_id", "cloud credentials"),
    ("/.npmrc", r"_authToken", "registry token"),
    ("/.htpasswd", r"(?m)^[^:\s<]+:\$?[A-Za-z0-9./$]{12,}\s*$", "password file"),
    ("/id_rsa", r"-----BEGIN [A-Z ]*PRIVATE KEY-----", "private key"),
    ("/backup.sql", r"(?i)\b(CREATE TABLE|INSERT INTO)\b", "database dump"),
    ("/dump.sql", r"(?i)\b(CREATE TABLE|INSERT INTO)\b", "database dump"),
    ("/database.sql", r"(?i)\b(CREATE TABLE|INSERT INTO)\b", "database dump"),
    ("/docker-compose.yml", r"(?m)^services:\s*$", "deployment file"),
    ("/.DS_Store", r"Bud1", "directory listing metadata"),
    ("/WEB-INF/web.xml", r"<web-app", "application descriptor"),
    ("/web.config", r"<configuration", "server configuration"),
    ("/wp-config.php.bak", r"DB_PASSWORD", "configuration backup"),
    ("/phpinfo.php", r"<title>phpinfo\(\)|<h1[^>]*>PHP Version", "PHP diagnostics"),
    ("/server-status", r"<title>Apache Status|<h1>Apache Server Status", "server status page"),
    ("/actuator/env", r"propertySources", "Spring Boot actuator (environment)"),
    ("/actuator/configprops", r"\bbeans\b|\bcontexts\b", "Spring Boot actuator (config)"),
    ("/debug/vars", r"\bmemstats\b|\bcmdline\b", "Go expvar"),
    ("/debug/pprof/", r"\bgoroutine\b.*\bheap\b|/debug/pprof/", "Go profiler"),
]

# High-precision patterns only: things that are ALWAYS a mistake in a browser
# bundle. (Publishable keys — Stripe pk_live_, map/analytics keys — are not.)
SECRETS = [
    ("AWS access key id", r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"),
    ("private key", r"-----BEGIN (?:RSA |EC |OPENSSH |DSA |PGP )?PRIVATE KEY-----"),
    ("Stripe secret key", r"\bsk_live_[0-9A-Za-z]{20,}\b"),
    ("GitHub token", r"\b(?:ghp|gho|ghs|ghu)_[A-Za-z0-9]{36}\b|\bgithub_pat_[A-Za-z0-9_]{50,}\b"),
    ("Slack token", r"\bxox[baprs]-[0-9A-Za-z-]{10,}\b"),
    ("hard-coded secret", r"""(?i)\b(?:client[_-]?secret|api[_-]?secret|secret[_-]?key|"""
                          r"""jwt[_-]?secret|db[_-]?password)["']?\s*[:=]\s*["'][^"'\s]{12,}["']"""),
]


def _text(resp) -> str:
    return resp.body.get("_text") or " ".join(strings(resp.body))


def _is_html(text: str) -> bool:
    head = text[:300].lower()
    return "<!doctype html" in head or "<html" in head


def build(cfg: Config) -> list[Attack]:
    user = cfg.users["user"]
    A: list[Attack] = []

    def add(id, desc, check, requires=None):
        A.append(Attack(id, "surface", desc, check, set(requires or [])))

    # ---- exposed files / management endpoints ------------------------------
    def exposed(where):
        def check(t):
            reached(t.fetch_path(where, "/"), f"the {where} origin")
            hits = []
            for path, signature, what in SENSITIVE:
                r = reached(t.fetch_path(where, path))
                body = _text(r)
                if r.ok and re.search(signature, body) and not (
                        _is_html(body) and "<" not in signature):
                    hits.append(f"{path} ({what})")
            if hits:
                raise Leak(f"served to anyone on the {where}: " + ", ".join(hits[:6])
                           + (f" and {len(hits) - 6} more" if len(hits) > 6 else ""))
            return True
        return check

    add("SUR1", f"backend serves no dotfiles, dumps or management endpoints ({len(SENSITIVE)} paths)",
        exposed("backend"))

    # ---- CORS --------------------------------------------------------------
    def cors(t):
        tok = authed(t, user)
        trusted = urlsplit(cfg.frontend_origin or "https://app.example").hostname
        probes = [
            ("https://evil.example", False, "an unrelated site"),
            ("https://evil.example", True, "an unrelated site (preflight)"),
            ("null", False, "the 'null' origin (sandboxed iframe / local file)"),
            (f"https://{trusted}.evil.example", False, "a look-alike suffix of the real origin"),
            (f"https://evil{trusted}", False, "a look-alike prefix of the real origin"),
        ]
        for origin, preflight, what in probes:
            r = reached(t.cors_probe(tok, origin, preflight=preflight), "cross-origin request")
            allow = (r.header("access-control-allow-origin") or "").strip()
            creds = (r.header("access-control-allow-credentials") or "").strip().lower() == "true"
            if creds and allow in (origin, "*"):
                raise Leak(f"the API grants credentialed cross-origin access to {what}: "
                           f"Access-Control-Allow-Origin: {allow} with Allow-Credentials: true")
        return True
    add("SUR2", "CORS grants no credentialed access to arbitrary origins (reflection, null, "
        "look-alikes)", cors)

    # ---- front end ---------------------------------------------------------
    FE = [Capability.FRONTEND]

    def page(t):
        return expect_ok(t.fetch_path("frontend", "/"), "loading the front-end page")

    add("FE1", f"front end serves no dotfiles, repositories or dumps ({len(SENSITIVE)} paths)",
        exposed("frontend"), FE)

    def csp(t):
        r = page(t)
        return bool(r.header("content-security-policy")) or \
            bool(re.search(r"<meta[^>]+http-equiv=[\"']?Content-Security-Policy", _text(r), re.I))
    add("FE2", "front end sends a Content-Security-Policy", csp, FE)

    def framing(t):
        r = page(t)
        xfo = (r.header("x-frame-options") or "").strip().lower()
        return xfo in ("deny", "sameorigin") or \
            "frame-ancestors" in (r.header("content-security-policy") or "").lower()
    add("FE3", "front end cannot be framed by another site (clickjacking)", framing, FE)

    add("FE4", "front end sends X-Content-Type-Options: nosniff",
        lambda t: (page(t).header("x-content-type-options") or "").strip().lower() == "nosniff", FE)

    def no_secrets(t):
        assets = t.frontend_assets()
        if not assets or not any(text for _, text in assets):
            raise Inconclusive("the front end returned an empty page — nothing to scan")
        found = []
        for path, text in assets:
            for name, pattern in SECRETS:
                m = re.search(pattern, text or "")
                if m:
                    found.append(f"{name} in {path} ({m.group(0)[:4]}…)")
        if found:
            raise Leak("secrets shipped to every browser: " + "; ".join(found[:5]))
        return True
    add("FE5", "no server-side secrets in the front-end page or its scripts", no_secrets, FE)

    return A
