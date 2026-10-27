# 04 · Screens

Each screen: id → files, then top-to-bottom content, actions and data. "C#" refers to a component in `03-components.md`. Screenshot of every screen: `../screenshots/<size>/<id>.png`; markup: `../screens/<size>/<id>.html`.

---

## Host — own profile

### HP-profile · Host profile with Quick Actions
Top bar (back, settings) → C18 profile block → **Quick Actions** 4-column grid (Calendar, Bookings, Hours, Services, Coupons, Customers, Team) → icon tabs (Videos, Reviews, Events) → C9 bottom nav (Profile active).
- The third icon tab (calendar) is **Reservations** → RV1, with the C35 amber badge = waiting requests (see `14-reservations.md`).
- Services tile → HS1 (services hosts) or HR1 (accommodation hosts, label "Rooms").
- Team tile → TM1 (not linked in the canvas prototype; implement it).
- Customers tile → CR1 (not linked in the canvas prototype; implement it).
- Icon set rules: `../screens/reference/icon-set.html`.

---

## Host — services (video first)

### HS1-services-list · Services
Top bar "Services" → count "2 services" → 2-column grid of **C8 host video cards** (Haircut with video; Beard trim "No video yet") → **New service** tile → C9 nav.
- Edit icon → HS4. New service → HS2.
- Data: Service[] (name, price, people, duration, video thumbnail).

### HS2-add-video · Add a video
C10 picker. Close → HS1. Next / Skip → HS3. Hint: "Pick a clip that shows the service".

### HS3-service-details · Service details (create)
C11 form with all sections:
- Name "Haircut", short description (shown as the video caption).
- Video thumb (Change → HS2).
- Price **120 RON / visit**, Duration **60 min**, People per booking **1**.
- Included · 10 (4 shown + "+6 more" + Add), Not included (Beard trim, Hair colouring), Not allowed (Pets, Late by 15+ min).
- Who does it: Andrei ✓, Radu ✓, Maria (off).
- **Save service** → HS1. Back → HS2.
- Medium board is 940 tall to show the whole form; on device it scrolls with Save pinned.

### HS4-edit-service · Edit service (no video yet)
Same as HS3 with: title "Edit service", red trash (Delete service) in header, values for **Beard trim** (50 RON, 30 min, 1 person; Included: Shape & line-up, Hot towel; Not included: Haircut; Not allowed: Pets; Who: Andrei only), dashed **Add video** tile (→ HS2), **Save changes** → HS1.

---

## Host — rooms (video first)

### HR1-rooms-list · Rooms
Same as HS1 for rooms: "2 rooms"; Double Room (video, **250 RON / night**, 👥 2), Family Room with Balcony (no video, 380 RON / night, 👥 4); New room tile.
- Edit → HR4. New room → HR2.

### HR2-add-video · Add a video (room)
C10 picker, hint "Pick a clip that shows the room". Close → HR1, Next/Skip → HR3.

### HR3-room-details · Room details (create)
C11 form **without Duration and Who does it**:
- Name "Double Room" + description.
- Price **250 RON / night** (fixed unit), **Guests 2**.
- Included · 18 (Wi-Fi, Free parking, Smart TV, Air conditioning, +14 more, Add).
- Not included (Breakfast, Airport transfer).
- Not allowed (Pets, Smoking, Parties).
- **Save room** → HR1.

### HR4-edit-room · Edit room (no video yet)
HR3 fields for Family Room with Balcony (380 / night, 4 guests, Included: Wi-Fi, Parking, Kitchen; Not included: Breakfast; Not allowed: Smoking, Parties), Add video tile, trash in header, **Save changes**.

---

## Host — team

Full spec, sizes and states: [`12-team.md`](12-team.md). Summary:

### TM1-team-list · Team
Top bar "Team · Maestro Host · 4 people" → **Active · 3**: Maestro Host (Owner, "@maestro_seed_host · You", 1 service), Andrei (Barber, 3 services), Radu (Stylist, 2 services) → **Paused · 1**: Maria (Stylist, 2 services) → **Invites · 1**: @ioana.nails ("Invited · waiting for an answer", Cancel) → note about paused people → pinned **Invite to team** → TM2. Any person → TM3. Back → HP.

