# appsec-sentinel

A standalone security test harness you point at your backend (host/port/path via
config, CLI flag or the web UI) to run a catalogue of attacks — SQL injection,
brute force, bot evasion, session spoofing, privilege escalation, OAuth/PKCE
abuse, account takeover, malicious uploads, hostile input shapes and a load
burst — and **prove** each one is blocked.

"Prove" is the point. A check only reports ✓ when a legitimate request worked
*and* the attack was refused. A wrong route, a locked-out test account or a dead
container is reported as **inconclusive**, never as a pass.

```
96 checks · 7 suites · 9 flows     secure reference build:      96 / 96 blocked
                                   vulnerable reference build:   96 / 96 leak   (every check has teeth)
```

---

## Quick start

```bash
pip install -r requirements.txt        # + ffmpeg on PATH for the media suite

# 1. self-test — no backend needed; proves the suites + runner work
python -m sentinel.cli run --target reference-secure --suite all

# 2. negative control — every check must catch the deliberately broken build
python -m sentinel.cli run --target reference-vulnerable --suite all

# 3. your app: give it the backend port, and the front-end port if there is one
python -m sentinel.cli run --target http --config config/target.yaml \
    --port 8080 --frontend-port 3000 --suite all

# 4. only some flows
python -m sentinel.cli run --target http --config config/target.yaml --port 8080 \
    --flow login registration upload

# 5. or do all of that in the web UI
python -m sentinel.ui                  # http://127.0.0.1:8090
```

## The web UI

Enter the **backend port** and the **front-end port**, tick the flows you want
attacked — login, registration, uploads, sessions, password reset, data access,
OAuth, front end, load — and press **Start run**. Each check lands live: a score
out of 100, a card per flow, the reason for every leak or inconclusive check,
and the fix for every leak.

```bash
python -m sentinel.ui                              # local
docker compose -f docker-compose.ui.yml up --build # in Docker → http://localhost:8090
```

What the page does, top to bottom:

- **Backend (API)** — host, port, scheme, base path.
- **Front end (web)** — host and port of the web app, if it has its own. With a
  port set, the front-end checks run (exposed files, security headers, secrets
  in its JavaScript). Tick *Send the API attacks through the front-end port* to
  hit the API the way a browser does, through the front end's proxy, and give
  the path it proxies under (e.g. `/api`).
- **Flows to attack** — pick by what you want tested, not by suite.
- **Try the flows** — before attacking anything, the harness performs each flow
  once, legitimately: reach the backend and the front end, log in, read the
  user's own data, register an account, upload a file, log in as admin. Each
  line is ✓, ✗ with the status and what to check, or skipped. A flow that can't
  be done legitimately can't be attacked meaningfully, so get these green first.
- **Flow settings** — the route and field names for login, registration and
  upload, where the token is in the login response, how it is sent, the route
  only its owner may read, and the test accounts. Edit a line, press *Try the
  flows* again, repeat until green — no YAML editing. **Save config** writes the
  result to `config/ui.<name>.yaml` (git-ignored; rename it to
  `target.<name>.yaml` to share it).
- **By flow / results** — click a flow card to see only its checks; filter by
  outcome; **Download JSON report** saves the finished run.
- **What to test** also offers the two built-in reference apps, to see what a
  clean and a broken result look like.

Reaching your app from the UI container (see `docker-compose.ui.yml`):
ports published on your machine → host `host.docker.internal` + those ports;
containers in another compose project → join its network and use the service
names + internal ports.

The page can launch attacks, so it is locked down: bound to loopback (published
on `127.0.0.1` only in the compose file), every API call needs a per-process
token, the `Host` header is checked, it can only write `config/ui.*.yaml`, and
the scope guard below still applies.
**Do not expose port 8090 to a network other people can reach.**

## How it's wired

```
        CLI · web UI · campaign runner
                    │
          ┌─────────┴───────── suites (the attacks) ─────────────────────┐
          │ access_control  media_injection  oct2026  nov2026            │
          │ automation (bots/spam)  resilience (load)  surface (front end) │
          └─────────┬────────────────────────────────────────────────────┘
                    │  Target contract (adapters/base.py)
   ┌────────────────┼──────────────────────────┐
 reference-secure   reference-vulnerable       http ──► YOUR backend
 (self-test)        (negative control)         (config: host/port/path)
```

- **Suites** are written once against an abstract `Target`. They never hard-code HTTP.
- **Adapters** implement `Target`: the in-process reference apps, and `HttpTarget`
  which turns each operation into a real HTTP call against your backend.
