# 09 · Acceptance checklist

Use this for every screen before calling it done.

## How to compare
1. Run the screen on simulators/emulators close to the three references: iPhone SE (3rd gen), iPhone 15, iPhone 15 Pro Max; a 360-wide, a ~393-wide and a ~430-wide Android device.
2. Take a screenshot and place it next to `screenshots/<size>/<id>.png` (references are 2×). Overlay at 50 % opacity to check alignment.
3. For exact numbers open `screens/<size>/<id>.html` in a browser and inspect the element.
4. Use realistic content extremes: a near-white and a near-black thumbnail, the longest translation (DE/ES), a 2-line title, a price like "1 250 RON", 0 and 99+ counts.

## Global checks
- [ ] Colours, radii, spacing and type sizes come from the theme (tokens), not literals.
- [ ] All icons are line icons from the agreed set; no emoji anywhere.
- [ ] Every tappable element has a ≥ 44 hit area and an accessibility label.
- [ ] Text over media is readable on white **and** black thumbnails.
- [ ] Greyed options are 0.4, still tappable; selected options have the ring + bold label.
- [ ] One primary action per screen, in the designed place; info bars are not tappable.
- [ ] Bottom bars and nav respect the safe-area inset; content scrolls under the fold, bars stay pinned.
- [ ] Small (360) layout has no clipped pills or overlapping text; large (430) cards keep their proportions.
- [ ] Works in light mode as designed (dark mode not designed — do not invent one).
- [ ] Copy is localised; long languages respect the overflow rules.