### TM2-invite · Invite to team (sheet)
C26 over TM1: "ioana" typed → 2 people: Ioana Pop @ioana.nails "✓ Invited", Ioana Marin @ioana.m **Invite**. X / dim → TM1.

### TM3-team-member · Team member
Profile card (Andrei, @andrei.barber, Active, Joined Mar 2025) → **Status**: Active (selected) / Paused → **Services · 3 of 4** (C27): Haircut ✓, Beard trim ✓, Kids haircut ✓, Couples massage ✗ → **Remove from team** → **Save changes** → TM1.

---

## Host — customers & rewards

Full spec, sizes and states: [`13-customers-rewards.md`](13-customers-rewards.md). Summary:

### CR1-customers · Customers · People tab
Tabs People / Rewards → group tiles (All 24 · **Regulars 8** · New 10 · Away 6) → "Regulars · 3+ visits · 2 selected" + Select all → rows (Elena ✓, Mihai ✓ with "10 RON OFF · not used", Cristina, Dan, Ioana with "15% OFF · not used") → **Send reward to 2 people** → CR2.

### CR2-new-reward · New reward
To: Elena and Mihai (Change) → ticket preview **15% OFF · Thanks for coming back** → Discount % / RON + 10–25% / Other → Message (22 / 40) → Valid for 1 week · 2 weeks · 3 weeks · **1 month** (Until Sun, 22 Nov) → **Send to 2 people** → CR3.

### CR3-reward-sent · Reward sent
Check, "Reward sent", "Elena and Mihai can use it for one booking until Sun, 22 Nov.", ticket, See rewards (→ CR4) / Done (→ CR1).

### CR4-rewards-tab · Customers · Rewards tab
**Automatic · 2 on**: Come back soon (every month on the 15th · 10% OFF · 5 days · exactly 1 visit in the month before · Next: Sun, 15 Nov · 10 people), Thanks for coming often (1st · 15% OFF · 1 week · 3 or more visits) → Idea to start: VIP thank you (+ Add) → **Sent · this month**: Come back soon (Auto, used by 4 of 9), Thanks for coming back (By you, used by 3 of 8) → **New automatic reward** → CR5.

### CR5–CR8 · New automatic reward
CR5 When (first send **Sun 15 Nov** on the week strip; next sends 15 Nov · 15 Dec · 15 Jan) → CR6 Who (**exactly 1** visit in the month before, **every month**, skip unused, 10 people match) → CR7 Reward (10% OFF, 5 days, "Come back soon" 14 / 40) → CR8 Check (sentence + When / Who / Reward with Change) → **Turn on** → CR4.

### CR9-auto-edit · Edit automatic reward
Trash in the header · Come back soon (On, switch) · 3 times sent · 27 people · 11 used · ticket · rule rows (When, Who, Discount, Valid for, Message) · **Save changes**.

### CR10-reward-details · Reward details
Ticket · 8 sent · 3 used · 5 not used yet · people with "Used · 14 Oct" / "Not used yet" · **Stop reward**.

---

## Host — reservations

Full spec, sizes and states: [`14-reservations.md`](14-reservations.md). The same screens serve services, tables and events. Summary:

### RV1-reservations · Reservations tab
HP icon tabs with the calendar tab selected and an amber **2** badge → amber banner **2 requests to answer · Oldest: 2 h ago · Answer** (→ RV2) → **Today · Fri, 23 Oct** (3 reservations · 1 done): 11:00 Mihai Ionescu · Haircut · 1 person · **Done** (→ RV6), 13:00 Cristina Marin · Table · 4 people · **Confirmed**, 19:00 Ioana Radu · Wine tasting · 2 people · **Confirmed** (→ RV5) → **Tomorrow · Sat, 24 Oct**: Sorin Matei · Couples massage · 2 people, Alina Dobre · Table · 2 people → C9 nav. No calendar strip.