- **Capabilities**: checks needing a gray-box hook (disable a user, read a stored
  field, a DB probe, the signing key) or an optional feature are **skipped** with
  a reason when it isn't configured.

## Reading a result

| Mark | Status | Meaning |
|---|---|---|
| `✓` | BLOCKED | Proven: the legitimate request worked and the attack was refused |
| `✗ LEAK` | LEAK | The attack was accepted. The line below says what was seen; the UI/report add the fix |
| `? n/a` | INCONCLUSIVE | Nothing was proven — a control request failed, the backend didn't answer, it returned a 5xx. The reason names what to fix. **Not a pass** |
| `– skip` | SKIPPED | A capability/feature isn't configured, or the control doesn't apply (e.g. cookie flags on a token-only API) |
| `! err` | ERROR | The check itself crashed (harness or config bug) |

**Score** = the share of checks that *ran* which were proven blocked. Leaks,
errors and inconclusive checks all count against it; skipped checks lower
**coverage** instead. A dead backend scores 0, not 100.

**Exit codes** (gate CI on them): `0` everything that ran was proven blocked ·
`1` a leak or a crashed check · `2` no leak, but something is unproven, the
config is unusable, or the target is out of scope. For `reference-vulnerable`
the meaning flips: `0` only if *every* check leaked.

## What it runs

| Suite | Checks | What it asserts |
|---|---|---|
| `access_control` | 48 | Brute force & lockout, SQLi/traversal/SSRF, security headers, JWT forgery (alg:none, key confusion, attacker secret, expiry, a token naming its own key), session fixation/revocation/refresh reuse/cookie flags/CSRF, admin escalation, IDOR/BOLA, verb tampering, mass assignment, weak passwords at sign-up, OAuth2/PKCE, reset-token and e-mail takeover, unauthenticated and abusive uploads, step-up, info leaks |
| `media_injection` | 4 | Malformed and disguised media are refused; SQL in file metadata creates no DB row and is never echoed |
| `oct2026` | 10 | Techniques exploited in October 2026: token-type confusion, reset-endpoint injection, unauthenticated privileged ops, SSRF in 16 spellings, disguised uploads, verb tampering, BOLA, mass assignment |
| `nov2026` | 12 | Flaws disclosed mid-Oct → early Nov 2026: empty-HMAC-key tokens, key-confusion encodings, tokens surviving logout / password change, deactivated accounts signing in, MFA skipped on reset or login, password change without step-up, credential fields in responses, spoofed identity headers, tokens without a grant, stolen authorization codes |
| `automation` | 6 | **Bots / scripted agents / spam** (OWASP Automated Threats): the login limit can't be dodged by rotating client-IP headers, User-Agent/device ids, route spellings or body encoding; sign-up bursts and reset-token guessing are throttled |
| `resilience` | 9 | **Load and hostile input shapes**: 1 MB field, 5,000-deep JSON, 20,000-key JSON, gzip bomb, bad encoding/charset, 2,000-part multipart, huge `Accept` header — refused or handled quickly, no 5xx, still healthy after; plus a 60-request concurrent burst with a p95 latency limit |
| `surface` | 7 | **What an anonymous visitor can reach**: no `.env`, `.git`, dumps or management endpoints served (23 paths, on backend and front end, confirmed by content); CORS grants no credentialed access to arbitrary origins; the front end sends CSP, anti-framing and nosniff headers and ships no server-side secrets in its JavaScript |
| `xss` | optional | Headless Chromium proves injected payloads don't execute. Needs `requirements-xss.txt`; run with `--suite xss` |

The same 96 checks are also grouped into **flows** — what the UI's checkboxes and
`--flow` select:

| Flow | Checks | |
|---|---|---|
| `login` | 17 | brute force, lockout, bots dodging the limit, SQL injection, MFA |
| `registration` | 5 | privilege fields at sign-up, weak passwords, sign-up bursts |
| `upload` | 12 | malicious, disguised and oversized files, anonymous uploads, SSRF via import-by-URL |
| `session` | 18 | forged tokens, logout and revocation, CSRF, account changes |
| `reset` | 8 | reset-token reuse and guessing, injection, enumeration |
| `access` | 9 | other users' data, admin endpoints, spoofed identity |
| `oauth` | 8 | PKCE, redirect URI, code replay and theft |
| `frontend` | 7 | exposed files, CORS, front-end headers, secrets in JavaScript |
| `platform` | 12 | hostile request shapes, a load burst, headers, error leaks |

