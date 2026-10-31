# 06 · Data model and display rules

The fields every screen needs. Names are suggestions; keep the meaning. Sample values come from the designs.

## Business profile
```ts
BusinessProfile {
  id, handle: "@stay_host_brasov", name: "Stay Host Brasov", verified: boolean,
  category: "SERVICES" | "ACCOMMODATION" | "FOOD_BEVERAGE",
  subcategoryLabel: "Barber & salon" | "Restaurant" | null,   // shown after "·" in the header
  avatarUrl?, stats: { posts: number, followers: number, rating?: number, reviewsCount: number },
  phone: string,                                    // Call
  address: { line: "Bulevardul Cazare Brasov 1", city?, lat, lng },   // map + copy
  openingHours: WeeklyHours,                        // SERVICES, FOOD_BEVERAGE
  checkIn?: "14:00", checkOut?: "11:00",            // ACCOMMODATION (About hours cell)
  priceLevel: 1 | 2 | 3 | 4                         // Budget, Moderate, Expensive, Luxury
}
```

## Video (attached to a service, room, coupon or event; optional)
```ts
Video { url, thumbnailUrl, durationSec, caption /* = item.shortDescription */, views, publishedAt, likes }
```
No video → card shows the "No video yet" placeholder (host) or category icon (public) and the booking path skips the video.

## Service (SERVICES)
```ts
Service {
  id, name: "Haircut", shortDescription,
  category: "Hair" | "Beard" | "Massage" | …,      // category tiles
  price: { amount: 120, currency: "RON", unit: "VISIT" | "PERSON", from?: boolean },  // "from 70 RON"
  durationMin: 60, peoplePerBooking: 1,
  included: string[], notIncluded: string[], notAllowed: string[],
  teamMemberIds: string[],                           // "Who does it" + avatar stack + "Can replace"
  video?: Video
}
```

## Room (ACCOMMODATION)
```ts
Room {
  id, name: "Double Room", shortDescription,
  pricePerNight: { amount: 250, currency: "RON" }, guestsMax: 2,
  included: { group: "Bedroom" | "Bathroom" | "Kitchen" | "Comfort & tech" | "Outside", item: string }[],
  notIncluded: string[], notAllowed: string[],
  video?: Video
}
```
Suggestion (not designed): offer hosts a checklist of common amenities per group instead of typing 15–20 items.

## Team member
```ts
TeamMember {
  id, name: "Andrei", initials: "A", avatarUrl?, avatarColor,
  username: "andrei.barber",                     // shown as "@andrei.barber" (TM1, TM3)
  status: "ACTIVE" | "PAUSED", isOwner: boolean, joinedAt,
  role: "Barber", yearsExperience: 8, specialties: string[],
  languages: ["RO","EN"], rating: 4.9, reviewsCount: 38
}
TeamInvite { id, username: "ioana.nails", invitedAt, state: "PENDING" | "ACCEPTED" | "DECLINED" | "CANCELLED" }
```
- A person's services = every `Service` whose `teamMemberIds` contains them (TM1 "N services", TM3 checklist). Editing either side edits the same list.
- `PAUSED` members are left out of the R1 team filter, F3, "Can replace" and "Anyone"; their existing bookings stay.
- TM1 lists `PENDING` invites only. The owner is `isOwner` and always `ACTIVE`.

## Availability (calendar)
```ts
DayAvailability { date, state: "OPEN" | "CLOSED" | "FULLY_BOOKED", slots: Slot[] }   // per team member
Slot { start: "14:30", end: "15:30", state: "FREE" | "TAKEN" }
```
- Slot length = service duration. Group slots into Morning (< 12:00), Afternoon (12–17), Evening (≥ 17) and **hide groups with no FREE slot**.
- `nextFree(member, service)` → "Today 14:30" / "Tomorrow" / "Fri 16:15".
- "Anyone" = earliest FREE slot across `service.teamMemberIds`.
- Defaults: preselect the picked/remembered member and the earliest FREE slot.