### RV2-requests · Requests to answer
"Requests · 2" → note "Oldest first. Answer within 24 hours…" → C39 cards: Elena Popescu · Mon 26 Oct · 14:30 – 15:30 · Haircut · 1 person · 15% OFF · 6 visits · "Please keep it short on the sides." (2 h ago); Dan Stoica · Tue 27 Oct · 19:00 – 20:30 · Table · 6 people · New customer · "Birthday dinner, a cake at 21:00 please." (20 min ago). Each with **Decline** (→ RV4) / **Accept** (→ RV5); card head → RV3.

### RV3-request · Reservation request
C40 summary (Mon 26 Oct · 14:30 – 15:30 · Waiting for you · Haircut · 1 person · 60 min · 120 RON · With Andrei) + coupon strip "15% OFF coupon · Pays 102 RON instead of 120 RON" → **Customer** (C41: Elena Popescu, 6 visits · last 12 Oct, phone with Call, email with Copy) → **Special requests** → requested-at note → pinned **Decline** / **Accept**.

### RV4-decline · Decline (sheet)
C42 over RV3: "Decline Elena’s request?" · "Mon, 26 Oct · 14:30 · Haircut. Pick a reason. We let them know so they can book another time." · **Fully booked** (selected) / **Closed that day** · red **Decline request** → RV2.

### RV5-confirmed · Reservation confirmed
Green "Accepted. Elena got a confirmation." → C40 with the dark date tile and **Confirmed** → Customer → Special requests → **Cancel reservation** (danger) + "If you cancel, Elena gets a message right away."

### RV6-after-visit · After the visit
Summary (Today 23 Oct · 11:00 – 12:00 · Haircut) → Mihai Ionescu (4 visits · last 9 Oct) → C43 "Did Mihai come?" **No-show** / **Yes, done** (→ RV1) → "If you do not answer, it is marked as done the next day."

---

## Customer — my activity

Full spec, sizes and states: [`15-my-activity.md`](15-my-activity.md). Same screens for services, tables and events. Summary:

### MA1-upcoming · Upcoming tab
"My activity" → tabs **Upcoming · 2** (selected) · Rewards · 2 · History → **Tomorrow · Sat, 24 Oct**: 19:00 – 20:30 Maestro Bistro · Table · 2 people · **Confirmed** (→ MA5) → **Mon, 26 Oct**: 14:30 – 15:30 Maestro Host · Haircut · 1 person · **Waiting** · 15% OFF (→ MA4) → note about waiting requests.

### MA2-rewards · Rewards tab
**Ready to use · 2**: 10 RON OFF · See you again soon · Maestro Bistro · until Wed, 28 Oct; 15% OFF · Thanks for coming back · Maestro Host · until Sun, 22 Nov (each → MA6) → note "Each reward works for one booking at that place…" → **Used or ended · 2**: 20% OFF Welcome back (Used · 12 Oct), 10% OFF Come back soon (Ended · 30 Sep), faded.

### MA3-history · History tab
**October**: 20 Oct Maestro Bistro · Table · 2 people · **Rate**; 12 Oct Maestro Host · Haircut · ★ 5; 2 Oct Maestro Bistro · **Declined** · Fully booked · **Book again** → **September**: 18 Sep Maestro Host · Beard trim · ★ 4; 5 Sep Maestro Bistro · **Cancelled** · By you · **Book again**.

### MA4-reservation-waiting · Reservation · waiting
Amber banner "Waiting for Maestro Host · They answer within 24 hours…" → summary (Mon 26 Oct · 14:30 – 15:30 · Waiting · Haircut · 1 person · 60 min · 120 RON · With Andrei) + coupon strip "You pay 102 RON instead of 120 RON" → **Place** (Maestro Host · Barber & salon → PS1; Strada Republicii 12, Brașov · Copy; +40 721 000 123 · Call) → **Your special requests** → **Cancel request** + "Maestro Host is told right away."

### MA5-reservation-confirmed · Reservation · confirmed
Green banner "Confirmed · Maestro Bistro is expecting you." → summary with the dark tile (Sat 24 Oct · 19:00 – 20:30 · Confirmed · Table · 2 people · 1 h 30 min) → **Place** (Maestro Bistro · Restaurant → PF1; address · Copy; phone · Call) → **Cancel reservation** + note. No Add to calendar.