`python -m sentinel.cli list` prints every check. Which incident each one comes
from, how each claim was verified, how far this goes against the OWASP API
Security Top 10, and what is **not** covered:
[`docs/THREATS-2026-Q4.md`](docs/THREATS-2026-Q4.md).

## Safety rails

The harness sends real attacks and changes data, so it is hard to aim at the wrong thing.

- **Scope guard.** It talks freely to internal targets: `localhost`, private and
  link-local IPs, single-label names (Docker service/container names),
  `host.docker.internal`, `*.test`, `*.internal`, `*.local`, … Any other host is
  **refused** unless listed in `safety.allowed_hosts` (or `$SENTINEL_ALLOWED_HOSTS`).
  Only list systems you own and are authorised to test; never production.
- **Disposable instance.** Checks change passwords, create junk accounts, upload
  files and trip lockouts. Seed accounts are restored on a best-effort basis.
- **Attributable traffic.** Every request carries `User-Agent: appsec-sentinel/…`,
  `X-Sentinel-Run` and `X-Sentinel-Check`, so backend logs show which check sent
  what (turn off with `safety.tag_requests: false`).
- **Bounded load.** The resilience suite is eight single requests and one small
  burst; the fuzzer's 10 MB payload is opt-in (`--huge`). `safety.max_rps` and
  `safety.max_requests` pace or cap a run on shared environments.

## Docker

```bash
# harness vs. the bundled demo backend (two containers, one network)
docker compose up --build --abort-on-container-exit
#   set DEMO_MODE: vulnerable in docker-compose.yml to watch every check leak

# the web UI
docker compose -f docker-compose.ui.yml up --build
docker compose -f docker-compose.ui.yml --profile demo up --build   # + demo backend

# one pass against an already-running project on its own network
docker compose -f docker-compose.videosanity.yml run --build --rm sentinel
```

The harness reaches a backend by **service name + internal port** on a shared
Docker network — nothing needs to be published on the host. Your backend lives
in its own project; sentinel only needs to reach it and know its routes.

## Configuration

One YAML file per project (`--config` or `$SENTINEL_CONFIG`), overlaid by env
vars, overlaid by CLI flags / the UI form. `config/target.example.yaml`
documents every key; `config/target.demo.yaml` is the working config for the demo.

| Parameter | YAML | Env | CLI |
|---|---|---|---|
| port | `target.port` | `SENTINEL_PORT` | `--port` |
| host | `target.host` | `SENTINEL_HOST` | `--host` |
| base path | `target.base_path` | `SENTINEL_BASE_PATH` | `--base-path` |
| front-end port | `frontend.port` | `SENTINEL_FRONTEND_PORT` | `--frontend-port` |
| front-end host | `frontend.host` | `SENTINEL_FRONTEND_HOST` | `--frontend-host` |
| API path on the front end | `frontend.api_path` | | `--frontend-api-path`, `--via-frontend` |
| scheme | `target.scheme` | `SENTINEL_SCHEME` | `--scheme` |
| any endpoint | `endpoints.<name>` | `SENTINEL_ENDPOINT_<NAME>` | |
| any field name | `fields.<name>` | `SENTINEL_FIELD_<NAME>` | |
| allowed public hosts | `safety.allowed_hosts` | `SENTINEL_ALLOWED_HOSTS` | |

A missing config file or a malformed endpoint is an error; an unknown key is a
warning. Nothing falls back to defaults silently.

### Wiring it to your API

Everything that differs between backends is in the config — no code edits. The
quickest way is the web UI: type the ports, open *Flow settings*, and use *Try
the flows* until every line is green, then *Save config*. By hand:

1. **Copy** `config/target.example.yaml` to `config/target.<project>.yaml`.
2. **Where it listens:** `target.scheme/host/port/base_path`, and
   `frontend.host/port` if the web app has its own port. A project that
   spans several internal services can give an absolute URL for any endpoint:
   `login: "POST http://auth-service:9000/login"`.
3. **Routes:** `endpoints.<name>: "METHOD /path/{params}"`. `resource` matters
   most — "the user reads their own resource" is the control most checks run first.
4. **Field names:** `fields.*` (`username: email` if login is by e-mail;
   `otp: ""` if there's no second factor; `old_password`, `upload_file`,
   `fetch_url`, `role`).