## Coupon / Event
```ts
Offer {
  id, type: "COUPON" | "EVENT", title: "Lunch menu",
  discount?: { type: "PERCENT", value: 20 } | { type: "AMOUNT", value: 10, currency: "RON" },  // coupons only
  startsAt?, endsAt, quantityLeft: 50, video?: Video,
  // Booking (table booking TB1–TB3 and salon F4): offers repeat over several days and several time windows a day.
  appliesTo: "TABLE" | { serviceIds: string[] },
  windows: { date: "2026-10-26", from: "12:00", to: "14:00" }[],                 // coupons: when the discount applies
  sittings?: { id, date: "2026-10-26", from: "19:00", to: "20:30", seatsLeft: 12 }[],   // events: bookable sittings / spots
  minGuests?, maxGuests?
}
```

## Restaurant booking (FOOD_BEVERAGE)
```ts
RestaurantBookingSettings {
  capacity: 40,                         // "Location maximum capacity · 40"; guests stepper max
  bookingHorizonMonths: 6,              // last month reachable with "next month" on TB1
  tableHoldMin: 90,                     // "Tables are held for 1 h 30 min" → time range "20:00 – 21:30"
  slotStepMin: 30,
  services: [{ name: "Lunch", from: "12:00", to: "16:00" }, { name: "Dinner", from: "17:30", to: "23:00" }]
}
DayAvailability { date, state: "FREE" | "FEW_LEFT" | "FULL" | "CLOSED" }        // TB1 tint, TB2 week-strip dot
TimeSlot { start: "20:00", state: "FREE" | "TAKEN" }                             // per service period, for the guest count
```

## Booking request
```ts
TableBookingRequest {
  businessId, date: "2026-10-26", from: "20:00", to: "21:30", guests: 2,
  offerId?: string, sittingId?: string,          // Any time = neither
  firstName: string, lastName: string,           // two fields, both required
  phone: { country: "RO", number: string }, email: string,
  specialRequests?: string                       // optional, max 1000
}
```

## Customer (host side)
```ts
Customer {
  id, name: "Elena Popescu", initials: "E", avatarColor, avatarUrl?,
  visitsCount: 6, lastVisitAt,                     // DONE reservations with this business (RV6); no-shows don't count
  groups: ("REGULAR" | "NEW" | "AWAY")[],          // REGULAR: 3+ visits · NEW: 1 visit · AWAY: no visit in 60 days (proposal)
  unusedRewardIds: string[]                        // CR1 chip "10 RON OFF · not used"
  // phone / email exist but are not shown in the list
}
```

## Reward
```ts
Reward {
  id, businessId, title: "Thanks for coming back",      // the message, max 40 characters
  discount: { type: "PERCENT", value: 15 } | { type: "AMOUNT", value: 10, currency: "RON" },
  sentAt, validUntil,                                     // validUntil = sentAt + length (1–3 weeks, 1 month; rules also 3 or 5 days)
  source: "MANUAL" | { ruleId: string },                  // "By you" / "Auto"
  grants: { customerId, state: "NOT_USED" | "USED" | "ENDED" | "STOPPED", usedAt?, bookingId? }[],
  stoppedAt?
}
```
- Single use: one grant can be used for one booking. "Used by U of N" = grants with state USED / all grants.

## Automatic reward rule
```ts
RewardRule {
  id, on: boolean, title: "Come back soon",
  dayOfMonth: 15, firstSendAt: "2026-11-15",               // months without that day send on their last day
  visits: { count: 1, mode: "EXACTLY" | "AT_LEAST" },      // counted in the month before each send
  repeat: "ONCE" | "EVERY_MONTH",                          // "Only once" / "Every month"
  skipIfUnused: true,
  discount, validForDays: 3 | 5 | 7 | 30,
  stats: { timesSent: 3, people: 27, used: 11 }
}
```
- At each send: candidates = customers whose visits between the same day last month and the day before the send match `visits`; remove those already granted (ONCE) and, if `skipIfUnused`, those with a NOT_USED grant from this rule; create one Reward with a grant per person.