### MA6-reward · Reward
Ticket 15% OFF · Thanks for coming back → From Maestro Host · 30 days left (until Sun, 22 Nov) · Single use → note → pinned **Book with Maestro Host** (→ PS1).

---

## Public — search

Full spec, sizes and states: [`16-search.md`](16-search.md). Opens from the **Search** tab of the bottom nav. Summary:

### SR1-start · Before you type
C50 search field (empty, "Search places, videos, coupons…") → **Recent** + **Clear all** → maestro · haircut brașov · wine tasting (each: `clock`, tap → SR3, X removes). No Browse / categories.

### SR2-no-results · No results
Field "sushi brașov" → C53 card "No results for “sushi brașov”" · "Check the spelling or try fewer words." No tabs.

### SR3-all · All
Field "maestro" → C51 tabs **All** (selected) · Videos · Places · Deals, the others greyed, no counts → one mixed feed, best match first: Maestro Host (place → PS1) · Haircut | Double Room (videos → F2 / PA2) · Maestro Bistro (→ PF1) · Haircut 15% OFF | Lunch 20% OFF (deals → F4C / TB2C) · Couples massage | Kids haircut · Maestro Rooms (→ PA1) · Wine tasting | Late cuts (events → TB2E / F4E) → **Loading more**.

### SR4-videos · Videos tab
2 per row: Haircut (Maestro Host, 120 RON, 1 · 60 min), Double Room (Maestro Rooms, 250 RON / night, 2 · Details), Couples massage, Kids haircut (from 70 RON) → **Loading more**.

### SR5-places · Places tab
One card: Maestro Host (verified, Barber & salon · Brașov, **Open now** · Closes 20:00), Maestro Bistro (verified, Restaurant, **Closes soon** · Until 22:30), Maestro Rooms (Guesthouse, **Check-in 14:00** · Check-out 11:00), Maestro Barber Shop (Cluj-Napoca, **Closed** · Opens 09:00), Maestro Café → **Loading more**.

### SR6-deals · Deals tab
Tiles **All** (selected) · Events · Coupons, no counts → 2 per row, ending soonest first: Haircut 15% OFF · Maestro Host · 1 day (red) · 20; Lunch 20% OFF · Maestro Bistro · 2 days · 50; Wine tasting · 4 days · 34; Late cuts · 8 days · 3 → note "Tap a deal to book with it…" → **Loading more**.

---

## Public — accommodation (Call only)

### PA1-profile-rooms · Accommodation profile · Rooms
Top bar (back, centred `@stay_host_brasov`, more) → C2 header with **Call** → C3 About (bed pin, address, **Check-in 14:00 / Check-out 11:00**, Moderate) → C4 tabs (Rooms selected) → "2 rooms" → C7 cards (Double Room 250 RON / night 👥 2 | Details; Family Room 380 RON / night 👥 4).
- Play or Details pill → PA2. Call → phone dialer with the host's number.
- Strings for this screen are translated in `strings.json › accommodation_rooms_list`.

### PA2-room-video · Room video
C12 overlay for a room:
- Creator: Stay Host Brasov.
- Caption: "Bright double room in the centre of Brașov, 5 minutes from the old town."
- Chips: ✓ Wi-Fi · ✓ Parking · **+16 more** → PA3.
- Side rail: **Call**.
- Info bar: Double Room · 👥 2 guests · **250 RON / night**.
- X → PA1.

### PA3-room-included · What's included (room)
C13 sheet over the dimmed video: "What's included · 18", subtitle "Double Room · 2 guests · 250 RON / night".
- Grouped Included list: Bedroom 4 · Bathroom 5 · Kitchen 3 · Comfort & tech 4 · Outside 2.
- Not included: Breakfast, Airport transfer.
- Not allowed: Pets, Smoking, Parties.
- Close → PA2.

---

## Public — services & food and beverage profiles

### PS1-profile-services · Services profile
Same structure as PA1:
- Header: @maestro_host, "Services · Barber & salon".
- CTA **Book now**.
- About: scissors pin, "Open now · Closes 20:00", Moderate.
- Tabs: Services selected.
- "2 services": C7 service cards (Haircut 120 RON, A+R, 👥 1 | ⏱ 60 min ›; Beard trim 50 RON, A, no video).

