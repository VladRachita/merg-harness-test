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
  visitsCount: 6, lastVisitAt,                     // from bookings made in the app
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
