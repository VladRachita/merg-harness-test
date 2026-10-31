# 03 · Components

The admin dashboard (web) has its own components, AC1–AC6, in `19-admin.md` §8.

Build these once and reuse them. Values are for the **medium** phone (390 × 844); see `07-responsive-and-platforms.md` for small/large. Exact markup for each component is in `../screens/medium/<screen>.html` (search the screen named in "Seen in").

---

## Icons (Lucide names)

| Meaning | Lucide | Meaning | Lucide |
|---|---|---|---|
| Back | `arrow-left` | Close / not included item | `x` |
| Play (filled) | `play` | Mute / sound | `volume-2` |
| Like | `heart` | Book / calendar / event | `calendar` |
| Call (filled) | `phone` | More | `more-vertical` / `more-horizontal` |
| People / guests | `users` | Duration / hours | `clock` |
| Price | `banknote` | Coupon / discount | `tag` |
| Ticket count | `ticket` | Time left | `hourglass` |
| Address | `map-pin` | Copy address | `copy` |
| Included | `check` | Not included (section) | `circle-x` |
| Not allowed | `ban` | Anyone (any stylist) | `shuffle` |
| Salon pin | `scissors` | Room / bedroom | `bed-double` |
| Restaurant pin | `utensils` | Services tab | `concierge-bell` |
| Coupons tab | `ticket-percent` | Reviews / rating | `star` |
| Languages | `globe` | Wi-Fi / comfort | `wifi` |
| Parking / outside | `car` | Bathroom | `bath` |
| Kitchen | `coffee` | "All" filter | `layout-grid` |
| Edit | `pencil` | Delete | `trash-2` |
| Add | `plus` | Chevron | `chevron-right` / `chevron-down` |
| Can replace | `arrow-left-right` | Video / no video | `video` |
| Check-in | `log-in` | Bookings | `clipboard-check` |
| Customers | `book-user` | Settings | `settings` |
| Coupon offer (badge, sticker) | `percent` | Event offer (badge, sticker) | custom 3-person "group" path (see `11-table-booking.md` §5) |
| Special requests | `message-square` | Add to calendar | `calendar-plus` |
| Email | `mail` | Info note | `info` |
| Home / Search / Map / Profile (nav) | `home` / `search` / `map-pin` / `user` | Videos tab | `square-play` |
| Reservations tab | `calendar` (+ C35 badge) | Visit check (did they come) | `calendar-check` |
| No-show | `user-x` | New customer | `sparkles` |
| Accept / Decline | `check` / `x` | Copy email | `copy` |
| Rewards (tab, from) | `gift` | History tab | `history` |
| Book again | `repeat` | Waiting for an answer | `hourglass` |
| Search field / no results | `search` | Recent search | `clock` |
| Places tab (search) | `store` | Deals tab (search) | `ticket-percent` |
| Tag a place (new post) | `store` | Change video | `refresh-cw` |
| Publish (new post) | `upload` | Title and description (delete list) | `text` |
| Save (edit post) | `check` | Delete video | `trash-2` |
| Email (account) | `mail` | Username | `at-sign` |
| Date of birth | `cake` | Pick / change a date | `calendar` |
| Password / show | `lock` / `eye` | Privacy & data | `shield` |
| Too young (alert) | `circle-alert` | Signed-out avatar | `user` |

Stroke 1.8 at 20–26 px, 2–2.4 at 12–16 px. Filled: play, phone, star, more dots.

---

## 1. Top bar
- Height 56 (64 if title has a second line), padding `0 6`.
- Left: back `arrow-left` 24 in a 44 target. Video screens use **X (close)** instead of back.
- Title: 18/500 left-aligned after the back button (host & booking screens) **or** centred 15/500 handle (public profile, e.g. `@stay_host_brasov`).
- Right: optional 44 icon button (`more-vertical`; on edit screens a red `trash-2` = Delete).
- Seen in: all light screens.

## 2. Public profile header
- Avatar 76 circle, white, 1px `line.divider`, placeholder `user` icon 34.
- Name 21/700 (margin-top 14) · category 13 secondary (e.g. "Accommodation", "Services · Barber & salon").
- Stats: 3 columns, max width 300, value 17/500, label 12 secondary (Posts · Followers · reviews).
- Actions row: grid `1fr 2fr`, gap 10, height 48, radius 14.
  - **Follow** — `bg.soft`, 15/500.
  - **Primary CTA** — slate `#3F5079`, white, 15/500, icon 18 + label: **Call** (`phone`, accommodation) or **Book now** (`calendar`, services & F&B).
- Seen in: PA1, PS1, PF1.

