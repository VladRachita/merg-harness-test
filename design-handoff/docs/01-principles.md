# 01 · Principles and rules

These rules were agreed with the product owner screen by screen. Every implementation decision must respect them.

## 1. "Stupid simple"
- Every action and fact must be understood **at a glance from its icon**. Icons always come with a short label or a number next to them; the icon carries the meaning, the label confirms it.
- One idea per element. No decorative text, no marketing copy in the UI.
- Prefer **numbers + icons** over words: `👥 2` (guests), `⏱ 60 min` (duration), `💵 120 RON` (price), `⏳ 1 day` (time left), `🎟 5` (how many left). (Shown here with emoji for readability only — in the app these are line icons, see §6.)

## 2. One way forward
- On any screen there is **one primary action** and it is always in the same place for that screen type:
  - Video screens: the action button on the **side rail** (`Book` for services, `Call` for accommodation).
  - Calendar: `Confirm` in the bottom bar.
  - Forms: `Save` in the bottom bar.
  - Public profile header: the slate CTA next to Follow (`Call` for accommodation, `Book now` for services and food & beverage).
- **Do not add alternative paths.** Info bars on videos are *not* tappable, have no arrow. Cards have one tap target per intent.

## 3. Video first
- Services and rooms are presented by a vertical video. The description of a service/room lives **on the video** (caption, included chips, info bar), not on a separate details page.
- Hosts create a service or room by **picking a video first** (no recording, no editing in-app), then filling the details that will be shown on that video.

## 4. Text on media is always readable
Thumbnails/videos can be white, black or anything in between. Every text on media uses one of:
- **Scrim** gradients (top and/or bottom) + `text-shadow: 0 1px 3px rgba(0,0,0,0.45)` for white text.
- **White pills** with dark text (price pill, info pill, Details pill).
- **Frosted glass panel** (dark tint 55 % + blur) on host cards.
- **Dark translucent chips** (`rgba(0,0,0,0.45)`) for chips on the video.
Test every card with a near-white and a near-black thumbnail.

## 5. Selection and "greyed out"
- A selected person/filter gets a **2px ring** (`0 0 0 2px bg, 0 0 0 4px ink`) and bold label.
- When one option is picked, the other options are **greyed out at 40 % opacity but stay tappable** (switching is always possible).
- Exception — R3/F4 calendar "Who": the people who can replace the picked stylist must stay **clearly readable** (grey avatar, full-opacity name and next free time) under the label "Can replace <name>".

## 6. Icons
- Outline icons on a 24 grid, 1.8 stroke (2–2.4 for 12–16 px icons), round caps and joins, single colour. Filled only: play, phone, star (rating), more-dots.
- Use **Lucide** names (see components doc) or the SVG paths in the HTML. **Never emoji.**

## 7. Touch and accessibility
- Every tappable element has a **≥ 44 × 44** hit area, even when its visible shape is smaller (e.g. 32 px circle edit button, 28 px "+8 more" chip).
- Every icon-only button has an accessibility label (see `aria-label` in the HTML: "Close video", "Mute", "Edit Double Room", …).
- Greyed (0.4) items stay focusable and announce their state (selected / not selected).
- Text colours on light surfaces meet 4.5:1 (secondary `#5F5B68` on `#F7F5FB` passes).

## 8. Translation-safe layout
The app ships in **EN, RO, DE, IT, ES, FR** (see `strings.json`). Layouts must survive the longest language:
- Card titles: **2-line clamp** with ellipsis (public video cards, host cards); **1-line ellipsis** on coupon tickets.
- Pills and chips: `nowrap`; prefer icon + number so the pill does not grow with language.
- Never truncate prices, times or counts.

## 9. Business types
The same building blocks serve three business types. Differences are data-driven:

| | Services (salon, barber…) | Accommodation (rooms, hotels…) | Food & Beverage (restaurants, bars…) |
|---|---|---|---|
| Profile CTA | Book now | Call | Book now |
| Content tab | Services | Rooms | — (About only) |
| Item price | per visit | per night | — |
| Item facts | people · duration | guests | — |
| Video side-rail action | Book (calendar icon) | Call (phone icon) | — |
| About hours cell | Open now / Closes soon / Closed | Check-in · Check-out | Open now / Closes soon / Closed |
| Booking | stylist + time (calendar) | phone call only | not designed yet |

## 10. Do not
- Do not add Not-designed screens (confirmation after Confirm, login, F&B booking, coupon video) — see `10-open-questions.md`.
- Do not use Material/Cupertino default component styling where it changes the look (ripple/haptics are fine). Build the visuals as designed on both platforms.
- Do not show a Directions button on the map (no routing). Address is **copy-to-clipboard**.
