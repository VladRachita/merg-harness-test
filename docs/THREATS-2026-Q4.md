# Threat mapping — October / November 2026

Which real incident each check comes from, how sure we are, and what the harness
does **not** cover. Compiled 2026-11-09.

## How this was verified

| Level | Meaning |
|---|---|
| **Record** | Read from the official CVE record (`github.com/CVEProject/cvelistV5`, `cves/2026/<NNN>xxx/CVE-2026-<id>.json`), the GitHub Security Advisory, or CISA's KEV catalogue mirror (`github.com/cisagov/kev-data`, catalogue version 2026.11.06). |
| **Summary** | Only seen in search-engine summaries of the publisher's page; the page itself could not be opened from the research environment. Treat as likely but unconfirmed. |
| **Unverified** | No supporting source found. Removed from the suites' claims. |

KEV additions made on 7–9 November are not covered (the catalogue read was dated 6 November).

Every check asserts a **defence** generically. None reproduces a product-specific
exploit, and a green check does not mean "not affected by CVE-X" — it means the
control that CVE-X broke holds on *your* backend. Patch the affected products too.

## Corrections to the earlier `oct2026` mapping

The previous version of this suite cited real CVE ids, but three mappings were wrong:

| Was claimed | What the record says | Change |
|---|---|---|
| Metabase CVE-2026-72898 is an October incident | Unauthenticated SQLi in `/api/session/reset_password` → admin, CVSS 10, in KEV — but disclosed **6–11 August 2026** | OCT3 kept (the class is still exploited); date corrected |
| Plex CVE-2026-96654/55/56: "crafted media writes a library into the Codecs dir → RCE" | 96654 = URL-value injection in `searchOne`; 96655 = authenticated SSRF via the transcode endpoint; 96656 = an **admin-set** `TranscoderH264Options` value passed verbatim, with `.so` files loaded unsigned at start-up. Not crafted media. CVE records date from 23 Sep; KEV 20 Oct. The record for 96652 (SSRF via `/player/timeline`) does not say it yields the admin token | OCT5 now cites 96652/96655 (SSRF); OCT6 re-mapped to the unrestricted-upload class |
| "Akamai SOTI 2026 — injection + BOLA + SSRF remain top techniques" | The 2026 report exists (March) but no such ranking was found in it | Claim removed |
| "SiteGuard WAF command-injection class" under verb tampering | CVE-2026-106931 is real (KEV 20 Oct) but its vector is **local, low-privilege** — not a request-level technique | Reference removed from OCT7 |
| Snipe-IT CVE-2026-116199 = "OAuth callback bypass" | The Google SSO callback ignores the `activated` flag, so deactivated users regain sessions | Moved to NOV5 (account-status check) |
| BeyondTrust CVE-2026-102764 = "unauthenticated file operations" | Messaging components did not validate message origin (CWE-290) → file operations. "Unauthenticated" is not in the vendor text (it follows from the CVSS vector) | OCT4 wording corrected |

## Check → incident

### oct2026

| Check | Control asserted | Incident | Level |
|---|---|---|---|
| OCT1 | A token is only valid for the flow that issued it | Better Auth CVE-2026-114607 / CVE-2026-110862 (GHSA-965c-763c-88jm): OAuth `state` accepted as a magic-link token. GHSA 30 Sep; CVEs 14 & 22 Oct | Record |
| OCT2 | An e-mail address takes effect only once verified | same advisory ("falsely email-verified account") | Record |
| OCT3a/b | Reset endpoint treats input as data; reset tokens single-use | Metabase CVE-2026-72898 (Aug 2026; KEV 11 Aug) | Record |
| OCT4 | No privileged operation without a proven identity | BeyondTrust Remote Support CVE-2026-102764 (15 Oct; KEV 16 Oct) | Record |
| OCT5 | "Fetch this URL" cannot reach internal addresses | Plex CVE-2026-96652, CVE-2026-96655 (KEV 20 Oct) | Record |
| OCT6 | Disguised / undecodable uploads are refused | Adobe Commerce CVE-2026-48356 (July; KEV 27 Oct), Cisco Secure Email Gateway CVE-2026-76519 (KEV 14 Oct) | Record |
| OCT7 | Authorization is identical for every HTTP verb | AhnLab ASEC October report on breaches via exposed web services/APIs | Summary |
| OCT8 | Object ownership checked on every access | Authlib CVE-2026-116672 (27 Oct) | Record |
| OCT9 | Privilege fields are assigned server-side | class (no single CVE) | — |

### nov2026