5. **Signals:** `signals.*` — the header your proxy uses for the client IP, and
   how a same-site write, a step-up re-auth and a verified e-mail are signalled.
6. **Tokens:** `token_json_path`, `refresh_json_path`, `auth_header`
   (`Authorization: Bearer {token}` or `Cookie: session={token}`),
   `session_cookie`, `jwt_iss`/`jwt_aud`, optional `jwks_url`.
7. **Test data:** `users.user/user2/admin` (real throwaway accounts),
   `bola_object` (something `user2` owns), `media_sample` (a media path that exists).
8. **Features and hooks** — the table below.
9. **Verify, then run:**

```bash
python scripts/preflight.py --config config/target.<project>.yaml
python -m sentinel.cli run --target http --config config/target.<project>.yaml --suite all
```

Each inconclusive line in the output names the key that still needs fixing.

> **Field-name gotcha:** the login identifier *value* comes from
> `users.<role>.username` and is sent under the JSON key `fields.username`. If
> your API logs in by e-mail, set `fields.username: email` **and** put the
> address in each user's `username`.

### What each feature / hook unlocks

| Capability | Turn it on with | Unlocks |
|---|---|---|
| `media_upload` | `features: [media_upload]` | INJ6, OUT5, UP1, UP2, UP3, MED1–4, OCT5, OCT6 |
| `frontend` | `frontend.port` (the front-end port) | FE1–FE5 |
| `oauth` | `features: [oauth]` + `oauth:` block | OA1–OA5, OCT1, NOV11, NOV12 |
| `mfa` | `features: [mfa]` (seed accounts have a 2nd factor) | BF5, NOV7, NOV6 |
| `csrf` | `features: [csrf]` (auth rides on a cookie) | SES6 |
| `two_accounts` | a real `users.user2` | AZ2, AZ3, OCT8 |
| `signing_key` | `jwks_url` | C2, NOV2 |
| `reset_introspect` | `hooks.reset_introspect: true` (test build echoes the reset link) | AT1, AT3, ID3, OCT3b, NOV6 |
| `user_admin` | `hooks.user_admin` (test endpoint: GET reads a user, POST `{"enabled": bool}`) | AZ5, AZ6, OCT9, NOV5; makes AT4/OCT2 conclusive when the server accepts the request |
| `other_aud_token` | `hooks.other_aud_token` (mint a token; supports `{aud}`, `{username}`, `{ttl}`) | SES7, C5 |
| `db_probe` | `hooks.db_probe` | MED3 |
| — | `hooks.reset` (restore clean state) | Nothing new, but keeps one check's lockout from making a later one inconclusive, and makes repeated campaign passes meaningful |

A pure black-box run (no hooks) against the demo backend proves 81 checks, skips
14 and leaves 1 inconclusive (the second lockout test finds the client address
already throttled by the first); with every hook it proves all 96.

## Fuzzer and campaign report

- **`scripts/fuzz.py`** — a fast, config-driven input fuzzer: 92 payloads in 11
  categories (SQLi, XSS, encoding, traversal, command/template injection,
  NoSQL/LDAP, CRLF, validation/boundary, and hidden-instruction text aimed at
  any LLM/agent that later reads the field) swept across login, registration and
  route fields, with response-signal detection (reflection, SQL errors, stack
  traces, auth bypass, 5xx, time-based latency). `--dry-run` shows the plan.
  **Signals are leads for human review, not confirmed vulnerabilities.**
- **`scripts/campaign.py`** — runs every suite (plus the fuzzer against an HTTP
  target) in a loop for `--minutes N`, then writes
  `reports/appsec-report-<ts>.md` + a `.json` sidecar: score, weak points with
  their fix, checks that couldn't be proven and why, strong points, coverage
  gaps, fuzzer signals, and a diff against the previous run.

```bash
python scripts/preflight.py --config config/target.videosanity.yaml
SENTINEL_CONFIG=config/target.videosanity.yaml python scripts/campaign.py --target http --minutes 10 --cooldown 60
```

Without `hooks.reset`, locked accounts and a throttled client address carry
from one pass into the next; use `--cooldown` longer than the backend's lockout
window, or expose a reset hook in its test profile.

## Tests

```bash
pip install -r requirements-dev.txt
pytest -q          # 68 tests, ~50 s
```

