#!/usr/bin/env python3
"""
xss_harness.py — a headless-browser XSS harness. Unlike a header check, it loads
the page in a real browser and proves injected payloads DO NOT EXECUTE.

How it detects execution: it installs hooks (window.__xss, overridden alert, a
sentinel image/error handler) before navigation, injects a battery of payloads
into a field, renders the page, and asserts none of the hooks fired.

Two modes:
  --demo    : self-contained. Serves a SAFE page (escapes output) and a
              VULNERABLE page (raw innerHTML) locally, and asserts the safe one
              does NOT execute while the vulnerable one DOES. The vulnerable page
              is the negative control — it proves the harness can see execution.
  (default) : point it at YOUR app with --base-url and a --reflect-path or a
              stored-content flow (see wire_in() and the README).

Run:
  pip install playwright && python -m playwright install chromium
  python3 xss_harness.py --demo
"""
import argparse
import sys

from playwright.sync_api import sync_playwright

PAYLOADS = [
    "<script>window.__xss('s')</script>",
    "<img src=x onerror=\"window.__xss('img')\">",
    "<svg onload=\"window.__xss('svg')\">",
    "\"><script>window.__xss('attr')</script>",
    "<body onload=window.__xss('body')>",
    "javascript:window.__xss('href')",
    "<iframe src=javascript:window.__xss('iframe')>",
    "<a href=\"javascript:window.__xss('a')\">x</a>",
]

# ---- the execution detector, installed before any page script runs ----------
DETECTOR_JS = """
window.__fired = [];
window.__xss = function(tag){ window.__fired.push(tag||'x'); };
window.alert = function(){ window.__fired.push('alert'); };
window.print = function(){ window.__fired.push('print'); };
"""
DETECTOR_HTML = "<script>" + DETECTOR_JS + "</script>"


def read_fired(page):
    page.wait_for_timeout(250)  # give async handlers (img onerror, etc.) a beat
    return list(page.evaluate("window.__fired || []"))


# ---- demo mode: safe vs vulnerable rendering ---------------------------------
import json as _json

SAFE_TEMPLATE = """<!doctype html><html><body>""" + DETECTOR_HTML + """<h1>Profile</h1>
<div id="out"></div>
<script>
 // SAFE: assigns as text, so markup is inert
 const v = __PAYLOAD_JSON__;
 document.getElementById('out').textContent = v;
</script></body></html>"""

VULN_TEMPLATE = """<!doctype html><html><body>""" + DETECTOR_HTML + """<h1>Profile</h1>
<div id="out"></div>
<script>
 // VULNERABLE: raw innerHTML -> payload can execute (event-handler vectors)
 const v = __PAYLOAD_JSON__;
 document.getElementById('out').innerHTML = v;
</script></body></html>"""


def render(template, payload):
    return template.replace("__PAYLOAD_JSON__", _json.dumps(payload))


def run_demo():
    print("=" * 66)
    print("XSS HARNESS — demo (safe vs vulnerable rendering)")
    print("=" * 66)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        safe_exec, vuln_exec = 0, 0
        for payload in PAYLOADS:
            # safe page
            ctx = browser.new_context(); page = ctx.new_page()
            page.set_content(render(SAFE_TEMPLATE, payload)); fired = read_fired(page)
            if fired:
                safe_exec += 1
                print(f"   ✗ SAFE page EXECUTED {fired} for: {payload[:40]}")
            ctx.close()
            # vulnerable page (negative control)
            ctx = browser.new_context(); page = ctx.new_page()
            page.set_content(render(VULN_TEMPLATE, payload)); fired = read_fired(page)
            if fired:
                vuln_exec += 1
            ctx.close()
        browser.close()

    print(f"\n  SAFE page   — payloads that executed: {safe_exec}/{len(PAYLOADS)} (want 0)")
    print(f"  VULN page   — payloads that executed: {vuln_exec}/{len(PAYLOADS)} (want >0 = teeth)")
    ok = safe_exec == 0 and vuln_exec > 0
    print("\nRESULT:", "PASS ✅" if ok else "FAIL ❌")
    return 0 if ok else 1


# ---- wire-in mode: test YOUR app --------------------------------------------
def run_against_app(base_url, reflect_path):
    """
    Reflected XSS: inject each payload into `reflect_path` (use {PAYLOAD} as the
    placeholder, e.g. '/search?q={PAYLOAD}') and assert nothing executes.

    For STORED XSS, replace this with your real flow:
      1) log in (page.goto(login), fill, submit) — or set an auth cookie/token
      2) POST the payload into a field (profile name, bio, comment, video caption)
      3) navigate to the page that renders it
      4) assert window.__fired is empty
    """
    import urllib.parse
    print(f"XSS HARNESS — reflected test against {base_url}{reflect_path}")
    executed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for payload in PAYLOADS:
            ctx = browser.new_context()
            ctx.add_init_script(DETECTOR_JS)          # installed BEFORE navigation
            page = ctx.new_page()
            url = base_url + reflect_path.replace("{PAYLOAD}", urllib.parse.quote(payload))
            page.goto(url, wait_until="networkidle")
            fired = read_fired(page)
            if fired:
                executed.append((payload, fired))
            ctx.close()
        browser.close()
    for payload, fired in executed:
        print(f"   ✗ EXECUTED {fired} for payload: {payload}")
    ok = not executed
    print("\nRESULT:", "PASS ✅ (no payload executed)" if ok else f"FAIL ❌ ({len(executed)} executed)")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--demo", action="store_true", help="run the self-contained safe-vs-vulnerable demo")
    ap.add_argument("--base-url", help="your app's base URL, e.g. https://localhost:8443")
    ap.add_argument("--reflect-path", default="/search?q={PAYLOAD}",
                    help="path with {PAYLOAD} placeholder for reflected-XSS testing")
    args = ap.parse_args()
    if args.demo or not args.base_url:
        sys.exit(run_demo())
    sys.exit(run_against_app(args.base_url, args.reflect_path))


if __name__ == "__main__":
    main()
