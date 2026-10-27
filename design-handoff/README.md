# Design handoff — Video-first profiles, booking, table booking, team, customer rewards, reservations, my activity, search, new post and host tools

Everything an implementing agent needs to build the screens designed in the **Profile Quick Actions** design canvas, for **Android and iOS**, on **small, medium and large phones**, so the result looks exactly like the designs.

> Design canvas (private, owner access): https://claude.ai/artifact/5317zoDgLoVqdsUCq6HUpd
> This folder is the exported, self-contained copy. It is the source of truth for implementation.

## Start here (for the implementing agent)

Read in this order, then build:

1. [`docs/01-principles.md`](docs/01-principles.md) — the rules every screen follows ("stupid simple", icon-first, one way forward, legibility on video). **Non-negotiable.**
2. [`tokens.json`](tokens.json) + [`docs/02-design-tokens.md`](docs/02-design-tokens.md) — colours, type, radii, spacing, overlays. Use these names in code; never hard-code a new value.
3. [`docs/03-components.md`](docs/03-components.md) — every reusable component with anatomy, sizes and states. Build these first.
4. [`docs/04-screens.md`](docs/04-screens.md) — every screen, top to bottom, with content, actions and data.
5. [`docs/05-flows.md`](docs/05-flows.md) — navigation and the rules that pick a path (regular vs first visit, Call vs Book, table booking).
6. [`docs/11-table-booking.md`](docs/11-table-booking.md) — the full spec of the **Table booking** page (month calendar → guests & time with offers → details → booked) and the offers in the salon calendar (F4). Exact sizes, states, copy and its own definition of done.
7. [`docs/06-data-model.md`](docs/06-data-model.md) — the data each screen needs and the display rules derived from it.
8. [`docs/07-responsive-and-platforms.md`](docs/07-responsive-and-platforms.md) — small / medium / large behaviour, safe areas, iOS vs Android notes.
9. [`docs/08-content-and-i18n.md`](docs/08-content-and-i18n.md) + [`strings.json`](strings.json) — copy, six languages, truncation rules.
10. [`docs/09-acceptance-checklist.md`](docs/09-acceptance-checklist.md) — how to verify the build matches the designs.
11. [`docs/12-team.md`](docs/12-team.md) — the full spec of the **Team** page (team list → invite by username → team member) with its own definition of done.
12. [`docs/13-customers-rewards.md`](docs/13-customers-rewards.md) — the full spec of the **Customers & rewards** page (send a reward by hand, monthly automatic rewards, results) with its own definition of done.
13. [`docs/14-reservations.md`](docs/14-reservations.md) — the full spec of the **Reservations** page (requests to answer → accept / decline with a reason → the day → did they come), the same for services, tables and events, with its own definition of done.
14. [`docs/15-my-activity.md`](docs/15-my-activity.md) — the full spec of the customer's **My activity** page (Upcoming · Rewards · History tabs, a reservation waiting or confirmed, a reward), with its own definition of done.
15. [`docs/16-search.md`](docs/16-search.md) — the full spec of the public **Search** page (before you type with recent searches → tabs All · Videos · Places · Deals → one mixed feed that keeps loading → no results), with its own definition of done.
16. [`docs/17-new-post.md`](docs/17-new-post.md) — the full spec of the **New post** page (the + button → pick a video → write the title and description on the video → tag a place, a service or a room → Publish; edit the post or delete the video later), with its own definition of done.
17. [`docs/10-open-questions.md`](docs/10-open-questions.md) — what is **not** designed yet. Do not invent these; ask.

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
| `properties-per-screen.md` | For the backend: every screen's displayed data, inputs, actions and open parameters, with the gaps. |

## What's new in this update