Links:
- Haircut → F2.
- Beard trim → F3, because there's no video.
- Book now → not designed for services (see open questions).

### PF1-profile-fnb · Food & Beverage profile
Header + About only:
- Header: @maestro_bistro, "Food & Beverage · Restaurant".
- CTA **Book now** → **TB1** (table booking).
- About: utensils pin, "**Closes soon** · Until 22:30" in amber, Expensive.
- **No tabs and no content grid** for this category.

---

## Salon booking — regular customer (knows the stylist, 3 taps)

### R1-services-stylist-picked · Services, stylist picked
Top bar (back, "Maestro Host" + verified, more) → C4 tabs (Services) → C5 team filter (**Andrei** selected; Everyone, Maria, Radu greyed) → C6 category tiles (All 2 selected, Hair 1, Beard 1, Massage 0 disabled) → C7 cards for Andrei's services only.
- Haircut play / pill → R2. Beard trim pill (no video) → R3. Everyone → F1.
- Translated strings: `strings.json › salon_services_list`.

### R2-video · Service video (regular)
C12 overlay:
- Caption "Classic cut, start to finish. Free cancellation up to 24 h before."
- Chips: ✓ Hair wash · ✓ Styling · **+8 more** → SV.
- Side rail: **Book** → R3.
- Info bar: **Haircut** · Andrei · 60 min · 1 person · 120 RON.
- X → R1.

### R3-pick-time · Pick a time (regular)
C14 calendar:
- Who: **Andrei** highlighted; Can replace Andrei: Radu 16:15.
- Thu 22 selected; Sun 25 closed; Tue 27 fully booked.
- Afternoon: 13:00 taken, **14:30 selected**, 15:30, 16:30 taken.
- Evening: 17:30, 18:30, 19:30 taken. Morning is hidden because it's fully booked.
- Bottom: "Thu, 22 Oct · with Andrei / 14:30 – 15:30" + **Confirm** (end of the designed flow).
- Back → R2.

### SV-included · What's included (service)
C13 sheet, services variant: "What's included · 10", "Haircut · 60 min · 120 RON".
- 10 ticked rows: Consultation, Hair wash, Cut & styling, Hot towel, Scalp massage, Styling product, Neck shave, Beard line-up, Coffee or tea, Free Wi-Fi.
- Not included: Beard trim, Hair colouring.
- Not allowed: Pets, Late by 15+ min.
- Close → back to the video it was opened from (R2 or F2).

---

## Salon booking — first visit ("Everyone", guided)

### F1-services-everyone · Services, Everyone
As R1 but **Everyone** selected (Andrei, Maria, Radu greyed); categories All 4, Hair 2, Beard 1, Massage 1.
- Four cards: Haircut (A, R), Beard trim (A, no video), Kids haircut ("from 70 RON", M, R), Couples massage (300 RON, M, 👥 2 | 90 min).
- Cards with video → F2. Beard trim → F3. Andrei → R1.

### F2-video · Service video (first visit)
Same as R2 but the info bar has no stylist name (Haircut · 60 min · 1 person · 120 RON). Side rail **Book** → **F3**. "+8 more" → SV. X → F1.

### F3-choose-stylist · Choose a stylist
C15:
- Options: Anyone (first free, Today 14:30) · **Andrei** (selected; Barber · 8 years; Fades, Beard trims, Classic cuts; ★ 4.9 (38); RO · EN; Today 14:30) · Radu (Stylist · 3 years; Classic cuts, Kids; ★ 4.7 (12); RO; Today 16:15).
- Bottom: "With Andrei · next free / Today 14:30" + **Pick a time** → F4.
- Back → F2.

### F4-pick-time · Pick a time (first visit)
R3 layout (C14) plus **C20 Choose an offer** between When and the times. **Any time** is selected and Afternoon/Evening slots are shown. Back → F3. The content scrolls under the pinned bar.

