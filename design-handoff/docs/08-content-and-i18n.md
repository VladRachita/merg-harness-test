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
- Currency in samples: RON. Format prices with the user's locale.
