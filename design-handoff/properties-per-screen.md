# Properties per screen — data the backend must provide and accept

Every page and screen of the **Profile Quick Actions** design canvas, with each **dynamic** element:
- what the screen **displays** (data the app reads from the backend);
- what the user **enters or picks** (inputs);
- what the screen **sends** (actions / requests);
- what it needs to **open** (parameters).

Static copy, icons, illustrations, layout and sample values are left out; the examples in *italics* are the sample values from the designs, only to show the shape.

The purpose is to let the backend check that every value exists in the API, in the right type. If a value is missing, they can raise it before the app is built.

- Source: the design canvas (https://claude.ai/artifact/5317zoDgLoVqdsUCq6HUpd) and the handoff in this folder (`screens/medium/<id>.html`, `screenshots/medium/<id>.png`).
- Small, medium and large phones show **the same data**, so each screen is listed once.
- Field names follow `docs/06-data-model.md` (suggested names; the meaning matters, not the name).
- **Where a field is missing from `06-data-model.md` or a rule is not decided**, it is marked **⚠ gap** and repeated in §B at the end.

## How to read a screen

| Block | Meaning |
|---|---|
| **Opens with** | Parameters / context the screen needs before it can load (ids, the chosen date, …). |
| **Elements displayed** | Data shown on the screen, read from the backend. *Computed in the app* = the backend sends the raw value and the app formats it (e.g. `durationMin: 60` → "60 min"). |
| **Inputs** | What the user types, picks or toggles on this screen. Type, limits and whether it is required. |
| **Actions** | What the screen sends to the backend, or what a tap needs from it. |

Types: `string`, `int`, `bool`, `money` = `{ amount: number, currency: "RON" }`, `date` = `YYYY-MM-DD`, `time` = `HH:MM` (business local time), `datetime` = ISO 8601 with time zone, `url`, `enum(A|B)`, `T[]` = list. `?` = optional.

## Context every screen needs (not repeated per screen)

| Value | Type | Used for |
|---|---|---|
| Signed-in user id + role on this business | `userId`, `enum(OWNER\|TEAM_MEMBER\|CUSTOMER)` | Host screens vs customer screens; owner-only actions (e.g. remove a team member). **⚠ gap:** roles are not in `06`. |
| Current business (host screens) | `businessId` | Every host screen loads data for this business. |
| Business category | `enum(SERVICES\|ACCOMMODATION\|FOOD_BEVERAGE)` | Which screens and labels exist (Services vs Rooms, Book now vs Call, duration / team only for services). |
| Locale | `enum(EN\|RO\|DE\|IT\|ES\|FR)` | All copy, plurals, dates. The backend sends raw values, never formatted text. |
| Business time zone | IANA zone, e.g. `Europe/Bucharest` | "Today", "Tomorrow", opening status, deadlines (24 h answer, done the next day, reward sends). **⚠ gap:** not in `06`. |
| Currency | `string` (`RON`) | Every price and discount. |
| Server "now" | `datetime` | Today / Tomorrow labels, time left, "2 h ago". |
| Avatar fallback colour | `avatarColor` (hex) or derived from the id in the app | Every person or place without a photo shows an initial on a colour (team members, customers, places). **⚠ gap:** decide whether the backend stores it. |

---

## Contents — 11 pages, 64 screens

| Page | Screens |
|---|---|
| Profile (host) | `HP-profile` |
| Services · Video flow (host) | `HS1-services-list`, `HS2-add-video`, `HS3-service-details`, `HS4-edit-service`, `HR1-rooms-list`, `HR2-add-video`, `HR3-room-details`, `HR4-edit-room` |
| Public · Profiles | `PA1-profile-rooms`, `PA2-room-video`, `PA3-room-included`, `PS1-profile-services`, `PF1-profile-fnb` |
| Public · Salon | `R1-services-stylist-picked`, `R2-video`, `R3-pick-time`, `SV-included`, `F1-services-everyone`, `F2-video`, `F3-choose-stylist`, `F4-pick-time`, `F4C-pick-time-coupon`, `F4E-pick-time-event` |
| Public · Coupons & Events | `CE1-coupons-events` |
| Public · Table booking | `TB1-pick-date`, `TB2-guests-time-any`, `TB2C-guests-time-coupon`, `TB2E-guests-time-event`, `TB3-details-any`, `TB3C-details-coupon`, `TB3E-details-event`, `TB4-booked` |
| Host · Team | `TM1-team-list`, `TM2-invite`, `TM3-team-member` |
| Host · Customers & rewards | `CR1-customers` … `CR10-reward-details` |
| Host · Reservations | `RV1-reservations` … `RV6-after-visit` |
| Customer · My activity | `MA1-upcoming` … `MA6-reward` |
| Public · Search | `SR1-start`, `SR2-no-results`, `SR3-all`, `SR4-videos`, `SR5-places`, `SR6-deals` |

Start with the **quick index** below (what each screen reads and sends). Then each page in detail, then: **§A** rules and jobs the backend runs · **§B** gaps to decide · **§C** entity and field index.

---

## Quick index — what each screen reads and sends

One line per screen.
- **Reads** = the fields the screen needs from the backend, written as `Entity.field`; `Entity{a, b}` = those fields of that entity.
- **Sends** = the request the screen makes.
- Device-only actions (copy, call, mute) are not listed.

Full detail per screen is in the page sections below. ⚠ = a gap listed in §B.

**Profile (host)**

| Screen | Reads | Sends |
|---|---|---|
| `HP-profile` | `BusinessProfile{avatarUrl, name, verified, handle, category, stats.posts, stats.followers, stats.following⚠}` · count of `Reservation` WAITING | upload profile photo → `BusinessProfile.avatarUrl` |

**Services · Video flow (host)**

| Screen | Reads | Sends |
|---|---|---|
| `HS1-services-list` | `Service[]{id, name, price, peoplePerBooking, durationMin, video.thumbnailUrl}` | — |
| `HS2-add-video` | — (phone gallery) | upload video file → `Video{id, url, thumbnailUrl, durationSec}` ⚠ |
| `HS3-service-details` | uploaded `Video.thumbnailUrl` · `TeamMember[]{id, name, avatarUrl, initials, avatarColor}` | create `Service{name, shortDescription, price{amount, currency, unit}, durationMin, peoplePerBooking, included[], notIncluded[], notAllowed[], teamMemberIds[], videoId?}` (+ `category`⚠, `price.from`⚠) |
| `HS4-edit-service` | `Service{…all HS3 fields, video?}` · `TeamMember[]` | update `Service` · delete `Service` |
| `HR1-rooms-list` | `Room[]{id, name, pricePerNight, guestsMax, video.thumbnailUrl}` | — |
| `HR2-add-video` | — (phone gallery) | upload video file → `Video` ⚠ |
| `HR3-room-details` | uploaded `Video.thumbnailUrl` | create `Room{name, shortDescription, pricePerNight, guestsMax, included[]{group⚠, item}, notIncluded[], notAllowed[], videoId?}` |
| `HR4-edit-room` | `Room{…all HR3 fields, video?}` | update `Room` · delete `Room` |

**Public · Profiles**

| Screen | Reads | Sends |
|---|---|---|
| `PA1-profile-rooms` | `BusinessProfile{handle, avatarUrl, name, category, subcategoryLabel, stats.posts, stats.followers, stats.rating, stats.reviewsCount, phone, address{line, city, lat, lng}, checkIn, checkOut, priceLevel}` · `viewer.isFollowing`⚠ · `Room[]{id, name, pricePerNight, guestsMax, video.thumbnailUrl}` | follow / unfollow ⚠ |
| `PA2-room-video` | `Video{url, thumbnailUrl, likes, views, publishedAt}` · `viewer.hasLiked`⚠ · `BusinessProfile{avatarUrl, name, handle, phone}` · `Room{name, shortDescription, guestsMax, pricePerNight, included[0..1].item, included.length}` | like / unlike · count a view ⚠ |
| `PA3-room-included` | `Room{name, guestsMax, pricePerNight, included[]{group, item}, notIncluded[], notAllowed[]}` | — |
| `PS1-profile-services` | `BusinessProfile` as PA1 with `openingHours` (not check-in / out) · `viewer.isFollowing`⚠ · `Service[]{id, name, category, price{amount, from}, peoplePerBooking, durationMin, video.thumbnailUrl}` + its ACTIVE `TeamMember{avatarUrl, initials, avatarColor}` | follow / unfollow |
| `PF1-profile-fnb` | `BusinessProfile` as PS1 | follow / unfollow |

**Public · Salon**

| Screen | Reads | Sends |
|---|---|---|
| `R1-services-stylist-picked` | `BusinessProfile{name, verified}` · ACTIVE `TeamMember[]{id, name, avatarUrl, initials, avatarColor}` · the customer's usual `TeamMember.id`⚠ · categories `{category, count, imageUrl⚠}` for that member · `Service[]` as PS1, filtered by member | — |
| `R2-video` | `Video{url, thumbnailUrl, likes, views, publishedAt}` · `viewer.hasLiked`⚠ · `BusinessProfile{avatarUrl, name, handle}` · `Service{name, shortDescription, durationMin, peoplePerBooking, price, included[0..1], included.length}` · `TeamMember.name` | like / unlike · count a view ⚠ |
| `R3-pick-time` | `Service{name, durationMin, price, teamMemberIds}` · `TeamMember[]{id, name, avatarUrl, initials}` + `nextFree` · `DayAvailability[7]{date, state}` per member · `Slot[]{start, end, state}` | `ServiceBookingRequest{businessId, serviceId, teamMemberId, date, from, to}` + customer details ⚠ |
| `SV-included` | `Service{name, durationMin, price, included[], notIncluded[], notAllowed[]}` | — |
| `F1-services-everyone` | as R1 with **Everyone** (all categories, all services) | — |
| `F2-video` | as R2 without `TeamMember.name` | like / unlike · count a view ⚠ |
| `F3-choose-stylist` | `Service{name, durationMin, price}` · ACTIVE `TeamMember[]{id, name, avatarUrl, initials, role, yearsExperience, specialties[], rating, reviewsCount, languages[]}` + `nextFree` · "Anyone" earliest `nextFree` | — |
| `F4-pick-time` | as R3 + the day's `Offer[]{id, type, discount \| title, windows[] / sittings[]}` for the service · "Any time" range ⚠ | service booking request + `offerId?` |
| `F4C-pick-time-coupon` | as F4 + the coupon's `windows[]` with `Slot[]` inside each | service booking request with `offerId` |
| `F4E-pick-time-event` | as F4 + `Offer.sittings[]{id, from, to, spotsLeft⚠}` | service booking request with `offerId`, `sittingId` |

**Public · Coupons & Events**

| Screen | Reads | Sends |
|---|---|---|
| `CE1-coupons-events` | counts per type · `Offer[]{id, type, title, discount, endsAt, quantityLeft, video.thumbnailUrl}` | claim a coupon / ticket (not designed) ⚠ |

**Public · Table booking**

| Screen | Reads | Sends |
|---|---|---|
| `TB1-pick-date` | `BusinessProfile.name` · `RestaurantBookingSettings.bookingHorizonMonths` · `DayAvailability[month]{date, state}` · `Offer[]` in the month `{id, type, title, dates, first start or window}` | — |
| `TB2-guests-time-any` | `DayAvailability[7]{date, state}` · `RestaurantBookingSettings{capacity, tableHoldMin, services[]{name, from, to}}` · the day's `Offer[]{id, type, discount, title, windows[], sittings[], minGuests, maxGuests}` · `TimeSlot[]{start, state}` for the guest count | — |
| `TB2C-guests-time-coupon` | as TB2 + the coupon's `windows[]` with `TimeSlot[]` inside each | — |
| `TB2E-guests-time-event` | as TB2 + `Offer.sittings[]{id, from, to, seatsLeft}` | — |
| `TB3-details-any` | `BusinessProfile.name` · the chosen `{date, from, to, guests}` · `tableHoldMin` | `TableBookingRequest{businessId, date, from, to, guests, firstName, lastName, phone{country, number}, email, specialRequests?}` → returns `Reservation.id` |
| `TB3C-details-coupon` | as TB3 + `Offer{discount, windows[]}` | as TB3 + `offerId` |
| `TB3E-details-event` | as TB3 + `Offer.title` + the sitting `{from, to}` | as TB3 + `offerId`, `sittingId` |
| `TB4-booked` | `Reservation{date, from, to, people, state}` · `BusinessProfile{name, address.line, phone}` | — |

**Host · Team**

| Screen | Reads | Sends |
|---|---|---|
| `TM1-team-list` | `BusinessProfile.name` · `TeamMember[]{id, userId⚠, name, avatarUrl, initials, avatarColor, status, isOwner, username, role}` + services count · `TeamInvite[]{id, username, invitedAt}` PENDING | cancel `TeamInvite` |
| `TM2-invite` | user search results `{userId, name, username, avatarUrl, inviteState}` ⚠ | search users by username · create `TeamInvite{businessId, userId}` |
| `TM3-team-member` | `TeamMember{id, name, username, avatarUrl, initials, avatarColor, status, isOwner, joinedAt}` · `Service[]{id, name, durationMin, price{amount, from}, teamMemberIds}` | update `TeamMember.status` + the member's services · remove member |

**Host · Customers & rewards**

| Screen | Reads | Sends |
|---|---|---|
| `CR1-customers` | `BusinessProfile.name` · counts per group · group rules ⚠ · `Customer[]{id, name, avatarUrl, initials, avatarColor, visitsCount, lastVisitAt, groups, unusedRewardIds → Reward.discount}` | — |
| `CR2-new-reward` | the chosen `Customer[]{name, avatarUrl, initials}` + group · `BusinessProfile.name` | create `Reward{title, discount{type, value}, validFor, source: MANUAL, customerIds[], audienceGroup?⚠}` |
| `CR3-reward-sent` | `Reward{discount, title, validUntil}` · recipients' names | — |
| `CR4-rewards-tab` | `RewardRule[]{id, title, dayOfMonth, on, discount, validForDays, visits, nextSendAt, matchingNow}` · idea templates ⚠ · `Reward[]` this month `{id, discount, title, source, validUntil, grants used / total}` | update `RewardRule.on` |
| `CR5-auto-when` | — (dates computed from the pick) | — (draft) |
| `CR6-auto-who` | match preview `{count, people[3]{name, avatarUrl, initials}}` | preview query `{visits, repeat, skipIfUnused, firstSendAt}` |
| `CR7-auto-reward` | `BusinessProfile.name` | — (draft) |
| `CR8-auto-check` | match preview `{count}` for the first send | create `RewardRule{title, discount, validForDays, dayOfMonth, firstSendAt, visits{count, mode}, repeat, skipIfUnused, on: true}` |
| `CR9-auto-edit` | `RewardRule{…all, stats{timesSent, people, used}, nextSendAt, matchingNow}` · `BusinessProfile.name` | update `RewardRule` · delete `RewardRule` |
| `CR10-reward-details` | `Reward{discount, title, validUntil, audienceGroup⚠, grants[]{customer{name, avatarUrl, initials}, state, usedAt}}` · `BusinessProfile.name` | stop `Reward` |

**Host · Reservations**

| Screen | Reads | Sends |
|---|---|---|
| `RV1-reservations` | count WAITING + the oldest `requestedAt` · `Reservation[]` today and tomorrow `{id, from, to, state, what, people}` + `Customer.name` · counts per day | — |
| `RV2-requests` | `Reservation[]` WAITING `{id, date, from, to, requestedAt, what, people, offer, specialRequests}` + `Customer{name, visitsCount}` | accept |
| `RV3-request` | `Reservation{…all, durationMin, price, teamMemberId → TeamMember.name, offer{discount, pays}}` · `Customer{name, avatarUrl, initials, avatarColor, visitsCount, lastVisitAt, phone, email}` | accept |
| `RV4-decline` | `Reservation{date, from, what}` · `Customer.name` | decline `{declineReason: FULLY_BOOKED \| CLOSED_THAT_DAY}` |
| `RV5-confirmed` | as RV3 | cancel (`cancelledBy: BUSINESS`) |
| `RV6-after-visit` | `Reservation{date, from, to, what, people, durationMin, price}` · `Customer{name, avatarUrl, initials, visitsCount, lastVisitAt}` | check `{state: DONE \| NO_SHOW}` |

**Customer · My activity**

| Screen | Reads | Sends |
|---|---|---|
| `MA1-upcoming` | `MyActivity.upcoming[]` = `Reservation{id, date, from, to, state, what, people, offer, place.name}` · tab counts | — |
| `MA2-rewards` | `MyActivity.rewards.ready[]` / `.usedOrEnded[]` = `RewardGrantView{rewardId, discount, title, validUntil, state, usedAt, place.name}` | — |
| `MA3-history` | `MyActivity.history[]` = `Reservation{id, date, from, state, what, people, declineReason, cancelledBy, myRating, place{name, businessId}}` | rating through the existing review flow ⚠ |
| `MA4-reservation-waiting` | `Reservation{…all, durationMin, price, teamMemberId → TeamMember.name, offer{discount, pays}, specialRequests, place{businessId, name, type, address, phone, avatarUrl, avatarColor}}` | cancel (`cancelledBy: CUSTOMER`) |
| `MA5-reservation-confirmed` | as MA4 | cancel (`cancelledBy: CUSTOMER`) |
| `MA6-reward` | `RewardGrantView{discount, title, validUntil, place{businessId, name, type, city}}` | — (booking with it: `rewardGrantId`⚠) |

**Public · Search**

| Screen | Reads | Sends |
|---|---|---|
| `SR1-start` | `RecentSearch[]{query, searchedAt}` ⚠ | search `{q, tab: ALL}` · delete one recent `{query}` · clear all recents |
| `SR2-no-results` | `SearchRequest.q` (echo) · `SearchPage.blocks` empty | — |
| `SR3-all` | `SearchPage{blocks[], nextCursor}` (tab ALL): `PlaceResult{businessId, name, verified, category, subcategoryLabel, city, avatarUrl, openingHours, checkIn, checkOut}` · `VideoResult{itemId, itemType, title, businessName, price, priceUnit, people, durationMin, thumbnailUrl}` · `DealResult{offerId, type, title, discount, businessId, businessName, businessCategory, endsAt, quantityLeft, thumbnailUrl, firstDate, serviceIds⚠}` | search `{q, tab: ALL, cursor}` (next page) |
| `SR4-videos` | `SearchPage` (tab VIDEOS) of `VideoResult` | search `{q, tab: VIDEOS, cursor}` |
| `SR5-places` | `SearchPage` (tab PLACES) of `PlaceResult` | search `{q, tab: PLACES, cursor}` |
| `SR6-deals` | `SearchPage` (tab DEALS) of `DealResult`, `endsAt` ascending | search `{q, tab: DEALS, dealType: ALL\|EVENT\|COUPON, cursor}` |

---

## Page: Profile (host)

### Screen · Host profile with Quick Actions (`HP-profile`, board *A · Medium*)

**Opens with:** `businessId` (the signed-in host's business).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Profile photo | `BusinessProfile.avatarUrl` | `url?` | No photo → initials from `name` (*MH*). |
| Name | `BusinessProfile.name` | `string` | *Maestro Host* |
| Verified badge | `BusinessProfile.verified` | `bool` | Badge only when true. |
| Handle | `BusinessProfile.handle` | `string` | *@maestro_seed_host*. A pencil sits next to it (looks editable; the edit flow is not designed). |
| Posts count | `stats.posts` | `int` | *10* |
| Followers count | `stats.followers` | `int` | *1* |
| Following count | `stats.following` | `int` | *0*. **⚠ gap:** not in `06` (`stats` has posts, followers, rating, reviewsCount). |
| Quick Actions tiles | `BusinessProfile.category` | `enum` | The tiles are fixed. The **Services** tile reads **Rooms** and opens HR1 for ACCOMMODATION. |
| Icon tabs: Videos · Reviews · Reservations | — | — | Videos selected. The tab contents are not drawn on this board (Reservations = RV1). |
| Reservations tab badge | count of reservations in state `WAITING` | `int` | Amber badge on the calendar tab, hidden at 0 (drawn on RV1). |

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Edit photo (pencil on the avatar) | image file | Upload a new profile photo. The picker / crop flow is not designed. |

**Actions:** upload the profile photo → update `avatarUrl`. Settings, Create post (+) and the Quick Actions **Calendar**, **Bookings**, **Hours** and **Coupons** tiles open screens that are not designed.

---

## Page: Services · Video flow (host)

### Screen 1 · Services (`HS1-services-list`, board *1 · Services*)

**Opens with:** `businessId`.

**Elements displayed** (one card per service)

| Element | Field | Type | Notes |
|---|---|---|---|
| Count | number of services | `int` | "2 services" (plural in the app). |
| Thumbnail | `Service.video.thumbnailUrl` | `url?` | No video → "No video yet" placeholder. A play icon is shown when a video exists. |
| Title | `Service.name` | `string` | Max 2 lines on the card. |
| Price | `Service.price` | `money` | *120 RON*. No unit on the card. |
| Guest number | `Service.peoplePerBooking` | `int` | *1* |
| Service time | `Service.durationMin` | `int` (minutes) | "60 min" computed in the app. |

**Inputs:** none.

**Actions:**
- the pencil on a card → HS4 with `serviceId`;
- **New service** → HS2 (create).

**⚠ gap:** the list order is not defined (proposal: creation order).

### Screen 2 · Add a video (`HS2-add-video`, board *2 · Add video*)

**Opens with:** mode `CREATE` (new service), or `ATTACH` / `REPLACE` for an existing `serviceId` (from HS4 **Add video** / HS3 **Change**).

**Elements displayed:** the phone's own videos (thumbnail + length) and the albums under **Recents**, with the "1 video · 0:24" footer. **All from the device gallery, nothing from the backend.**

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Pick one clip | one local video file | Single selection. |

**Actions**
- **Next** → upload the clip. The backend returns `Video { id, url, thumbnailUrl, durationSec }`. The clip is attached to the service on Save (HS3 / HS4).
- **Skip** → continue with no video.
- **⚠ gap:** upload endpoint, accepted formats, maximum length and size, and transcoding / thumbnail generation are not defined.

### Screen 3 · Service details — create (`HS3-service-details`, board *3 · Service details*)

**Opens with:** the clip picked on HS2 (or none after Skip) and the business's team members.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Video thumbnail | `Video.thumbnailUrl` | `url` | **Change** → HS2. When there is no video, an **Add video** tile shows instead (as on HS4). |
| Team members ("Who does it") | `TeamMember[]`: `TeamMember.id`, `.name`, `.avatarUrl?`, `.initials`, `.avatarColor` | list | All team members of the business. The selected ones get a green check; the others are greyed. |
| Included count | `included.length` | `int` | "Included · 10". |
| "+6 more" | `included.length − 4` | `int` | Computed in the app. The first 4 items are shown. |

**Inputs**

| Input | Field | Type | Required | Notes |
|---|---|---|---|---|
| Title | `Service.name` | `string` | yes | Placeholder "Name your service". **⚠ gap:** max length (proposal 40; the cards clamp to 2 lines). |
| Description | `Service.shortDescription` | `string` | **⚠** | Shown as the video caption (max 2 lines). **⚠ gap:** required? max length (proposal 120). |
| Price | `Service.price.amount` | decimal | yes | Currency = the business currency (RON). |
| Price unit | `Service.price.unit` | `enum(VISIT\|PERSON)` | yes | "/ visit ▾" picker. |
| Duration | `Service.durationMin` | `int` (minutes) | yes | The row opens a picker (not designed). **⚠ gap:** allowed steps (5 / 15 min?) and maximum. |
| People per booking | `Service.peoplePerBooking` | `int` | yes | − / + stepper, min 1. **⚠ gap:** maximum. |
| Labels · Included | `Service.included` | `string[]` | no | Chips. **Add** adds an item; tapping a chip edits or removes it (the item editor is not designed). |
| Labels · Not included | `Service.notIncluded` | `string[]` | no | Same. |
| Labels · Not allowed | `Service.notAllowed` | `string[]` | no | Same. |
| Team members ("Who does it") | `Service.teamMemberIds` | `string[]` | **⚠** | Multi-select. Same data as the TM3 services checklist. **⚠ gap:** at least one required? |

**Actions:** **Save service** → create `Service { name, shortDescription, price { amount, currency, unit }, durationMin, peoplePerBooking, included[], notIncluded[], notAllowed[], teamMemberIds[], videoId? }`. The backend returns the new service; the app goes back to HS1.

**⚠ gaps (data used elsewhere that this form never asks for):**
- `Service.category` (*Hair*, *Beard*, *Massage*) drives the R1 / F1 category tiles;
- `Service.price.from` ("from 70 RON" on public cards);
- how a service is linked to coupons and events (`Offer.appliesTo.serviceIds`).

### Screen 4 · Edit service — no video yet (`HS4-edit-service`, board *Edit service · no video yet*)

**Opens with:** `serviceId` → load the `Service`.

**Elements displayed:**
- every HS3 field with its current value (*Beard trim*, *Clean beard shape…*, *50 RON / visit*, *30 min*, *1*, Included · 2, Not included, Not allowed, Who does it with Andrei selected);
- an **Add video** tile, because the service has no video (with a video, the thumbnail + **Change** shows as on HS3);
- team members as on HS3.

**Inputs:** the same as HS3.

**Actions**
- **Save changes** → update the `Service` (changed fields).
- **Delete service** (red trash in the header) → delete the `Service`. The confirmation is not designed. **⚠ gap:** what happens to future reservations and to offers linked to it.
- **Add video** → HS2 (`ATTACH`).

### Screen 5 · Rooms (`HR1-rooms-list`, board *1 · Rooms*) — accommodation hosts

**Opens with:** `businessId`.

**Elements displayed** (one card per room)

| Element | Field | Type | Notes |
|---|---|---|---|
| Count | number of rooms | `int` | "2 rooms" |
| Thumbnail | `Room.video.thumbnailUrl` | `url?` | No video → "No video yet". |
| Title | `Room.name` | `string` | Max 2 lines (*Family Room with Balcony*). |
| Price | `Room.pricePerNight` | `money` | "/ night" is added by the app. |
| Guest number | `Room.guestsMax` | `int` | *2*, *4* |

**Actions:**
- the pencil → HR4 with `roomId`;
- **New room** → HR2.

### Screen 6 · Add a video — room (`HR2-add-video`)

**Opens with:** mode `CREATE`, `ATTACH` or `REPLACE` for a `roomId`.

Same as HS2 (device gallery, single pick, **Next** uploads, **Skip**).

### Screen 7 · Room details — create (`HR3-room-details`, board *3 · Room details*)

**Opens with:** the clip from HR2 (or none).

**Elements displayed:**
- the video thumbnail + **Change**;
- the included count ("Included · 18") and "+14 more" (`included.length − 4`, computed in the app).

**Inputs**

| Input | Field | Type | Required | Notes |
|---|---|---|---|---|
| Title | `Room.name` | `string` | yes | Placeholder "Name your room". **⚠ gap:** max length. |
| Description | `Room.shortDescription` | `string` | **⚠** | Video caption. |
| Price per night | `Room.pricePerNight.amount` | decimal | yes | The unit is fixed "/ night"; currency of the business. |
| Guests | `Room.guestsMax` | `int` | yes | − / + stepper, min 1. **⚠ gap:** maximum. |
| Labels · Included | `Room.included` | `{ group, item }[]` | no | **⚠ gap:** the form adds plain chips with no **group**, but PA3 shows Included grouped (Bedroom, Bathroom, Kitchen, Comfort & tech, Outside). A group picker or an amenity checklist is needed. |
| Labels · Not included | `Room.notIncluded` | `string[]` | no | |
| Labels · Not allowed | `Room.notAllowed` | `string[]` | no | |

Rooms have **no** duration and **no** team members.

**Actions:** **Save room** → create `Room { name, shortDescription, pricePerNight, guestsMax, included[], notIncluded[], notAllowed[], videoId? }`.

### Screen 8 · Edit room — no video yet (`HR4-edit-room`, board *Edit room · no video yet*)

**Opens with:** `roomId` → load the `Room`.

**Elements displayed:** every HR3 field with its current value (*Family Room with Balcony*, *380 RON / night*, *4 guests*, Included · 3), plus the **Add video** tile.

**Inputs:** the same as HR3.

**Actions:**
- **Save changes** → update the `Room`;
- **Delete room** (trash) → delete the `Room` (confirmation not designed);
- **Add video** → HR2.

---

## Page: Public · Profiles (customer view of a business)

The profile header is the same on PA1, PS1 and PF1 and is described once, under PA1.

### Screen 1 · Accommodation profile · Rooms (`PA1-profile-rooms`, board *Public profile · Accommodation · Rooms*)

**Opens with:** `businessId` (or `handle`).

**Elements displayed — profile header (shared)**

| Element | Field | Type | Notes |
|---|---|---|---|
| Handle (top bar) | `BusinessProfile.handle` | `string` | *@stay_host_brasov* |
| Profile photo | `BusinessProfile.avatarUrl` | `url?` | Placeholder icon when there is none. |
| Name | `BusinessProfile.name` | `string` | |
| Category line | `BusinessProfile.category` + `BusinessProfile.subcategoryLabel?` | `enum` + `string?` | *Accommodation*; *Services · Barber & salon*; *Food & Beverage · Restaurant* |
| Posts | `BusinessProfile.stats.posts` | `int` | |
| Followers | `BusinessProfile.stats.followers` | `int` | |
| Rating | `BusinessProfile.stats.rating?`, `BusinessProfile.stats.reviewsCount` | `number?`, `int` | "–" and "No reviews yet" when there are no reviews. |
| Follow button state | `viewer.isFollowing` | `bool` | **⚠ gap:** not in `06` (Follow / Following). |
| Map | `BusinessProfile.address.lat`, `BusinessProfile.address.lng` | `number` | OpenStreetMap tiles. The pin icon comes from `BusinessProfile.category`. |
| Address | `BusinessProfile.address.line` (+ `.city`) | `string` | Tap = copy. |
| Hours cell | ACCOMMODATION: `BusinessProfile.checkIn`, `BusinessProfile.checkOut` · others: `BusinessProfile.openingHours` + now | `time` / `WeeklyHours` | "Check-in 14:00 · Check-out 11:00", or the opening status (see PS1). |
| Price level | `BusinessProfile.priceLevel` | `int 1–4` | Shown as Budget / Moderate / Expensive / Luxury. |

**Elements displayed — Rooms tab** (tabs: Videos · Rooms · Coupons · Reviews)

| Element | Field | Type | Notes |
|---|---|---|---|
| Count | number of rooms | `int` | "2 rooms" |
| Thumbnail | `Room.video.thumbnailUrl` | `url?` | Play button over it. |
| Title | `Room.name` | `string` | |
| Price | `Room.pricePerNight` | `money` | "/ night" is added by the app. |
| Guest number | `Room.guestsMax` | `int` | |

**Inputs:** the selected tab (local).

**Actions**
- **Follow / Unfollow** → toggle following this business (**⚠ gap:** endpoint).
- **Call** → the phone dialer with `phone`.
- Copy the address (on the device).
- A card, its play button or **Details** → PA2 with `roomId`.
- The **Videos** and **Reviews** tabs and the **More (⋮)** menu are not designed. **Coupons** = CE1.

### Screen 2 · Room video · Call on the side (`PA2-room-video`, board *Rooms video · Call on the side*)

**Opens with:** `roomId` (and its `Video`).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Video | `Video.url`, `Video.thumbnailUrl` (poster) | `url` | Full screen. Mute is local. |
| Likes | `Video.likes`, `viewer.hasLiked` | `int`, `bool` | **⚠ gap:** `hasLiked` is not in `06`. |
| Business avatar, name, handle | `BusinessProfile.avatarUrl` (or initial), `BusinessProfile.name`, `BusinessProfile.handle` | | |
| Caption | `Room.shortDescription` | `string` | Max 2 lines. |
| Included chips | `Room.included[0..1].item` | `string` | The first 2 items. |
| "+16 more" | `Room.included.length − 2` | `int` | Computed in the app → PA3. |
| Views · date | `Video.views`, `Video.publishedAt` | `int`, `datetime` | "5 views · Oct 21, 2026" |
| Info bar | `Room.name`, `Room.guestsMax`, `Room.pricePerNight` | | "Double Room · 2 guests · 250 RON / night" (not tappable). |

**Actions**
- **Like / unlike** → backend.
- **Call** → dialer.
- **⚠ gap:** count a view (when, and how often per viewer).
- **More (⋮)** is not designed.
- **X** → PA1.

### Screen 3 · Room · what is included (sheet) (`PA3-room-included`, board *Included · full list*)

**Opens with:** `roomId`.

**Elements displayed**
- Count "What's included · 18" (`included.length`).
- Subtitle: `Room.name` · `guestsMax` · `pricePerNight`.
- **Included grouped:** for each `group` (Bedroom, Bathroom, Kitchen, Comfort & tech, Outside), its icon and name, then its items. **⚠ gap:** a group enum is needed, see HR3.
- **Not included** (`notIncluded[]`) and **Not allowed** (`notAllowed[]`).

**Inputs / Actions:** none (close only).

### Screen 4 · Services profile (`PS1-profile-services`, board *Public profile · Services · Book now*)

**Opens with:** `businessId`.

**Elements displayed:** the PA1 profile header, with:
- the **opening status** in the hours cell: `openingHours` + now → "Open now · Closes 20:00" / "Closes soon · Until 22:30" / "Closed · Opens 09:00". The chevron opens the weekly hours sheet (not designed).
- tabs Videos · Services · Coupons · Reviews.

**Services tab**

| Element | Field | Type | Notes |
|---|---|---|---|
| Count | number of services | `int` | "2 services" |
| Thumbnail | `Service.video.thumbnailUrl` | `url?` | No video → the icon of `Service.category` (scissors). |
| Title | `Service.name` | `string` | |
| Team avatars | `Service.teamMemberIds` → `TeamMember.avatarUrl` / `TeamMember.initials` / `TeamMember.avatarColor` | list | Avatar stack (*A R*). ACTIVE members only. |
| Price | `Service.price` (+ `Service.price.from`) | `money` | "from 70 RON" when `Service.price.from` is true. |
| Guest number | `Service.peoplePerBooking` | `int` | |
| Service time | `Service.durationMin` | `int` | |

**Actions**
- **Book now** → not designed for services (open question #2).
- **Follow**, copy address and hours as on PA1.
- A card with a video → F2; a card without a video → F3 (the booking skips the video).

### Screen 5 · Food & Beverage profile (`PF1-profile-fnb`, board *Public profile · Food & Beverage · About + Book now*)

**Opens with:** `businessId`.

**Elements displayed:** the profile header only (category *Food & Beverage · Restaurant*, opening status *Closes soon · Until 22:30*, price level *Expensive*). No tabs and no content grid.

**Actions:**
- **Book now** → TB1;
- **Follow**, copy address and hours as above.

---

## Page: Public · Salon (customer books a service)

### Screen 1 · R1 · Services, team member picked (`R1-services-stylist-picked`, board *R1 · Services · Andrei picked*)

**Opens with:** `businessId` and the team member already picked (a regular customer's usual stylist).
- **⚠ gap:** how the app knows the customer's usual stylist is not decided (open question #10; proposal: the team member of their last DONE reservation).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Business name + verified (top bar) | `BusinessProfile.name`, `BusinessProfile.verified` | | |
| Team filter | **Everyone** + ACTIVE `TeamMember[]`: `TeamMember.id`, `.name`, `.avatarUrl` / `.initials` / `.avatarColor` | list | The picked person has the ring; the others are greyed. PAUSED members are not listed. |
| Category tiles | `Service.category` values + count per category for the picked member | `{ category, count }[]` | *All 2 · Hair 1 · Beard 1 · Massage 0*. A count of 0 is disabled. **⚠ gap:** each tile shows a cover image; its source (per category? per business?) and the category list are not defined. |
| Service cards | as on PS1, filtered to `Service.teamMemberIds ∋ pickedMember` | | |

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Team member filter | `TeamMember.id \| EVERYONE` | **Everyone** → F1 (the first-visit path). |
| Category filter | `Service.category \| ALL` | |

**Actions:** a card → R2 (`serviceId`, `teamMemberId`). A card without a video → R3.

### Screen 2 · R2 · Service video (regular) (`R2-video`, board *R2 · Video · Book on the side…*)

**Opens with:** `serviceId`, `teamMemberId`.

**Elements displayed:** as PA2, but for the service:
- `Video.url` and its poster;
- likes and `hasLiked`;
- business avatar, name and handle;
- caption = `Service.shortDescription`;
- the first 2 `included` items + "+8 more" (`included.length − 2`) → SV;
- views · date;
- info bar = `Service.name`, **the picked team member's name**, `durationMin`, `peoplePerBooking` ("1 person") and `price`.

**Actions:**
- **Book** (side rail) → R3;
- **Like**;
- count a view (**⚠ gap** as PA2);
- **More** is not designed.

### Screen 3 · R3 · Pick a time (regular) (`R3-pick-time`, board *R3 · Pick a time · Andrei highlighted*)

**Opens with:** `serviceId`, `teamMemberId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Title | `Service.name` | `string` | "Book Haircut" |
| Duration, price (top right) | `Service.durationMin`, `Service.price` | | |
| Who · picked person | `TeamMember.avatarUrl` / `.initials`, `TeamMember.name` + `nextFree(member, service)` | `datetime` | *Andrei 14:30*. Check badge. |
| Who · "Can replace <name>" | the other ACTIVE `TeamMember[]` in `Service.teamMemberIds`, each with `TeamMember.name`, avatar and `nextFree(member, service)` | list | *Radu 16:15*. Readable, not greyed. |
| Month label | month of the visible week | | "When · October 2026" |
| Week strip | `DayAvailability[]` (per member) for 7 days: `DayAvailability.date`, `.state(OPEN\|CLOSED\|FULLY_BOOKED)`, has a FREE slot | list | Green dot = free slots. Closed and fully booked days are struck through and disabled. |
| Time slots | `Slot[]` for the day and member: `Slot.start`, `Slot.end`, `Slot.state(FREE\|TAKEN)` | list | Grouped Morning / Afternoon / Evening. A group with no FREE slot is hidden. TAKEN = struck through. The earliest FREE slot is preselected. |
| Bottom bar | the chosen `date`, `TeamMember.name`, `Slot.start – Slot.end` (start + `Service.durationMin`) | | "Thu, 22 Oct · with Andrei / 14:30 – 15:30" |

**Inputs**
- **Who:** the picked person or a "Can replace" person (`teamMemberId`).
- Previous / next week.
- Day (`date`).
- Time slot (`start`).

**Actions**
- Load availability per member and week (**⚠ gap:** the endpoint, and how far ahead booking is allowed).
- **Confirm** → creates the booking request `{ businessId, serviceId, teamMemberId, date, from, to }` + customer details. It becomes a `Reservation` in state WAITING (see Reservations).
- **⚠ gap:** the screen after Confirm (customer details, sign-in) is not designed for services (open question #1).
- R3 has no offers yet (open question #14).

### Screen 4 · SV · Service · what is included (sheet) (`SV-included`, board *Included · full list (from “+8 more”…)*)

**Opens with:** `serviceId`.

**Elements displayed:**
- count "What's included · 10";
- subtitle `Service.name` · `durationMin` · `price`;
- the full `included[]` (flat, no groups);
- `notIncluded[]` and `notAllowed[]`.

**Actions:** close only.

### Screen 5 · F1 · Services, Everyone (`F1-services-everyone`, board *F1 · Services · Everyone*)

**Opens with:** `businessId`.

**Elements displayed:** as R1, but with **Everyone** selected:
- the category counts cover all services (*All 4 · Hair 2 · Beard 1 · Massage 1*);
- every service card is shown (*Haircut, Beard trim, Kids haircut "from 70 RON", Couples massage 2 people · 90 min*).

**Inputs:** team member (→ R1) and category filter.

**Actions:** a card → F2 (or F3 when the service has no video).

### Screen 6 · F2 · Service video (first visit) (`F2-video`, board *F2 · Video · Book on the side…*)

**Opens with:** `serviceId`.

As R2, but the info bar has **no** team member name (`name`, `durationMin`, `peoplePerBooking`, `price`).

**Actions:**
- **Book** → F3;
- "+8 more" → SV;
- **Like**.

### Screen 7 · F3 · Choose a stylist (`F3-choose-stylist`, board *F3 · Choose a stylist*)

**Opens with:** `serviceId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Service line | `Service.name`, `Service.durationMin`, `Service.price` | | |
| Anyone | the earliest `nextFree(member, service)` across `Service.teamMemberIds` | `datetime` | "First free stylist · Today 14:30" |
| Person card | `TeamMember.avatarUrl` / `.initials`, `.name`, `.role`, `.yearsExperience`, `.specialties[]`, `.rating`, `.reviewsCount`, `.languages[]` + `nextFree(member, service)` | | *Andrei · Barber · 8 years · Fades / Beard trims / Classic cuts · 4.9 (38) · RO · EN · Today 14:30*. ACTIVE members who do the service only. |
| Bottom bar | the chosen person + their next free | | "With Andrei · next free / Today 14:30" |

**Inputs:** **Anyone** or one person (single choice).

**Actions:** **Pick a time** → F4 with `serviceId` + `teamMemberId` (or `ANY`).

**⚠ gap:** who edits `role`, `yearsExperience`, `specialties` and `languages` is not designed (open question #24).

### Screen 8 · F4 · Pick a time · Any time (`F4-pick-time`, board *F4 · Pick a time · Any time*)

**Opens with:** `serviceId`, `teamMemberId`.

**Elements displayed:** everything on R3 (title, duration, price, Who + Can replace with next free, month, week strip, time slots, bottom bar), plus **Choose an offer** for the selected day:

| Element | Field | Type | Notes |
|---|---|---|---|
| **Any time** card | the bookable range that day | `time–time` | "All times · 13:00 – 20:00". **⚠ gap:** define the source (the member's working hours or the business opening hours that day). |
| **Coupon** card | `Offer` (type COUPON): `Offer.id`, `Offer.discount`, that day's `Offer.windows[]` | | "15% OFF · 14:00 – 16:00 · 18:00 – 19:00". Only offers with `appliesTo.serviceIds ∋ serviceId` on that date. |
| **Event** card | `Offer` (type EVENT): `Offer.id`, `Offer.title`, that day's `Offer.sittings[]` | | "Late cuts · 19:00 – 20:00 · 20:00 – 21:00" |

**Inputs:**
- everything on R3;
- the **offer** (`ANY` \| `offerId`, radio; the others are greyed 0.4).

**Actions:** **Confirm** → booking request `{ serviceId, teamMemberId, date, from, to, offerId?, sittingId? }`.

### Screen 9 · F4C · Pick a time · coupon chosen (`F4C-pick-time-coupon`, board *F4 · Pick a time · 15% OFF (coupon)*)

**Opens with:** `serviceId`, `teamMemberId`, `date`, `offerId` (the coupon).

As F4 with the coupon chosen:
- **times are grouped by coupon window** ("14:00 – 16:00" with the discount sticker), showing only FREE / TAKEN slots inside each window;
- the bottom bar adds the sticker (`discount`).

**Inputs:** a slot inside a window.

**Actions:** **Confirm** with `offerId`.

### Screen 10 · F4E · Pick a time · event chosen (`F4E-pick-time-event`, board *F4 · Pick a time · Late cuts (event)*)

**Opens with:** `serviceId`, `teamMemberId`, `date`, `offerId` (the event).

As F4 with the event chosen. Instead of times, the screen shows **spots**:
- "Spots · 60 min" (spot length);
- spot buttons with `from – to` and `spotsLeft` ("1 spot left"). A spot with no place left is hidden.

The bottom bar shows the event title.

**Inputs:** one spot (`sittingId`).

**Actions:** **Confirm** with `offerId` + `sittingId`.

**⚠ gap:** in `06`, `sittings.seatsLeft` is named for tables. Services use the same field as "spots left", so confirm the name.

---

## Page: Public · Coupons & Events

### Screen 1 · Coupons & Events tab (`CE1-coupons-events`, board *Coupons & Events tab · final*)

**Opens with:** `businessId` (a profile tab).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Filter tiles | count of offers per type | `{ all, events, coupons }` | *All 6 · Events 3 · Coupons 3* |
| Card media | `Offer.video.thumbnailUrl` | `url?` | Play button. **⚠ gap:** the card when an offer has no video. |
| Discount sticker | `Offer.discount` | `{ type, value, currency? }` | Coupons only: "20% OFF", "10 RON OFF". |
| Title | `Offer.title` | `string` | 1 line. |
| Time left | `Offer.endsAt` vs now | `datetime` | "Today" / "1 day" / "n days"; red at Today and 1 day. |
| Quantity left | `Offer.quantityLeft` | `int` | Ticket icon + number. |

**Inputs:** filter (All / Events / Coupons).

**Actions:**
- a card → the coupon / event video with **Get coupon / Get ticket** (not designed, open question #3; **⚠ gap:** how a customer claims a coupon or ticket, and what `quantityLeft` counts);
- the profile tab set differs from PA1 / PS1 (open question #12).

---

## Page: Public · Table booking (Food & Beverage)

### Screen 1 · Pick a date (`TB1-pick-date`, board *1 · Pick a date*)

**Opens with:** `businessId` (from PF1 **Book now**).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Business line | `BusinessProfile.name` | `string` | "Maestro Bistro · free to book". **⚠** "free to book" is fixed copy today; it would need a field if deposits come (open question #19). |
| Month label + month grid | `DayAvailability[]` (tables) for the month: `DayAvailability.date`, `.state(FREE\|FEW_LEFT\|FULL\|CLOSED)` | list | Past days are light and not tappable. Today has a ring. **No offer icons in the cells**, but each cell's accessibility label names that day's offers ("free tables, event: Live jazz night"), so the app needs to know which offers fall on each date (from the month list below). |
| Previous / next month | `RestaurantBookingSettings.bookingHorizonMonths` | `int` | Previous is disabled on the current month; next stops at the horizon. |
| "Events & coupons in <month>" list | `Offer[]` active in the month: `Offer.id`, `.type`, `.title`, its dates (`windows[].date` / `sittings[].date`) and the first start time or window | list | Row: date badge (*FRI 23*, *MON–FRI 26–30*) · title (*Wine tasting*, *20% OFF lunch*) · "Mon, 26 Oct · from 19:00" or "Mon 26 – Fri 30 Oct · 12:00 – 15:00" · type icon (event / coupon). |
| Bottom bar | the chosen date | `date` | "Your date · Mon, 26 Oct" |

**Inputs:**
- month (previous / next);
- date (a FREE or FEW_LEFT day);
- or an offer row, which picks its first day + that offer.

**Actions:** **Choose a time** → TB2 with `date` (+ `offerId` when a row was tapped). **⚠ gap:** "few left" threshold (open question #17).

### Screen 2 · Guests & time · Any time (`TB2-guests-time-any`, board *2 · Guests & time · Any time*)

**Opens with:** `businessId`, `date`, `offerId?`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Business line | `BusinessProfile.name` | | |
| Week strip | `DayAvailability[]` (tables) for 7 days from today: `.date`, `.state` | list | "Today" label; dot green FREE / amber FEW_LEFT; CLOSED / FULL struck through. |
| Guests | the chosen number + `RestaurantBookingSettings.capacity` | `int`, `int` | "Location maximum capacity · 40". The stepper max = capacity. |
| Offer · **Any time** | `RestaurantBookingSettings.services[]`: `.name`, `.from`, `.to` | list | "Lunch 12:00 – 16:00 · Dinner 17:30 – 23:00" |
| Offer · coupon | `Offer` (COUPON): `Offer.id`, `.discount`, that day's `.windows[]` | | "20% OFF · 12:00 – 14:00 · 17:30 – 18:30" |
| Offer · event | `Offer` (EVENT): `Offer.id`, `.title`, that day's `.sittings[]` (`from`, `to`) | | "Wine tasting · 19:00 – 20:30 · 21:00 – 22:30" |
| Time slots | `TimeSlot[]` per service period **for the chosen guest count**: `TimeSlot.start`, `TimeSlot.state(FREE\|TAKEN)` | list | Grouped Lunch / Dinner. TAKEN struck through. |
| Hold note | `RestaurantBookingSettings.tableHoldMin` | `int` | "Tables are held for 1 h 30 min." |
| Bottom bar | `date` · `guests` · `TimeSlot.start – (start + tableHoldMin)` | | "Mon, 26 Oct · 2 guests / 20:00 – 21:30" |

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Day | `date` | Week strip, previous / next week. |
| Guests | `int` 1…capacity | Changing it reloads the slots. With an offer, also `minGuests` / `maxGuests`. |
| Offer | `ANY \| offerId` | Radio. |
| Time | `TimeSlot.start` (or `Offer.sittings[].id`) | |

**Actions:**
- load availability for `{ date, guests }`;
- **Continue** → TB3 with `{ date, from, to, guests, offerId?, sittingId? }`.

### Screen 3 · Guests & time · coupon (`TB2C-guests-time-coupon`, board *2 · Guests & time · 20% OFF (coupon)*)

**Opens with:** `businessId`, `date`, `guests`, `offerId` (the coupon).

As TB2 with the coupon chosen:
- the slots are grouped **by coupon window** ("12:00 – 14:00" + sticker);
- the bottom bar adds the discount sticker.

**Continue** → TB3C.

### Screen 4 · Guests & time · event (`TB2E-guests-time-event`, board *2 · Guests & time · Wine tasting (event)*)

**Opens with:** `businessId`, `date`, `guests`, `offerId` (the event).

As TB2 with the event chosen. **Sittings** replace the times:
- "Sittings · 1 h 30 min" (sitting length = `to − from`);
- buttons with `from – to` and `seatsLeft` ("12 seats left"). **A sitting with `seatsLeft < guests` is hidden.**

The bottom bar shows the event title.

**Inputs:** one sitting (`sittingId`).

**Continue** → TB3E.

### Screen 5 · Your details · Any time (`TB3-details-any`, board *3 · Your details · Any time*)

**Opens with:** `{ businessId, date, from, to, guests, offerId?, sittingId? }`.

**Elements displayed:**
- business line;
- **summary**: date tile (weekday, day, month), `from – to`, guests ("2 guests"), duration (`tableHoldMin` or sitting length, "1 h 30 min");
- **Change** → back to TB2 in the same state.

**Inputs**

| Input | Field | Type | Required | Notes |
|---|---|---|---|---|
| First name | `TableBookingRequest.firstName` | `string` | yes | Two separate fields, never "Full name". |
| Last name | `TableBookingRequest.lastName` | `string` | yes | |
| Country code | `TableBookingRequest.phone.country` | ISO country (default RO, +40) | yes | Picker (the list is not designed). |
| Phone number | `TableBookingRequest.phone.number` | `string` (tel) | yes | **⚠ gap:** format and validation (open question #16). |
| Email | `TableBookingRequest.email` | `string` (email) | yes | |
| Special requests | `TableBookingRequest.specialRequests` | `string` | no | Max 1000; "0 / 1000" counter. |

**Actions**
- **Confirm reservation** → `TableBookingRequest { businessId, date, from, to, guests, offerId?, sittingId?, firstName, lastName, phone { country, number }, email, specialRequests? }`.
- The backend creates a `Reservation` in state WAITING and returns its id (needed by TB4 and My activity).
- **⚠ gaps:** error states (#16); whether the fields are pre-filled from the signed-in customer's account; whether a guest without an account can book.

### Screen 6 · Your details · coupon (`TB3C-details-coupon`, board *3 · Your details · 20% OFF*)

**Opens with:** as TB3, with `offerId` (the coupon).

As TB3, plus the **coupon strip** under the summary: `Offer.discount` + " your bill" ("20% OFF your bill") and "Valid <the `Offer.windows[]` entry that holds `from`> · applied at the restaurant".

**Inputs / Actions:** as TB3. The `TableBookingRequest` carries `offerId`.

### Screen 7 · Your details · event (`TB3E-details-event`, board *3 · Your details · Wine tasting*)

**Opens with:** as TB3, with `offerId` + `sittingId` (the event sitting).

As TB3, plus the **event strip**: `Offer.title` + "Sitting `Offer.sittings[].from – to` · `guests` seats held for you".

**Inputs / Actions:** as TB3. The `TableBookingRequest` carries `offerId` + `sittingId`.

### Screen 8 · Booked (`TB4-booked`, board *4 · Reserved*)

**Opens with:** the `reservationId` returned by TB3.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Title | — | — | Fixed copy (*Succesfully Booked*). **⚠** Now that every booking is a request, this should say "Request sent" while WAITING (open questions #15, #36). |
| "<Business> is expecting you." | `BusinessProfile.name` | `string` | |
| Date · time | `Reservation.date`, `Reservation.from – Reservation.to` | | "Mon, 26 Oct · 20:00 – 21:30" |
| Guests | `Reservation.people` | `int` | |
| Address | `BusinessProfile.address.line` | `string` | Copy button. |
| Call the restaurant | `BusinessProfile.phone` | `string` | Opens the dialer. |

**Actions**
- **Add to calendar** → a calendar event on the phone (no backend). **⚠** My activity (MA5) dropped Add to calendar because the feature is not built; confirm it for TB4 too.
- **Done** / **X** → PF1.

---

## Page: Host · Team

### Screen 1 · Team (`TM1-team-list`, board *1 · Team (list, one Invite button)*)

**Opens with:** `businessId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Subtitle | `BusinessProfile.name` + number of team members | `string`, `int` | "Maestro Host · 4 people" (invites not counted). |
| Section counts | count of `TeamMember` per `TeamMember.status` + count of PENDING `TeamInvite` | `int` | "Active · 3", "Paused · 1", "Invites · 1". An empty section is hidden. |
| Member avatar + status dot | `TeamMember.avatarUrl` / `.initials` / `.avatarColor`, `TeamMember.status` | | Green dot ACTIVE, amber dot PAUSED. |
| Name | `TeamMember.name` | `string` | |
| Owner chip | `TeamMember.isOwner` | `bool` | |
| "@username · Role" | `TeamMember.username`, `TeamMember.role` | `string` | The signed-in person's own row says "@username · You". **⚠ gap:** link `TeamMember.userId` ↔ signed-in user. |
| Status word | `TeamMember.status` | `enum(ACTIVE\|PAUSED)` | |
| "N services" | number of `Service` whose `Service.teamMemberIds` holds this member | `int` | |
| Invite row | `TeamInvite.id`, `TeamInvite.username`, `TeamInvite.state = PENDING`, `TeamInvite.invitedAt` | | "Invited · waiting for an answer". Newest first. |

**Inputs:** none.

**Actions**
- A person → TM3 with `teamMemberId`.
- **Invite to team** → TM2.
- **Cancel** on an invite → `TeamInvite.state = CANCELLED`.

### Screen 2 · Invite to team (sheet) (`TM2-invite`, board *2 · Invite to team (sheet)*)

**Opens with:** `businessId` (over TM1).

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Username search | `string` | Opens with the keyboard; clear (X). **⚠ gap:** minimum characters, debounce, privacy of usernames (open question #25). |

**Elements displayed:**
- result count ("2 people");
- each result: avatar (`avatarUrl` / initial), `name`, `@username`, and its invite state:
  - can invite → **Invite**;
  - already has a PENDING invite → "✓ Invited".
- People already in the team are not listed (proposal).

**Actions**
- Search users by username → `{ userId, name, username, avatarUrl?, inviteState }[]`.
- **Invite** → create `TeamInvite { businessId, userId / username }`, state PENDING. It appears under **Invites** on TM1.
- **⚠ gap:** how the invited person receives and accepts the invite (open question #23).

### Screen 3 · Team member (`TM3-team-member`, board *3 · Team member (status, services)*)

**Opens with:** `teamMemberId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Avatar + status dot | `TeamMember.avatarUrl` / `.initials` / `.avatarColor`, `TeamMember.status` | | |
| Name, username | `TeamMember.name`, `TeamMember.username` | `string` | |
| Status chip | `TeamMember.status` | `enum` | |
| "Joined Mar 2025" | `TeamMember.joinedAt` | `datetime` | |
| "Customers can book <name>" | `TeamMember.name` (first name) | `string` | Inside the Active card. |
| Services · N of M | every `Service` of the business: `Service.id`, `.name`, `.durationMin`, `.price` (+ `.price.from`), and whether `Service.teamMemberIds` holds this member | list | "Haircut · 60 min · 120 RON" ✓ |

**Inputs**

| Input | Type | Notes |
|---|---|---|
| Status | `enum(ACTIVE\|PAUSED)` | Radio cards. The owner's screen hides Paused (proposal). |
| Services checklist | `Service.id[]` this member does | The same data as "Who does it" on HS3 / HS4. |

**Actions**
- **Save changes** → update `TeamMember.status` and the member's services (adds / removes this member in each `Service.teamMemberIds`).
- **Remove from team** → remove the member (hidden for the owner). The confirmation is not designed.
- **⚠ gap:** what happens to their future reservations (open question #22).
- **⚠ gap:** role / experience / specialties / languages are not edited here (#24).

---

## Page: Host · Customers & rewards

### Screen 1 · Customers · People tab (`CR1-customers`, board *1 · Customers · People tab (pick people)*)

**Opens with:** `businessId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Subtitle | `BusinessProfile.name` + number of `Customer` | `string`, `int` | "Maestro Host · 24 people" |
| Group tiles | count of `Customer` per `Customer.groups`: `ALL`, `REGULAR`, `NEW`, `AWAY` | `int` | *All 24 · Regulars 8 · New 10 · Away 6* |
| Group line | the selected group + its rule + selected count | | "Regulars · 3+ visits · 2 selected". **⚠ gap:** group rules (proposal: Regulars 3+ visits, New 1 visit, Away no visit in 60 days; #26). |
| Customer row | `Customer.id`, `.avatarUrl` / `.initials` / `.avatarColor`, `.name`, `.visitsCount`, `.lastVisitAt` | | "6 visits · last 12 Oct". No phone or email in the list. |
| Unused reward chip | `Customer.unusedRewardIds` → that `Reward.discount` (from this business) | | "10 RON OFF · not used" |

**Inputs**
- Group filter.
- Select / unselect people (`customerIds[]`).
- **Select all** (everyone in the group).

**Actions:** **Send reward to N people** (disabled when nobody is selected) → CR2 with `customerIds[]` + group.

**⚠ gaps:** list order (the sample looks like newest visit first), paging for big lists, search.

### Screen 2 · New reward (`CR2-new-reward`, board *2 · New reward*)

**Opens with:** `customerIds[]` (+ the group they were picked from).

**Elements displayed:**
- **recipients:** the first 2 avatars, the names ("Elena and Mihai"), and "2 people · Regulars"; **Change** → CR1;
- **live ticket preview:**
  - discount value + unit;
  - business name;
  - message;
  - "Single use · until <date>" (`validUntil` = today + Valid for, computed in the app).

**Inputs**

| Input | Field | Type | Required | Notes |
|---|---|---|---|---|
| Discount type | `Reward.discount.type` | `enum(PERCENT\|AMOUNT)` | yes | % / RON toggle. |
| Discount value | `Reward.discount.value` | `number` | yes | Presets 10 · 15 · 20 · 25 % or **Other**. **⚠ gap:** the custom value input and the RON presets (#30). |
| Message | `Reward.title` | `string` | **⚠** | Max **40** characters, "22 / 40" counter. The host's own text, not translated. |
| Valid for | `validFor` (the backend sets `Reward.validUntil`) | `enum(1_WEEK\|2_WEEKS\|3_WEEKS\|1_MONTH)` | yes | "Until <date>" next to it. |

**Actions:** **Send to N people** → create `Reward { businessId, title, discount, validFor, source: MANUAL, customerIds[], audienceGroup? }` (the backend sets `sentAt` and `validUntil`). The backend creates one grant per person (NOT_USED). The app goes to CR3.

**⚠ gaps:**
- the group label shown later ("Regulars" on CR10) has no field on `Reward`;
- the reward's scope (any service? combined with a coupon? #27).

### Screen 3 · Reward sent (`CR3-reward-sent`, board *3 · Reward sent*)

**Opens with:** the created `rewardId`.

**Elements displayed:**
- the recipients' names ("Elena and Mihai");
- `validUntil`;
- the ticket (discount, business name, title, `validUntil`).

**Actions:**
- **See rewards** → CR4;
- **Done** / **X** → CR1.

### Screen 4 · Customers · Rewards tab (`CR4-rewards-tab`, board *4 · Customers · Rewards tab (automatic + sent)*)

**Opens with:** `businessId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Subtitle and tabs | as CR1 | | "Maestro Host · 24 people", People · Rewards |
| "Automatic · N on" | count of `RewardRule.on = true` | `int` | |
| Rule card | `RewardRule.id`, `.title`, `.dayOfMonth`, `.on`, `.discount`, `.validForDays`, `.visits { count, mode }` | | "Come back soon · Every month on the 15th · 10% OFF · valid 5 days · Exactly 1 visit in the month before" |
| Rule status | `RewardRule.nextSendAt`, `RewardRule.matchingNow` (people) | `date`, `int` | "Next: Sun, 15 Nov · 10 people". Computed by the backend. |
| Idea to start | template: `title`, `discount`, `visits { count, mode }` | | "VIP thank you · 20 RON OFF · 5 or more visits in the month before". **⚠ gap:** ideas fixed in the app, or sent by the backend? |
| Sent · this month | `Reward[]` with `sentAt` this month: `Reward.id`, `.discount`, `.title`, `.source`, count of `grants` USED / all `grants`, `.validUntil` ("ended" when past) | list | "Come back soon · Auto · Used by 4 of 9 · ended 20 Oct"; "Thanks for coming back · By you · Used by 3 of 8 · until 22 Nov" |

**Inputs:** the **on / off switch** on each rule.

**Actions**
- Switch → update `RewardRule.on`. Off stops future sends; rewards already sent stay valid.
- A rule → CR9.
- A sent reward → CR10.
- **New automatic reward** → CR5.
- **Add** on an idea → CR5 pre-filled.
- **⚠ gap:** earlier months' rewards (only "this month" is designed).

### Screen 5 · New automatic reward · When (`CR5-auto-when`, board *5 · New automatic reward · When*)

**Opens with:** nothing (new draft), or a template from "Idea to start".

**Elements displayed:**
- the month of the visible week ("First send · November 2026");
- the week strip (future dates);
- "Then every month on the **15th**";
- **Next sends:** the first 3 send dates. The rule: a month without that day sends on its last day. Computed in the app or by the backend.

**Inputs:** the first send date (`firstSendAt`); `dayOfMonth` is taken from it.

**Actions:** **Next** → CR6. Nothing is saved until CR8.

**⚠ gaps:** the earliest allowed first send (today or tomorrow); the send time of day (#33).

### Screen 6 · New automatic reward · Who (`CR6-auto-who`, board *6 · New automatic reward · Who*)

**Opens with:** the draft rule from CR5 (`firstSendAt`, `dayOfMonth`).

**Elements displayed:**
- the counting period for the first send ("15 Oct – 14 Nov"; computed);
- **live match preview:** the number of people who match today + up to 3 avatars + names ("10 people match today · Cristina, Dan, Ioana and 7 more").

**Inputs**

| Input | Field | Type | Notes |
|---|---|---|---|
| Visits in that month · mode | `RewardRule.visits.mode` | `enum(EXACTLY\|AT_LEAST)` | "Exactly" / "Or more" |
| Visits in that month · number | `RewardRule.visits.count` | `int 1–5` | |
| A person can get it | `RewardRule.repeat` | `enum(ONCE\|EVERY_MONTH)` | |
| Skip people with an unused reward | `RewardRule.skipIfUnused` | `bool` | Switch, on by default. |

**Actions:**
- the live preview → backend `{ visits, repeat, skipIfUnused, firstSendAt }` → `{ count, people: [{ name, avatarUrl / initials }] (first 3) }`;
- **Next** → CR7.

### Screen 7 · New automatic reward · Reward (`CR7-auto-reward`, board *7 · New automatic reward · Reward*)

**Opens with:** the draft rule from CR5–CR6.

**Elements displayed:** the live ticket (discount, business name, message, "Single use · valid 5 days").

**Inputs**

| Input | Field | Type | Notes |
|---|---|---|---|
| Message | `RewardRule.title` | `string` | Max 40, "14 / 40" counter. |
| Discount type | `RewardRule.discount.type` | `enum(PERCENT\|AMOUNT)` | |
| Discount value | `RewardRule.discount.value` | `number` | Presets 5 · 10 · 15 · 20 % or **Other** (⚠ #30). |
| Valid for | `RewardRule.validForDays` | `enum(3\|5\|7\|30)` | "3 days · 5 days · 1 week · 1 month", counted from the day it is sent. |

**Actions:** **Next** → CR8.

### Screen 8 · New automatic reward · Check and turn on (`CR8-auto-check`, board *8 · New automatic reward · Check and turn on*)

**Opens with:** the full draft rule from CR5–CR7.

**Elements displayed:**
- the rule as one sentence (built in the app from the draft);
- "First send: Sun, 15 Nov · 10 people" (match preview);
- **When / Who / Reward** summaries;
- the ticket.

**Actions**
- **Change** → the step.
- **Turn on** → create `RewardRule { title, discount, validForDays, dayOfMonth, firstSendAt, visits { count, mode }, repeat, skipIfUnused, on: true }` → CR4.
- **Backend job:** run each rule on its day (see §A).

### Screen 9 · Edit automatic reward (`CR9-auto-edit`, board *9 · Edit automatic reward*)

**Opens with:** `ruleId`.

**Elements displayed**

| Element | Field | Type |
|---|---|---|
| Title | `RewardRule.title` | `string` |
| State line | `RewardRule.on`, `.nextSendAt`, `.matchingNow` | "On · next send Sun, 15 Nov · 10 people" |
| Stats | `RewardRule.stats.timesSent`, `.stats.people`, `.stats.used` | `int` ×3 |
| Ticket preview | `RewardRule.discount`, `BusinessProfile.name`, `RewardRule.title`, `RewardRule.validForDays` | |
| Rule rows | When (`RewardRule.dayOfMonth`), Who (`.visits`, `.repeat`, `.skipIfUnused`), Discount (`.discount`), Valid for (`.validForDays`), Message (`.title`) | |

**Inputs:**
- the on / off switch;
- each rule row opens that step to change it (CR5–CR7 in edit mode).

**Actions**
- **Save changes** → update the `RewardRule`. Changes apply from the next send.
- Delete (trash) → delete the rule (confirmation not designed; #31).

### Screen 10 · Reward details (`CR10-reward-details`, board *10 · Reward details (who used it)*)

**Opens with:** `rewardId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Ticket | `Reward.discount`, `BusinessProfile.name`, `Reward.title`, `Reward.validUntil`, group label | | "Single use · until Sun, 22 Nov · Regulars". **⚠ gap:** the group label is not on `Reward`. |
| Stats | count of `Reward.grants`: all, USED, NOT_USED | `int` ×3 | "8 Sent · 3 Used · 5 Not used yet" |
| People · N | each `Reward.grants[]`: `Customer.avatarUrl` / `.initials`, `Customer.name`, `grant.state`, `grant.usedAt?` | list | Sorted **used first**. "Used · 14 Oct" / "Not used yet". The first 5, then "Show all 8". |

**Actions**
- **Show all** → the full list (not designed).
- **Stop reward** → NOT_USED grants become STOPPED (`stoppedAt`). The confirmation is not designed.

---

## Page: Host · Reservations

### Screen 1 · Reservations tab (`RV1-reservations`, board *1 · Reservations tab…*)

**Opens with:** `businessId` (the calendar tab of HP).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Tab badge | count of `Reservation` with `state = WAITING` | `int` | Hidden at 0. |
| Requests banner | count of WAITING, the oldest `Reservation.requestedAt` | `int`, `datetime` | "2 requests to answer · Oldest: 2 h ago". Hidden at 0. |
| Day headings | today and tomorrow (business time zone) | `date` | "Today · Fri, 23 Oct" |
| Day counts | count of `Reservation` that day; count with `state = DONE` | `int` | "3 reservations · 1 done" |
| Reservation row | `Reservation.id`, `.from`, `.to`, `Customer.name`, `.state`, `.what`, `.people` | | State bar + chip: CONFIRMED green, DONE grey. |

**Actions**
- Banner → RV2.
- A confirmed row → RV5.
- A past row → RV6 (`reservationId`).

**⚠ gap:** how NO_SHOW looks in the list, and later days (#40, #41).

### Screen 2 · Requests to answer (`RV2-requests`, board *2 · Requests to answer…*)

**Opens with:** `businessId`.

**Elements displayed** (WAITING, oldest first)

| Element | Field | Type | Notes |
|---|---|---|---|
| Count | count of `Reservation` with `state = WAITING` | `int` | "Requests · 2" |
| Date tile | `Reservation.date` | `date` | Weekday, day, month. |
| Time | `Reservation.from – Reservation.to` | `time` | |
| Requested ago | `Reservation.requestedAt` | `datetime` | "2 h ago", "20 min ago" |
| Customer | `Customer.name` | `string` | |
| What · people | `Reservation.what`, `Reservation.people` | | "Haircut · 1 person", "Table · 6 people" |
| Offer sticker | `Reservation.offer` (coupon `discount`, or event `title`) | | "15% OFF" |
| Visits chip | `Customer.visitsCount` (with this business) | `int` | "6 visits", or **New customer** at 0 DONE visits. |
| Note | `Reservation.specialRequests` | `string?` | 1 line here. |

**Actions:**
- **Accept** → `state = CONFIRMED` (`answeredAt`), the customer is told → RV5;
- **Decline** → RV4;
- the card head → RV3.

**Backend job:** a WAITING request past `answerBy` (requestedAt + 24 h) → DECLINED with `declineReason = NO_ANSWER`, and the customer is told.

### Screen 3 · Reservation request (`RV3-request`, board *3 · Reservation request…*)

**Opens with:** `reservationId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Summary | `Reservation.date`, `.from – .to`, `.state`, `.what`, `.people`, `.durationMin?`, `.price?`, `TeamMember.name?` (via `.teamMemberId`) | | Each fact shows only when it exists ("With Andrei"). |
| Offer strip | coupon: `Reservation.offer.discount`, `.offer.pays`, `.price` · event: `Offer.title`, the sitting `from – to` | | "15% OFF coupon · Pays 102 RON instead of 120 RON" |
| Customer | `Customer.avatarUrl` / `.initials` / `.avatarColor`, `.name`, `.visitsCount`, `.lastVisitAt` | | "6 visits · last 12 Oct" |
| Phone | `Customer.phone` | `string` | **Call** → dialer. |
| Email | `Customer.email` | `string` | **Copy**. |
| Special requests | `Reservation.specialRequests` | `string?` | Full text. |
| Requested at | `Reservation.requestedAt` | `datetime` | "Requested in the app today at 12:31." |

**Actions:**
- **Accept** → CONFIRMED;
- **Decline** → RV4.

### Screen 4 · Decline (reason sheet) (`RV4-decline`, board *4 · Decline (reason sheet)*)

**Opens with:** `reservationId` (over RV3).

**Elements displayed:** customer first name, `date`, `from`, `what` ("Mon, 26 Oct · 14:30 · Haircut").

**Inputs**

| Input | Field | Type | Notes |
|---|---|---|---|
| Reason | `Reservation.declineReason` | `enum(FULLY_BOOKED\|CLOSED_THAT_DAY)` | Required. Fully booked is pre-selected. **No message field.** |

**Actions:**
- **Decline request** → `state = DECLINED`, `declineReason`, `answeredAt`; the customer is told the reason;
- close → nothing is sent.

### Screen 5 · Accepted / confirmed reservation (`RV5-confirmed`, board *5 · Accepted / confirmed reservation*)

**Opens with:** `reservationId`.

**Elements displayed:**
- "Accepted. <first name> got a confirmation." — only right after Accept;
- the RV3 summary with **Confirmed**;
- the offer strip;
- the customer with phone and email;
- special requests.

**Actions**
- **Cancel reservation** → `state = CANCELLED`, `cancelledBy = BUSINESS`, `cancelledAt`; the customer gets a message.
- **⚠ gap:** the confirmation dialog, and whether a cancel reason is asked (#39).
- Call / Copy email.

### Screen 6 · After the visit (`RV6-after-visit`, board *6 · After the visit: did they come?*)

**Opens with:** `reservationId` (a past CONFIRMED / DONE reservation).

**Elements displayed:**
- the summary: date ("Today"), `from – to`, `what`, `people`, `durationMin`, `price`;
- the customer: avatar, name, `visitsCount`, `lastVisitAt`;
- "Did <first name> come?".

**Inputs:** attendance — **Yes, done** (`DONE`) or **No-show** (`NO_SHOW`).

**Actions:**
- update `state` + `checkedAt`;
- **backend job:** CONFIRMED reservations still unanswered at the start of the day after `date` → DONE;
- only DONE counts in `visitsCount` / `lastVisitAt`, which feed CR1 groups and the reward rules.

---

## Page: Customer · My activity

### Screen 1 · Upcoming tab (`MA1-upcoming`, board *1 · Upcoming tab*)

**Opens with:** the signed-in customer (`userId`).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Tab counts | `MyActivity.upcoming.length`; `MyActivity.rewards.ready.length` | `int` ×2 | "Upcoming · 2", "Rewards · 2" (hidden at 0). History has no count. |
| Day headings | `Reservation.date` | `date` | "Tomorrow · Sat, 24 Oct", "Mon, 26 Oct" |
| Reservation row | `Reservation.id`, `.from`, `.to`, `.place.name`, `.state(WAITING\|CONFIRMED)`, `.what`, `.people`, `.offer?` | | Bar + chip: Confirmed green / Waiting amber. Offer sticker "15% OFF". |

**Actions:**
- a WAITING row → MA4;
- a CONFIRMED row → MA5 (`reservationId`);
- tabs → MA2 / MA3.

**⚠ gap:** empty state (#43).

### Screen 2 · Rewards tab (`MA2-rewards`, board *2 · Rewards tab (ready to use, used or ended)*)

**Opens with:** the signed-in customer (`userId`). Same top bar and tabs as MA1.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Ready to use · N | `MyActivity.rewards.ready[]` (grants NOT_USED, not past `validUntil`) | list | **Ending soonest first.** |
| Ticket (ready) | `RewardGrantView.rewardId`, `.discount`, `.place.name`, `.title`, `.validUntil` | | "10 RON OFF · Maestro Bistro · See you again soon · Single use · until Wed, 28 Oct" |
| Used or ended · N | `MyActivity.rewards.usedOrEnded[]` (USED / ENDED / STOPPED) | list | Newest first. |
| Ticket (faded) | `RewardGrantView.discount`, `.place.name`, `.title`, `.state`, `.usedAt` or `.validUntil` | | "Used · 12 Oct", "Ended · 30 Sep" |

**Actions:** a ready ticket → MA6 (`rewardId` / grant id).

### Screen 3 · History tab (`MA3-history`, board *3 · History tab (rate, book again)*)

**Opens with:** the signed-in customer (`userId`). Same top bar and tabs as MA1.

**Elements displayed** (grouped by month, newest first)

| Element | Field | Type | Notes |
|---|---|---|---|
| Month heading | month of `Reservation.date` | | "October" |
| Date, time | `Reservation.date`, `Reservation.from` | | "20 Oct · 19:00" |
| Place | `Reservation.place.name` | `string` | |
| What · people (DONE) | `Reservation.what`, `Reservation.people` | | |
| State + reason (DECLINED / CANCELLED) | `Reservation.state`, `.declineReason` / `.cancelledBy` | `enum` | "Declined · Fully booked", "Cancelled · By you" |
| Your rating | `Reservation.myRating` | `int 1–5` | "★ 5" when already rated. |

**Inputs / Actions**
- **Rate** (DONE, not rated) → the app's existing review flow for this `reservationId` (#44). Afterwards `myRating` is set.
- **Book again** (DECLINED / CANCELLED) → the place's booking start (`place.businessId`).

### Screen 4 · Reservation · waiting (`MA4-reservation-waiting`, board *4 · Reservation · waiting for an answer*)

**Opens with:** `reservationId`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Banner | `Reservation.place.name` | `string` | "Waiting for Maestro Host · They answer within 24 hours." |
| Summary | `Reservation.date`, `.from – .to`, `.state`, `.what`, `.people`, `.durationMin?`, `.price?`, `TeamMember.name?` | | |
| Coupon strip | `Reservation.offer.discount`, `.offer.pays`, `.price` | | "15% OFF coupon · You pay 102 RON instead of 120 RON" (or the event strip). |
| Place card | `Reservation.place.avatarUrl` (or initial + `.avatarColor`), `.place.name`, `.place.type`, `.place.address`, `.place.phone`, `.place.businessId` | | Head → the place's profile. |
| Your special requests | `Reservation.specialRequests` | `string?` | Hidden when empty. |

**Actions**
- **Cancel request** → `state = CANCELLED`, `cancelledBy = CUSTOMER`; the place is told. The confirmation is not designed (#46).
- Copy address, Call.

### Screen 5 · Reservation · confirmed (`MA5-reservation-confirmed`, board *5 · Reservation · confirmed*)

**Opens with:** `reservationId` (state CONFIRMED).

As MA4 (same fields) with:
- the green banner "Confirmed · <place> is expecting you.";
- the dark date tile and the **Confirmed** chip;
- *Table · 2 people · 1 h 30 min* (no price, no team member).

**No Add to calendar.**

**Actions:**
- **Cancel reservation** → CANCELLED (`cancelledBy = CUSTOMER`);
- Copy address, Call, the place card → its profile.

### Screen 6 · Reward (`MA6-reward`, board *6 · Reward (how to use it)*)

**Opens with:** `rewardId` (this customer's grant).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Ticket | `RewardGrantView.discount`, `.place.name`, `.title`, `.validUntil` | | |
| From | `RewardGrantView.place.name`, `.place.type`, `.place.city` | | "From Maestro Host · Barber & salon · Brașov" |
| Days left | `RewardGrantView.validUntil` − today | `int` | "30 days left · Until Sun, 22 Nov" (red at Today / 1 day). |
| Single use | `RewardGrantView.place.name` | | "For one booking at Maestro Host" |

**Actions:**
- **Book with <place>** → the place's booking start;
- **⚠ gap:** picking the reward at the last booking step is not designed (#45). The booking request will need a `rewardGrantId?`.

## Page: Public · Search

Opens from the **Search** tab of the bottom navigation, for anyone (signed in or not ⚠ #54). One request shape serves every tab: `SearchRequest { q, tab, dealType?, cursor? }` → `SearchPage { blocks[], nextCursor }` (see `docs/06-data-model.md` → *Search*). **No result counts** are shown anywhere, so the backend does not need to send totals.

### Screen 1 · Before you type (`SR1-start`, board *1 · Before you type: recent searches*)

**Opens with:** nothing (the Search tab); the signed-in `userId` for recent searches.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Recent list | `RecentSearch.query`, `.searchedAt` | list | This person's, **newest first**. *maestro · haircut brașov · wine tasting*. Hidden when empty. **⚠ gap:** stored on the device or the account, how many (proposal 10), signed-out people (#54). |

**Inputs**

| Input | Type | Rules |
|---|---|---|
| Search field | `q: string` | Trimmed. **⚠ gap:** max length (proposal 100) and when the request is sent (proposal: from 2 characters, 300 ms after the last key; #50). |

**Actions:**
- typing → search `{q, tab: ALL}` → SR3, or SR2 when nothing matches;
- a recent row → the same search with that `query`;
- **X** on a row → delete that recent search `{query}`;
- **Clear all** → delete all recent searches;
- a search is **saved to recents** when its results are shown (A19).

### Screen 2 · No results (`SR2-no-results`, board *2 · No results*)

**Opens with:** `q`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Query echo | `SearchRequest.q` | `string` | "No results for “sushi brașov”", as typed. |
| When shown | `SearchPage.blocks` is empty on the first page of tab ALL | | No tabs on this screen. |

**Actions:** clear **X** → SR1; editing the query → a new search.

### Screen 3 · All (`SR3-all`, board *3 · All (one mixed feed: places, videos, deals; keeps loading)*)

**Opens with:** `q` (tab ALL).

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Feed | `SearchPage.blocks[]` | `SearchBlock[]` | **In the order received** (the backend ranks, best match first; #51). `PLACE` = one row; `VIDEOS` / `DEALS` = one row of 1–2 cards. |
| Place row | `PlaceResult.businessId`, `.name`, `.verified`, `.category`, `.subcategoryLabel`, `.city`, `.avatarUrl?` | | Initial on the place's colour when there is no logo (B28). "Barber & salon · Brașov". No icon. |
| Place status line | `PlaceResult.openingHours` + now (A4), or `.checkIn` / `.checkOut` (ACCOMMODATION) | | "**Open now** · Closes 20:00", "**Closes soon** · Until 22:30", "**Closed** · Opens 09:00", "**Check-in 14:00** · Check-out 11:00". |
| Video card | `VideoResult.itemId`, `.itemType`, `.title`, `.businessName`, `.price{amount, currency, from}`, `.priceUnit?`, `.people`, `.durationMin?`, `.thumbnailUrl` | | *Haircut · Maestro Host · 120 RON · 1 · 60 min*; *Double Room · 250 RON / night · 2 · Details* (rooms have no duration). |
| Deal card | `DealResult.offerId`, `.type`, `.title`, `.discount?`, `.businessName`, `.endsAt`, `.quantityLeft`, `.thumbnailUrl?` | | Sticker "15% OFF" (coupons only); time left from `endsAt` (red at Today / 1 day); `ticket` + quantity left. |
| Loading more | `SearchPage.nextCursor` | `string \| null` | Shown while the next page loads; `null` = last page (#53). |

**Inputs:** tabs (All · Videos · Places · Deals; the query stays); the query.

**Actions:**
- near the end of the list → next page `{q, tab: ALL, cursor: nextCursor}`;
- a place → its profile by `category`: SERVICES → PS1, FOOD_BEVERAGE → PF1, ACCOMMODATION → PA1 (`businessId`);
- a video → SERVICE → F2 (`serviceId` = `itemId`, no team member), ROOM → PA2 (`roomId` = `itemId`);
- a deal → the booking with the deal picked: SERVICES coupon → F4C, event → F4E; FOOD_BEVERAGE coupon → TB2C, event → TB2E (`businessId`, `offerId`, date = `firstDate`). **⚠ gap:** F4C / F4E also need a `serviceId`; which one when the offer applies to several services (B30).

### Screen 4 · Videos tab (`SR4-videos`, board *4 · Videos tab*)

**Opens with:** `q` (tab VIDEOS).

**Elements displayed:** `SearchPage.blocks[]` of `VIDEOS` (rows of 2) — the video card fields as SR3. Loading more from `nextCursor`.

**Actions:** next page `{q, tab: VIDEOS, cursor}`; a video → F2 / PA2 as SR3. **⚠ gap:** empty tab while All has results (#56).

### Screen 5 · Places tab (`SR5-places`, board *5 · Places tab*)

**Opens with:** `q` (tab PLACES).

**Elements displayed:** `SearchPage.blocks[]` of `PLACE` — the place row and status line fields as SR3, all rows in one card. Loading more from `nextCursor`.

**Actions:** next page `{q, tab: PLACES, cursor}`; a place → PS1 / PF1 / PA1 as SR3. **⚠ gap:** location / distance is not designed (#52).

### Screen 6 · Deals tab (`SR6-deals`, board *6 · Deals tab (coupons and events)*)

**Opens with:** `q` (tab DEALS), `dealType: ALL`.

**Elements displayed**

| Element | Field | Type | Notes |
|---|---|---|---|
| Filter tiles | — | | All · Events · Coupons, **no counts**. |
| Deal cards | `SearchPage.blocks[]` of `DEALS` (rows of 2): the deal card fields as SR3 | | **Ending soonest first** (`endsAt` ascending). Only bookable deals: not ended, `quantityLeft > 0` (A19). |

**Inputs**

| Input | Type | Rules |
|---|---|---|
| Filter | `dealType: enum(ALL\|EVENT\|COUPON)` | One selected; default ALL. Changing it reloads the list from the first page. |

**Actions:** next page `{q, tab: DEALS, dealType, cursor}`; a deal → F4C / F4E / TB2C / TB2E as SR3. **⚠ gap:** deals at accommodation places (Call only) — proposal: not returned (#59).

---

## A. Rules and jobs the screens rely on (backend logic, not one screen)

| # | Rule / job | What the screens expect | Screens |
|---|---|---|---|
| A1 | **Service availability** | Per team member and day: `OPEN \| CLOSED \| FULLY_BOOKED` and `Slot { start, state FREE\|TAKEN }`, with the slot length = service duration. Also `nextFree(member, service)` and "Anyone" = the earliest free across the service's members. Week by week. | R3, F3, F4, F4C, F4E |
| A2 | **Table availability** | Per day `FREE \| FEW_LEFT \| FULL \| CLOSED` (month and week). Per service period, `TimeSlot { start, FREE\|TAKEN }` **for a given guest count**. `capacity`, `tableHoldMin`, `bookingHorizonMonths`, `services[]`. | TB1, TB2 |
| A3 | **Offers per day** | For a date (and service, for salons): coupons with that day's `windows[]`; events with `sittings[] { id, from, to, seatsLeft }`. A month list for TB1. `quantityLeft` and `endsAt` for CE1. | TB1, TB2*, TB3*, F4*, CE1 |
| A4 | **Opening status** | From `openingHours` + now in the business time zone: open / closes soon (< 60 min, proposal) / closed + the next opening time. Can be computed in the app if the hours are sent. | PS1, PF1, SR3, SR5 |
| A5 | **Reservation lifecycle** | Every booking creates a `Reservation` in WAITING with `answerBy = requestedAt + 24 h`. Accept → CONFIRMED; Decline + reason → DECLINED; the customer can cancel (WAITING or CONFIRMED); the host can cancel CONFIRMED. | RV1–RV6, MA1–MA5, TB3, F4, R3 |
| A6 | **Auto-decline job** | WAITING past `answerBy` → DECLINED with `NO_ANSWER`, and the customer is told. | RV2, MA3 |
| A7 | **Auto-done job** | CONFIRMED still unanswered at the start of the day after `date` → DONE. | RV6 |
| A8 | **Visits** | `visitsCount` and `lastVisitAt` per customer per business count **DONE only**. They feed the "N visits" chips, the CR1 groups and the reward rules. | RV2, RV3, RV6, CR1, CR6 |
| A9 | **Customer groups** | REGULAR / NEW / AWAY with counts (rules to confirm, see B). | CR1 |
| A10 | **Manual reward** | Create one `Reward` with one grant per chosen customer (NOT_USED). `validUntil` = send date + length. | CR2, CR3 |
| A11 | **Reward rule scheduler** | On `dayOfMonth` every month (the last day for shorter months) from `firstSendAt`, at a fixed time (proposal 10:00, business time zone): <br>1. count each customer's DONE visits from the same day last month to the day before; <br>2. match `visits { count, mode }`; <br>3. apply `repeat` (ONCE = never again for this rule) and `skipIfUnused`; <br>4. create one `Reward` (source = rule) with grants; <br>5. update `stats`. | CR4, CR8, CR9 |
| A12 | **Rule preview** | For a draft or saved rule: people matching **now** (count + the first 3 names / avatars) and `nextSendAt`. | CR4, CR6, CR8, CR9 |
| A13 | **Grant end and stop** | A grant past `validUntil` → ENDED; **Stop reward** → NOT_USED grants become STOPPED. A grant is USED when a booking uses it (`usedAt`, `bookingId`). | CR4, CR10, MA2 |
| A14 | **Notifications** | To the customer: accepted / declined (with the reason) / cancelled / auto-declined; the reward received. To the host: a new request; the customer cancelled. **Channels and design are not decided** (open question #37). | RV*, MA*, CR* |
| A15 | **Media** | Video upload → `url`, `thumbnailUrl`, `durationSec`. Views counting; likes per viewer. | HS2, HR2, PA2, R2, F2 |
| A16 | **Social** | Follow / unfollow, posts / followers / following counts, rating + reviews count, `myRating` per DONE reservation. | HP, PA1, PS1, PF1, MA3 |
| A17 | **Team** | Search users by username; invites PENDING → ACCEPTED / DECLINED / CANCELLED; PAUSED members are excluded from R1 / F1 filters, F3, "Can replace" and "Anyone" (their existing reservations stay). The salon boards still show Maria, who is Paused on TM1: that sample data is older than the Team page, so follow the rule. | TM1–TM3, R1, F1, F3, R3, F4 |
| A18 | **My activity** | Across all businesses for the signed-in customer: upcoming (WAITING + CONFIRMED, from now on), history (DONE, DECLINED, CANCELLED; newest first), reward grants (ready ending soonest first; used / ended newest first). | MA1–MA6 |
| A19 | **Search** | One query over place names, types and cities, video titles and deal titles (diacritics and small typos: #60). **Ranks** the results (best match first, #51) and returns **blocks**: a place = one block; videos and deals in blocks of 1–2 (one grid row). ALL mixes the three types; each tab returns only its own. **Cursor paging** (`nextCursor`, null on the last page; page size #53). Deals: only bookable ones (not past `endsAt`, `quantityLeft > 0`, at a business that takes bookings in the app), `endsAt` ascending in the Deals tab; `firstDate` = the first day the deal applies. **Recent searches**: saved when results are shown, newest first, delete one / all (#54). No totals are needed. | SR1–SR6 |

---

## B. Gaps to decide (data the designs need that is missing or undecided)

| # | Gap | Screens | Proposal / note |
|---|---|---|---|
| B1 | User roles on a business (owner, team member, customer) and the link `TeamMember.userId` ↔ signed-in user ("You") | all host screens, TM1 | Add `userId` on `TeamMember` and a role per business. |
| B2 | Business time zone | RV1, A6, A7, A11, opening status | Add `BusinessProfile.timeZone`. |
| B3 | `stats.following` | HP | Add to `stats`. |
| B4 | Viewer state: `isFollowing`, `hasLiked` (per video) | PA1, PS1, PF1, PA2, R2, F2 | Return with the profile / video. |
| B5 | Video upload: endpoint, formats, max length / size, thumbnail; view counting rule | HS2, HR2, PA2, R2, F2 | |
| B6 | Service form limits: name and description max length, description required?, duration steps and max, people max, at least one team member? | HS3, HS4 | Name 40, description 120 (proposals). |
| B7 | `Service.category` (and category tile images) and `Service.price.from`: used publicly, but not set on HS3 / HS4 | R1, F1, PS1, HS3 | Add both to the service form. |
| B8 | Room included items need a `group` (Bedroom, Bathroom, …); HR3 adds plain chips | HR3, HR4, PA3 | A group picker or an amenity checklist. |
| B9 | Deleting a service or room: what happens to future reservations and linked offers | HS4, HR4 | |
| B10 | Services list order | HS1, PS1, R1, F1 | Creation order, or manual reorder. |
| B11 | A customer's usual stylist (regular path) | R1 | The team member of their last DONE reservation. |
| B12 | Service booking after **Confirm** (customer details, sign-in) | R3, F4 | Reuse TB3 (open question #1). |
| B13 | Availability endpoints and booking horizon for services | R3, F4 | |
| B14 | F4 "Any time · All times 13:00 – 20:00": the source of the range | F4 | The member's working hours that day. |
| B15 | Event spots for services: `seatsLeft` vs `spotsLeft` naming | F4E | One field, two labels. |
| B16 | CE1: card without video; how a coupon / ticket is claimed; what `quantityLeft` counts | CE1 | Open question #3. |
| B17 | "Few left" threshold; "free to book" vs deposits | TB1, TB2 | ≤ 20 % (open question #17); #19. |
| B18 | TB3 form: validation, phone format, country list, prefill from the account, booking without an account | TB3* | Open question #16. |
| B19 | TB4 title while the reservation is WAITING ("Request sent") and Add to calendar (dropped on MA5) | TB4 | Open questions #15, #36. |
| B20 | Username search rules and privacy; how an invite is received and accepted | TM2 | Open questions #23, #25. |
| B21 | Remove from team: future reservations; who edits role / experience / specialties / languages | TM3, F3 | Open questions #22, #24. |
| B22 | Customer group rules, list order, paging, search | CR1 | Regulars 3+, New 1, Away no visit in 60 days (#26). |
| B23 | Reward: custom "Other" value and RON presets; scope (which services, combine with a coupon); the group label shown on CR10 (not on `Reward`) | CR2, CR7, CR10 | #27, #30; add `Reward.audienceGroup?`. |
| B24 | "Idea to start" templates: fixed in the app or from the backend | CR4 | |
| B25 | Rule send time, earliest first send, rewards history beyond this month | CR4, CR5 | 10:00 business time (#33). |
| B26 | Reservation: no-show display, later days on RV1, cancel confirmation and reason, auto-accept, the answer deadline for requests that start soon, holding the time while WAITING | RV1–RV6 | Open questions #34–#42. |
| B27 | My activity: empty states, the Rate target (existing review flow), picking a reward at booking (`rewardGrantId` on the booking request), cancel rules, no-show visibility, the entry point | MA1–MA6 | Open questions #43–#49. |
| B28 | Avatar fallback colour: stored or derived | all people / places | Derive in the app from the id. |
| B29 | Search: when the request is sent, ranking, location / distance, page size and the end of a list, where recent searches are kept (and how many, signed-out people), one tab empty, matching (diacritics, typos), deals at accommodation places, query max length | SR1–SR6 | Open questions #50–#60; query max 100 (proposal). |
| B30 | A deal opens F4C / F4E, which also need a **service**: an offer's `appliesTo.serviceIds` can list several | SR3, SR6 | Open question #61. Proposal: `DealResult.serviceIds`; with one service open on it, with several open the services list (F1) showing only those. |

---

## C. Entity and field index (what each object must carry, and where it is used)

| Entity | Fields used by the screens | Used on |
|---|---|---|
| **BusinessProfile** | `id`, `handle`, `name`, `verified`, `category`, `subcategoryLabel?`, `avatarUrl?`, `stats { posts, followers, following⚠, rating?, reviewsCount }`, `phone`, `address { line, city, lat, lng }`, `openingHours`, `checkIn?`, `checkOut?`, `priceLevel`, `timeZone⚠`, currency | HP, PA1, PS1, PF1, PA2, R1–R3, F1–F4, TB1–TB4, MA4–MA6, SR3, SR5 |
| **Viewer state** | `isFollowing⚠`, `hasLiked⚠` (per video), signed-in `userId` + role⚠ | PA1, PS1, PF1, PA2, R2, F2, TM1 |
| **Video** | `id`, `url`, `thumbnailUrl`, `durationSec`, `views`, `publishedAt`, `likes` | HS1–HS4, HR1–HR4, PA1, PA2, PS1, R1, R2, F1, F2, CE1, SR3, SR4, SR6 |
| **Service** | `id`, `name`, `shortDescription`, `category⚠ form`, `price { amount, currency, unit VISIT\|PERSON, from⚠ form }`, `durationMin`, `peoplePerBooking`, `included[]`, `notIncluded[]`, `notAllowed[]`, `teamMemberIds[]`, `video?`; categories list for R1 / F1 tiles: `{ category, count, imageUrl⚠ }` | HS1–HS4, PS1, R1–R3, SV, F1–F4, TM3, RV*, MA*, SR3, SR4 |
| **Room** | `id`, `name`, `shortDescription`, `pricePerNight`, `guestsMax`, `included[] { group⚠, item }`, `notIncluded[]`, `notAllowed[]`, `video?` | HR1–HR4, PA1–PA3, SR3, SR4 |
| **TeamMember** | `id`, `userId⚠`, `name`, `initials`, `avatarUrl?`, `avatarColor`, `username`, `status ACTIVE\|PAUSED`, `isOwner`, `joinedAt`, `role`, `yearsExperience`, `specialties[]`, `languages[]`, `rating`, `reviewsCount`; derived: services count, `nextFree` | HS3, HS4, TM1–TM3, PS1, R1–R3, F1–F4, RV3, RV5, MA4 |
| **TeamInvite** | `id`, `username` / `userId`, `invitedAt`, `state PENDING\|ACCEPTED\|DECLINED\|CANCELLED` | TM1, TM2 |
| **User search result** | `userId`, `name`, `username`, `avatarUrl?`, invite state | TM2 |
| **Service availability** | `DayAvailability { date, state OPEN\|CLOSED\|FULLY_BOOKED }`, `Slot { start, end, state FREE\|TAKEN }`, `nextFree(member, service)`, "Any time" range⚠ | R3, F3, F4* |
| **RestaurantBookingSettings** | `capacity`, `bookingHorizonMonths`, `tableHoldMin`, `slotStepMin`, `services[] { name, from, to }` | TB1, TB2*, TB3* |
| **Table availability** | `DayAvailability { date, state FREE\|FEW_LEFT\|FULL\|CLOSED }`, `TimeSlot { start, state }` per guest count | TB1, TB2* |
| **Offer** (coupon / event) | `id`, `type`, `title`, `discount?`, `startsAt?`, `endsAt`, `quantityLeft`, `video?`, `appliesTo`, `windows[] { date, from, to }`, `sittings[] { id, date, from, to, seatsLeft }`, `minGuests?`, `maxGuests?` | CE1, TB1, TB2*, TB3*, F4*, RV2, RV3, MA1, MA4, SR3, SR6 |
| **TableBookingRequest** (table booking) | `businessId`, `date`, `from`, `to`, `guests`, `offerId?`, `sittingId?`, `firstName`, `lastName`, `phone { country, number }`, `email`, `specialRequests?` (max 1000), `rewardGrantId?⚠` | TB3* → creates Reservation |
| **ServiceBookingRequest** (service booking) | `businessId`, `serviceId`, `teamMemberId \| ANY`, `date`, `from`, `to`, `offerId?`, `sittingId?`, customer details⚠, `rewardGrantId?⚠` | R3, F4* → creates Reservation |
| **Reservation** | `id`, `businessId`, `customerId`, `kind SERVICE\|TABLE\|EVENT`, `what`, `people`, `date`, `from`, `to`, `durationMin?`, `price?`, `teamMemberId?` (+ name), `offer? { COUPON: discount, pays } \| { EVENT: title, sittingId }`, `specialRequests?`, `requestedAt`, `answerBy`, `state WAITING\|CONFIRMED\|DECLINED\|CANCELLED\|DONE\|NO_SHOW`, `declineReason? FULLY_BOOKED\|CLOSED_THAT_DAY\|NO_ANSWER`, `answeredAt?`, `cancelledAt?`, `cancelledBy? CUSTOMER\|BUSINESS`, `checkedAt?`, `myRating?`, `place { businessId, name, type, city, address, phone, avatarUrl?, avatarColor }` | RV1–RV6, MA1–MA5, TB4, HP badge |
| **Customer** (host side) | `id`, `name`, `initials`, `avatarUrl?`, `avatarColor`, `visitsCount` (DONE), `lastVisitAt`, `groups[]`, `unusedRewardIds[]` (→ `Reward.discount`, this business only), `phone`, `email` (RV3 / RV5 only) | CR1, CR2, CR3, CR6, CR10, RV1–RV6 |
| **Reward** | `id`, `businessId`, `title` (max 40), `discount`, `validFor` (input: 1_WEEK \| 2_WEEKS \| 3_WEEKS \| 1_MONTH), `sentAt`, `validUntil`, `source MANUAL \| { ruleId }`, `audienceGroup?⚠`, `grants[] { customerId, state NOT_USED\|USED\|ENDED\|STOPPED, usedAt?, bookingId? }`, `stoppedAt?`; derived: used / total | CR2–CR4, CR10, MA2, MA6 |
| **RewardRule** | `id`, `on`, `title`, `dayOfMonth`, `firstSendAt`, `visits { count 1–5, mode EXACTLY\|AT_LEAST }`, `repeat ONCE\|EVERY_MONTH`, `skipIfUnused`, `discount`, `validForDays 3\|5\|7\|30`, `stats { timesSent, people, used }`; derived: `nextSendAt`, `matchingNow` (count + the first 3 people) | CR4–CR9 |
| **MyActivity** (customer) | `upcoming[]` and `history[]` (Reservation with `place`), `rewards.ready[]` / `rewards.usedOrEnded[]` (`RewardGrantView { rewardId, place, discount, title, validUntil, state, usedAt? }`), tab counts | MA1–MA6 |
| **Search** | `SearchRequest { q, tab ALL\|VIDEOS\|PLACES\|DEALS, dealType? ALL\|EVENT\|COUPON, cursor? }` → `SearchPage { blocks[], nextCursor }`; `SearchBlock { type PLACE\|VIDEOS\|DEALS, place \| items[] }`; `PlaceResult { businessId, name, verified, category, subcategoryLabel, city, avatarUrl?, openingHours?, checkIn?, checkOut? }`; `VideoResult { itemId, itemType SERVICE\|ROOM, title, businessId, businessName, price { amount, currency, from? }, priceUnit?, people, durationMin?, thumbnailUrl }`; `DealResult { offerId, type, title, discount?, businessId, businessName, businessCategory, endsAt, quantityLeft, thumbnailUrl?, firstDate, serviceIds⚠ }` | SR1–SR6 |
| **RecentSearch** | `query`, `searchedAt` (this person's, newest first; storage⚠) | SR1 |

*Screen ids with `*` cover all their states (for example, `TB2*` = TB2, TB2C, TB2E).*
