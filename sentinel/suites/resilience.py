"""
resilience suite — does the backend stay up, and stay fast, when it is fed
hostile SHAPES and a burst of traffic? ("handles load and spam correctly")

This is a bounded resilience test for a backend you own, not a flood: eight
single pathological requests and one small concurrent burst (60 requests, 12 at
a time by default — set `load:` in the config). Nothing here can take down a
healthy service; all of it takes down a service that has no limits.

  RES1  oversize       a 1 MB field
  RES2  deep-json      5,000 levels of nesting (parser recursion)
  RES3  wide-json      20,000 keys in one object
  RES4  gzip-bomb      16 MB that arrives as a few KB of gzip
  RES5  bad-encoding   Content-Encoding: br with a garbage body
  RES6  bad-charset    a compression codec named as the JSON charset
  RES7  many-parts     a multipart body with 2,000 parts
  RES8  long-accept    an Accept header with 2,000 media ranges
  RES9  burst          N concurrent requests: no 5xx, no dropped connections,
                       p95 latency within `load.p95_ms`, healthy afterwards

For RES1–8 the backend may refuse the request (4xx) or handle it — either is
fine — but it must do so quickly, without a 5xx, and still be answering normal
requests afterwards. Shedding load with 429/503 during the burst is correct
behaviour, not a failure.

Why these shapes — the parser/decoder resource-exhaustion bugs of Oct 2026:
  decompression  Django REST framework CVE-2026-114136 (a client-named codec
                 such as bz2_codec makes a decompression bomb, 21 Oct);
                 Brotli decoder CVE-2026-111497 (KEV 27 Oct) — RES4/5/6
  multipart      aiohttp CVE-2026-111066 (19 Oct), @hapi/content
                 CVE-2026-119202 (29 Oct), Payload CVE-2026-105854 (6 Oct) — RES7
  headers        Django REST framework CVE-2026-114138 (crafted Accept, 21 Oct) — RES8
  allocation     ASP.NET Core CVE-2026-70181 (13 Oct) — RES1/2/3
RES5/RES6 send harmless garbage, not the crafted streams behind those CVEs: they
only check that an unexpected encoding is refused instead of being fed to a
decoder. Keeping the runtime patched is what fixes the decoder bugs themselves.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

from ..adapters.base import STRESS_KINDS, Unreachable
from ..config import Config
from .common import Attack, STRESS, Inconclusive, Leak

DESCRIPTIONS = {
    "oversize": "a 1 MB field is refused or handled quickly",
    "deep-json": "5,000-level nested JSON doesn't crash the parser",
    "wide-json": "a 20,000-key JSON object is refused or handled quickly",
    "gzip-bomb": "a 16 MB gzip bomb is not inflated into a failure (DRF CVE-2026-114136)",
    "bad-encoding": "an unexpected Content-Encoding is refused, not decoded (cf. CVE-2026-111497)",
    "bad-charset": "a codec named as the JSON charset is refused (DRF CVE-2026-114136)",
    "many-parts": "a 2,000-part multipart body is handled cheaply (aiohttp CVE-2026-111066)",
    "long-accept": "a 2,000-entry Accept header is handled cheaply (DRF CVE-2026-114138)",
}


def build(cfg: Config) -> list[Attack]:
    load = cfg.load
    slow_s = float(load.get("max_latency_ms", 5000)) / 1000.0
    A: list[Attack] = []

    def probe(t):
        """One ordinary request; (status, seconds). status 0 = no answer."""
        t0 = time.monotonic()
        try:
            return t.buggy_endpoint("1").status, time.monotonic() - t0
        except Unreachable:
            return 0, time.monotonic() - t0

    def healthy_before(t):
        status, took = probe(t)
        if status == 0 or status >= 500:
            raise Inconclusive(f"the backend isn't healthy before the test (HTTP {status}) — "
                               f"nothing can be concluded from stressing it")

    def recovers(t, what):
        """After the stress, an ordinary request must be answered again (allow a
        moment: answering 429/503 while it sheds load is fine)."""
        status = 0
        for _ in range(6):
            status, took = probe(t)
            if status and status < 500:
                return
            time.sleep(0.5)
        raise Leak(f"after {what} the backend stopped answering normal requests (HTTP {status})")

    def stress(kind):
        def check(t):
            healthy_before(t)
            t0 = time.monotonic()
            try:
                r = t.stress_input(kind)
            except Unreachable:
                # the server hung up on us: acceptable, IF it is still alive
                recovers(t, f"dropping the '{kind}' request")
                return True
            took = time.monotonic() - t0
            if r.status >= 500 and r.status != 501:
                raise Leak(f"HTTP {r.status} on '{kind}' input — the request reached code that "
                           f"could not cope with it")
            if took > slow_s:
                raise Leak(f"one '{kind}' request tied up the server for {took:.1f}s "
                           f"(limit {slow_s:.0f}s)")
            recovers(t, f"the '{kind}' request")
            return True
        return check

    for i, kind in enumerate(STRESS_KINDS, 1):
        A.append(Attack(f"RES{i}", "resilience", DESCRIPTIONS[kind], stress(kind), set(), STRESS))

    def burst(t):
        healthy_before(t)
        n, workers = int(load["burst_requests"]), int(load["concurrency"])
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(lambda _: probe(t), range(n)))
        dropped = sum(1 for s, _ in results if s == 0)
        errors = sum(1 for s, _ in results if s >= 500 and s != 503)
        times = sorted(e for _, e in results)
        p95_ms = times[max(0, int(len(times) * 0.95) - 1)] * 1000
        recovers(t, f"a burst of {n} requests")
        if errors or dropped:
            raise Leak(f"under {n} requests ({workers} at a time): {errors} server error(s), "
                       f"{dropped} dropped connection(s)")
        if p95_ms > float(load["p95_ms"]):
            raise Leak(f"p95 latency {p95_ms:.0f} ms under a burst of {n} "
                       f"(limit {load['p95_ms']} ms)")
        return True
    A.append(Attack(f"RES{len(STRESS_KINDS) + 1}", "resilience",
                    f"a burst of {load['burst_requests']} concurrent requests: no 5xx, no drops, "
                    f"p95 within {load['p95_ms']} ms", burst, set(), STRESS))

    return A