### F4C-pick-time-coupon · Pick a time · coupon chosen
"15% OFF" selected. Times grouped by window: **14:00 – 16:00** (14:30 selected, 15:30) and **18:00 – 19:00** (18:30), each with the green sticker. Bottom bar: "14:30 – 15:30" + "15% OFF". Note: "The discount is applied at the salon when you pay."

### F4E-pick-time-event · Pick a time · event chosen
"Late cuts" selected. "Spots · 60 min": **19:00 – 20:00 · 1 spot left** (selected), 20:00 – 21:00 · 2 spots left (C22). Bottom bar: "19:00 – 20:00" + purple "Late cuts". Note: "Your spot is held for the whole hour.

---

## Coupons & Events tab

### CE1-coupons-events · Coupons & Events
- C4 tabs (Videos · **Coupons** · Reviews).
- C6 tiles filling the row: **All 6** (selected), Events 3, Coupons 3.
- 3-column grid of C16 ticket cards:

| Card | Type | Time left | Left | Discount sticker |
|---|---|---|---|---|
| Live jazz night | event | 1 day (red) | 5 | none |
| Wine tasting | event | 4 days | 34 | none |
| Lunch menu | coupon | 2 days | 50 | 20% OFF |
| Cocktail hour | coupon | Today (red) | 18 | 10 RON OFF |
| Sunday brunch | event | 6 days | 12 | none |
| Any dessert | coupon | 5 days | 100 | 15% OFF |

- Tap card → coupon/event video — **not designed yet** (see open questions).

---

## Table booking (Food & Beverage)

Full spec, sizes and states: [`11-table-booking.md`](11-table-booking.md). Summary:

### TB1-pick-date · Pick a date
C19 month calendar (October 2026; today Fri 23; **Mon 26 selected**; Sun closed; Wed 28 full; Sat 24 and Fri 30 few left), legend, "Events & coupons in October": Live jazz night (Fri 23), 10 RON OFF dinner (Sat 24), **Wine tasting** (Mon 26), **20% OFF lunch** (Mon 26 – Fri 30), Halloween night (Sat 31). Bottom: "Your date · Mon, 26 Oct" + **Choose a time** → TB2. Wine tasting row → TB2E, 20% OFF lunch row → TB2C. Back → PF1.

### TB2-guests-time-any · Guests & time · Any time
When week strip (Today 23 … Thu 29, Mon 26 selected) · C21 Guests (2, capacity 40) · C20 offers: **Any time** / 20% OFF (12:00 – 14:00 · 17:30 – 18:30) / Wine tasting (19:00 – 20:30 · 21:00 – 22:30) · Lunch and Dinner slots (**20:00** selected) · "Tables are held for 1 h 30 min." · bottom "Mon, 26 Oct · 2 guests / 20:00 – 21:30" + **Continue** → TB3.

### TB2C-guests-time-coupon · Guests & time · coupon
As TB2 with **20% OFF** chosen: windows 12:00 – 14:00 (12:00, **12:30**, 13:00 taken, 13:30) and 17:30 – 18:30 (17:30, 18:00), each with the sticker. Bottom "12:30 – 14:00" + "20% OFF" → TB3C.

### TB2E-guests-time-event · Guests & time · event
As TB2 with **Wine tasting** chosen: "Sittings · 1 h 30 min": **19:00 – 20:30 · 12 seats left** (selected), 21:00 – 22:30 · 6 seats left. Bottom "19:00 – 20:30" + purple "Wine tasting" → TB3E.

### TB3-details-any / TB3C-details-coupon / TB3E-details-event · Your details
C23 summary (day tile Mon 26 Oct · time · 2 guests · 1 h 30 min · Change), plus the coupon strip ("20% OFF your bill · Valid 12:00 – 14:00 · applied at the restaurant") or the event strip ("Wine tasting · Sitting 19:00 – 20:30 · 2 seats held for you"). C24 form: First name | Last name, RO +40 phone, Email, Special requests (optional, 0 / 1000). Info note. **Confirm reservation** → TB4. Back and Change → the same TB2 state.

### TB4-booked · Booked
Success check, title (copy to confirm), "Maestro Bistro is expecting you.", summary rows (date · time, guests, address with copy, Call the restaurant), **Add to calendar** + **Done** (→ PF1). X → PF1.