## Screen-specific checks
- [ ] **HS1/HR1**: glass panel readable on light thumbnail; edit icon in the card corner never touches the title or "/ night"; New tile dashed.
- [ ] **HS2/HR2**: single selection; Next enabled only with a selection (Skip always).
- [ ] **HS3/HS4/HR3/HR4**: price unit "/ visit ▾" (services) vs fixed "/ night" (rooms); rooms have no Duration and no Who does it; delete only on edit screens; "+N more" when Included is long.
- [ ] **PA1/PS1/PF1**: CTA = Call (accommodation) / Book now (services, F&B); address pill copies; OSM attribution visible; F&B has no tabs/grid.
- [ ] **PA2/R2/F2**: X top-left; Book/Call on the side rail; 2 included chips + white "+N more" opens the sheet; info bar shows the right facts (stylist name only when picked).
- [ ] **PA3/SV**: sheet max height = screen − 64, scrolls; three sections with the right icons/colours; dismiss by X, handle, dim tap.
- [ ] **R1/F1**: Team filter selection switches path; stylist view shows only that stylist's services; empty category disabled.
- [ ] **R3/F4**: picked stylist highlighted with check badge; "Can replace" group readable; earliest free slot preselected; fully booked/closed days disabled; empty part of day hidden.
- [ ] **F3**: Anyone first; one selection; bottom bar updates with name + next free.
- [ ] **CE1**: discount sticker only on coupons (percent or amount); time left red at Today/1 day; tear line at media bottom; 1-line titles.
- [ ] **HP**: 4-column Quick Actions grid with labels; brand tone off by default.
- [ ] **F4/F4C/F4E**: Choose an offer sits between When and the times; switching offers changes only times, note and bottom bar; coupon windows carry the green sticker; event spots show "N spots left".
- [ ] **TB1**: availability tints only (no icons in cells); today ring; past/closed/full not tappable; list rows show date badge + offer badge; previous month disabled on the current month.
- [ ] **TB2**: When strip identical to F4; guests 1…capacity; offers greyed 0.4 when not chosen; sittings with fewer seats than guests hidden; Continue goes to the TB3 state of the chosen offer.
- [ ] **TB3**: day tile summary; coupon/event strip only for that offer; First name | Last name on one row; Special requests optional with 0 / 1000 counter.
- [ ] **TB4**: summary rows, copy address, Call the restaurant, Add to calendar, Done → PF1.
- [ ] Everything in `11-table-booking.md` §12 (definition of done).
- [ ] **TM1**: grouped Active / Paused / Invites with counts; status dot + status word per person; Owner chip; one pinned Invite to team; no username field on the list.
- [ ] **TM2**: sheet max height screen − 64; Invite → "✓ Invited" and the invite appears on TM1.
- [ ] **TM3**: Active / Paused radio cards; services checklist mirrors "Who does it"; Remove in danger red; Save changes pinned.
- [ ] Everything in `12-team.md` §8 (definition of done).
- [ ] **CR1/CR4**: two tabs; group tiles with the 0.4 rule; no phone/email; Send reward disabled with nobody selected.
- [ ] **CR2/CR7**: live ticket; message max 40 shown on ≤ 2 lines; stacked duration chips fit RO/DE at 360.
- [ ] **CR5–CR8**: progress bar without step text; F4 week strip; Who counted in the month before each send; summary sentence; Change returns to the step.
- [ ] **CR9/CR10**: switch, stats, rule rows, delete in the header; Stop reward in danger red.
- [ ] Everything in `13-customers-rewards.md` §13 (definition of done).
- [ ] **RV1**: calendar tab with the amber badge (= waiting requests, hidden at 0); requests banner hidden at 0; Today / Tomorrow lists with C37 chips; no calendar strip; no phone or email.
- [ ] **RV2**: oldest first; card head → RV3; inline Decline / Accept; note quote on 1 line.
- [ ] **RV3/RV5**: duration, price and "With <name>" only when the booking has them; offer strip only with an offer; Call opens the dialer, Copy copies the email.
- [ ] **RV4**: exactly two reasons, Fully booked preselected, no message field; dismiss sends nothing.
- [ ] **RV6**: No-show / Yes, done; auto-done the next day; only done visits count.
- [ ] Same screens render a service, a table and an event booking correctly; no gendered pronouns.
- [ ] Everything in `14-reservations.md` §13 (definition of done).
- [ ] **MA1–MA3**: three tabs with counts (no Total / Completed / Upcoming counters); Upcoming = waiting + confirmed by day; History by month with Rate / ★ N / Book again.
- [ ] **MA2**: ready rewards end soonest first and open MA6; used or ended are faded and not tappable.
- [ ] **MA4/MA5**: status banner (amber / green), place card with Copy address and Call; no Add to calendar, no Directions; Cancel in danger red.
- [ ] **MA6**: days left follows the Time left rule; Book with <place> pinned.
- [ ] Everything in `15-my-activity.md` §13 (definition of done).
- [ ] **SR1/SR2**: field outline when empty, ink with clear X when typing; recent searches with remove and Clear all; no Browse / categories; no results card without tabs.
- [ ] **SR3–SR6**: four tabs without counts, unselected greyed 0.4, the query kept across tabs; All mixes place blocks, video rows and deal rows in the received order, no headings, no See all; Loading more at the end of every list.
- [ ] **SR5**: place rows without a category icon; verified badge only for verified places; status colour per the Opening status rule.
- [ ] **SR6**: deals 2 per row, ending soonest first, tiles without counts; a deal opens F4C / F4E / TB2C / TB2E with the deal picked.
- [ ] Everything in `16-search.md` §14 (definition of done).
- [ ] **NP1**: the + opens the picker; one clip, up to 100 MB, no Skip.
- [ ] **NP2/NP3**: the whole video with the frosted caption panel; title max 30 and description max 100 with counters; Publish greyed until there is a title; no tag pill on the video.
- [ ] **NP4**: Tag sheet with search and From your visits (check to tag); the Tag icon turns white with the count badge.
- [ ] **EP1**: "Edit post", no Change video, saved text and tag, Delete video (danger on dark) and Save on one row.
- [ ] **EP2**: what is deleted (video, title and description, tag, likes), red Delete video; X or the dim area keeps it.
- [ ] Everything in `17-new-post.md` §12 (definition of done).
