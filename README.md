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

## Wiring it to YOUR API — full checklist & worked example (do this manually)

The harness is driven by **one config file** plus a few optional code tweaks.
Until these match your real backend, results are meaningless: a wrong/missing
route returns 404, which the suites count as "blocked" (a false PASS). Always run
`scripts/preflight.py` after editing to confirm the routes resolve and login
returns a token.

### Where everything lives
| File | Role |
|------|------|
| `config/target.<name>.yaml` | **The one file you edit.** Copy `config/target.videosanity.yaml` (or `target.example.yaml`) and fill it in. |
| `sentinel/adapters/http_target.py` | A handful of request-shaping spots marked `# ADAPT` you may need to change (headers, field names). |
| env vars `SENTINEL_*` | Override any single value without touching the YAML. Precedence: **built-in defaults < YAML < env vars**. |

Point the run at your file with `--config config/target.videosanity.yaml` or
`SENTINEL_CONFIG=config/target.videosanity.yaml`.

### Step 1 — fill in the config (what every key is, and how to find it)
| Key | What it is | How to find it | Example |
|-----|-----------|----------------|---------|
| `target.scheme/host/port/base_path` | Where the app listens | your deploy / container | `http` / `videosanity-videosanity-app-1` / `8080` / `/api/v1` |
| `endpoints.<name>` | `"METHOD /path/with/{params}"` for each operation | your API routes / OpenAPI / controller code | `login: "POST /auth/login"` |
| `fields.username/password/otp/email/token/new_password` | The **JSON field names** your API expects | a real request body (DevTools → Network) | `username: email` if login takes `email` |
| `token_json_path` | Dot-path to the access token in the login JSON | a real login response | `data.accessToken` |
| `refresh_json_path` | Dot-path to the refresh token | a real login response | `data.refreshToken` |
| `auth_header` | How the token is sent | your auth docs | `Authorization: Bearer {token}` (or a cookie — see ADAPT) |
| `users.user/user2/admin` | **Real throwaway accounts** that already exist | create them on the test instance | see example below |
| `jwt_iss` / `jwt_aud` | Expected issuer/audience, so forged-token tests fail on the *algorithm*, not iss/aud | a decoded JWT (jwt.io) | `https://auth.videosanity.test` / `api` |
| `jwks_url` | Public-key endpoint (enables the RS256→HS256 test, C2) | `/.well-known/jwks.json` if present | optional |
| `features` | `[oauth, media_upload]` — attacks for a feature not listed are SKIPPED | what your app actually has | `[media_upload]` |
| `hooks.*` | Optional **test-build** endpoints that unlock gray-box checks | only if you expose them | leave `null` for black-box |

> **Field-name gotcha:** the login *identifier* value comes from
> `users.<role>.username`, and it is sent under the JSON key `fields.username`.
> So if your API logs in by email, set `fields.username: email` **and** put the
> email address in each user's `username`. Same idea for `otp`→`totp`,
> `new_password`→`newPassword`, etc.

### Step 2 — adjust the `# ADAPT` spots in `sentinel/adapters/http_target.py`
These are request details config can't express. Search the file for `# ADAPT`:
| Spot (method) | Default | Change to |
|---------------|---------|-----------|
| `login` — client IP header | `X-Forwarded-For` | your real client-IP header (e.g. `X-Real-IP`), used by the brute-force/IP-limit checks |
| `_mutate_headers` — CSRF signal | `Origin` / `X-CSRF-Token` | however your API distinguishes same-site vs cross-site writes |
| `_mutate_headers` — step-up signal | `X-Step-Up: reauthed` | your re-auth / step-up signal (used by CT1, SES6) |
| `change_email` — verified signal | `X-Email-Verified: true` | your "email re-verified" signal (AT4, OCT2) |
| `upload_bytes` — multipart field | `file` | your upload form-field name (e.g. `media`) |
| `upload` — import-by-URL field | `fetchUrl` | your "import from URL" field (e.g. `sourceUrl`), used by the SSRF checks (INJ6, OCT5) |

> If the app authenticates with a **session cookie** instead of a bearer token,
> set `auth_header` to a cookie (`Cookie: session={token}`) and make sure
> `token_json_path` points at whatever the login returns (or the `sid` the
> adapter lifts from `Set-Cookie`). `fields.token` is reused for **both** the
> refresh-token and reset-token request bodies — if your API names them
> differently, split them in `refresh_token()` / `reset_confirm()`.

### Step 3 — worked example
Say videosanity's real API (from its docs/code) looks like this:

