# appsec-sentinel

A standalone security test harness you point at your backend (host/port/path via
config) to run a catalogue of attacks — SQL injection, brute force, XSS, session
spoofing, privilege escalation, OAuth/PKCE abuse, account takeover, malicious
media uploads — and prove each one is blocked. It's the three harnesses from our
earlier work (media-injection, login/auth, expanded app-security) combined into
one project with pluggable **adapters** so the same suites run against the
in-process reference app *or* your real backend over HTTP.

Everything here was verified end-to-end: the self-test passes 48/48, the
deliberately-broken build is caught on 44, and the HTTP adapter was run against a
live backend over a real socket (48/48 blocked; 17 flaws found against the
broken backend).

---

## How it's wired

```
                 ┌─────────────── suites (the attacks) ───────────────┐
   CLI  ───────► │ access_control (44)   media_injection (4)   xss     │
                 └───────────────────────┬─────────────────────────────┘
                                          │ Target contract (adapters/base.py)
          ┌───────────────────────────────┼───────────────────────────────┐
   reference-secure            reference-vulnerable                 http  ──┼──► YOUR backend
   (self-test, no backend)     (negative control)         (config: host/port/path)
```

- **Suites** are written once against an abstract `Target`. They never hard-code HTTP.
- **Adapters** implement `Target`: the in-process reference apps, and `HttpTarget`
  which turns each operation into a real HTTP call against your backend.
- **Capabilities**: attacks needing a gray-box hook (disable a user, read a stored
  field, a DB probe, the signing key) are **SKIPPED** with a reason when that hook
  isn't configured — so a pure black-box run stays honest instead of faking a pass.

## Quick start

```bash
# 1. self-test — runs with no backend, proves the suites + runner work
python -m sentinel.cli run --target reference-secure --suite all

# 2. negative control — proves the suites actually catch flaws
python -m sentinel.cli run --target reference-vulnerable --suite all

# 3. against a backend over HTTP (see config below)
SENTINEL_CONFIG=config/target.yaml python -m sentinel.cli run --target http --suite all
```

## Docker — the two-container workflow

`docker compose up` builds one image and runs two containers on a shared network:
a backend and the harness, which reaches it by **service name + port** — exactly
how you point it at your own backend.

```bash
docker compose up --build --abort-on-container-exit     # harness vs. the bundled demo
# flip the demo to its broken build and watch the harness light up:
#   docker compose run -e DEMO_MODE=vulnerable demo-target   (or edit compose)
```

To test **your** backend instead of the demo:
1. Add your backend as a compose service (or point config at an external host).
2. Copy `config/target.example.yaml` → `config/target.yaml` and fill in
   `host`, `port`, `base_path`, the `endpoints` map, and the login `fields`.
3. Point the `sentinel` service's `SENTINEL_CONFIG` at it.

Your backend lives in its own project/repo/image; sentinel only needs to reach it
over the network and know its routes.

## Configuration (the input parameters)

Config comes from a YAML file (`--config` or `SENTINEL_CONFIG`) overlaid with env
vars. The two you asked about:

| Parameter | YAML | Env |
|-----------|------|-----|
| port | `target.port` | `SENTINEL_PORT` |
| base path | `target.base_path` | `SENTINEL_BASE_PATH` |
| host | `target.host` | `SENTINEL_HOST` |
| scheme | `target.scheme` | `SENTINEL_SCHEME` |
| any endpoint | `endpoints.<name>` | `SENTINEL_ENDPOINT_<NAME>` |

`config/target.example.yaml` documents every key (endpoints, field names, token
extraction path, OAuth client, seed users, feature flags, gray-box hooks).
`config/target.demo.yaml` is the working config for the bundled demo.

## What it runs

**access_control** (44 attacks): brute force (lockout, spraying, XFF-spoof, OTP,
enumeration), injection (SQLi, path traversal, SSRF), output headers (nosniff,
CSP, upload disposition), session/token (alg:none, RS256→HS256 confusion,
attacker-secret, expired, fixation, logout & password-change revocation, refresh
reuse, cookie flags, CSRF, token substitution), authorization (admin escalation,
IDOR, BOLA, method-confusion BFLA, mass assignment, disabled account),
OAuth2/PKCE (mandatory PKCE, exact redirect_uri, state, single-use & client-bound
code), account takeover (single-use/expiring reset, session revocation, email
re-verification), credential-theft mitigations (step-up re-auth, short tokens),
info disclosure (no stack traces, uniform responses, Host-header injection).

**media_injection** (4 checks): generates benign media carrying SQL strings in
filename/metadata/pixels plus malformed and content/extension-mismatch files,
uploads them, and asserts malformed/mismatched are rejected and valid-but-hostile
files create no injected DB row (and never crash or reflect the payload).

**xss** (headless browser, optional): loads pages in real Chromium and proves
injected payloads don't execute. Needs `requirements-xss.txt` + a browser; run via
`python -m sentinel.cli run --suite xss` or the standalone `sentinel/suites/xss.py`.

