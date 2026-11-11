# Design handoff — Video-first profiles, booking, table booking, team, customer rewards, reservations, my activity, search, new post, account, host tools, the admin dashboard, Convert to Business and the website landing page

Everything an implementing agent needs to build the screens designed in the **Profile Quick Actions** design canvas, for **Android and iOS**, on **small, medium and large phones**, so the result looks exactly like the designs.

> Design canvas (private, owner access): https://claude.ai/artifact/5317zoDgLoVqdsUCq6HUpd
> Convert to Business comes from the Business conversion canvas (private, owner access): https://claude.ai/artifact/Vwih7Qv5GPRzwhYsL6zS6x
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
17. [`docs/18-account.md`](docs/18-account.md) — the full spec of the **Account** page (the Profile tab when signed out → continue with email → create account with the date of birth and an age check), with its own definition of done.
18. [`docs/19-admin.md`](docs/19-admin.md) — the full spec of the **Admin dashboard** (web, desktop): the three tabs Reviews · Analytics · Platform Users, every page name kept, the moderation queue, analytics by category, Host Approval, and the roles and security rules, with its own definition of done.
19. [`docs/20-coupons-events.md`](docs/20-coupons-events.md) — the full spec of **Coupons & events** for hosts (upload a video promo → write the title and description on it → set value, usage limit and schedule, or capacity, booking channel and schedule → a checklist shows what is left → check → create), with its own definition of done.
20. [`docs/21-business-conversion.md`](docs/21-business-conversion.md) — the full spec of **Convert to Business** (a person becomes a host: an overview with three steps → Legal Documents → Business Category, Kind of place, Business details → Operating hours → Create Business Account), with its own definition of done.
21. [`docs/22-landing-page.md`](docs/22-landing-page.md) — the full spec of the **website** for the MVP: one static page (computer and phone) that shows what Merg is and sends people to the App Store or Google Play, with its pictures, copy in RO and EN, links and its own definition of done.
22. [`docs/23-video-review.md`](docs/23-video-review.md) — the full spec of the customer's **Video review** (Rate in My activity → how many stars → what you liked / didn't like → one video, optional → a title on the video, optional → posted), with its own definition of done.
23. [`docs/10-open-questions.md`](docs/10-open-questions.md) — what is **not** designed yet. Do not invent these; ask.

## What is in this folder

| Path | What it is |
|---|---|
| `screenshots/{small,medium,large}/*.png` | Pixel reference for every screen at 2× (360×640, 390×844, 430×932 points). **What "done" looks like.** |
| `screenshots/desktop/*.png`, `screens/desktop/*.html` | The admin dashboard (web) and the website landing page (LP1) at 1440 × 900 (2× PNG), same format as the phone screens. The landing page on phones (LP2) is in the small, medium and large folders. |
| `screens/{small,medium,large}/*.html` | The original design markup, standalone. Open in a browser to inspect exact values (every style is inline). Links between screens work, so it is also a clickable prototype. |
| `screens/reference/icon-set.html` | The Quick Actions icon set and icon rules. |
| `assets/tiles/` | The standard images for the **Events** and **Coupons** tiles of the Coupons & Events tab: SVG master, Android WebP for each density, iOS image sets. **Use these files as they are**; the rules are in `assets/tiles/README.md`. |
| `screens/reference/tile-image*.html` | The two tile images, the tiles in the tab at small, medium and large, and the files, crop and rules. |
| `assets/landing/` | The website pictures: the phone picture for computers and for phones (WebP, 1× to 3×, transparent) and the link preview image. **Use these files as they are**; the rules are in `assets/landing/README.md`. Source: `screens/reference/landing-hero.html`. |
| `screens.json` | Manifest: every screen id, title, purpose, files per size, and the screens it links to. |
| `tokens.json` | Design tokens. |
| `strings.json` | UI strings in EN, RO, DE, IT, ES, FR taken from the designs. |
| `docs/` | The written spec (above). |
| `properties-per-screen.md` | For the backend: every screen's displayed data, inputs, actions and open parameters, with the gaps. |

## What's new in this update