- **New post (profile)** — anyone posts a video on their own profile from the **+** in the bottom nav, the way people know from Instagram and TikTok:
  - `NP1` **pick a video**: one clip, up to 100 MB, no Skip.
  - `NP2` **on the video, empty**: the whole video, the title and description typed where people will read them, **Tag** on the side rail, **Publish** greyed until there is a title.
  - `NP3` **written and tagged**: title **max 30** and description **max 100** characters (counters, shown at the caps so the longest case is checked at every size), the Tag icon white with a count badge.
  - `NP4` **Tag a place** (sheet): search places, or one tap on a visit (tags the place and what was booked there).
  - `EP1` **Edit post**: the same editor with the saved post (no Change video), **Delete video** bottom left, **Save** bottom right.
  - `EP2` **Delete video** (sheet): the video and everything linked to it (title and description, tag, likes) are deleted for everyone.
  - No hashtags, no people tags, no location, no tag pill on the video.

  Spec: [`docs/17-new-post.md`](docs/17-new-post.md). Small / medium / large references; components C57–C62; *Post* data in `docs/06`. The **+** on the host profile (HP) now opens NP1.

### Earlier updates

- **Search (public)** — a new page that replaces the current Search mock. It opens from the **Search** tab of the bottom nav:
  - `SR1` **before you type**: the search field and **Recent** searches (tap to run again, X to remove, **Clear all**). No Browse / categories.
  - `SR2` **no results**: "No results for “<query>”" and one hint. No tabs.
  - `SR3` **All**: one mixed feed, best match first: places (one row each), videos (2 per row) and deals (2 per row). No headings, no "See all"; it keeps loading (**Loading more**).
  - `SR4` **Videos**, `SR5` **Places** (no icons in the rows: initial, name, verified, type · city, status), `SR6` **Deals** (coupons and events as video cards, 2 per row, ending soonest first; All / Events / Coupons tiles). Every tab keeps loading.
  - Tabs **All · Videos · Places · Deals** with **no result counts**; the unselected tabs are greyed (0.4).
  - A place opens its profile (PS1 / PF1 / PA1), a video its item video (F2 / PA2), a deal its booking with the deal already picked (F4C / F4E / TB2C / TB2E).

  Spec: [`docs/16-search.md`](docs/16-search.md). Small / medium / large references; components C50–C56; *Search* data (result blocks, paging, recent searches) in `docs/06`; open questions #50–#61 (when to search, ranking, location, paging, recent searches storage, empty states, matching, which service a deal opens on).
- **Backend contract** — [`properties-per-screen.md`](properties-per-screen.md): for every screen, what it displays, what the user enters, what it sends and what it needs to open, with the gaps for the backend.
- **My activity (customer)** — a new page that replaces the current My Activity screen (the Total / Completed / Upcoming counters are gone):
  - `MA1` **Upcoming** tab: reservations by day, **Confirmed** or **Waiting** for the place's answer.
  - `MA2` **Rewards** tab: ready to use (ending soonest first), then used or ended in grey.
  - `MA3` **History** tab by month: **Rate**, your rating (★ N), or **Book again** after a decline (with the reason) or a cancel.
  - `MA4` reservation waiting for an answer, `MA5` confirmed (no Add to calendar), both with the place (copy address, call) and Cancel.
  - `MA6` a reward: from, days left, single use, **Book with <place>**.

  It is the customer side of Reservations and Customers & rewards. Spec: [`docs/15-my-activity.md`](docs/15-my-activity.md). Small / medium / large references; components C44–C49; *My activity* data rules. Fixed: the `## Display rules` heading in `docs/06-data-model.md` is back.
- **Reservations (host)** — a new page for answering bookings, inside the host profile's calendar tab (amber badge = requests waiting):
  - `RV1` the tab: a requests banner, then **Today** and **Tomorrow**. No calendar strip.
  - `RV2` requests to answer, oldest first, with **Decline / Accept** on each card.
  - `RV3` one request with everything: offer used, customer with Call / Copy email, special requests.
  - `RV4` decline sheet with two reasons only, **Fully booked** and **Closed that day**, and no message.
  - `RV5` confirmed, with Cancel reservation.
  - `RV6` after the visit: **No-show / Yes, done**.

  Same screens for services, tables and events (what · people · optional team member), and no gendered copy. Spec: [`docs/14-reservations.md`](docs/14-reservations.md). Small / medium / large references; components C35–C43; the new *Reservation* data model.
  - Visits are now defined as done reservations (used by Customers & rewards).
