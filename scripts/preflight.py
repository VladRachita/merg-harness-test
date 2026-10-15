#!/usr/bin/env python3
"""
Preflight: prove the harness is actually talking to the target BEFORE you trust
a result. This exists because the suites treat any non-2xx reply (including a
404 on a wrong route, or a connection error) as "attack blocked" — so a config
whose routes don't match the backend prints a clean PASS while testing nothing.

What it does (all non-destructive):
  1. Checks the base URL is reachable at all.
  2. Probes each configured endpoint with OPTIONS and reports whether the route
     looks present (anything but 404) or missing (404 / unreachable).
  3. Does a REAL login with the configured credentials and checks that a token
     actually comes back at `token_json_path` — the linchpin: if this fails,
     every authenticated attack silently "passes".

Usage:
    SENTINEL_CONFIG=config/target.videosanity.yaml python scripts/preflight.py
    python scripts/preflight.py --config config/target.videosanity.yaml

Exit code is non-zero if the base URL is unreachable or login yields no token,
so you can gate a run on it:
    python scripts/preflight.py && python -m sentinel.cli run --target http --suite all
"""
from __future__ import annotations

import argparse
import os
import sys

# make `sentinel` importable whether run as `python scripts/preflight.py` or `-m`
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests

from sentinel import config as cfgmod
from sentinel.config import dotget


def _probe(session, method, url, timeout):
    """Return (status:int, note:str). status 0 means transport error."""
    try:
        r = session.request(method, url, timeout=timeout, allow_redirects=False)
        return r.status_code, ""
    except Exception as e:
        return 0, type(e).__name__


def main(argv=None):
    ap = argparse.ArgumentParser(description="appsec-sentinel target preflight")
    ap.add_argument("--config", help="path to YAML config (else $SENTINEL_CONFIG / defaults)")
    args = ap.parse_args(argv)

    cfg = cfgmod.load(args.config)
    s = requests.Session()
    s.verify = cfg.verify_tls
    base = cfg.base_url

    print(f"target base URL : {base}")
    print(f"token_json_path : {cfg.token_json_path}")
    print(f"auth_header     : {cfg.auth_header}\n")

    hard_fail = False

    # 1) base reachability -----------------------------------------------------
    st, note = _probe(s, "GET", base + "/", cfg.timeout_s)
    if st == 0:
        print(f"[FAIL] base URL unreachable ({note}). Is the container up and on "
              f"the same docker network? Is host/port correct?")
        hard_fail = True
    else:
        print(f"[ok]   base URL answered (HTTP {st}) — something is listening\n")

    # 2) per-route existence probe --------------------------------------------
    print("route probe (OPTIONS; 404 or conn-error => route likely wrong):")
    missing = []
    for name, spec in sorted(cfg.endpoints.items()):
        try:
            method, path = spec.split(" ", 1)
        except ValueError:
            print(f"   [!] {name:16} malformed endpoint spec: {spec!r}")
            continue
        # substitute any {param} with a harmless placeholder for the probe
        probe_path = path
        while "{" in probe_path and "}" in probe_path:
            probe_path = probe_path[:probe_path.index("{")] + "1" + probe_path[probe_path.index("}") + 1:]
        st, note = _probe(s, "OPTIONS", base + probe_path, cfg.timeout_s)
        if st == 0:
            verdict = f"conn-error ({note})"
            missing.append(name)
        elif st == 404:
            verdict = "404 — route MISSING?"
            missing.append(name)
        else:
            verdict = f"HTTP {st} — present"
        print(f"   {name:16} {method:6} {path:32} {verdict}")
    print()

    # 3) the linchpin: does login actually return a token? --------------------
    f = cfg.fields
    u = cfg.users.get("user", {})
    try:
        method, path = cfg.endpoints["login"].split(" ", 1)
        payload = {f["username"]: u.get("username"), f["password"]: u.get("password")}
        if "otp" in f:
            payload[f["otp"]] = "000000"
        r = s.request(method, base + path, json=payload, timeout=cfg.timeout_s,
                      allow_redirects=False)
        body = {}
        try:
            body = r.json()
        except Exception:
            body = {}
        token = dotget(body, cfg.token_json_path) if isinstance(body, dict) else None
        if token:
            print(f"[ok]   login returned a token at '{cfg.token_json_path}' "
                  f"(HTTP {r.status_code}) — authenticated tests will be real")
        else:
            print(f"[FAIL] login did NOT yield a token (HTTP {r.status_code}). "
                  f"Check the login route, field names, test creds, and "
                  f"token_json_path. Until this works, every authenticated "
                  f"attack will silently report BLOCKED.")
            hard_fail = True
    except Exception as e:
        print(f"[FAIL] login probe crashed: {e!r}")
        hard_fail = True

    if missing:
        print(f"\n{len(missing)} route(s) look missing: {', '.join(missing)}")
        print("Fix these in the config before trusting a result — a missing "
              "route is counted as 'blocked'.")

    print("\nPREFLIGHT:", "FAIL ❌ — do not trust a run yet" if hard_fail
          else "basic plumbing looks OK ✅ (still verify the route list above)")
    return 1 if hard_fail else 0


if __name__ == "__main__":
    sys.exit(main())
