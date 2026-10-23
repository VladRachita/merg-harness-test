# 10 · Not designed yet (do not invent — ask)

| # | Topic | Where it starts | Current decision / note |
|---|---|---|---|
| 1 | After **Confirm** on the salon calendar (confirmation, sign-in / guest details) | R3, F4 | Still out of scope. Table booking has its own details + confirmation (TB3, TB4); reusing them for services is a proposal. |
| 2 | **Book now** target on the Services profile | PS1 | F&B is designed (→ TB1). Services: proposal → services list. Not designed. |
| 3 | Coupon / event **video** with **Get coupon / Get ticket** | CE1 card tap | Proposed: same video overlay as R2 with the action on the side rail. Not designed. |
| 4 | Host editor for the **full Included list** ("+N more" on host forms) and an **amenity checklist** for rooms | HS3, HR3 | Proposal: grouped checklist of common amenities. Not designed. |
| 5 | **Delete** confirmation | HS4, HR4 trash | Use the platform's standard destructive confirmation. |
| 6 | Weekly **opening hours** sheet (tap on hours cell) | About card | Not designed; show a simple 7-row list until designed. |
| 7 | **Check-in / check-out** data for accommodation | About card | Needs host fields; fallback to opening hours if missing. |
| 8 | Price level labels for 1 and 4 | About card | "Budget" / "Luxury" proposed. |
| 9 | "Closes soon" threshold | About card | 60 minutes proposed. |
| 10 | Returning signed-in customer auto-"regular" with last stylist | R1 | Proposed improvement, not designed. |
| 11 | Dark mode | all | Not designed. |
| 12 | Coupons & Events tab set on profiles (3 vs 4 tabs) | CE1 vs PA1/PS1 | CE1 mock shows Videos · Coupons · Reviews; profiles show 4 tabs with Rooms/Services. Use the profile's tab set. |
| 13 | Tablets / landscape | all | Not designed. Phones portrait only. |
| 14 | **R3 offers** | R3 | F4 now has Choose an offer; R3 does not yet. Expected to mirror F4 — confirm before building. |
| 15 | **TB4 per offer** and its title copy | TB4 | TB4 shows the Any time summary for every path. Proposal: add the TB3 coupon/event strip. Canvas title reads "Succesfully Booked" — confirm final copy (spelling: "Successfully booked"). |
| 16 | Form validation and errors | TB3 | Required: first name, last name, phone, email (only Special requests is optional). Error states, phone formats and the country list are not designed. |
| 17 | "Few left" threshold and booking horizon | TB1, TB2 | Proposal: few left ≤ 20 % of capacity for that day; horizon 6 months (per restaurant setting). |
| 18 | Host tools for offers in booking | host | Creating coupon windows, event sittings/spots and the restaurant capacity is not designed. |
| 19 | Paid events / deposits | TB2E, TB3E | Designs say "free to book". Ticket prices or deposits are not designed. |
| 20 | **Pause** rules | TM1, TM3 | Proposal used in the designs: hidden from booking (R1, F3, "Can replace", "Anyone"), existing bookings stay. Confirm. |
| 21 | Owner rules | TM1, TM3 | Proposal: the owner is always Active, cannot be paused or removed; their TM3 hides Paused and Remove. Confirm. |
| 22 | Remove from team | TM3 | Confirmation dialog and what happens to their future bookings are not designed. |
| 23 | Invitee side | TM2 | How an invite is received and accepted (notification, accept / decline screen) is not designed. |
| 24 | Stylist profile fields | TM3, F3 | Role, experience, specialties and languages (shown on F3 "Choose a stylist") are not edited on TM3. Who edits them (the member on their own profile?) is not designed. |
| 25 | Search results | TM2 | Proposal: people already in the team are not listed. Privacy / discoverability of usernames to confirm. |
| 26 | Customer groups | CR1 | Proposal: Regulars = 3+ visits, New = 1 visit, Away = no visit in 60 days (all time). Confirm, and whether hosts can change them. |
| 27 | Reward scope | CR2, CR7 | Any service, or only some? Can it be combined with a coupon/offer in the same booking? Not decided. |
| 28 | Several rewards per person | CR1 | Proposal: a person can hold several, one is used per booking. |
| 29 | Customer details | CR1 | Phone, email and visit history moved out of the list; a customer details screen is not designed. |
| 30 | "Other" discount and RON presets | CR2, CR7 | The custom value input and the RON chip values (proposal: 10 · 20 · 30 · 50 RON) are not designed. |
| 31 | Confirmations | CR9, CR10 | Delete rule and Stop reward confirmations are not designed (use the platform's destructive dialog). |
| 32 | Customer side | — | How a customer is told about a new reward (push, "My activity") is not designed here. |
| 33 | Send time | CR5 | Time of day for automatic sends is not shown. Proposal: 10:00 in the business's time zone. |
| 34 | **Auto-accept** | RV1–RV3 | The designs make every booking a request. Whether a business can accept all bookings automatically (a setting) is not designed. |
| 35 | Answer deadline | RV2 | 24 hours, then declined automatically (designed copy). For requests whose time starts sooner than 24 h away, proposal: the deadline is 1 hour before the start. Confirm. |
| 36 | **Customer side of a request** | TB3/TB4, F4, R3 | With requests, the customer's last step should say the booking is waiting for the business ("Request sent"), then accepted / declined (with the reason) / cancelled. TB4 currently says booked. Not designed; ties to #1 and #15. |
| 37 | Notifications | RV1, RV5 | Push to the host for a new request, and to the customer for accepted / declined / cancelled / auto-declined, are not designed. |
| 38 | Time held while waiting | RV2 | Proposal: a waiting request holds its time (not offered to others) until it is answered or declined automatically. Confirm. |
| 39 | Cancel reservation | RV5 | Confirmation dialog, whether a reason is asked, and the customer message are not designed (use the platform's destructive dialog). |
| 40 | **No-show** | RV6, RV1 | Not counted as a visit. The "No-show" chip on RV1 (proposal: `status.danger` text on `bg.soft`) and any consequence (repeated no-shows, deposits) are not designed. |
| 41 | Days after tomorrow, empty states | RV1 | The tab shows Today and Tomorrow only (no calendar, by decision). Where later reservations are seen (proposal: the Quick Actions **Calendar** / **Bookings** tiles) and the empty states ("No reservations today", no banner) are not designed. |
| 42 | Who / which table | RV3 | Changing the team member on a request, or assigning a restaurant table, is not designed. "With <name>" is read-only. |