## 3. About card (map card)
White section, radius 18, 1px `line.card`, margin-top 16.
1. **Map** 150 tall (OpenStreetMap tiles in production; `bg.map` placeholder in mocks). Centre pin: 34 ink circle, white type icon 17 (`bed-double` / `scissors` / `utensils`), shadow `mapPin`.
   - Attribution "© OpenStreetMap" top-right, 9.5 secondary on `rgba(255,255,255,.8)`, radius 4 — **required by OSM**.
   - **Address pill** (left/right/bottom 10, height 40, radius 20, white, shadow): `map-pin` 16 + address 14/500 (ellipsis) + `copy` 16 secondary. **Tap copies the address** (show a toast "Address copied"). No Directions button.
2. **Fact strip**, 2 equal columns, min-height 64, 1px vertical separator `line.rowSeparator`:
   - Left — **Hours cell** (button, opens the weekly hours): `clock` 18 + status line 14/600 + detail 12.5 secondary + `chevron-down` 16 tertiary. Status states:
     - Open now (`status.successText`) · "Closes 23:59"
     - Closes soon (`status.warningText`) · "Until 22:30" (proposal: < 60 min to closing)
     - Closed (`status.danger`) · "Opens 09:00"
     - **Accommodation:** not a button — `log-in` icon + "Check-in 14:00" / "Check-out 11:00".
   - Right — **Price level**: price meter + level 14/600 + "Price level" 12.5 secondary.
- **Price meter**: 4 bars 3 wide, heights 6/9/12/15, gap 2, filled `text.primary`, empty `line.strong`. Levels: 1 Budget · 2 Moderate · 3 Expensive · 4 Luxury (1 and 4 labels are proposals).
- Seen in: PA1, PS1, PF1.

## 4. Profile tabs
Equal columns, 60 tall, icon 20 + label 12. Selected: `text.primary` 500 + 2px bottom border; others `text.secondary`. Track: 1px bottom `line.divider`.
Accommodation: Videos · Rooms · Coupons · Reviews. Services: Videos · Services · Coupons · Reviews. (Coupons tab mock shows Videos · Coupons · Reviews.)

## 5. Team filter (stylist rail)
Horizontal row, padding `14 16 0`, gap 4. Item 68 wide: avatar 52 (Everyone = ink circle with `users` 22; person = colour circle with initial 17/600) + name 12.
- Selected: ring + name 600. **All others 0.4** (still tappable).
- Picking a stylist switches the list to that stylist's services and decides the booking path (see flows).
- Seen in: R1, F1.

## 6. Category tiles (filter)
- R1/F1: horizontal scroll, tiles 98 × 66, radius 13, gap 9.
- CE1: 3 tiles fill the row (flex 1), 72 tall.
- **All** tile: ink background, `layout-grid` 18 top-left, label 12.5/600 + count 11 (white .8) at the bottom.
- **Photo tile**: category image, bottom gradient 42–46 tall (`0 → rgba(0,0,0,.7)`), label + count bottom (left/right 9, bottom 7).
- Selected: ring. Empty category (count 0): 0.4 and disabled.
- Search Deals (SR6): plain icon tiles (All `layout-grid` · Events group icon · Coupons `percent`), 60 tall, white with 1px `line.card` at 0.4 when not selected, **no counts**. Spec: `16-search.md` §8.

## 7. Public video card (2 columns)
- Height 290, radius 22, `dark.card` base, media full-bleed, **top scrim + bottom scrim** (tokens).
- Play button 44 centred.
- Top content (padding 14): title 16/600, 2-line clamp, text-shadow; services also show an **avatar stack** of who does it (24 avatars, white 2px border, overlap −7).
- **Price pill**: white .94, height 26, radius 13, `banknote` 15 + amount 13/700 + optional unit 11/400 secondary ("/ night"); services without fixed price show "from" before the amount.
- **Bottom pill** (centred, 44 hit area, visible 36 tall, white, radius 18, padding `0 10 0 12`, 13/500):
  - Rooms: `users` 15 + **N** (600) · 1×16 divider · "Details" + `chevron-right` 14.
  - Services: `users` 15 + **N** · divider · `clock` 14 + "60 min" + `chevron-right` 14.
- No-video variant: `dark.noVideo` background with the category icon (e.g. `scissors` 56, white .28) and no play button.
- Tap play or pill → item video (or the booking step if there is no video — see flows).
- Search variant (SR3, SR4): **the place's name** under the title (12.5, white .88, 1 line, ellipsis) instead of the avatar stack.
- Seen in: PA1, PS1, R1, F1, SR3, SR4.