| Check | Control asserted | Incident | Level |
|---|---|---|---|
| NOV1 | An empty HMAC key can't sign a token | Authlib CVE-2026-114616 (22 Oct); PyJWT GHSA-pxh4-856f-4h89 | Record |
| NOV2 | The public key can't be used as an HMAC secret, in any encoding | Authlib CVE-2026-114615 (22 Oct) | Record |
| NOV3 | Logout really revokes | Django REST framework CVE-2026-114137 (21 Oct) | Record |
| NOV4 | A password change revokes refresh tokens | wger CVE-2026-46437 (7 Oct) | Record |
| NOV5 | A deactivated account gets no new session | Snipe-IT CVE-2026-116199 (25 Oct) | Record |
| NOV6 | Password reset issues no session (MFA still required) | SilverStripe MFA CVE-2026-55186 (3 Nov) | Record |
| NOV7 | The second factor is enforced on login | SonicWall SonicOS SSLVPN CVE-2026-19868 (6 Nov; KEV same day) | Record |
| NOV8 | Password change requires step-up | Nginx UI CVE-2026-84314 (12 Oct), Arcane CVE-2026-96627 (16 Oct) | Record |
| NOV9 | Auth responses contain no credential fields | Payload CMS CVE-2026-105853 (6 Oct) | Record |
| NOV10 | Identity can't be asserted by a client header | Ivanti Connect Secure CVE-2026-104935 (13 Oct; KEV) | Record |
| NOV11 | No token without a valid grant | OAuthLib device flow CVE-2026-49272 (5 Nov) | Record |
| NOV12 | An authorization code needs its PKCE verifier | Python Social Auth CVE-2026-115910 (26 Oct) — same control family (code bound to whoever started the flow); the CVE itself is about nonce binding | Record |

### automation (bots, scripted agents, spam)

| Check | Control asserted | Incident | Level |
|---|---|---|---|
| BF2 | Password spraying is throttled per client | Microsoft report on "Storm-0940" (21 Oct): a 10–14 Oct spray of 151,000+ failed sign-ins, peak 2,900/min | Summary |
| BF4, BOT1 | The limiter is not keyed on a client-supplied address | Echo (Go) CVE-2026-118653 (28 Oct): default rate limiter keyed on `X-Forwarded-For` | Record |
| BOT3 | Every route to the same handler shares the limit | Vikunja CVE-2026-91972 (CVE Sep; GHSA 9 Oct): `/api/v2` auth routes unthrottled — related class, not the same bug | Record |
| BOT2, BOT4–6 | Limits survive fingerprint rotation / body encoding; sign-ups and token guesses throttled | OWASP Automated Threats OAT-008 / OAT-019 / OAT-002 (taxonomy, not an incident) | — |

A design tension worth knowing: Payload CVE-2026-105866 (6 Oct) is the *opposite*
failure — a lockout that any anonymous caller can trigger against a known
account (denial of service). BF1 asserts a lockout exists; it does not judge
whether yours can be abused to lock real users out. Prefer throttling by client
plus progressive delays over a hard per-account lock.

### resilience (load and hostile input shapes)

| Check | Control asserted | Incident | Level |
|---|---|---|---|
| RES4, RES6 | Compressed / exotic-charset bodies can't become a bomb | Django REST framework CVE-2026-114136 (21 Oct) | Record |
| RES5 | An unexpected `Content-Encoding` is refused, not decoded | Brotli decoder CVE-2026-111497 (22 Oct; KEV 27 Oct). The check sends harmless garbage, not the crafted stream | Record |
| RES7 | Multipart parsing is bounded | aiohttp CVE-2026-111066 (19 Oct), @hapi/content CVE-2026-119202 (29 Oct), Payload CVE-2026-105854 (6 Oct) | Record |
| RES8 | Header parsing is bounded | Django REST framework CVE-2026-114138 (21 Oct) | Record |
| RES1–3 | Size / depth / width limits before parsing | ASP.NET Core CVE-2026-70181 (13 Oct) | Record |
| RES9 | A burst is absorbed or shed, never 5xx | — (general resilience) | — |

### surface (front end, CORS, exposed files) and the remaining additions

These are not tied to a single October/November incident; they are the standing
classes every scanner and intruder tries first.

| Check | Control asserted | Class |
|---|---|---|
| SUR1, FE1 | No dotfiles, repositories, dumps or management endpoints served (23 paths, confirmed by content) | Footprinting / exposed configuration. Related in the window: Atlassian Data Center CVE-2026-21589 (file read in the web root, KEV 15 Oct) — a different mechanism, same asset |
| SUR2 | CORS grants no credentialed access to arbitrary origins | CORS misconfiguration |
| FE2–FE4 | Front end sends CSP, anti-framing and nosniff headers | Browser-side hardening |
| FE5 | No server-side secrets in the page or its scripts | Secrets shipped to the browser |
| C6 | A token cannot name its own verification key (`jwk`, `jku`, `x5u`, `kid` injection) | JWT key injection |
| REG1 | Sign-up refuses the most common passwords | Credential-stuffing resistance |
| UP1 | Uploads require authentication | Unauthenticated upload (cf. the unrestricted-upload KEV entries under OCT6) |