- **Video review (customer)** — **Rate** on a done visit in My activity › History now opens a full-screen review, in this order:
  - `VR1` **how many stars**: five stars with their word (Bad · Not great · OK · Good · Great); Next waits for a star.
  - `VR2` **what you liked / didn't like**: two optional groups of six aspect chips (per category); an aspect is never in both.
  - `VR3` **add a video? (optional)**: one slot for **one** video, never a list. With nothing added, **Post review** posts the stars and the +/- right away.
  - `VR4` **one video added**: the video with **Change** and **Remove**; **Next**, or **Post without video**.
  - `VR5` **on the video**: the New post editor with the stars and +/- on it; title and description optional; the **Rate** tool ("4 / 5") on the side rail; **Publish**.
  - `VR6` **posted**: back in History, ★ N on the visit and "Review posted".
  - On VR1–VR4 the place card stays at the top, at the same position; the other cards are centred below it.

  Spec: [`docs/23-video-review.md`](docs/23-video-review.md). Small / medium / large references; components C89–C93; *Review* data in `docs/06`; rule A26 in the backend contract.

### Earlier updates

- **Convert to Business · How do you take bookings?** is now its own step, `BC5B`, right after the business details. It shows what each option covers before the person picks, as two cards (C87) with covered and not-covered rows (C88):
  - **In-app**: "People book in Merg. You answer in Reservations." Merg does it for you:
    - a Book button on your profile and videos;
    - requests in Reservations, accepted or declined in one tap;
    - confirmations and cancellations sent for you;
    - today's reservations in one list;
    - visits counted, to see regulars and send them rewards;
    - coupons and rewards taken off the price.

    "You: answer each request within 24 hours."
  - **By phone**: "People call you. You keep your own agenda."
    - Included: a Call button, your number on your events, nothing to answer in the app.
    - Not included: requests, confirmations and the day's list; visit counts, regulars and automatic rewards; coupons and rewards at booking.

    "You: answer calls and note each booking yourself." `BC5BP` shows By phone picked, with the required **Phone number people will call**.

  Two references at small, medium and large, drawn taller. BC5 no longer asks the question: its reference is unchanged in this update, and `docs/21` §6 says what to leave out. Spec: [`docs/21-business-conversion.md`](docs/21-business-conversion.md) §6a.

- **Website · Landing page (MVP)** — the MVP has no web version of the app, so the website is one static page that shows what Merg is and sends people to the stores. Two references:
  - `LP1` **on a computer** (1440 × 900, one screen):
    - the label "New · Now in Brașov", the headline "Deals and events near you, in short videos.", one lead line;
    - the App Store and Google Play buttons and a QR code to scan with the phone;
    - on the right, the app's feed on a phone, with the offer card and a reward ticket popping out.
  - `LP2` **on a phone** (360, 390 and 430 wide, full scroll): the same text with the two store buttons side by side in the first screen, the phone picture under them, and "Own a place? Merg for businesses" in the footer. No QR.

  The page calls no API: it is static, served from a CDN, and the store choice happens in a server redirect (`/get`, rule A25). The pictures are files in `assets/landing/` (WebP, about 100 KB on a phone), plus `og-image.jpg` for link previews. Copy in Romanian and English. Spec: [`docs/22-landing-page.md`](docs/22-landing-page.md). New components C83–C86; new tokens `font.size.landingTitle*` and `landingLead*`. The other boards on the canvas's Web version page (the map ideas) are work in progress and not in this handoff.

- **Convert to Business** — a signed-in person turns their account into a business (a host). Every text, input and option of the owner's sketch is kept, and only **Continue** is added. The page has 7 screens plus the category states (11 references at small, medium and large):
  - `BC1` **Overview**: home of the flow, with three step cards (Legal Documents · Business Information · Business Hours), the two agreements and **Create Business Account**, disabled until every step is done.
  - `BC2` **Legal Documents**: CUI (Tax ID) and the Company Certificate photo with "Before you upload".
  - `BC3` **Business Category**: Food & Beverage, Entertainment or Accommodation (C71 cards, the others greyed at 0.4). `BC3F` / `BC3S` are the other two picked.
  - `BC4` **Kind of place**: the category's place types, 3 per row, and "What do you offer?", 5 small tiles per row. `BC4F` (16 types, drawn taller) and `BC4S` (12 types, no offers) are the other categories.
  - `BC5` **Business details**: one form with Business Name, Phone Number, **How do you take bookings?** (In-app · By phone, now for every category), Price Range, Business Address on the map, both capacities and Services Offered. Drawn taller.
  - `BC6` **Operating hours**: seven days, 09:00 to 17:00 with a switch each.
  - `BC7` **Ready to submit**: every step checked, both boxes ticked, Create Business Account on. It sends the application that the admin approves in **Host Approval** (AD3).

  The screens use the app's components and tokens (C1, C17, C30, C32, C71); the differences from the canvas are listed in `docs/21` §12. Spec: [`docs/21-business-conversion.md`](docs/21-business-conversion.md). New components C74–C82; new token `font.size.stepTitle` (28, 24 on small); *Convert to Business* data in `docs/06`; rule A24 in the backend contract.