## 8. Host video card (2 columns)
- Height 306, radius 22. Media full-bleed (no scrims). Play 44 at top 80 **or** "No video yet" (`video` 24 + 12/400 white .7) at top 76.
- **Glass panel** at the bottom (inset 10, padding `10 12 12`, radius 16, glass token): title 14.5/600 2-line clamp · price row `banknote` 16 + 14/700 (+ "/ night" 11.5 white .78) · facts 12.5/500 white .9 (`users` 14 + N, rooms only; services: + divider + `clock` + "60 min").
- **Edit** button: card corner, top 4 / right 4, 44 hit area, white 32 circle, `pencil` 15 ink, shadow. Opens Edit. **No other buttons** on the card.
- **New item tile**: dashed 1.5 `line.strong`, radius 22, min-height 140; ink 52 circle with `plus`; "New service"/"New room" 15/500; "Start with a video" 12.5 secondary.
- Seen in: HS1, HR1.

## 9. Host bottom navigation
72 tall, `dark.navBar`, 5 columns: Home · Search · Create (44 circle `dark.navCreate`, `plus`) · Map · Profile. Icon 24, label 10.5; active white 500, inactive `dark.navInactive`. Seen in HP, HS1, HR1.

## 10. Video picker
- Dark (`dark.pickerBg`), white text. Header 56: X (Close) left · "Add a video" 16/500 centred · "Skip" right (white .78).
- Sub-header 48: "Recents ▾" button + hint 13 white .62 ("Pick a clip that shows the service" / "…the room").
- Grid 3 columns, gap 2, tiles 172 tall; duration 12/500 bottom-right; selection circle 24 top-right (unselected: 1.5 border white .85; selected: white circle with ink check + inset 3px white frame on the tile). **Single selection.**
- Bottom: "1 video · 0:24" 14 white .72 + **Next** (white pill 48, radius 24, ink 16/500). No record, no edit.
- Seen in: HS2, HR2, NP1 (title "New post", hint "Pick one clip · up to 100 MB", **no Skip**).

## 11. Host form
Header (back + title; edit screens add red trash). Then, gap 12:
1. Helper line: `video` 15 + "Everything here is shown on your video" 13 secondary.
2. **Name & description card** (white, radius 18, border, padding 14, gap 14): name input 19/500 (32 tall, no border) + short description textarea 15/1.45 (≈ 2 lines) on the left; **video thumb** 84 × 112 radius 12 on the right (play + "Change" bar 26, `rgba(0,0,0,.55)`), or a dashed **Add video** tile when there is none.
3. **Facts card** (rows 56, separators `line.rowSeparator`):
   - Price: `banknote` 22 + "Price" 16 + right-aligned input 16/500 + "RON" 15 secondary + unit: services **"/ visit ▾"** (picker: visit / person) · rooms **"/ night"** (fixed).
   - Duration (services only): `clock` + "Duration" + value + chevron → duration picker.
   - People per booking (services) / Guests (rooms): stepper − value + (32 outlined circles in 44 targets).
4. **What's included card** (padding `12 14 14`, gap 8): three chip groups, each header 14/600:
   - **Included · N** — chips 32 tall, radius 16, `bg.soft`, 13/500, green `check` 15. Show the first 4 + an ink "+N more" chip when long.
   - **Not included** — same chips with grey `x`.
   - **Not allowed** — same chips with red `ban`.
   - Each group ends with a dashed **Add** chip (`plus`).
5. **Who does it** (services only): avatars 40 + name 12; ticked = green 18 check badge; not ticked = 0.4.
- Bottom bar: **Save service / Save room / Save changes** — ink, 52 tall, radius 16, full width, padding `12 16 28`.
- The form scrolls; Save stays pinned.
- Seen in: HS3, HS4, HR3, HR4.

## 12. Video player overlay
Full-bleed vertical video, video top & bottom scrims.
- **X close** top-left (44, `x` 24 white, stroke 2.2, drop shadow) below the status bar. **Mute** top-right (38 circle `rgba(0,0,0,.35)`, `volume-2` 19).
- **Side rail** (right 8, bottom 120, width 60, gap 12), each item = 44 circle `rgba(0,0,0,.4)` + label 12/500 with text-shadow:
  - Like (`heart`) + count.
  - **Action**: **Book** (`calendar`) for services · **Call** (`phone`, filled) for rooms.
  - More (`more-vertical`).
- **Creator block** (left 16, right 84, bottom 116, gap 8): avatar 36 + name 14/600 + handle 12 white .8 · caption 14/1.4 (2-line clamp) · **included chips** · "5 views · Oct 21, 2026" 12 white .75.
- **Included chips**: first 2 included items as dark chips (28 tall, radius 14, `rgba(0,0,0,.45)`, `check` 14 `status.successOnDark` + 12.5/500) + a **white "+N more ›"** chip (12.5/600) with a 44 hit area → opens the Included sheet.
- **Info bar** (left/right 12, bottom 28, height 64, radius 18, white, shadow): title 15/600 (ellipsis) + facts 12.5 secondary. Services: [stylist name if picked] · `clock` 60 min · `users` 1 person · `banknote` **120 RON** (ink 600). Rooms: `users` 2 guests · **250 RON / night**. **Not tappable, no arrow.**
- Seen in: R2, F2, PA2.