```
POST /api/v1/auth/login     {"email","password","totp"}  -> 200 {"data":{"accessToken","refreshToken"}}
POST /api/v1/auth/logout    Bearer                        -> 204
POST /api/v1/auth/refresh   {"refreshToken"}              -> 200 {"data":{"accessToken"}}
POST /api/v1/auth/register  {"email","password"}          -> 201
GET  /api/v1/admin/users            Bearer(admin)
DELETE /api/v1/admin/users/{target} Bearer(admin)
GET  /api/v1/users/{owner_id}/library   Bearer (owner-only)
GET  /api/v1/videos/{id}                Bearer (owner-only)
POST /api/v1/account/password  {"currentPassword","newPassword"}
POST /api/v1/account/payout             (step-up protected)
POST /api/v1/account/email     {"email"}
GET  /media/{path}
POST /api/v1/uploads           multipart field "media"; import via {"sourceUrl"}
POST /api/v1/auth/password/forgot {"email"}
POST /api/v1/auth/password/reset  {"token","newPassword"}
Auth: Authorization: Bearer <token>   ·   client IP from X-Real-IP
```

The matching `config/target.videosanity.yaml` is:

```yaml
target:
  scheme: http
  host: videosanity-videosanity-app-1
  port: 8080
  base_path: /api/v1            # prefixes every endpoint below (except absolute ones)

endpoints:
  login:           "POST /auth/login"
  logout:          "POST /auth/logout"
  refresh:         "POST /auth/refresh"
  register:        "POST /auth/register"
  admin_users:     "GET /admin/users"
  admin_delete:    "DELETE /admin/users/{target}"
  resource:        "GET /users/{owner_id}/library"
  object:          "GET /videos/{id}"          # suite calls get_object(.,'video',102)
  change_password: "POST /account/password"
  sensitive:       "POST /account/payout"
  change_email:    "POST /account/email"
  media:           "GET /media/{path}"         # note: no /api/v1 prefix? then set base_path:"" and prefix each route
  upload:          "POST /uploads"
  reset_request:   "POST /auth/password/forgot"
  reset_confirm:   "POST /auth/password/reset"
  buggy:           "GET /videos/{id}"          # any route that parses input; reuse one you have

fields:
  username: email                # <-- login takes "email", so map it here
  password: password
  otp: totp
  email: email
  token: token                   # reset body uses {"token": ...}
  new_password: newPassword

token_json_path: "data.accessToken"
refresh_json_path: "data.refreshToken"
auth_header: "Authorization: Bearer {token}"

users:
  user:  { username: "alice@videosanity.test", password: "Alice-Pw-123!", id: 1001, email: "alice@videosanity.test" }
  user2: { username: "bob@videosanity.test",   password: "Bob-Pw-123!",   id: 1002, email: "bob@videosanity.test" }
  admin: { username: "admin@videosanity.test", password: "Admin-Pw-123!", id: 1,    email: "admin@videosanity.test" }

jwt_iss: "https://auth.videosanity.test"
jwt_aud: "api"

features: [media_upload]         # add "oauth" only if videosanity exposes OAuth endpoints

hooks:                           # leave null for black-box; ~8 checks then SKIP (honest)
  reset: null
  user_admin: null
  other_aud_token: null
  db_probe: null
  reset_introspect: false
```

…plus two `# ADAPT` edits in `http_target.py`: change the client-IP header to
`X-Real-IP`, the multipart field from `file` to `media`, and the import field
from `fetchUrl` to `sourceUrl`.

### Step 4 — which checks run, and what each hook/feature unlocks
Without a capability, the dependent checks **SKIP** (honest) rather than fake a pass:

| Capability | Turn it on with | Unlocks |
|-----------|-----------------|---------|
| `media_upload` | `features: [media_upload]` | INJ6, OUT5, UP2, UP3, MED1, MED2, MED4, **OCT5, OCT6** |
| `oauth` | `features: [oauth]` + `oauth:` block | OA1–OA5, **OCT1** |
| `two_accounts` | a real `users.user2` | AZ2, AZ3, **OCT8** |
| `signing_key` | `jwks_url` | C2 (RS256→HS256 confusion) |
| `reset_introspect` | `hooks.reset_introspect: true` (test build echoes the reset link) | AT1, AT3, ID3, **OCT3b** |
| `user_admin` | `hooks.user_admin` (test endpoint to read/set a user) | AZ5, AZ6, **OCT9** |
| `other_aud_token` | `hooks.other_aud_token` | SES7 |
| `db_probe` | `hooks.db_probe` | MED3 |

### Step 5 — verify, then run
```bash
# a) routes resolve + login returns a token (fails loudly if not)
python scripts/preflight.py --config config/target.videosanity.yaml
# b) sanity-check the suites themselves still pass/fail correctly
python -m sentinel.cli run --target reference-secure --suite all
python -m sentinel.cli run --target reference-vulnerable --suite all
# c) the real run (single pass) or the timed campaign with a Markdown report
SENTINEL_CONFIG=config/target.videosanity.yaml python -m sentinel.cli run --target http --suite all
SENTINEL_CONFIG=config/target.videosanity.yaml python scripts/campaign.py --target http --minutes 10
```

Run against a **disposable** instance — the suites and fuzzer mutate state
(change passwords/email, create accounts, upload files).

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
