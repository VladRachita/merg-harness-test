# 04 · Screens

Each screen: id → files, then top-to-bottom content, actions and data. "C#" refers to a component in `03-components.md`. Screenshot of every screen: `../screenshots/<size>/<id>.png`; markup: `../screens/<size>/<id>.html`.

---

## Host — own profile

### HP-profile · Host profile with Quick Actions
Top bar (back, settings) → C18 profile block → **Quick Actions** 4-column grid (Calendar, Bookings, Hours, Services, Coupons, Customers, Team) → icon tabs (Videos, Reviews, Events) → C9 bottom nav (Profile active).
- Services tile → HS1 (services hosts) or HR1 (accommodation hosts, label "Rooms").
- Team tile → TM1 (not linked in the canvas prototype; implement it).
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