## 13. "What's included" bottom sheet
- Opens over the video; video stays visible, dimmed `rgba(0,0,0,.45)`. Close by X, handle, or tapping the dim area.
- Sheet: white, top radius 24, padding `0 20 24`, height = content but **max = screen height − 64** (then scrolls).
- Handle 36 × 4 `line.strong` (64 × 24 hit area) · title "What's included" 19/600 + " · N" 400 secondary · close: 32 `bg.soft` circle with `x` 16 (44 hit) · subtitle 13 secondary (e.g. "Haircut · 60 min · 120 RON").
- **Services list**: rows 36, tick circle 22 (`status.successBg` + `status.successText` check), text 14.5, separators `line.rowSeparator`.
- **Rooms list**: grouped (Bedroom `bed-double`, Bathroom `bath`, Kitchen `coffee`, Comfort & tech `wifi`, Outside `car`); group header 14/600 with icon 18; items in **2 columns**, rows 28, green `check` 14 + 13.5 body.
- Then, each with a top separator (14 margin + 14 padding): **Not included** (`circle-x` 18 secondary; items `x` 14 tertiary, text secondary) and **Not allowed** (`ban` 18 danger; items `ban` 14 danger, text primary), 2 columns.
- Seen in: SV, PA3.

## 14. Calendar (pick a time)
- Header: back + "Book Haircut" 18/500 + right facts 13 secondary (`clock` 60 min · `banknote` **120 RON**).
- **Who** (15/600): picked stylist — avatar 48 with ring + 20 ink check badge, name 12/600, next free 11 secondary · 1px vertical divider · group "**⇄ Can replace Andrei**" (12/600 secondary, `arrow-left-right` 14) with every other person who does this service: grey avatar (`#E2DEE9` bg, initial `text.body`), name 12/500, next free time. Readable, not 0.4.
- **When · October 2026** 15/600 + previous/next week buttons (44; previous disabled when at current week).
- **Week strip**: 7 columns, gap 6, day buttons 62 tall radius 14: weekday 11 + date 17/600 + 5 px dot (free = `status.success`). Selected: ink bg, white text, dot `status.successOnDark`. Closed / fully booked: `bg.soft`, `text.disabled`, date line-through, no dot, disabled.
- **Times** grouped by part of day ("Morning / Afternoon / Evening" 12.5/500 secondary). **Hide a part of day with no free times.** Slots 4 columns, gap 8, 44 tall radius 12: free = white + 1px `line.outline` 14/500; selected = ink, white 600; taken = `bg.soft`, `text.disabled`, line-through, disabled.
- Bottom bar: summary ("Thu, 22 Oct · with Andrei" 12.5 secondary / "14:30 – 15:30" 17/700) + **Confirm** (ink 48, radius 16).
- Defaults: picked stylist preselected; **earliest free slot preselected** so a regular customer can just tap Confirm.
- **F4 adds C20 "Choose an offer"** between When and the times. The times then follow the chosen offer (Any time / coupon windows / event spots), and the bottom bar shows the offer sticker. R3 has no offers yet.
- The **When** area (header + week strip) is reused unchanged on table booking TB2.
- Seen in: R3, F4, F4C, F4E, TB2.

## 15. Stylist choice (first visit)
- Header "Choose a stylist"; summary line 13 (Haircut 600 · `clock` 60 min · `banknote` 120 RON).
- Options list (gap 10), white cards radius 18, 1px `line.divider`, padding 14; selected = 2px ink border.
  - **Anyone**: ink 48 circle with `shuffle` · "Anyone" 16/600 · "First free stylist · **Today 14:30**" (green 600).
  - **Stylist**: avatar 48 · name 16/600 · "Barber · 8 years" 13 secondary · specialty chips (26 tall, radius 13, `bg.soft`, 12/500) · facts row with top separator: `star` (filled `#E0A21B`) 4.9 (38) · `globe` RO · EN · right: `clock` **Today 14:30** (green 600).
  - Radio 22: selected = ink circle with white check; unselected = 2px `line.strong` ring.
- Bottom bar: "With Andrei · next free" / "Today 14:30" + **Pick a time ›** (ink 48).
- Seen in: F3.

## 16. Coupon / event ticket card (3 columns)
- Card 206 tall (medium), radius 14, white, 1px `line.card`.
- **Media** height = card − 52 (154), play 34 centred.
- **Discount sticker** (coupons only): bottom-left of media (left 6, bottom 8), 22 tall, radius 6, `status.success` bg, white 11.5/800, text "20% OFF" (percent) or "10 RON OFF" (fixed amount), small shadow.
- **Tear line** at the media bottom: two 14 px notches (page-bg circles with 1px `line.card` border, centred on the left/right card edges) + dashed 1.5 `line.outline` line inset 10.
- **Stub** 50 tall, padding `0 9`, centred: title 12.5/600 **1 line, ellipsis** · facts 11/500 secondary: `hourglass` 12 + time left (**red** when "Today" or "1 day") · 1×11 divider · `ticket` 12 + quantity left.
- No Event/Coupon label on the card (the filter tells the type).
- Seen in: CE1. The 2-per-row version for search is C55.