- **Coupons & Events tab · tile images** — the **Events** and **Coupons** filter tiles on CE1 now use two standard images instead of a video thumbnail:
  - **Events** (`tile_events`): a ticket with the event (group) icon, spotlights and confetti, on event purple.
  - **Coupons** (`tile_coupons`): a ticket with the percent icon, a soft glow and sparkles, on coupon green.
  - **Size and use:** 144 × 96 pt (3:2), opaque, with no text. The app draws them center-cropped and puts the gradient, the label and the count on top. White label contrast is at least 7.5 : 1 at every size.
  - **Files:** `assets/tiles/`, with an SVG master (about 3 KB), Android WebP quality 90 for mdpi → xxxhdpi (2–9 KB each) and iOS image sets with PNG @2x / @3x.
  - **References:** CE1 is updated at small, medium and large and loads the files. `screenshots/reference/tile-image*.png` shows each image, the tiles in the tab, and the files, crop and rules.

  Rules: `assets/tiles/README.md`, C6 in `docs/03`, *Images bundled in the app* in `docs/07`.

- **Coupons & events (host)** — a host creates a coupon or an event on its video promo, the way people post a video. Every element of the host's sketch is kept with its name. The page has 13 screens at small, medium and large:
  - `OF1` **Upload Video Promo**: one clip ("Short clips perform best (15-30s)").
  - `OF2` **on the video, empty**:
    - the **Coupon | Event** switch;
    - Title (n / 100) and Description ("Minimum 10 characters required", n / 500) written on the video;
    - Value, Usage Limit and Schedule on the side rail;
    - a **checklist** "To create the coupon · 2 of 6 done";
    - a smaller **Create Coupon**, disabled until the checklist is done.
  - `OF3` **Value** (% | RON, the sticker preview), `OF4` **Usage Limit** (Unlimited by default), `OF5` **Active Schedule** (Start / End Date, Start / End Time, said in one sentence): one sheet each, each explained in one line; Done opens the next.
  - `OF6` **all set**: "Checklist: all 6 done", Create Coupon on.
  - `OF7` **Check your coupon**: every item with its value, tap to change, Create Coupon → the Coupons & Events tab.
  - `OF8`–`OF13` **the same for an event**: Capacity (Unlimited by default) and **Booking channel** (In-app or Phone, explained) instead of Value and Usage Limit.

  Spec: [`docs/20-coupons-events.md`](docs/20-coupons-events.md). Components C67–C73; *Create a coupon or an event* data in `docs/06`; rule A23 in the backend contract. The **Coupons** tile in the host profile's Quick Actions now opens OF1.

- **Admin dashboard (web)** — the platform team's admin, restructured with **every page name kept**. Desktop screens at 1440 × 900:
  - `AD1` **Reviews**: one moderation queue (Pending Reviews · Approved Videos · Rejected Videos), the video in the middle, **Reject (R) · Approve (A) · Next (J)**, uploader and post details on the right.
  - `AD2` **Analytics**: grouped into Videos, People, Reservations and System Health, with a 24h / 7 days / 30 days switch.
  - `AD3` **Platform Users · Host Approval**: the Super Admin menu in groups (Approvals, People, Bookings & catalog, Platform, Audit Log with its seven pages), the applications table and the selected application with Approve / Reject.
  - Roles and security: the server checks every request; Moderator sees Reviews and Analytics, Super Admin everything; two-factor sign-in; every decision in a read-only Audit Log.

  Spec: [`docs/19-admin.md`](docs/19-admin.md). Components AC1–AC6; *Admin* data in `docs/06`.