They cover the two reference invariants (secure: all blocked; vulnerable: all
leak), the full catalogue over a real socket against the demo backend in both
modes, and each failure this harness must never repeat: a dead backend, a wrong
route or wrong credentials passing; state bleed in a black-box run; traversal
sequences being normalised away by the HTTP client; cookie bleed; ignored config
keys; plus the scope guard, the bot-evasion checks (each catches exactly its own
bypass), the front-end checks (a single-page app's catch-all page is not
mistaken for an exposed file; publishable keys are not mistaken for secrets),
flow selection, "try the flows", and the web UI's own lockdown.

## Layout

```
appsec-sentinel/
├── sentinel/
│   ├── cli.py                      # sentinel run | list | ui
│   ├── engine.py                   # one definition of "a run" (CLI, UI, campaign)
│   ├── config.py                   # YAML + env config, validation, retarget()
│   ├── safety.py                   # scope guard, pacing, request budget
│   ├── adapters/
│   │   ├── base.py                 # Target contract, Capability, Inconclusive
│   │   ├── http_target.py          # ← the real backend adapter (HTTP)
│   │   ├── reference_target.py     # in-process self-test + negative control
│   │   └── reference/              # the secure / vulnerable app models
│   ├── suites/
│   │   ├── common.py               # runner, verdict helpers, score
│   │   ├── access_control.py  media_injection.py  oct2026.py  nov2026.py
│   │   ├── automation.py           # bots / agents / spam
│   │   ├── resilience.py           # hostile input shapes + load burst
│   │   ├── surface.py              # exposed files, CORS, the web front end
│   │   ├── flows.py                # checks grouped by product flow
│   │   ├── remediation.py          # the fix for each leak
│   │   └── xss.py  jwt_forge.py  pkce.py
│   ├── media/generator.py          # hostile-media corpus generator
│   └── ui/                         # the web UI (stdlib server + one page)
├── demo_target/server.py           # bundled demo backend (stand-in for yours)
├── scripts/                        # preflight.py  fuzz.py  campaign.py
├── config/                         # target.example / demo / videosanity .yaml
├── docs/THREATS-2026-Q4.md         # check → incident mapping, sources, gaps
├── tests/                          # pytest: suites + the harness itself
├── kotlin/                         # OPTIONAL JVM variant (see below)
└── Dockerfile  docker-compose*.yml  requirements*.txt
```

## The Kotlin variant (optional)

`kotlin/` holds an earlier version of the access-control catalogue as a JUnit suite
behind an `AppUnderTest` seam, for teams that prefer to run security tests
inside their Gradle build. It has **not** been updated with the control-first
verdicts, the `nov2026`/`automation`/`resilience` suites or the corrected threat
mapping — the Python project is the primary runner.

## Honesty notes

- **Verified here:** the Python runner against both reference apps (96/96 each
  way); the HTTP adapter against the demo backend over a real socket in secure,
  vulnerable, black-box and dead-backend configurations; the web UI driven in
  headless Chromium (ports, try the flows, fixing a route, saving, running by
  flow); the fuzzer, preflight and campaign scripts; 68 pytest tests.
- **Not verified here:** the Docker image build and the compose files (syntax
  checked only — no Docker daemon in the environment this was written in), the
  Kotlin `gradle test`, the `xss` suite (Python Playwright not installed), and
  any run against a real application of yours.
- **Abstractions that may not fit your app.** Step-up, CSRF and "e-mail verified"
  are modelled as request headers (`signals.*`). If your app expresses them
  differently (e.g. step-up as a recent-login timestamp inside the token), CT1,
  NOV8, SES6 and AT4 need adapting — expect inconclusive or misleading results
  there until then. OAuth checks assume the authorize endpoint can be called
  directly; flows that require an interactive login first will be inconclusive.
- **The front-end checks look at what the front end serves** (files, headers,
  scripts). They do not click through your app in a browser; driving your real
  login or upload screens needs selectors only you know (the optional `xss`
  suite is the place to add that).
- **A green run is not a penetration test.** It shows these specific controls
  hold. Against the OWASP API Top 10 it is good on authentication, resource
  consumption and SSRF, partial on authorization and misconfiguration, and does
  not cover API inventory or third-party API trust (table in
  `docs/THREATS-2026-Q4.md`). It can't find business-logic flaws, and it says nothing about the
  classes listed under "not covered" in `docs/THREATS-2026-Q4.md` (runtime RCEs
  fixed by patching, HTTP/2–3 protocol floods, volumetric load, LLM behaviour).
- A keylogger can't be tested server-side — the suites check its *mitigations*
  (step-up auth, short tokens). Full DOM-XSS coverage wants a DAST crawler
  alongside the headless checks.