## 17. Buttons
| Button | Style |
|---|---|
| Primary (Book, Confirm, Save, Pick a time) | ink fill, white 16/500, 48–52 tall, radius 16 |
| Profile CTA (Call, Book now) | slate `#3F5079`, white 15/500, 48 tall, radius 14, icon 18 |
| Secondary (Follow) | `bg.soft`, ink 15/500, 48 tall, radius 14 |
| Picker Next | white pill 48, radius 24, ink 16/500 |
| Destructive | red `trash-2` icon button in the header (edit screens) |
| Destructive (confirm in a sheet) | `action.danger` fill, white 16/500, 52 tall, radius 16, full width (RV4 **Decline request**) |
| Destructive (on a page) | white, 1px `line.card`, `action.danger` icon 18 + 15/500, 52 tall, radius 16 (TM3 Remove, CR10 Stop reward, RV5 **Cancel reservation**) |
| Decline / Accept pair | two equal buttons, gap 8–10: `action.secondary` + `x` / ink + `check`; 52 in a bottom bar (RV3), 44 radius 12 inside a card (RV2) |
| Icon button | 44 hit area, icon 20–24 |

## 18. Host profile — Quick Actions (HP)
Avatar 96 with 2.5 `brand.accent` ring + 30 edit badge · name 22/400 + verified badge · handle 13 + pencil · stats (Posts · Followers · Following) · "Quick Actions" 16/500 · **4-column grid** of tiles 56 (radius 18, `bg.soft`, icon 26 ink) with label 12/500: Calendar · Bookings · Hours · Services · Coupons · Customers · Team · icon-only content tabs (Videos · Reviews · Events, 46 tall, 22 × 2 underline) · bottom nav.
Optional "Brand" tone: tile `#EEEAFD`, icon `#5B3FD6`. Default is Mono.

## 19. Month calendar (availability)
- Month header 16/600 + previous/next month (44). Weekday row 11.5/500 secondary, 7 columns.
- Day cells 48 tall, radius 10, gap 4, date 15/600, tinted by availability: free `calendar.freeBg`, few left `calendar.fewBg`, full/closed `bg.soft` + line-through (disabled), past `calendar.pastText` (disabled), today = inset 1.5 ink ring, selected = ink.
- **No icons or dots in cells.** Legend below (Free · Few left · Full / closed).
- Followed by the **Events & coupons list** (date badge 46 × 40 · title 14/600 · sub 12.5 · offer badge 28).
- Seen in: TB1. Full spec: `11-table-booking.md` §2.

## 20. Offer cards ("Choose an offer")
- Radio cards (min 60, radius 16): badge 30 (Any time `clock` on `bg.soft`; coupon `percent` on `offer.coupon`; event group icon on `offer.event`), title 14.5, the day's windows 12.5 secondary, radio 22.
- Selected = selection ring; others greyed 0.4 (tappable). Any time always first.
- Seen in: TB2, F4. Full spec: `11-table-booking.md` §5–6.

## 21. Guests stepper
- Card (radius 16): "Guests" 15/600 + "Location maximum capacity · N" 12 secondary · − / value 18/700 / + (44 outlined circles). Limits 1…capacity.
- Seen in: TB2.

## 22. Sitting / spot buttons (events)
- 2 columns, 60 tall, radius 14: group icon 16 + "19:00 – 20:30" 14.5/600 + "N seats left" 12. Unselected `offer.eventTint` / `offer.eventText`; selected ink.
- Seen in: TB2E, F4E.

## 23. Booking summary card
- Day tile 52 × 60 (ink, weekday / day / month) · time range 17/700 · guests + duration 13 · Change.
- Optional offer strip at the bottom: coupon (green tint) or event (purple tint), badge 30 + title 14.5/700 + one line 12.5.
- Seen in: TB3, TB3C, TB3E.

## 24. Booking form
- One card, rows ≥ 56: **First name | Last name** on one row with a 1 × 28 divider · phone with country button · email · special requests (textarea, 1000 max, counter).
- Seen in: TB3.

## 25. Team member row
- Min 76, padding `12 8 12 14`: avatar 48 + status dot 14 (Active `status.success`, Paused `status.warning`, 2.5 white border) · name 15/600 (+ Owner chip, `brand.tintBg` / `brand.tintIcon`) · "@username · Role" 12.5 secondary · status word 12.5/600 + `scissors` "N services" · chevron. Whole row opens the person.
- Invite variant: dashed avatar · "@username" · "Invited · waiting for an answer" tertiary · Cancel text button.
- Seen in: TM1. Full spec: `12-team.md` §2.

