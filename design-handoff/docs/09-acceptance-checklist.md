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