## Reservation (host side, every category)
```ts
Reservation {
  id, businessId, customerId,
  kind: "SERVICE" | "TABLE" | "EVENT",
  what: "Haircut" | "Table" | "Wine tasting",     // service name · "Table" · event title
  people: 1,
  date: "2026-10-26", from: "14:30", to: "15:30",
  durationMin?: 60, price?: { amount: 120, currency: "RON" },   // services only
  teamMemberId?: string,                          // "With Andrei"; only when the business assigns one
  offer?: { type: "COUPON", couponId, discount, pays: 102 }      // "Pays 102 RON instead of 120 RON"
        | { type: "EVENT", eventId, sittingId },
  specialRequests?: string,
  requestedAt, answerBy,                          // answerBy = requestedAt + 24 h
  state: "WAITING" | "CONFIRMED" | "DECLINED" | "CANCELLED" | "DONE" | "NO_SHOW",
  declineReason?: "FULLY_BOOKED" | "CLOSED_THAT_DAY" | "NO_ANSWER",   // NO_ANSWER = declined automatically
  answeredAt?, cancelledAt?, checkedAt?,
  cancelledBy?: "CUSTOMER" | "BUSINESS",        // "By you" / "By the place" (My activity)
  myRating?: 1 | 2 | 3 | 4 | 5,                  // customer's own rating of a DONE visit ("★ N")
  place: { businessId, name, type: "Barber & salon", city, address, phone, avatarUrl?, avatarColor }   // customer side
}
```
- Created from a `TableBookingRequest` (TB3) or a services booking (F4 / R3) in state WAITING.
- WAITING → CONFIRMED (Accept) · DECLINED (Decline with a reason, or `answerBy` passed → NO_ANSWER) · CANCELLED (the customer cancels the request, MA4).
- CONFIRMED → CANCELLED (host RV5 or customer MA5; `cancelledBy`) · NO_SHOW (host) · DONE (host, or automatically at the start of the day after `date` if still CONFIRMED).
- RV1 day lists: CONFIRMED / DONE (and NO_SHOW) for today and tomorrow, by `from`. RV2: WAITING by `requestedAt` ascending. Tab badge = count of WAITING.
- Visible to the host only: the customer's phone and email (RV3, RV5).

## My activity (customer side)
```ts
MyActivity {
  upcoming: Reservation[],        // state WAITING | CONFIRMED, start >= now; grouped by date, earliest first
  history: Reservation[],         // DONE | DECLINED | CANCELLED; grouped by month, newest first
  rewards: {
    ready: RewardGrantView[],     // NOT_USED and validUntil >= today; validUntil ascending (ends soonest first)
    usedOrEnded: RewardGrantView[]   // USED ("Used · usedAt") · ENDED / STOPPED ("Ended · validUntil or stoppedAt"); newest first
  }
}
RewardGrantView { rewardId, place, discount, title, validUntil, state, usedAt? }
```
- Tab counts: `upcoming.length`, `rewards.ready.length`; hidden at 0.
- History action: DONE without `myRating` → Rate; DONE with `myRating` → "★ N"; DECLINED / CANCELLED → Book again.
- Decline reason text: FULLY_BOOKED → "Fully booked" · CLOSED_THAT_DAY → "Closed that day" · NO_ANSWER → "No answer". Cancelled: CUSTOMER → "By you" · BUSINESS → "By the place".