- **Customers & rewards (host)** — a new page that replaces the current Customers / Send Loyalty Reward screens: `CR1` customers with group tiles and selection → `CR2` new reward with a live ticket preview (40-character message, stacked "Valid for" chips that fit other languages) → `CR3` sent; `CR4` Rewards tab with **monthly automatic rewards** (on/off) and what was sent; `CR5`–`CR8` a 4-step rule set-up (When · Who · Reward · Check); `CR9` edit a rule; `CR10` who used a reward. Spec: [`docs/13-customers-rewards.md`](docs/13-customers-rewards.md). Small / medium / large references; components C28–C34.
- **Team (host)** — a new page that replaces the current Team screen: `TM1` team grouped Active / Paused / Invites with one **Invite to team** button → `TM2` invite by username (sheet) → `TM3` team member (Active / Paused status, the services they do, remove). Spec: [`docs/12-team.md`](docs/12-team.md). Small / medium / large references; new token `status.warningBg`; components C25–C27.
- **Table booking (Food & Beverage)** — a new page: `TB1` month calendar (book weeks or months ahead) → `TB2` guests, offer and time on one screen (Any time / coupon / event states) → `TB3` your details with an offer reminder (three states) → `TB4` booked. Book now on `PF1` now opens `TB1`.
- **Offers in the salon calendar** — `F4` gets the same *Choose an offer* section, with coupon (`F4C`) and event (`F4E`) states.
- Small / medium / large references for all of the above; new tokens `color.calendar.*`, `color.offer.*` and radii for calendar cells, day tile and offer cards.
- Booking form: **First name and Last name are two fields** on one row (never "Full name").

## Screen inventory (70 screens × 3 sizes)

| Area | Screens |
|---|---|
| Host — own profile | `HP-profile` |
| Host — services (video first) | `HS1-services-list`, `HS2-add-video`, `HS3-service-details`, `HS4-edit-service` |
| Host — rooms (video first) | `HR1-rooms-list`, `HR2-add-video`, `HR3-room-details`, `HR4-edit-room` |
| Host — team | `TM1-team-list`, `TM2-invite`, `TM3-team-member` |
| Host — customers & rewards | `CR1-customers`, `CR2-new-reward`, `CR3-reward-sent`, `CR4-rewards-tab`, `CR5-auto-when`, `CR6-auto-who`, `CR7-auto-reward`, `CR8-auto-check`, `CR9-auto-edit`, `CR10-reward-details` |
| Host — reservations | `RV1-reservations`, `RV2-requests`, `RV3-request`, `RV4-decline`, `RV5-confirmed`, `RV6-after-visit` |
| Customer — my activity | `MA1-upcoming`, `MA2-rewards`, `MA3-history`, `MA4-reservation-waiting`, `MA5-reservation-confirmed`, `MA6-reward` |
| Profile — new post | `NP1-pick-video`, `NP2-empty`, `NP3-written`, `NP4-tag-place`, `EP1-edit-post`, `EP2-delete-video` |
| Public — search | `SR1-start`, `SR2-no-results`, `SR3-all`, `SR4-videos`, `SR5-places`, `SR6-deals` |
| Public — accommodation | `PA1-profile-rooms`, `PA2-room-video`, `PA3-room-included` |
| Public — services & F&B profiles | `PS1-profile-services`, `PF1-profile-fnb` |
| Salon booking — regular customer | `R1-services-stylist-picked`, `R2-video`, `R3-pick-time`, `SV-included` |
| Salon booking — first visit | `F1-services-everyone`, `F2-video`, `F3-choose-stylist`, `F4-pick-time` (+ offer states `F4C-pick-time-coupon`, `F4E-pick-time-event`) |
| Coupons & Events tab | `CE1-coupons-events` |
| Table booking — Food & Beverage | `TB1-pick-date`, `TB2-guests-time-any` (+ `TB2C-guests-time-coupon`, `TB2E-guests-time-event`), `TB3-details-any` (+ `TB3C-details-coupon`, `TB3E-details-event`), `TB4-booked` |

Ids with a `C` or `E` suffix are **states** of the screen before them (coupon or event chosen), not separate screens.

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

