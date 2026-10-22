# Design handoff — Video-first profiles, booking and host tools

Everything an implementing agent needs to build the screens designed in the **Profile Quick Actions** design canvas, for **Android and iOS**, on **small, medium and large phones**, so the result looks exactly like the designs.

> Design canvas (private, owner access): https://claude.ai/artifact/5317zoDgLoVqdsUCq6HUpd
> This folder is the exported, self-contained copy. It is the source of truth for implementation.

## Start here (for the implementing agent)

Read in this order, then build:

1. [`docs/01-principles.md`](docs/01-principles.md) — the rules every screen follows ("stupid simple", icon-first, one way forward, legibility on video). **Non-negotiable.**
2. [`tokens.json`](tokens.json) + [`docs/02-design-tokens.md`](docs/02-design-tokens.md) — colours, type, radii, spacing, overlays. Use these names in code; never hard-code a new value.
3. [`docs/03-components.md`](docs/03-components.md) — every reusable component with anatomy, sizes and states. Build these first.
4. [`docs/04-screens.md`](docs/04-screens.md) — every screen, top to bottom, with content, actions and data.
5. [`docs/05-flows.md`](docs/05-flows.md) — navigation and the rules that pick a path (regular vs first visit, Call vs Book).
6. [`docs/06-data-model.md`](docs/06-data-model.md) — the data each screen needs and the display rules derived from it.
7. [`docs/07-responsive-and-platforms.md`](docs/07-responsive-and-platforms.md) — small / medium / large behaviour, safe areas, iOS vs Android notes.
8. [`docs/08-content-and-i18n.md`](docs/08-content-and-i18n.md) + [`strings.json`](strings.json) — copy, six languages, truncation rules.
9. [`docs/09-acceptance-checklist.md`](docs/09-acceptance-checklist.md) — how to verify the build matches the designs.
10. [`docs/10-open-questions.md`](docs/10-open-questions.md) — what is **not** designed yet. Do not invent these; ask.

## What is in this folder

| Path | What it is |
|---|---|
| `screenshots/{small,medium,large}/*.png` | Pixel reference for every screen at 2× (360×640, 390×844, 430×932 points). **What "done" looks like.** |
| `screens/{small,medium,large}/*.html` | The original design markup, standalone. Open in a browser to inspect exact values (every style is inline). Links between screens work, so it is also a clickable prototype. |
| `screens/reference/icon-set.html` | The Quick Actions icon set and icon rules. |
| `screens.json` | Manifest: every screen id, title, purpose, files per size, and the screens it links to. |
| `tokens.json` | Design tokens. |
| `strings.json` | UI strings in EN, RO, DE, IT, ES, FR taken from the designs. |
| `docs/` | The written spec (above). |

## Screen inventory (23 screens × 3 sizes)

| Area | Screens |
|---|---|
| Host — own profile | `HP-profile` |
| Host — services (video first) | `HS1-services-list`, `HS2-add-video`, `HS3-service-details`, `HS4-edit-service` |
| Host — rooms (video first) | `HR1-rooms-list`, `HR2-add-video`, `HR3-room-details`, `HR4-edit-room` |
| Public — accommodation | `PA1-profile-rooms`, `PA2-room-video`, `PA3-room-included` |
| Public — services & F&B profiles | `PS1-profile-services`, `PF1-profile-fnb` |
| Salon booking — regular customer | `R1-services-stylist-picked`, `R2-video`, `R3-pick-time`, `SV-included` |
| Salon booking — first visit | `F1-services-everyone`, `F2-video`, `F3-choose-stylist`, `F4-pick-time` |
| Coupons & Events tab | `CE1-coupons-events` |

## How to use the references

- **Screenshots decide what it looks like.** If text in the docs and a screenshot disagree, the screenshot wins; note the mismatch in your report.
- **HTML decides the exact numbers.** Sizes, paddings, colours and gradients are inline styles in `screens/medium/*.html`. 1 CSS px = 1 dp (Android) = 1 pt (iOS).
- **Sample data is sample.** Names, prices, items, ratings and dates in the designs are placeholders; bind them to real data (see `docs/06-data-model.md`).
- **Icons:** use the Lucide icon set (names listed in `docs/03-components.md`) or the exact SVG paths from the HTML. Never emoji.

## Prompt to give the implementing agent

Copy this as the first message, adjusted for your app's repository:

```text
You are implementing new screens in our mobile app (Android + iOS). The complete design
handoff is in design-handoff/ (README.md first). Follow it exactly:

1. Read design-handoff/README.md and every file in design-handoff/docs/ before writing code.
2. Map tokens.json into the app's theme (colours, type, radii, spacing). Do not add new values.
3. Build the shared components from docs/03-components.md first, then the screens from
   docs/04-screens.md, in the order: host services → host rooms → public profiles →
   salon booking (regular, then first visit) → coupons & events.
4. Every screen must match screenshots/{small,medium,large}/<id>.png. Use the HTML in
   screens/ for exact sizes. Respect docs/07 for small/medium/large and safe areas.
5. Wire navigation exactly as docs/05-flows.md (and screens.json "links_to").
6. Anything listed in docs/10-open-questions.md is out of scope: leave a TODO and ask.
7. When a screen is done, compare it to the screenshots at all three sizes and go through
   docs/09-acceptance-checklist.md. Report any deviation instead of silently changing the design.
```
