# 02 · Design tokens

Machine-readable values: [`../tokens.json`](../tokens.json). Map them once into the app theme (Compose `MaterialTheme`/custom theme object, SwiftUI `Color`/`Font` extensions, Flutter `ThemeExtension`, etc.). All sizes: 1 px in the HTML = 1 dp (Android) = 1 pt (iOS).

## Colour

| Token | Value | Used for |
|---|---|---|
| `bg.page` | `#F7F5FB` | Screen background (all light screens) |
| `bg.surface` | `#FFFFFF` | Cards, sheets, bottom bars, white pills |
| `bg.soft` | `#ECE9F2` | Secondary buttons (Follow), chips, pills, tile backgrounds, disabled slots |
| `text.primary` / `action.primary` | `#1D1B22` | Main text; primary button fill (Book, Confirm, Save, Pick a time) |
| `text.body` | `#3A3742` | Body text inside cards |
| `text.secondary` | `#5F5B68` | Secondary text, counts, labels |
| `text.tertiary` | `#8E8A96` | Chevrons, inactive icons |
| `text.disabled` | `#9B97A3` | Disabled day/time (with line-through) |
| `line.card` | `#E7E3ED` | 1px card/section borders |
| `line.divider` | `#E2DEE9` | Tab underline track, chip outlines, pill dividers |
| `line.rowSeparator` | `#EEEBF2` | Row separators inside cards |
| `line.outline` | `#DCD7E4` | Outlined time slots, dashed tear line |
| `line.strong` | `#CFC9DA` | Sheet handle, dashed "Add" chips, unselected radio, price-meter empty bars |
| `action.profileCta` | `#3F5079` | Slate CTA in public profile header (Call / Book now) |
| `action.danger` | `#B3261E` | Delete (trash), "Closed", urgent countdown, Not allowed icon |
| `brand.accent` | `#7155E0` | Host avatar ring, creator avatar on videos |
| `brand.verified` | `#2F7BEA` | Verified badge |
| `status.success` | `#1F8A55` | Status dots, ticks, **discount sticker** background, "who does it" check badges |
| `status.successText` | `#11673F` | "Open now", next free time text |
| `status.successBg` | `#DDF5E8` | Tick circle background (services included list) |
| `status.successOnDark` | `#5ED39A` | Ticks on video chips, selected-day dot |
| `status.warning` / `warningText` | `#E0A21B` / `#8A5A00` | "Closes soon" |
| `status.dangerOnDark` | `#FFB4AB` | Urgent text on dark glass |
| `dark.card` | `#1D1B22` | Video card base under media |
| `dark.noVideo` | `#2E2B36` | Placeholder when an item has no video |
| `dark.pickerBg` | `#0E0D11` | Video picker screen |
| `dark.navBar` | `#111113` | Bottom navigation bar (host) |
| `dark.videoGradient` | `160deg #5A4A63 → #2E2535 → #141016` | Placeholder for video content in mocks only |
| `calendar.freeBg` / `freeBorder` | `#E7F4EC` / `#BFE3CD` | Month calendar: day with free tables (border only on the legend swatch) |
| `calendar.fewBg` / `fewBorder` | `#FDF1D8` / `#F1D79A` | Month calendar: day with few tables left |
| `calendar.pastText` | `#C4BFCC` | Month calendar: past days |
| `calendar.arrowDisabled` | `#B9B4C2` | Previous month/week arrow when disabled |
| `offer.coupon` / `couponTint` / `couponText` | `#1F8A55` / `#E7F4EC` / `#11673F` | Coupon badge and sticker / coupon strip in the booking summary |
| `offer.event` / `eventTint` / `eventText` | `#7155E0` / `#EEEAFD` / `#5B3FD6` | Event badge and sticker / sitting buttons and event strip |
| `offer.eventSubText` / `eventOnDark` | `#6A55C8` / `#C9BCFF` | "N seats left" on a sitting / event icon on the selected (ink) sitting |

## Typography
- Family: **Roboto** on Android, **system (SF Pro)** on iOS. Weights 400 / 500 / 600 / 700 / 800.
- Sizes (pt/dp): profile name 21/700 · host profile name 22/400 · screen title 18/500 · sheet title 19/600 · form name 19/500 · video title 19/700 (F2 legacy) · public card title 16/600 · host card title 14.5/600 · coupon title 12.5/600 · body 14–15 · button 16/500 · pills 13/600–700 (12 on small phones) · secondary 13 · tabs 12 · micro 11 (10.5 on small phones) · nav labels 10.5.
- Line heights: titles 1.25, body 1.45, captions 1.4.
- Support Dynamic Type / font scale: let text wrap or clamp, never overlap. Pills keep `nowrap`.

## Radius
Sheet 24 · video card 22 · white section card 18 · 36-high pills 18 · primary buttons and glass panel 16 · offer cards, guests card 16 · ticket card, Follow/Call, day buttons, day tile, sittings 14 · category tiles, price pill 13 · time slots, thumbnails 12 · month calendar cells 10 · date tile / list date badge 9 · discount sticker, offer sticker 6 · avatars, icon buttons: round.

## Spacing
Screen side padding **16**. Grid gap **12** (2 columns), **8** (3-column coupons), **2** (video picker). Section gaps 12–16. Header 56 (64 with a two-line title). Bottom action bar padding `10 16 24 16` (24 = home-indicator area; replace with the real safe-area inset). Host bottom nav 72. Minimum touch target **44**.

## Elevation and overlays
| Token | Value |
|---|---|
| Info card on video | `0 4px 16px rgba(0,0,0,.25)` |
| Bottom sheet | `0 -6px 20px rgba(0,0,0,.25)` |
| Map pin | `0 2px 8px rgba(0,0,0,.25)` |
| Floating icon (edit, sticker) | `0 1px 4px rgba(0,0,0,.25–.3)` |
| Selection ring | `0 0 0 2px <bg>, 0 0 0 4px #1D1B22` |
| Card top scrim | `rgba(0,0,0,.65) → .55 @55% → 0`, height 140 |
| Card bottom scrim | `0 → .3 @30% → .62 @60% → .85`, height 62 % of card |
| Video top scrim | `.55 → 0`, height 140 |
| Video bottom scrim | `0 → .35 @35% → .8`, height 420 |
| Glass panel | tint `rgba(22,20,28,.55)`, blur 16, saturate 150 %, border 1 `rgba(255,255,255,.22)`, inset top highlight `rgba(255,255,255,.12)` |
| Sheet dim | `rgba(0,0,0,.45)` over the video |
| Chip on video | `rgba(0,0,0,.45)`; round button on video `rgba(0,0,0,.4)` |
| Play button | fill `rgba(0,0,0,.5)` + 1.5 border `rgba(255,255,255,.75)`; 44 on cards, 64 on detail, 34 on tickets |

## Opacity
Greyed-out option: **0.4** (still tappable). Disabled control: 0.4 + not interactive.