1. Read design-handoff/README.md and every file in design-handoff/docs/ (01–17) before writing code.
2. Map tokens.json into the app's theme (colours, type, radii, spacing). Do not add new values.
3. Build the shared components from docs/03-components.md first (C1–C62), then the screens from
   docs/04-screens.md, in the order: host services → host rooms → host team (TM1 → TM3, see
   docs/12-team.md) → host customers & rewards (CR1 → CR10, see docs/13-customers-rewards.md) →
   host reservations (RV1 → RV6, see docs/14-reservations.md) → public profiles →
   salon booking (regular, then first visit incl. the F4 offer states) →
   table booking (TB1 → TB4, see docs/11-table-booking.md) → coupons & events →
   customer my activity (MA1 → MA6, see docs/15-my-activity.md) → public search
   (SR1 → SR6, see docs/16-search.md) → new post (NP1 → NP4, EP1 → EP2, see docs/17-new-post.md).
4. Every screen must match screenshots/{small,medium,large}/<id>.png. Use the HTML in
   screens/ for exact sizes. Respect docs/07 for small/medium/large and safe areas.
5. Wire navigation exactly as docs/05-flows.md (and screens.json "links_to"). Screens with a
   C/E suffix are states of one screen (the chosen offer), not separate destinations.
6. Anything listed in docs/10-open-questions.md is out of scope: leave a TODO and ask.
7. When a screen is done, compare it to the screenshots at all three sizes and go through
   docs/09-acceptance-checklist.md (and docs/11 §12 for table booking, docs/12 §8 for team,
   docs/13 §13 for customers & rewards, docs/14 §13 for reservations, docs/15 §13 for my
   activity, docs/16 §14 for search, docs/17 §12 for new post). Report any deviation
   instead of silently changing the design.