- **Account (create or sign in)** — replaces the current welcome screen. No welcome wall: people watch and search without an account, and the Profile tab is where they sign up:
  - `AU1` **Profile tab, signed out**: Your profile, **Create account**, **Sign in**, **Privacy & data** at the bottom. No tagline, no feature rows, no terms line, no Skip.
  - `AU2` **Continue with email**: a new email creates an account, a known email signs in. Email only.
  - `AU3` **Create account**: First name | Last name, username (✓ Available), **date of birth** with a calendar **Change** pill, password.
  - `AU4` **Date of birth**: a dialog with three dark wheels Day · Month · Year, Cancel / Confirm.
  - `AU5` **under the minimum age** (16): red date and message, Create account disabled.

  Spec: [`docs/18-account.md`](docs/18-account.md). Small / medium / large references; components C63–C66; *Account* data in `docs/06`.
- **New post (profile)** — anyone posts a video on their own profile from the **+** in the bottom nav, the way people know from Instagram and TikTok:
  - `NP1` **pick a video**: one clip, up to 100 MB, no Skip.
  - `NP2` **on the video, empty**: the whole video, the title and description typed where people will read them, **Tag** on the side rail, **Publish** greyed until there is a title.
  - `NP3` **written and tagged**: title **max 30** and description **max 100** characters (counters, shown at the caps so the longest case is checked at every size), the Tag icon white with a count badge.
  - `NP4` **Tag a place** (sheet): search places, or one tap on a visit (tags the place and what was booked there).
  - `EP1` **Edit post**: the same editor with the saved post (no Change video), **Delete video** bottom left, **Save** bottom right.
  - `EP2` **Delete video** (sheet): the video and everything linked to it (title and description, tag, engagement: views and likes) are deleted for everyone.
  - No hashtags, no people tags, no location, no tag pill on the video.

  Spec: [`docs/17-new-post.md`](docs/17-new-post.md). Small / medium / large references; components C57–C62; *Post* data in `docs/06`. The **+** on the host profile (HP) now opens NP1.
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

## Screen inventory (105 phone screens × 3 sizes + 3 desktop screens)

| Area | Screens |
|---|---|
| Host — own profile | `HP-profile` |
| Host — services (video first) | `HS1-services-list`, `HS2-add-video`, `HS3-service-details`, `HS4-edit-service` |
| Host — rooms (video first) | `HR1-rooms-list`, `HR2-add-video`, `HR3-room-details`, `HR4-edit-room` |
| Host — team | `TM1-team-list`, `TM2-invite`, `TM3-team-member` |
| Host — customers & rewards | `CR1-customers`, `CR2-new-reward`, `CR3-reward-sent`, `CR4-rewards-tab`, `CR5-auto-when`, `CR6-auto-who`, `CR7-auto-reward`, `CR8-auto-check`, `CR9-auto-edit`, `CR10-reward-details` |
| Host — reservations | `RV1-reservations`, `RV2-requests`, `RV3-request`, `RV4-decline`, `RV5-confirmed`, `RV6-after-visit` |
| Host — coupons & events (create) | `OF1-pick-video`, `OF2-coupon-empty`, `OF3-value`, `OF4-usage-limit`, `OF5-coupon-schedule`, `OF6-coupon-ready`, `OF7-coupon-check`, `OF8-event-empty`, `OF9-capacity`, `OF10-booking-channel`, `OF11-event-schedule`, `OF12-event-ready`, `OF13-event-check` |
| Customer — my activity | `MA1-upcoming`, `MA2-rewards`, `MA3-history`, `MA4-reservation-waiting`, `MA5-reservation-confirmed`, `MA6-reward` |
| Customer — video review | `VR1-stars`, `VR2-details`, `VR3-add-video`, `VR4-video-added`, `VR5-on-video`, `VR6-posted` |
| Profile — new post | `NP1-pick-video`, `NP2-empty`, `NP3-written`, `NP4-tag-place`, `EP1-edit-post`, `EP2-delete-video` |
| Account — create or sign in | `AU1-profile-signed-out`, `AU2-email`, `AU3-create-account`, `AU4-date-of-birth`, `AU5-too-young` |
| Admin — web dashboard (desktop) | `AD1-reviews`, `AD2-analytics`, `AD3-host-approval` |
| Public — search | `SR1-start`, `SR2-no-results`, `SR3-all`, `SR4-videos`, `SR5-places`, `SR6-deals` |
| Public — accommodation | `PA1-profile-rooms`, `PA2-room-video`, `PA3-room-included` |
| Public — services & F&B profiles | `PS1-profile-services`, `PF1-profile-fnb` |
| Salon booking — regular customer | `R1-services-stylist-picked`, `R2-video`, `R3-pick-time`, `SV-included` |
| Salon booking — first visit | `F1-services-everyone`, `F2-video`, `F3-choose-stylist`, `F4-pick-time` (+ offer states `F4C-pick-time-coupon`, `F4E-pick-time-event`) |
| Coupons & Events tab | `CE1-coupons-events` |
| Table booking — Food & Beverage | `TB1-pick-date`, `TB2-guests-time-any` (+ `TB2C-guests-time-coupon`, `TB2E-guests-time-event`), `TB3-details-any` (+ `TB3C-details-coupon`, `TB3E-details-event`), `TB4-booked` |
| Account — convert to business | `BC1-overview`, `BC2-legal`, `BC3-category` (+ `BC3F-category-fnb`, `BC3S-category-entertainment`), `BC4-place-type` (+ `BC4F-place-type-fnb`, `BC4S-place-type-entertainment`), `BC5-details`, `BC6-hours`, `BC7-ready` |