## October-2026 threat suite, fuzzer & campaign report

Three additions model this month's real app-level attacks and make a fast,
repeatable pass that produces an improvement report:

- **`oct2026` suite** (`--suite oct2026`): checks mapped to October-2026
  incidents — OAuth state/token confusion (Better Auth CVE-2026-110862),
  reset-endpoint SQLi & token replay (Metabase CVE-2026-72898), unauthenticated
  privileged ops (BeyondTrust CVE-2026-102764), media SSRF and malicious-media /
  transcode abuse (Plex CVE-2026-96652/54/55/56), verb-tampering on edge APIs,
  BOLA, and mass assignment. Validated against the reference controls
  (10 blocked on secure; 8 leaks on vulnerable).
- **`scripts/fuzz.py`**: a fast, config-driven input fuzzer — 87 payloads (SQLi,
  XSS, HTML-entity/encoding, traversal, command/template injection, NoSQL/LDAP,
  CRLF, and a large validation/boundary set) swept across login/registration/
  route fields, with response-signal detection (reflection, SQL errors, stack
  traces, auth bypass, 5xx, time-based latency). `--dry-run` shows the plan;
  signals are leads for human review, not confirmed vulns.
- **`scripts/campaign.py`**: runs the suites (plus the fuzzer against an HTTP
  target) on a loop for `--minutes N`, then writes
  `reports/appsec-report-<ts>.md` + a `.json` sidecar — strong vs. weak points
  (each weakness mapped to its technique and fix), coverage gaps, fuzzer signals,
  and a diff vs. the previous run so you can track improvement run-over-run.

```bash
# 0. confirm the config maps to videosanity's real routes (guards false PASS)
python scripts/preflight.py --config config/target.videosanity.yaml
# 1. a 10-minute threat-informed campaign that writes a Markdown report
SENTINEL_CONFIG=config/target.videosanity.yaml python scripts/campaign.py --target http --minutes 10
```

These are defensive, authorized tests; run them against a **disposable**
instance (they mutate state / create junk accounts).

## Exit codes & reports

The CLI exits non-zero if any attack is unblocked (gate CI with it). `--json PATH`
writes a machine-readable report. The `reference-vulnerable` target inverts the
verdict: it *expects* leaks and fails if it finds none (so the suites can't rot).

## Adapting to your backend

Open `sentinel/adapters/http_target.py`. Each method is a thin, documented mapping;
the spots most likely to need a tweak are marked `# ADAPT` (your client-IP header,
CSRF/step-up signals, multipart field name, the "import from URL" field). Most
real differences are just config: route paths, field names, and `token_json_path`.

Gray-box hooks (`hooks:` in config) are optional test-profile endpoints. Without
them, ~8 attacks report SKIPPED; the rest run black-box. With them (as the demo
shows), the full 48 run.

## Layout

```
appsec-sentinel/
├── sentinel/
│   ├── cli.py                      # entry point: sentinel run --target --suite
│   ├── config.py                   # YAML + env config (host/port/path/endpoints)
│   ├── adapters/
│   │   ├── base.py                 # Target contract + Capability enum
│   │   ├── http_target.py          # ← the real backend adapter (HTTP)
│   │   ├── reference_target.py     # in-process self-test + negative control
│   │   └── reference/              # the proven secure/vulnerable app models
│   ├── suites/
│   │   ├── access_control.py       # 44 attacks, capability-gated
│   │   ├── media_injection.py      # upload-injection checks
│   │   ├── xss.py                  # headless-browser XSS
│   │   └── common.py / jwt_forge.py / pkce.py
│   └── media/generator.py          # hostile-media corpus generator
├── demo_target/server.py           # bundled demo backend (stand-in for yours)
├── config/                         # target.example.yaml, target.demo.yaml
├── tests/test_suites.py            # pytest wrappers (self-test + negative control)
├── kotlin/                         # OPTIONAL JVM variant: JUnit + WebTestClient seam
├── Dockerfile  docker-compose.yml  requirements*.txt
```

## The Kotlin variant (optional)

`kotlin/` holds the same catalogue as a JUnit suite behind an `AppUnderTest` seam,
for teams that prefer to run security tests inside their Gradle build (wire it to
your Spring Security filter chain with `WebTestClient`). The Python project is the
primary, dockerized runner; the two don't need to be used together.

## Honesty notes

- Verified in this environment: the Python runner (self-test, negative control)
  and the HTTP adapter against a live socket. `docker compose config` validates;
  the image build and the Kotlin `gradle test` should be run on your machine
  (this sandbox blocks the base-image/Maven mirrors).
- A keylogger can't be tested server-side — the suites check its *mitigations*
  (step-up auth, short tokens). Full DOM-XSS coverage wants a DAST crawler
  alongside the headless checks here.
```
