# 07 · Small / medium / large phones, iOS and Android

Every screen has a reference at three sizes (points/dp):

| Size | Reference | Typical devices |
|---|---|---|
| Small | 360 × 640 | iPhone SE (375 × 667), compact Android |
| Medium | 390 × 844 | iPhone 13/14/15, most Android phones |
| Large | 430 × 932 | iPhone Pro Max / Plus, large Android |

Do **not** build three fixed layouts. Build one flexible layout that produces these three references.

## What stays constant
- Screen side padding 16, grid gaps, radii, icon sizes, text sizes (except the small-screen compactions below).
- Touch targets ≥ 44.
- Column counts: 2 columns for service/room cards (public and host), 3 for coupon tickets and the video picker, 4 for time slots, 7 for the week strip, 4 for Quick Actions.

## What scales with width
Card heights keep their aspect ratio with the column width:

| Card | Ratio (height ÷ column width) | Small | Medium | Large |
|---|---|---|---|---|
| Public video card | 1.676 | 265 | 290 | 324 |
| Host video card | 1.769 | 279 | 306 | 341 |
| Coupon ticket | 1.807 (stub fixed 50, media = rest) | 188 | 206 | 229 |
| Deal card, 2 per row (search) | 1.676, as the public video card (stub fixed 76, media = rest) | 265 | 290 | 324 |
| Video picker tile | 1.337 | 159 | 172 | 190 |

Column width = (screen width − 2×16 − gaps) ÷ columns. Inside cards, keep top content anchored to the top, pills/panels anchored to the bottom, and the play button centred on the media area.

## Small-screen compactions (screen width < 375)
- Card bottom pills (Details / guests / time): font 12, gap 6, padding `0 8 0 10`.
- Price pill: font 12, gap 4.
- Coupon facts row: font 10.5, gap 5.
- Chip rows may wrap to a second line (e.g. "+8 more" on the video).
- Booking bottom bars (TB1, TB2, F4): button horizontal padding 16 (table) / 18 (F4 Confirm) so time + offer sticker + button stay on one row.
- Guests card (TB2): gap 6 and value width 26, so "Location maximum capacity · 40" stays on one line.
- Offer card subtitles may wrap to 2 lines (the card grows).

## Height
- Lists, videos and calendars show one screen; content below scrolls (see small references: the calendar's Evening row and the Included sheet continue under the fold).
- Bottom action bars (Book/Confirm/Save) and the host nav **stay pinned**.
- Bottom sheets: height = content, **max = screen height − 64**, then scroll inside.
- Long forms (HS3/HS4/HR3/HR4) scroll; their reference boards are drawn taller to show the full form.
- Team screens (TM1, TM3) scroll under their pinned bottom button on small phones; the TM2 sheet follows the sheet rule above.
- Customers & rewards screens (CR1, CR2, CR4, CR6–CR10) scroll under their pinned bottom button on small phones; CR3 and CR5 fit.
- Reservations: on small phones RV1 scrolls under the nav, RV3 under its pinned Decline / Accept bar, RV5 scrolls; RV2 (two request cards), the RV4 sheet and RV6 fit. Names and items ellipsize before a status chip or "N people" would move.
- My activity: on small phones MA2, MA3 and MA4 scroll under the tabs / top bar; MA1, MA5 and MA6 fit. On MA3 the decline / cancel reason wraps under its chip instead of being cut.
- Search: on small phones SR3–SR6 scroll under the tabs (the nav stays pinned); SR1 and SR2 fit. Place names and status lines ellipsize; tabs, field and tiles keep their size. SR3's reference board is drawn taller (1731 / 1831 / 1967) to show one page of the feed.
- Admin dashboard (web): references at 1440 × 900; works from 1280 wide; side columns keep their width, the middle (video, tables, card grids) flexes. Not a phone layout.
- Account: AU1–AU5 fit without scrolling at every size; the AU4 dialog keeps its three wheels and both buttons at 360; on AU1 Privacy & data sits right above the nav.
- New post: NP2 / NP3 are placed from the edges; the caption panel is screen width − 92 and grows upward with the text. At the caps (30 / 100) the title stays on one line and the description on three at 360, 390 and 430. The NP4 and EP2 sheets fit at every size; on EP1 Delete video and Save share the bottom row at 360.
- Booking steps (TB1–TB3, F4 with offers) scroll under their pinned bottom bar at every size. On small phones the end of the content is under the fold in the references; that is expected.

## Safe areas
- Replace the fixed 24 px bottom padding of bottom bars with the real bottom safe-area inset (home indicator / Android gesture bar), minimum 16.
- On video screens the X and mute buttons sit below the status bar (top inset + 0–8). The side rail and info bar keep their distance from the bottom inset.
- Draw video and dark screens edge-to-edge behind the status bar with light status-bar icons; light screens use dark status-bar icons.

## iOS and Android
- Fonts: **Roboto** on Android, **system font (SF Pro)** on iOS, same sizes and weights.
- Keep the designed look on both platforms (do not swap in Material or Cupertino default components). Native touch feedback (ripple / highlight) and haptics on selection are welcome.
- **Glass panel**: iOS `UIVisualEffectView` / SwiftUI `.ultraThinMaterial` + the dark tint; Android 12+ `RenderEffect.createBlurEffect` (Compose `Modifier.blur` on the background layer) + tint; older Android: tint only (`rgba(22,20,28,.55)`), still readable.
- Bottom sheet: native modal sheet behaviour (drag to dismiss, tap-outside to dismiss) with the designed visuals.
- Dialer: `tel:` intent/URL for Call. Copy address: system clipboard + short toast/snackbar "Address copied".
- Dynamic Type / font scale: allow up to ~130 % without overlap — titles clamp, pills keep one line, rows grow.
- Maps: OpenStreetMap tiles (e.g. MapLibre / osmdroid / MapKit with OSM tiles). Show the "© OpenStreetMap" attribution. No routing.