## Search (public)
```ts
SearchRequest {
  q: "maestro",                                   // as typed, trimmed
  tab: "ALL" | "VIDEOS" | "PLACES" | "DEALS",
  dealType?: "ALL" | "EVENT" | "COUPON",          // Deals tab tiles; default ALL
  cursor?: string                                  // from the previous page; none = first page
}
SearchPage {
  blocks: SearchBlock[],                           // ranked, best match first
  nextCursor: string | null                        // null = last page (hide "Loading more")
}
SearchBlock =                                      // ALL mixes the three; a tab returns only its own type
  | { type: "PLACE",  place: PlaceResult }                     // one row
  | { type: "VIDEOS", items: VideoResult[] }                   // 1–2: one row of the 2-column grid
  | { type: "DEALS",  items: DealResult[] }                    // 1–2: one row of the 2-column grid
PlaceResult {
  businessId, name: "Maestro Host", verified: boolean,
  category: "SERVICES" | "ACCOMMODATION" | "FOOD_BEVERAGE",   // which profile opens (PS1 / PA1 / PF1)
  subcategoryLabel: "Barber & salon", city: "Brașov", avatarUrl?,
  openingHours?: WeeklyHours,                      // SERVICES, FOOD_BEVERAGE → Opening status rule
  checkIn?: "14:00", checkOut?: "11:00"            // ACCOMMODATION
}
VideoResult {
  itemId, itemType: "SERVICE" | "ROOM",            // SERVICE → F2, ROOM → PA2
  title: "Haircut", businessId, businessName: "Maestro Host",
  price: { amount, currency, from?: boolean }, priceUnit?: "NIGHT",
  people: 1,                                       // Service.peoplePerBooking / Room.guestsMax
  durationMin?: 60,                                // services only; rooms show "Details"
  thumbnailUrl
}
DealResult {
  offerId, type: "COUPON" | "EVENT", title: "Haircut" | "Wine tasting",
  discount?: { type: "PERCENT", value: 15 } | { type: "AMOUNT", value: 10, currency: "RON" },   // coupons only
  businessId, businessName: "Maestro Bistro",
  businessCategory: "SERVICES" | "FOOD_BEVERAGE",  // F4C / F4E vs TB2C / TB2E
  endsAt, quantityLeft: 50, thumbnailUrl?,
  firstDate: "2026-10-26",                         // first day the deal applies: the booking opens on it
  serviceIds?: string[]                            // SERVICES deals: the services it applies to (open question #61)
}
RecentSearch { query: "haircut brașov", searchedAt }   // this person's, newest first
```
- **Ranking** of ALL (and inside each tab) is the backend's; the app shows the blocks in the order received and never re-sorts. Deals inside the Deals tab: `endsAt` ascending (ending soonest first).
- **Rows of two** come from the backend as one block; a block with a single item shows one card in the left column.
- **Only bookable deals**: not past `endsAt`, `quantityLeft > 0`, at a business that takes bookings in the app.
- **Recent searches**: saved when results are shown; tapping one runs it again; remove one; clear all.
- **Status line** (place row): SERVICES / FOOD_BEVERAGE use the Opening status rule; ACCOMMODATION shows "Check-in HH:MM · Check-out HH:MM".

## Post (profile, any person)
```ts
Post {
  id, authorUserId, publishedAt,
  video: { url, thumbnailUrl },                    // one clip, up to 100 MB; its length is not measured
  title: "Fresh cut for a sunny weekend!",          // required, 1–30 characters
  description?: string,                             // 0–100 characters
  tag?: PostTag                                     // one tag per post
}
PostTag {
  businessId,                                       // the place
  itemType?: "SERVICE" | "ROOM",                    // SERVICES → a service, ACCOMMODATION → a room; FOOD_BEVERAGE: none
  itemId?
}
CreatePostRequest { videoUploadId, title, description?, tag?: PostTag }
UpdatePostRequest { title, description?, tag?: PostTag | null }   // EP1 Save; null removes the tag; the video can't change
DeletePost { postId }                                              // EP2: deletes the video file, title, description, tag and engagement (views, likes)
VisitForTag {                                       // "From your visits" (NP4): this person's DONE reservations, newest first
  businessId, name, verified, avatarUrl?, category,
  what: "Haircut" | "Table for 2" | "Double Room",  // Reservation.what
  itemType?, itemId?,                               // what was booked, when it is a service or a room
  date
}
```
- Caps count characters as shown (an emoji counts as one); the server enforces them too.
- Publish needs a title with at least one non-space character.
- Viewer: `tag.itemId` → the service / room video (F2 / PA2); place only → the profile (PS1 / PF1 / PA1); no tag → no Tag icon.
- Only the author can edit or delete a post. Delete is permanent and removes everything linked to the post for everyone.
- EP2 shows the title and the tag (place · item); "The video" and "Engagement · Views and likes" are labels with no length and no counts.

## Account (create or sign in)
```ts
EmailCheck { email } → { exists: boolean }                   // AU2: false → AU3 (create), true → sign in with the password
UsernameCheck { username } → { available: boolean }          // AU3 "✓ Available", checked while typing
SignUpRequest {
  email, firstName, lastName,                                // two name fields, never "Full name"
  username,                                                  // unique
  dateOfBirth: "1998-03-12",                                 // date; never shown on the profile
  password                                                   // at least 8 characters
}
```
- **Minimum age: 16** — age on the sign-up day = years between `dateOfBirth` and today. Under it, the app disables Create account (AU5) and the server refuses the request too.
- The date picker opens on 2000-01-01 when empty; valid dates only (no 31 Feb); years back to 100 years ago.
- Signed out, the Profile tab shows AU1; no other screen asks for an account.