## 26. Username search (invite sheet)
- Bottom sheet (C13 visuals). Search field 52, radius 14, focused border 1.5 ink, `at-sign` 20 + clear `x`. Result rows: avatar 40 · name 15/600 · "@username" 12.5 · **Invite** (ink 36, radius 12) → "✓ Invited" (`status.successText`).
- Seen in: TM2.

## 27. Service checklist
- One card, rows min 60: service name 15/500 + "duration · price" 12.5 secondary + check 26 (on: `status.success` circle with white check; off: 2px `line.strong` ring). Rows are checkboxes.
- Seen in: TM3 (same data as "Who does it" on HS3/HS4).

## 28. Reward ticket (wide)
- 108 tall, radius 16: green stub 104 (`offer.coupon`, value 28/800 + unit 12/700), dashed tear line with two notches, then business 12 · title 16/600 (**max 2 lines**, it is the host's message) · "Single use · until <date>" 12.5.
- Seen in: CR2, CR3, CR7–CR10. Full spec: `13-customers-rewards.md` §9.

## 29. Customer row (pick)
- Min 68: avatar 44 · name 15/600 · "N visits · last <date>" · optional unused-reward chip · check 26 (ink when selected). Whole row toggles. No phone/email.
- Seen in: CR1.

## 30. Switch
- Track 48 × 28 (on `status.success`, off `line.strong`), white knob 22, 44 hit area. Native switch with these colours.
- Seen in: CR4, CR6, CR9.

## 31. Duration chips
- 4 per row, 56 tall, radius 12: number 17/700 above unit 12/500. Unit never wraps. Fits RO/DE at 360.
- Seen in: CR2, CR7.

## 32. Step progress bar
- 4 segments, 4 tall, gap 4, radius 2 under the header; done + current `text.primary`, rest `line.divider`. No "Step x of y" text.
- Seen in: CR5–CR8.

## 33. Automatic rule card
- Calendar icon · name + "Every month on the <Nth>" · switch · sticker + "valid <length>" + who · status "Next: <date> · N people" (`status.successText`).
- Seen in: CR4.

## 34. Stat tiles
- 3 equal white tiles (radius 14): value 22/700 + label 12 secondary.
- Seen in: CR9, CR10.

## 35. Tab badge
- Amber count on an icon tab: min 18 × 18, padding `0 5`, radius 9, 2px `bg.page` border, `status.warning` fill, `text.primary` 10.5/700. Hidden at 0.
- Seen in: RV1 (calendar tab = waiting requests). Full spec: `14-reservations.md` §2.

## 36. Requests banner
- Radius 18, `status.warningBg`, padding `12 10 12 14`: circle 40 `status.warning` + `clock` 20 · "N requests to answer" 16/700 · "Oldest: <ago>" 12.5 `status.warningText` · ink **Answer** pill 36. The whole card is one tap target. Hidden with nothing to answer.
- Seen in: RV1.

## 37. Reservation status chip
- 22 tall, radius 11, padding `0 8`, 11.5/600, never wraps: **Waiting for you** (`status.warningText` / `status.warningBg`), **Confirmed** (`status.successText` / `status.successBg`), **Done** (`text.secondary` / `bg.soft`).
- Customer labels (My activity): **Waiting** (amber), **Confirmed** (green), **Declined** (`action.danger` on `bg.soft`), **Cancelled** (`text.secondary` on `bg.soft`).
- Seen in: RV1, RV3, RV5, MA1, MA3–MA5.

## 38. Reservation row
- Min 68, padding `10 8 10 14`: time column 50 (start 16/700, end 12 tertiary) · 3-wide bar (Confirmed `status.success`, Done `line.strong`) · name 15/600 + C37 chip · "what · `users` N people" 12.5 secondary · chevron. Item ellipsizes first; "N people" never truncates.
- Seen in: RV1. Category-neutral: "what" is a service, "Table" or an event title.

## 39. Request card
- White, radius 18, padding 12, gap 10: head (52 × 60 date tile · time 17/700 + "N h ago" · name · what · people) → chips (offer sticker, "N visits" or **New customer**) → 1-line special-request quote → **Decline** / **Accept** (44, radius 12). Head opens the request.
- Seen in: RV2.

## 40. Reservation summary card
- White, radius 18: date tile (light while waiting, `dark.card` once confirmed) · time 17/700 + C37 chip · item 14/500 · facts (people, duration, price, "With <team member>" — each only when the booking has it), then the optional offer strip (coupon green as TB3C, event purple as TB3E).
- Seen in: RV3, RV5, RV6 (no chip).

## 41. Customer contact card
- White, radius 18: avatar 44 · name 15/600 · "N visits · last <date>" / "New customer · first visit", then rows min 52: icon 18 · value 15 (ellipsis) · 44 action (**Call** opens the dialer; **Copy** copies the email + toast).
- Seen in: RV3, RV5 (RV6 shows the head only).

## 42. Reason sheet
- C13 sheet visuals: title 19/600 + X, one context line, radio cards (min 52, radius 14; selected ring + 600 + filled ink radio, others 0.4), one full-width `action.danger` button. No free-text field.
- Seen in: RV4 (Fully booked · Closed that day).

## 43. Visit check card
- White, radius 18, padding `18 16`, centred: circle 52 `bg.soft` + `calendar-check` 24 · "Did <name> come?" 20/700 · rule line 13.5 secondary · **No-show** (`action.secondary`, `user-x`) / **Yes, done** (ink, `check`), 52 each.
- Seen in: RV6.

## 44. Upcoming row (customer)
- C38 with the **place** instead of the customer: time column · bar (Confirmed `status.success`, Waiting `status.warning`) · place 15/600 + C37 chip · what · people · optional offer sticker line · chevron.
- Seen in: MA1. Full spec: `15-my-activity.md` §3.

## 45. History row
- Min 68, padding `10 10 10 14`: date column 50 ("20 Oct" 15/700 + time 12 tertiary) · place 15/600 · what · people, or C37 chip + reason (wraps under the chip, never cut) · one action: **Rate** (outline pill 36, `star` filled `status.warning`), **★ N** (static), or **Book again** (`action.secondary` pill 36, `repeat`). The row itself is not tappable.
- Seen in: MA3.

## 46. Status banner
- Radius 16, padding `12 14`: circle 36 + icon 18 · title 15/700 · line 12.5. Waiting: `status.warningBg`, `status.warning` circle, `hourglass`, `status.warningText`. Confirmed: `status.successBg`, `status.success` circle, white `check`, `status.successText`.
- Seen in: MA4, MA5.

## 47. Place card
- White, radius 18: head (avatar 44 · name 15/600 · type 12.5 · chevron → place profile), then C41-style rows: `map-pin` address + **Copy** · `phone` number + **Call**. No Directions.
- Seen in: MA4, MA5.

## 48. Reward facts
- Card of rows min 60: circle 36 `bg.soft` + icon 18 · title 15/600 · line 12.5: From <place> (`gift`), N days left (`hourglass`), Single use (`ticket`).
- Seen in: MA6.

## 49. Faded reward ticket
- C28 with the stub in `line.strong`, value and title in `text.secondary`, last line "Used · <date>" / "Ended · <date>". Not tappable.
- Seen in: MA2.

## 50. Search field
- 52 tall, radius 14, white, padding `0 2 0 14`, gap 10: `search` 20 `text.secondary` · input 16 (placeholder `text.placeholder`) · clear `x` 18 `text.tertiary` in a 44 target, only with text. Border 1.5 `line.outline` when empty, `text.primary` when it has text.
- Seen in: SR1–SR6. Full spec: `16-search.md` §2.

## 51. Tabs, greyed variant
- The CR1 / MA tabs with four equal columns: icon 20 + label 12.5, 56 tall, selected `text.primary` 500 + 2px underline; **unselected at opacity 0.4** (400). No counts.
- Seen in: SR3–SR6 (All `layout-grid` · Videos `square-play` · Places `store` · Deals `ticket-percent`).

## 52. Recent search row
- Min 52, padding `4 4 4 14`, gap 12: `clock` 18 `text.tertiary` · query 15 (1 line, ellipsis; tap runs it) · remove `x` 16 in a 44 target. Heading "Recent" + **Clear all** (13/500 `brand.tintIcon`).
- Seen in: SR1.

## 53. No results card
- White, radius 18, 1px `line.card`, padding `20 16`, centred: circle 52 `bg.soft` + `search` 24 · "No results for “<query>”" 18/700 · hint 13.5 / 1.45 `text.secondary` (max width 280).
- Seen in: SR2.

## 54. Place result row
- Min 76, padding `12 8 12 14`, gap 12: avatar 48 (logo, or initial 17/600 on the place's colour) · name 15/600 + verified 16 · "<type> · <city>" 12.5 secondary, **no icon** · status line 12.5 (word 600 in the Opening status colour, or check-in for accommodation) · chevron. Whole row opens the profile.
- Seen in: SR3, SR5.

## 55. Deal card (2 per row)
- C16 at the video-card height (290 at medium, scales like C7): radius 18; media = card − 76, play 40; sticker left 9 / bottom 8 (coupons only); tear line; stub 76, padding `0 12`: title 14.5/600 · place 12 secondary · `hourglass` 13 time left (red at Today / 1 day) | `ticket` 13 quantity left, 12/500.
- Tap → the booking with the deal picked (F4C / F4E / TB2C / TB2E).
- Seen in: SR3, SR6.

## 56. Loading more
- `role=status`, 44 tall, margin-top 16, gap 8: spinning ring 22 (track `line.divider`, arc `text.primary`) + "Loading more" 12.5 `text.secondary`. End of every infinite list.
- Seen in: SR3–SR6.

## 57. Post editor on the video
- The whole screen is the picked video: top scrim 140, bottom scrim 460; X (top 40, left 8) → profile; **Change video** pill top right (34, radius 17, `rgba(0,0,0,.4)`, `refresh-cw` 15 + 13/500) → NP1; poster (avatar 36, name 14/600, "@username" 12); C58 caption panel; C59 Tag tool on the side rail; bottom row: hint 13 white .8 + **Publish** white pill 52 (radius 26, `upload` 20 + 16/500), disabled at 0.4 until there is a title.
- Seen in: NP2, NP3 (and behind NP4); EP1 uses it with "Edit post" centred instead of Change video, C61 bottom left and **Save** (`check`) instead of Publish. Full spec: `17-new-post.md` §3, §6.

## 58. Caption panel
- Left 12, right 80, bottom 112; padding `10 12`, radius 16, 1px `rgba(255,255,255,.22)`, frosted `rgba(20,18,24,.55)` + blur 12.
- Title field 16/600 (max **30**) · divider row: 1px line + "n / 30" 11.5 white .65 · description 14 / 1.4 white .9 (max **100**) · "n / 100" right. Fields grow with the text; placeholders "Add a title" / "Add a description" white .7.
- Seen in: NP2, NP3.

## 59. Tag tool
- Side rail button: circle 44, `store` 21; dark `rgba(0,0,0,.4)` + white icon without a tag, white + ink icon with one; badge 18 `status.success` with the count (11/700 white); label "Tag" 12/500. Opens C60.
- Seen in: NP2, NP3.

## 60. Tag sheet
- C13 sheet: "Tag a place" 19/600 + X · line 13 secondary · search field 52 (`search`, "Search places") · "From your visits" 13/600 · visit rows min 64 (avatar 40 · name 15/600 + verified · `calendar` 13 + "what · d Mon" · check 26) · **Done** ink 52.
- Seen in: NP4. Full spec: `17-new-post.md` §5.

## 61. Delete video button on the video
- Bottom row left on EP1: pill 52, radius 26, padding `0 18 0 14`, 1px `rgba(255,255,255,.22)`, `rgba(0,0,0,.45)`; `trash-2` 19 + "Delete video" 15/500 in `status.dangerOnDark`. Opens C62.
- Seen in: EP1. Full spec: `17-new-post.md` §6.

## 62. Delete sheet
- C13 sheet: "Delete this video?" 19/600 + X · one line 13.5 secondary · card listing what is deleted (rows min 56: circle 36 `bg.soft` + icon · title 15/500 · line 12.5): The video · Title and description · The tag (only with a tag) · Engagement ("Views and likes", no counts) · red **Delete video** (C17 destructive confirm in a sheet, `trash-2`).
- Seen in: EP2. Full spec: `17-new-post.md` §7.

## 63. Signed-out profile
- Profile tab before signing in: dashed avatar 96 (`user` 40 tertiary) · "Your profile" 22/600 · one line 14 secondary · **Create account** (ink 52) · **Sign in** (white 52, 1.5 ink border) · **Privacy & data** link (`shield` 16 + 13.5/500) at the bottom, above the C9 nav.
- Seen in: AU1. Full spec: `18-account.md` §2.

## 64. Account form card
- The TB3 details card: rows min 56, icon 20 secondary, inputs 15: First name | Last name · username + "✓ Available" (`status.successText`) · date of birth + C65 · password + eye (Show / Hide).
- Seen in: AU3, AU5. Full spec: `18-account.md` §4.

## 65. Change pill
- `bg.soft` pill 32, radius 16, padding `0 12 0 10`: `calendar` 16 + "Change" 13.5/500 ("Pick date" while empty). Says a picker opens; the whole row is the tap target.
- Seen in: AU3, AU5.

## 66. Date of birth dialog
- Centred dialog (left / right 20, radius 24, padding `20 20 14`): title 19/600 · headers Day · Month · Year · three ink wheels (gap 10, 1 : 1.25 : 1.25, 5 rows of 44, picked row on a `rgba(255,255,255,.12)` band, 20/600 white; neighbours 17 at 0.5 and 15 at 0.25) · **Cancel** (text) / **Confirm** (ink 44, radius 14). Months as names.
- Seen in: AU4. Full spec: `18-account.md` §5.