Ids with a `C` or `E` suffix are **states** of the screen before them (coupon or event chosen), not separate screens. In Convert to Business, `BC3` / `BC4` ids with an `F` or `S` suffix are the Food & Beverage or Entertainment (`SERVICES`) states.

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

1. Read design-handoff/README.md and every file in design-handoff/docs/ (01–23) before writing code.
2. Map tokens.json into the app's theme (colours, type, radii, spacing). Do not add new values.
   Copy the images in design-handoff/assets/ into the app as they are (assets/tiles/README.md says
   where each file goes). Do not redraw, recolour or replace them.
3. Build the shared components from docs/03-components.md first (C1–C93), then the screens from
   docs/04-screens.md, in the order: host services → host rooms → host team (TM1 → TM3, see
   docs/12-team.md) → host customers & rewards (CR1 → CR10, see docs/13-customers-rewards.md) →
   host reservations (RV1 → RV6, see docs/14-reservations.md) → public profiles →
   salon booking (regular, then first visit incl. the F4 offer states) →
   table booking (TB1 → TB4, see docs/11-table-booking.md) → coupons & events (CE1, then the
   host's create flow OF1 → OF13, see docs/20-coupons-events.md) →
   customer my activity (MA1 → MA6, see docs/15-my-activity.md) → customer video review (VR1 → VR6,
   see docs/23-video-review.md) → public search
   (SR1 → SR6, see docs/16-search.md) → new post (NP1 → NP4, EP1 → EP2, see docs/17-new-post.md) → account
   (AU1 → AU5, see docs/18-account.md) → convert to business (BC1 → BC7 with the BC3 / BC4 category
   states, see docs/21-business-conversion.md). The admin dashboard (AD1 → AD3, web, see
   docs/19-admin.md) is a separate web app: build it after the mobile app, or in its own repository.
4. Every screen must match screenshots/{small,medium,large}/<id>.png. Use the HTML in
   screens/ for exact sizes. Respect docs/07 for small/medium/large and safe areas.
5. Wire navigation exactly as docs/05-flows.md (and screens.json "links_to"). Screens with a
   C/E suffix are states of one screen (the chosen offer), not separate destinations.
6. Anything listed in docs/10-open-questions.md is out of scope: leave a TODO and ask.
7. When a screen is done, compare it to the screenshots at all three sizes and go through
   docs/09-acceptance-checklist.md (and docs/11 §12 for table booking, docs/12 §8 for team,
   docs/13 §13 for customers & rewards, docs/14 §13 for reservations, docs/15 §13 for my
   activity, docs/16 §14 for search, docs/17 §12 for new post, docs/18 §11 for account, docs/19 §11 for the admin, docs/20 §11 for coupons & events, docs/21 §13 for convert to business, docs/23 §12 for the video review). Report any deviation
   instead of silently changing the design.
```

## Running it in Claude Code (step by step)

1. **Put the handoff next to the code.** Copy `design-handoff/` into the root of the mobile app repository (or add this repository as a git submodule) so the agent can read the docs and open the screenshots.
2. **Start Claude Code in the app repository** (`claude` in a terminal at the repo root, or a Claude Code session on claude.ai/code with the app repo attached).
3. **Plan first.** Paste the prompt above and ask for a plan before code: theme mapping (tokens → theme), the component list C1–C93 with where each will live, and the screen order. Review the plan, then let it implement.
4. **One phase per session / pull request.** Use these follow-up prompts in order and review each PR against the screenshots before starting the next:

   | Phase | Prompt to paste |
   |---|---|
   | 1 · Theme + components | "Phase 1: map tokens.json into the theme and build components C1–C93 from docs/03 with previews at 360, 390 and 430 width. No screens yet." |
   | 2 · Host tools | "Phase 2: build HS1–HS4 and HR1–HR4 (docs/04, flow C in docs/05). Match screenshots/*/hs*.png and hr*.png." |
   | 2b · Team | "Phase 2b: build the Team page exactly as docs/12-team.md: TM1 team list grouped Active / Paused / Invites with one pinned Invite to team, TM2 invite-by-username sheet, TM3 team member (Active / Paused, services checklist = Who does it, Remove, Save changes). Replace the existing Team screen. Wire HP Team tile → TM1. Data per docs/06 (Team member, Team invite). Done = docs/12 §8 at small, medium and large." |
   | 2c · Customers & rewards | "Phase 2c: build the Customers & rewards page exactly as docs/13-customers-rewards.md: CR1 People tab (group tiles, pick people, Send reward), CR2 New reward (live ticket, 40-char message, duration chips), CR3 sent, CR4 Rewards tab (automatic rules with switches, sent rewards with Used by), CR5–CR8 the 4-step monthly rule (When on the F4 week strip, Who from visits in the month before the send, Reward, Check and turn on), CR9 edit, CR10 details. Replace the existing Customers and Send Loyalty Reward screens. Wire HP Customers tile → CR1. Data and the monthly send logic per docs/06 (Customer, Reward, Automatic reward rule). Done = docs/13 §13 at small, medium and large." |
   | 2d · Reservations | "Phase 2d: build the Reservations page exactly as docs/14-reservations.md: RV1 as the calendar tab of the host profile (amber badge = waiting requests, requests banner, Today and Tomorrow lists, no calendar strip), RV2 requests oldest first with Decline / Accept on each card, RV3 request details (summary with the offer strip, customer with Call / Copy email, special requests, pinned Decline / Accept), RV4 decline sheet with only Fully booked / Closed that day and no message, RV5 confirmed with Cancel reservation, RV6 did they come (No-show / Yes, done). Replace the existing Reservations tab. Category-neutral: one set of screens for services, tables and events. Data and states per docs/06 (Reservation): 24 h auto-decline, done automatically the next day, only DONE counts as a visit (feeds Customers & rewards). Done = docs/14 §13 at small, medium and large." |
   | 3 · Public profiles | "Phase 3: build HP, PA1–PA3, PS1, PF1 (CTA rules in docs/05 §E)." |
   | 4 · Salon booking | "Phase 4: build R1–R3, SV, F1–F4 with the F4 offer states F4C/F4E (docs/05 §B, docs/11 §8)." |
   | 5 · Table booking | "Phase 5: build the Table booking page exactly as docs/11-table-booking.md: TB1 month calendar, TB2 guests + Choose an offer + times (Any time / coupon / event states), TB3 details with the offer strip and First name / Last name fields, TB4 booked. Wire PF1 Book now → TB1. Data per docs/06 (Restaurant booking, Offer windows and sittings, Booking request). Done = docs/11 §12 at small, medium and large." |
   | 6 · Coupons & Events | "Phase 6: build CE1 (docs/03 C6 and C16, docs/04). The Events and Coupons tiles use the bundled images from assets/tiles/ exactly as assets/tiles/README.md says: Android res/drawable-* WebP, iOS image sets, center-cropped to fill the tile, with the bottom gradient, label and count drawn on top; a dark fallback colour while loading; never a video thumbnail. Match screenshots/*/ce1-coupons-events.png and screenshots/reference/tile-images-in-tab.png." |
   | 7 · My activity | "Phase 7: build the customer's My activity page exactly as docs/15-my-activity.md: MA1–MA3 with the three tabs Upcoming · Rewards · History (counts in the labels, no Total / Completed / Upcoming counters), MA1 upcoming by day with Confirmed / Waiting, MA2 rewards ready to use (ending soonest first, faded used or ended), MA3 history by month with Rate / ★ N / Book again and the decline or cancel reason, MA4 / MA5 reservation waiting or confirmed (status banner, place card with Copy address and Call, Cancel; no Add to calendar, no Directions), MA6 reward with Book with <place>. Replace the existing My Activity screen. Data per docs/06 (Reservation customer fields, My activity). It reads the same reservations as phase 2d and the rewards from phase 2c. Done = docs/15 §13 at small, medium and large." |
   | 8 · Search | "Phase 8: build the public Search page exactly as docs/16-search.md: the Search tab of the bottom nav opens SR1 (search field, Recent searches with remove and Clear all, no Browse); typing shows SR3 with tabs All · Videos · Places · Deals (icon + label, no counts, unselected greyed 0.4, the query kept across tabs); All is one mixed feed in the order the backend ranks it (place rows, video rows of two, deal rows of two; no headings, no See all); SR4 videos (C7 with the place name), SR5 places (no icons: initial, name, verified, type · city, status), SR6 deals (2 per row, ending soonest first, All / Events / Coupons tiles); every list keeps loading with Loading more; SR2 no results. A place opens PS1 / PF1 / PA1, a video F2 / PA2, a deal F4C / F4E / TB2C / TB2E with the deal picked. Replace the existing Search screen. Data per docs/06 (Search). Done = docs/16 §14 at small, medium and large." |
   | 9 · New post | "Phase 9: build the New post page exactly as docs/17-new-post.md: the + in the bottom navigation opens NP1 (the video picker, one clip up to 100 MB, no Skip); NP2 / NP3 are the whole video with X, Change video, the poster, the frosted caption panel (title max 30 and description max 100 characters, fields that grow, counters n / 30 on the divider and n / 100 under the description, typing stops at the cap), the Tag tool on the side rail (dark without a tag, white with a green count badge with one) and Publish bottom right (greyed until there is a title); NP4 is the Tag a place sheet (search places, From your visits with a check, Done). A tag is a place, a service or a room; restaurants tag the place only. EP1 Edit post (from More on your own post: same editor, no Change video, Delete video bottom left, Save bottom right) and EP2 Delete video (sheet listing what is deleted, red Delete video). No hashtags, people tags, location or tag pill on the video. Data per docs/06 (Post). Done = docs/17 §12 at small, medium and large." |
   | 10 · Account | "Phase 10: build the Account page exactly as docs/18-account.md: no welcome wall, people browse without an account; signed out, the Profile tab shows AU1 (dashed avatar, Your profile, one line, Create account, Sign in, Privacy & data at the bottom, the bottom nav); both buttons open AU2 Continue with email; a new email goes to AU3 Create account (First name and Last name as two fields, username with Available, date of birth with the calendar Change pill, password with show / hide); the date opens AU4, a centred dialog with three ink wheels Day · Month · Year (months as names) and Cancel / Confirm; under the minimum age AU5 shows the red date and alert line and disables Create account. Email only, no terms line, no Skip. Replace the existing welcome screen. Data per docs/06 (Account). Done = docs/18 §11 at small, medium and large." |
   | 11 · Admin dashboard (web) | "Phase 11: build the admin web app exactly as docs/19-admin.md, at 1440 × 900 and working from 1280 wide: the top bar with the three tabs Reviews · Analytics · Platform Users (badges for pending reviews and host applications); Reviews as one moderation queue (Pending Reviews, Approved Videos, Rejected Videos; oldest first; Reject R with a reason, Approve A, Next J, Undo); Analytics in four sections with a 24h / 7 days / 30 days switch; Platform Users with the grouped Super Admin menu keeping every page name, and Host Approval with the applications table and detail card. Enforce the roles on the server (Moderator: Reviews and Analytics; Super Admin: everything), two-factor sign-in, password again for risky actions, every decision in the read-only Audit Log. Data per docs/06 (Admin). Done = docs/19 §11." |
   | 12 · Coupons & events (host) | "Phase 12: build the host's create flow exactly as docs/20-coupons-events.md. Quick Actions → Coupons opens OF1 Upload Video Promo (one clip). OF2 / OF8 are the video with the Coupon \| Event switch (keeps the video, title, description and schedule), the checklist card "To create the coupon / event · n of 6 done" (done items green, to-do items with an amber ring, each opens its field or sheet; when done it becomes the green "Checklist: all 6 done" pill), the side rail (Value, Usage Limit, Schedule or Capacity, Booking channel, Schedule: white with the value when set, dark with an amber dot when missing), Title 1–100 and Description 10–500 written on the video, and Create Coupon / Create Event 44 tall, disabled until the checklist is done. One sheet per setting with one explaining line; Done opens the next; Usage Limit and Capacity default to Unlimited; Value, Booking channel and Active Schedule have no default. Create opens the check sheet (OF7 / OF13); its Create sends OfferCreateRequest and opens CE1. Data per docs/06 (Create a coupon or an event) and A23. Done = docs/20 §11 at small, medium and large." |
   | 13 · Convert to Business | "Phase 13: build the Convert to Business page exactly as docs/21-business-conversion.md. The person's own profile opens BC1, the overview: three C74 step cards (the next step with the ink border and tile, a done step with the green check), the C75 agreements card and Create Business Account, disabled at 0.4 until the three steps are done and both boxes are ticked. Every step has the C1 top bar 'Convert to Business' with the n/3 counter, the C32 progress bar with three segments and a pinned C17 button. BC2 Legal Documents: CUI (numeric, RO allowed) and the certificate photo (C80) under 'Before you upload'; Continue to Business Info opens BC3. BC3 Business Category with C71 cards (the others at 0.4). BC4 Kind of place: the category's place types as C77 tiles, 3 per row, and for Food & Beverage and Accommodation 'What do you offer?' as C78 tiles, 5 per row, up to 6. Changing the category clears both. BC5 Business details is one form in the order of docs/21 §6, with How do you take bookings? (C71 In-app / By phone), the C81 map picker and the n / 1000 counter. BC6 has seven C82 rows with 24-hour pickers and a C30 switch. Create Business Account sends BusinessApplicationRequest, which shows as a Pending HostApplication in Host Approval. Keep every owner's text exactly. Place type names must never overflow: 'Mediterranean' fits at 360. Data per docs/06 (Convert to Business) and A24. Done = docs/21 §13 at small, medium and large." |
   | 14 · Video review | "Phase 14: build the customer's video review exactly as docs/23-video-review.md. Rate on an unrated done visit in My activity › History (MA3) opens VR1, full screen: the place card pinned at the top, the other cards centred below it, the button pinned at the bottom. VR1 five stars with their word (Next waits for a star); VR2 the same screen after a star with What you liked / What you didn't like (six aspect chips per category, optional, never both). VR3 Add a video? (optional): one slot for one video, never a list; Post review without a video. VR4 the one video with Change / Remove; Next or Post without video; the card keeps its size. VR5 the New post editor with the stars and +/- on the video, the Rate tool 'N / 5' on the side rail, title (0–30) and description (0–100) optional, Publish. Posting sends ReviewCreateRequest, sets myRating and returns to MA3 with ★ N and 'Review posted' (VR6). Data per docs/06 (Review) and A26. Done = docs/23 §12 at small, medium and large." |

5. **Verify every phase visually.** Run on an iPhone SE / 15 / 15 Pro Max simulator and 360 / ~393 / ~430-wide Android emulators, take screenshots, put them next to `screenshots/<size>/<id>.png` (overlay at 50 %), and go through `docs/09-acceptance-checklist.md`. Ask the agent to attach the screenshots and list any deviation in the PR description.
6. **Keep open questions open.** If the agent hits anything in `docs/10-open-questions.md` (for example validation errors on TB3 or R3 offers), it adds a TODO and asks; it does not design it.