## Admin (dashboard)
```ts
AdminRole = "MODERATOR" | "SUPER_ADMIN"                     // checked on the server for every page and action
ReviewItem {                                                 // AD1 queue: Post (see Post) + review fields
  postId, title, author { userId, name, username, role, memberSince, approvedBefore, rejectedBefore },
  tag?: { label: "Maestro Host · Haircut" }, uploadedAt, fileSizeMb, resolution: "1080 × 1920",
  state: "PENDING" | "APPROVED" | "REJECTED", decidedBy?, decidedAt?, rejectReason?
}
ReviewDecision { postId, decision: "APPROVE" | "REJECT", reason?: "NOT_ALLOWED" | "LOW_QUALITY" | "WRONG_TAG" | "SPAM" }   // reason required for REJECT
AnalyticsSummary {
  period: "24H" | "7D" | "30D",
  videos: { pending, approved, rejected, timeToReviewMin }, people: { newUsers, newHosts, hostApplicationsWaiting },
  reservations: { requests, confirmed, declined, noShows }, health: { playbackErrors, uploadFailures, uptimePct },
  previous: { /* same shape, the period before: for the change lines */ }, series: { /* per card: values over the period, for the sparklines */ }
}
HostApplication {
  id, business { name, category, type, city, address }, owner { name, email, phone },
  documents: { name, url /* short-lived */ }[], appliedAt, state: "PENDING" | "APPROVED" | "REJECTED", decidedBy?, reason?
}
HostDecision { applicationId, decision: "APPROVE" | "REJECT", reason? }
```
- Pending reviews are oldest first; counts feed the tab badges (Reviews, Platform Users / Host Approval).
- Every `ReviewDecision` and `HostDecision` writes an Audit Log entry (who, what, when, reason); the Audit Log is read only.
- Host application personal data and documents are returned only to roles that approve hosts; every document view is logged.

## Display rules
| Rule | Output |
|---|---|
| Discount | PERCENT → "20% OFF"; AMOUNT → "10 RON OFF" |
| Time left (until `endsAt`) | same day → "Today"; 1 → "1 day"; n → "n days". **Red** when Today or 1 day |
| Opening status | open → "Open now · Closes HH:MM" (green); < 60 min to close → "Closes soon · Until HH:MM" (amber); closed → "Closed · Opens HH:MM" (red) |
| Price | "120 RON"; rooms add "/ night"; services with `from` add "from" before amount |
| Price level | 4-bar meter + label |
| Guests / people | icon + number only on cards; "2 guests" / "1 person" (localised plural) on the video info bar |
| Duration | "60 min" |
| Included chips on video | first 2 `included` items + "+N more" where N = total − 2 |
| Included count | "What's included · N" where N = included count |
| Offer windows (offer card sub) | that day's windows, "HH:MM – HH:MM" joined by " · " |
| Offer sticker | coupon → discount text ("20% OFF", "10 RON OFF"); event → event title |
| Seats / spots | "N seats left" (tables) / "N spots left" (services), localised plural; hide a sitting when seatsLeft < guests |
| Booking time range | start + `tableHoldMin` (tables) or service duration (salon): "20:00 – 21:30" |
| Coupon reminder (TB3) | "Valid <window containing the picked time> · applied at the restaurant" |
| Event reminder (TB3) | "Sitting <from – to> · <guests> seats held for you" |
| Month calendar | FREE → green tint, FEW_LEFT → amber tint, FULL/CLOSED → grey + line-through, past → light text; no offer marks in cells |
| Reservation status chip | WAITING → "Waiting for you" (amber) · CONFIRMED → "Confirmed" (green) · DONE → "Done" (grey) |
| Requested ago (RV2) | < 60 min → "N min ago"; otherwise "N h ago" |
| Reservation facts | "what · N people"; add "60 min", "120 RON", "With <name>" only when the reservation has them |
| Reward days left (MA6) | same as Time left: "N days left", red at Today / 1 day; "Until <Ddd, d Mon>" |
| Coupon strip, customer side | "You pay <new> instead of <old>" (host side: "Pays …") |
| Search place status (SR3/SR5) | Opening status word (600, its colour) + " · " + the time in `text.secondary`; accommodation: "Check-in 14:00 · Check-out 11:00" |
| Search query echo (SR2) | "No results for “<query>”", the query as typed |
| Visits (RV2/RV3) | 0 done → "New customer" / "New customer · first visit"; else "N visits" / "N visits · last <d Mon>" |