```

## Running it in Claude Code (step by step)

1. **Put the handoff next to the code.** Copy `design-handoff/` into the root of the mobile app repository (or add this repository as a git submodule) so the agent can read the docs and open the screenshots.
2. **Start Claude Code in the app repository** (`claude` in a terminal at the repo root, or a Claude Code session on claude.ai/code with the app repo attached).
3. **Plan first.** Paste the prompt above and ask for a plan before code: theme mapping (tokens → theme), the component list C1–C62 with where each will live, and the screen order. Review the plan, then let it implement.
4. **One phase per session / pull request.** Use these follow-up prompts in order and review each PR against the screenshots before starting the next:

   | Phase | Prompt to paste |
   |---|---|
   | 1 · Theme + components | "Phase 1: map tokens.json into the theme and build components C1–C62 from docs/03 with previews at 360, 390 and 430 width. No screens yet." |
   | 2 · Host tools | "Phase 2: build HS1–HS4 and HR1–HR4 (docs/04, flow C in docs/05). Match screenshots/*/hs*.png and hr*.png." |
   | 2b · Team | "Phase 2b: build the Team page exactly as docs/12-team.md: TM1 team list grouped Active / Paused / Invites with one pinned Invite to team, TM2 invite-by-username sheet, TM3 team member (Active / Paused, services checklist = Who does it, Remove, Save changes). Replace the existing Team screen. Wire HP Team tile → TM1. Data per docs/06 (Team member, Team invite). Done = docs/12 §8 at small, medium and large." |
   | 2c · Customers & rewards | "Phase 2c: build the Customers & rewards page exactly as docs/13-customers-rewards.md: CR1 People tab (group tiles, pick people, Send reward), CR2 New reward (live ticket, 40-char message, duration chips), CR3 sent, CR4 Rewards tab (automatic rules with switches, sent rewards with Used by), CR5–CR8 the 4-step monthly rule (When on the F4 week strip, Who from visits in the month before the send, Reward, Check and turn on), CR9 edit, CR10 details. Replace the existing Customers and Send Loyalty Reward screens. Wire HP Customers tile → CR1. Data and the monthly send logic per docs/06 (Customer, Reward, Automatic reward rule). Done = docs/13 §13 at small, medium and large." |
   | 2d · Reservations | "Phase 2d: build the Reservations page exactly as docs/14-reservations.md: RV1 as the calendar tab of the host profile (amber badge = waiting requests, requests banner, Today and Tomorrow lists, no calendar strip), RV2 requests oldest first with Decline / Accept on each card, RV3 request details (summary with the offer strip, customer with Call / Copy email, special requests, pinned Decline / Accept), RV4 decline sheet with only Fully booked / Closed that day and no message, RV5 confirmed with Cancel reservation, RV6 did they come (No-show / Yes, done). Replace the existing Reservations tab. Category-neutral: one set of screens for services, tables and events. Data and states per docs/06 (Reservation): 24 h auto-decline, done automatically the next day, only DONE counts as a visit (feeds Customers & rewards). Done = docs/14 §13 at small, medium and large." |
   | 3 · Public profiles | "Phase 3: build HP, PA1–PA3, PS1, PF1 (CTA rules in docs/05 §E)." |
   | 4 · Salon booking | "Phase 4: build R1–R3, SV, F1–F4 with the F4 offer states F4C/F4E (docs/05 §B, docs/11 §8)." |
   | 5 · Table booking | "Phase 5: build the Table booking page exactly as docs/11-table-booking.md: TB1 month calendar, TB2 guests + Choose an offer + times (Any time / coupon / event states), TB3 details with the offer strip and First name / Last name fields, TB4 booked. Wire PF1 Book now → TB1. Data per docs/06 (Restaurant booking, Offer windows and sittings, Booking request). Done = docs/11 §12 at small, medium and large." |
   | 6 · Coupons & Events | "Phase 6: build CE1 (docs/03 C16, docs/04)." |
   | 7 · My activity | "Phase 7: build the customer's My activity page exactly as docs/15-my-activity.md: MA1–MA3 with the three tabs Upcoming · Rewards · History (counts in the labels, no Total / Completed / Upcoming counters), MA1 upcoming by day with Confirmed / Waiting, MA2 rewards ready to use (ending soonest first, faded used or ended), MA3 history by month with Rate / ★ N / Book again and the decline or cancel reason, MA4 / MA5 reservation waiting or confirmed (status banner, place card with Copy address and Call, Cancel; no Add to calendar, no Directions), MA6 reward with Book with <place>. Replace the existing My Activity screen. Data per docs/06 (Reservation customer fields, My activity). It reads the same reservations as phase 2d and the rewards from phase 2c. Done = docs/15 §13 at small, medium and large." |
   | 8 · Search | "Phase 8: build the public Search page exactly as docs/16-search.md: the Search tab of the bottom nav opens SR1 (search field, Recent searches with remove and Clear all, no Browse); typing shows SR3 with tabs All · Videos · Places · Deals (icon + label, no counts, unselected greyed 0.4, the query kept across tabs); All is one mixed feed in the order the backend ranks it (place rows, video rows of two, deal rows of two; no headings, no See all); SR4 videos (C7 with the place name), SR5 places (no icons: initial, name, verified, type · city, status), SR6 deals (2 per row, ending soonest first, All / Events / Coupons tiles); every list keeps loading with Loading more; SR2 no results. A place opens PS1 / PF1 / PA1, a video F2 / PA2, a deal F4C / F4E / TB2C / TB2E with the deal picked. Replace the existing Search screen. Data per docs/06 (Search). Done = docs/16 §14 at small, medium and large." |
   | 9 · New post | "Phase 9: build the New post page exactly as docs/17-new-post.md: the + in the bottom navigation opens NP1 (the video picker, one clip up to 100 MB, no Skip); NP2 / NP3 are the whole video with X, Change video, the poster, the frosted caption panel (title max 30 and description max 100 characters, fields that grow, counters n / 30 on the divider and n / 100 under the description, typing stops at the cap), the Tag tool on the side rail (dark without a tag, white with a green count badge with one) and Publish bottom right (greyed until there is a title); NP4 is the Tag a place sheet (search places, From your visits with a check, Done). A tag is a place, a service or a room; restaurants tag the place only. EP1 Edit post (from More on your own post: same editor, no Change video, Delete video bottom left, Save bottom right) and EP2 Delete video (sheet listing what is deleted, red Delete video). No hashtags, people tags, location or tag pill on the video. Data per docs/06 (Post). Done = docs/17 §12 at small, medium and large." |

5. **Verify every phase visually.** Run on an iPhone SE / 15 / 15 Pro Max simulator and 360 / ~393 / ~430-wide Android emulators, take screenshots, put them next to `screenshots/<size>/<id>.png` (overlay at 50 %), and go through `docs/09-acceptance-checklist.md`. Ask the agent to attach the screenshots and list any deviation in the PR description.
6. **Keep open questions open.** If the agent hits anything in `docs/10-open-questions.md` (for example validation errors on TB3 or R3 offers), it adds a TODO and asks; it does not design it.
