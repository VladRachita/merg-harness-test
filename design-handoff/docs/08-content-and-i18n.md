# 08 · Content, copy and languages

## Languages
EN (default), RO, DE, IT, ES, FR. The designs were checked against the longest strings (e.g. "Habitación familiar", "Kinderhaarschnitt", "Massaggio di coppia").
Translations that already exist in the designs are in [`../strings.json`](../strings.json):
- `accommodation_rooms_list` — PA1 rooms grid (count, room names, "/ night", Details, Play video, guests).
- `salon_services_list` — R1/F1 (Team, Everyone, categories, service names, "from", Details, minutes, people).

All other copy is English in the designs and must go through the app's localisation system (no hard-coded strings).

## Overflow rules
| Element | Rule |
|---|---|
| Public/host card title | max 2 lines, ellipsis |
| Coupon ticket title | 1 line, ellipsis (tell hosts to keep titles short) |
| Post title / description (NP2, NP3) | hard caps 30 / 100 characters with counters; never ellipsized in the editor |
| Address pill | 1 line, ellipsis |
| Pills, chips, prices, times, counts | never wrap, never truncate; reduce label words instead (icons carry meaning) |
| Video caption | max 2 lines |
| Info bar on video | title 1 line, facts 1 line |
| Category tile label | 1 line, ellipsis |

## Copy used in the designs (EN)
- Profile CTAs: **Follow**, **Call**, **Book now**.
- Video: **Book**, **Call**, "+N more", "N views · <date>".
- Calendar: **Who**, "Can replace <name>", "When · <Month YYYY>", Morning / Afternoon / Evening, **Confirm**, "<Day, dd Mon> · with <name>".
- First visit: **Choose a stylist**, **Anyone**, "First free stylist", **Pick a time**, "With <name> · next free".
- What's included sheet: "What's included · N", **Not included**, **Not allowed**.
- Host: "Everything here is shown on your video", **Included · N**, **Not included**, **Not allowed**, **Add**, **Who does it**, "/ visit", "/ night", **Save service**, **Save room**, **Save changes**, **New service**, **New room**, "Start with a video", "No video yet", **Add a video**, "Pick a clip that shows the service / room", **Skip**, **Next**, "Recents".
- About: "Open now · Closes 23:59", "Closes soon · Until 22:30", "Closed · Opens 09:00", "Check-in 14:00 / Check-out 11:00", "Price level", Budget / Moderate / Expensive / Luxury, "© OpenStreetMap".
- Coupons: "All", "Events", "Coupons", "20% OFF", "10 RON OFF", "Today", "1 day", "n days".
- Customers & rewards: full list in [`13-customers-rewards.md`](13-customers-rewards.md) §10. The reward message is the host's own text (max 40 characters). Duration chips are built so "1 săptămână / 2 săptămâni / 1 lună" fit.
- Reservations: full list in [`14-reservations.md`](14-reservations.md) §10 ("N requests to answer", "Oldest: 2 h ago", **Answer**, "Waiting for you", "Confirmed", "Done", **Accept**, **Decline**, "Fully booked", "Closed that day", **Decline request**, **Cancel reservation**, "Did <name> come?", **No-show**, **Yes, done**). Copy is category-neutral ("what · N people", never "stylist" or "haircut" in fixed text).
- My activity: full list in [`15-my-activity.md`](15-my-activity.md) §10 ("My activity", "Upcoming · N", "Rewards · N", "History", "Waiting", "Confirmed", "Declined", "Cancelled", "Ready to use · N", "Used or ended · N", **Rate**, **Book again**, "Waiting for <place>", **Cancel request**, **Book with <place>**).
- Search: full list in [`16-search.md`](16-search.md) §11 ("Search places, videos, coupons…", "Recent", **Clear all**, "No results for “<query>”", "Check the spelling or try fewer words.", "All", "Videos", "Places", "Deals", "Events", "Coupons", "Tap a deal to book with it: the coupon or event is already picked.", "Loading more"). No result counts in any label.
- Admin dashboard: full list in [`19-admin.md`](19-admin.md) §9; every page name exactly as in §1 there. The admin is English-only unless decided otherwise.
- Account: full list in [`18-account.md`](18-account.md) §8 ("Your profile", "Sign in to post videos, book and keep your rewards.", **Create account**, **Sign in**, "Privacy & data", "Continue with email", **Continue**, "Available", "Date of birth", **Change** / **Pick date**, "Day", "Month", "Year", **Cancel**, **Confirm**, "You need to be 16 or older to create an account."). Months as names, localised.
- New post: full list in [`17-new-post.md`](17-new-post.md) §9 ("New post", "Pick one clip · up to 100 MB", **Change video**, "Add a title", "Add a description", "n / 30", "n / 100", "Tag", "Add a title to publish", "This is how people see it", **Publish**, "Tag a place", "Search places", "From your visits", **Done**, "Edit post", **Save**, **Delete video**, "Delete this video?", "The video and everything linked to it are deleted for everyone. You can't undo this."). The person's title and description are not translated.
- **Customers' gender is unknown**: never "he / she / his / her" in copy about a customer. Use their first name or "they" ("We let them know so they can book another time.").
- Team: full list in [`12-team.md`](12-team.md) §5 ("Team", "Invite to team", "Active · N", "Paused · N", "Invites · N", "Owner", "Invited · waiting for an answer", "Team member", "Remove from team", …).
- Table booking and offers: full list in [`11-table-booking.md`](11-table-booking.md) §9 ("Book a table", "Choose a time", "Choose an offer", "Any time", "Location maximum capacity · N", "Sittings", "N seats left", "Your details", "First name", "Last name", "Confirm reservation", …).
- Currency in samples: RON. Format prices with the user's locale.