## Coverage against the OWASP API Security Top 10 (2023)

A plain statement of how far the harness goes, so "covered" is not over-read.

| Risk | Coverage | Checks | What is missing |
|---|---|---|---|
| API1 Broken object-level authorization | Partial | AZ2, AZ3, OCT8 | Only *reading* another user's resource/object. Changing or deleting someone else's object is not modelled |
| API2 Broken authentication | Good | BF1–6, C1–6, SES1–7, NOV1–8, OA1–5, AT1–4, BOT1–4, REG1 | Flows the contract has no operation for (magic links, SSO callbacks, device flow) |
| API3 Broken object-property-level authorization | Partial | AZ5, AZ7, OCT9, NOV9 | Excess data is only looked for in login/refresh responses, not in every API response |
| API4 Unrestricted resource consumption | Good, bounded | RES1–9, UP2, UP3, BOT5, BOT6 | Not a capacity, soak or protocol-level (HTTP/2–3) test |
| API5 Broken function-level authorization | Partial | AZ1, AZ4, OCT4, OCT7, NOV10 | One admin route (the one you configure), not every privileged route |
| API6 Unrestricted access to sensitive business flows | Partial | BOT5 (sign-up), BF/BOT (login), UP3 | Your own business flows — bookings, coupons, rewards, likes, purchases — are not modelled |
| API7 Server-side request forgery | Good for one field | INJ6, OCT5 | Only the one "import by URL" field you configure |
| API8 Security misconfiguration | Partial | OUT1, OUT3, ID1, SUR1, SUR2, FE1–5, SES5 | TLS/HSTS configuration, default credentials, cloud/storage permissions |
| API9 Improper inventory management | Not covered | — | Old API versions and undocumented endpoints are not discovered |
| API10 Unsafe consumption of APIs | Not covered | — | How your backend trusts third-party APIs |

Outside that list and also not covered: stored/DOM XSS without the optional
browser suite, vulnerable dependencies (use a dependency scanner), and anything
that needs knowledge of your business rules.

## Seen in the window, NOT covered by this harness

Be aware of these; a green run says nothing about them.

- **Runtime / memory-corruption RCE** — PHP CVE-2026-109618/109619 (KEV 26 Oct), Brotli
  CVE-2026-111497 itself, GitLab CVE-2026-97229, WordPress core CVE-2026-119977, Collabora
  CVE-2026-110447, Atlassian Data Center CVE-2026-21589. These are fixed by **patching**, not by
  an application control a black-box check can assert. Track KEV for what you run.
- **Protocol-level DoS** — Twisted HTTP/2 rapid stream reset (GHSA-vpp8-g58w-m8mp, 22 Oct),
  lsquic HTTP/3 QPACK CVE-2026-115482. This harness speaks HTTP/1.1 through `requests`; it cannot
  exercise HTTP/2 or HTTP/3 framing. Use a dedicated tool and keep the server patched.
- **Volumetric load** — RES9 is a 60-request burst. It finds missing limits; it is not a capacity
  or soak test.
- **SQL injection in list/sort/filter parameters** — Payload CVE-2026-105845, JHipster
  CVE-2026-107375 (`sort` → `ORDER BY`). The contract has no generic "list with sort" operation;
  `scripts/fuzz.py` probes the fields it can reach, nothing more.
- **Prompt injection against LLM features** — Flowise CVE-2026-73487 (Aug; reviewed 7 Oct) and
  similar. The fuzzer's `agent` payloads only tell you whether hidden-instruction text is stored
  and served back unmodified; they do not test what a model does with it. If the app has an LLM
  or agent feature, it needs its own evaluation.
- **Supply chain / third-party app credentials** — the Storm-0940 campaign (Summary level) abused
  a vendor's application identities. Out of scope for a request-level harness.
- **Stored-secret hygiene** — e.g. Vikunja CVE-2026-62376 (reset tokens stored in plaintext) is
  not observable from outside.
- **Scope escalation of API tokens** — Vikunja CVE-2026-57458; no scoped-token operation in the
  contract yet.

Not found in the window: a dated credential-stuffing wave, bot-driven sign-up campaign or
scraping incident for Oct/Nov 2026, or a new cross-vendor HTTP/2 flood or request-smuggling CVE.
The bot checks therefore map to the OWASP taxonomy and the two rate-limiter CVEs above rather
than to a named campaign.
