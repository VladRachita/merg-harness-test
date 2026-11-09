# 22 · Landing page (website, MVP)

The full spec of the **website** for the MVP. There is no web version of the app in the MVP: the site is **one page** whose only job is to show what Merg is in one look and send people to the App Store or Google Play.

It comes from the **Web version** page of the canvas (private, owner access): https://claude.ai/artifact/Vwih7Qv5GPRzwhYsL6zS6x — boards *Landing · Desktop* and *Landing · Phone*. The other boards on that page (the map ideas and how they load) are work in progress and **not** part of this handoff.

References:
- desktop: `../screenshots/desktop/lp1-landing-desktop.png` (1440 × 900, 2×) and `../screens/desktop/lp1-landing-desktop.html`;
- phone: `../screenshots/{small,medium,large}/lp2-landing-phone.png` (full scroll, 2×) and `../screens/{small,medium,large}/lp2-landing-phone.html`;
- pictures: `../assets/landing/` (see its `README.md`), drawn in `../screens/reference/landing-hero.html`.

| Screen | Screen id | Canvas board |
|---|---|---|
| Landing page on a computer | `LP1-landing-desktop` | Landing · Desktop — headline, store buttons and QR, one phone |
| Landing page on a phone | `LP2-landing-phone` | Landing · Phone — web on mobile (full scroll) |

Decisions, so they are not undone:
- **One page, no web app.** No sign-in, feed, search or map on the web in the MVP. Every action leads to a store.
- **Static.** The page is built once and served from a CDN. It calls **no API** and reads no database.
- **The phone picture is an image** from `assets/landing/`, not rebuilt in HTML or CSS.
- **White page** with the app's tokens. The only dark area is inside the phone picture (the app's real feed).
- **On a computer** the page is one screen (no scrolling at 1440 × 900); **on a phone** it scrolls, and the headline and both store buttons are in the first screen.

---

## 1. Structure

**LP1 · computer (1440 × 900)**
1. **Top bar** 80 tall, side padding 120: `merg` wordmark (link to the top) · **For businesses** (text button) · **Get the app** (ink pill).
2. **Left column** at x 120, top 168, 580 wide:
   - label "New · Now in Brașov" (C83);
   - headline "Deals and events near you, in short videos." (H1);
   - lead, max 520 wide;
   - 36 below it, the download block (`id="download"`): the two store buttons (C84), then 16 below the QR card (C85).
3. **Picture** (C86) `hero-desktop`, 750 × 800 at left 690, top 100. It reaches the right edge of the page.
4. **Footer** at left 120, 28 from the bottom: © 2026 Merg · Terms · Privacy · Contact.

**LP2 · phone (full scroll: 1221 / 1291 / 1289 tall at 360 / 390 / 430)**
1. **Top bar** 64 tall, padding `0 12 0 20`: wordmark · **Get the app** (ink pill).
2. **Text**, padding `20 20 0`: label (C83) · H1 · lead · 24 below, the two store buttons side by side, each half the width (C84) · "Free on iPhone and Android". All of this is in the first screen.
3. **Picture** (C86) `hero-phone`, 20 below, full width (393 × 660, scales with the width). Its top shows in the first screen on medium and large phones, so people scroll.
4. **Footer**, padding `20 20 32`, top line `line.card`: "Own a place? Merg for businesses →" (44 tall) · © 2026 Merg · Terms · Privacy · Contact.

There is no QR code on phones (the person is already on their phone).

## 2. Sizes and type

| Element | Computer (LP1) | Phone (LP2) |
|---|---|---|
| Side padding | 120 | 20 |
| Wordmark `merg` | 28/32, 700, −0.035em, link 44 tall | 26/30, 700, link 44 tall |
| Top bar buttons | 44 tall, radius 22, 15/20 500; **Get the app** `action.primary` + white, padding `0 20`; For businesses transparent, padding `0 16`, `bg.page` on hover | Get the app only, padding `0 18` |
| Label (C83) | 32 tall, radius 16, padding `0 14 0 12`, `brand.tintBg`, text `brand.tintIcon` 14/18 500, dot 8 `brand.accent`, gap 8 | same |
| H1 | `font.size.landingTitle` 60/66, 700, −0.035em, `text.primary`; 22 under the label | `landingTitlePhone` 38/44 (`landingTitleSmallScreen` 34/40 under 375), −0.03em; 18 under the label |
| Lead | `landingLead` 19/30, `text.body`, max 520; 20 under the H1 | `landingLeadPhone` 17/26 (16/24 under 375); 16 under the H1 |
| Store buttons (C84) | 52 tall, at least 156 wide, gap 12 | 52 tall, half the width each, gap 10 |
| QR card (C85) | QR 80, padding `10 20 10 10`, radius 18 | — |
| "Free on iPhone and Android" | inside the QR card, 13/18 `text.secondary` | under the buttons, 13/18 `text.secondary`, 10 below |
| Footer | 13/18 `text.secondary`, gap 20 | same, wraps |

Font: Roboto (the app's font), weights 500 and 700 only. Focus: 2 px ink outline, offset 3.

## 3. Behaviour

- **Store buttons (C84).** App Store opens the app's App Store page; Google Play opens its Google Play page, in a new visit (no `target="_blank"` on phones). In production they are the **official badges** ("Download on the App Store" from Apple, "Get it on Google Play" from Google) in the page language, at the same height. The references draw plain ink buttons in their place.
- **Get the app (top bar).**
  - On a computer: moves to the download block and focuses the first store button.
  - On a phone: opens the **download link** (below), which picks the store.
- **Download link.** One address, `https://<site>/get`, is redirected **on the server** by the phone's system:
  - iPhone or iPad → App Store;
  - Android → Google Play;
  - anything else → the landing page, at the download block.

  It keeps `?for=business` and other query values for counting.
- **QR code (C85, computer only).** It encodes the download link. The reference QR is a placeholder pattern. Generate the real one from the final link **at build time** as an inline SVG: error correction H, the `m` mark in the middle, a 2-module quiet zone. It must scan on iOS and Android.
- **For businesses** and **Own a place? Merg for businesses →.** The MVP has no business website. The link goes to the download block (computer) or the download link with `?for=business` (phone). In the app, a person becomes a business from their profile → **Convert to Business** (BC1, `21-business-conversion.md`).
- **Terms · Privacy · Contact.**
  - Terms and Privacy: the same documents the app links to.
  - Contact: an email link to the support address.
- **iPhone Safari.** Add the Smart App Banner (`<meta name="apple-itunes-app" content="app-id=…">`), so Safari offers the app at the top.
- **Counting.** Count store clicks from the `/get` redirect on the server: no cookies and no third-party scripts, so the page needs no cookie banner. If tracking cookies are ever added, a consent banner is required first.

## 4. The pictures (C86)

| File | Size (px) | Weight | Where |
|---|---|---|---|
| `hero-desktop.webp` · `hero-desktop@2x.webp` | 750 × 800 · 1500 × 1600 | 56 KB · 109 KB | LP1 |
| `hero-phone.webp` · `@2x` · `@3x` | 393 × 660 · 786 × 1320 · 1179 × 1980 | 42 · 98 · 140 KB | LP2 |
| `og-image.jpg` | 1200 × 630 | 70 KB | link previews (§7) |

- **Background:** transparent; they sit on the white page.
- **Markup:** use an `<img>` with `srcset` and `sizes`, and set `width` and `height` so nothing moves while it loads. Add `fetchpriority="high"` and no lazy loading, because it is the main picture.
- **Alt text:** "The Merg app on a phone: a short video from Maestro with a 30% off deal on all coffee drinks, and a 15% reward from Studio Nails for coming back".
- **What they show:** the app's real feed screen (the deal post with the offer card and the bottom nav), the offer card popping out in white, and a reward ticket (MA6 style).
- **Sample content:** Maestro and Studio Nails. To show real partners later, change the source (`screens/reference/landing-hero.html`) and export again.
- **Font in the pictures:** the text is set in **Inter**, because Roboto could not be loaded where the pictures were made. Export again from the source with Roboto installed to match the app exactly.

## 5. Computer, tablet and phone widths

| Page width | Layout |
|---|---|
| ≥ 1200 | LP1 as drawn. Content 1200 wide, centred (side padding 120 at 1440). Below 900 tall the page simply scrolls; nothing is pinned. |
| 1024–1199 | LP1. The picture takes 50 % of the page width (keeps its ratio), the column the rest; H1 52/58. |
| 600–1023 | LP2 centred, at most 560 wide; the picture at most 480 wide. |
| < 600 | LP2 as drawn; the picture full width. Under 375: H1 34/40, lead 16/24. |

## 6. Copy (EN and RO)

The site has two languages: **Romanian** and **English**, as two static pages (`/ro`, `/en`) with `hreflang`. The first visit goes to the browser's language, Romanian by default. The design has no language switch; if one is wanted, put "Română · English" in the footer in the same style.

| Key | EN | RO (proposed, check before launch) |
|---|---|---|
| label | New · Now in Brașov | Nou · Acum în Brașov |
| headline | Deals and events near you, in short videos. | Oferte și evenimente lângă tine, în clipuri scurte. |
| lead | Watch what cafés, salons and venues around you post. Grab a deal or a spot in one tap, and get rewarded when you come back. | Vezi ce postează cafenelele, saloanele și localurile din jurul tău. Prinde o ofertă sau un loc dintr-o atingere și primești recompense când revii. |
| getApp | Get the app | Descarcă aplicația |
| forBusinesses | For businesses | Pentru afaceri |
| scanTitle | Scan to get the app | Scanează ca să descarci aplicația |
| free | Free on iPhone and Android | Gratuită pe iPhone și Android |
| ownPlace | Own a place? Merg for businesses | Ai un local? Merg pentru afaceri |
| terms · privacy · contact | Terms · Privacy · Contact | Termeni · Confidențialitate · Contact |
| page title | Merg — deals and events near you, in short videos | Merg — oferte și evenimente lângă tine, în clipuri scurte |
| description | Watch short videos from cafés, salons and venues near you, grab deals and spots at events, and get rewarded for coming back. Free on iPhone and Android. | Urmărește clipuri scurte de la cafenele, saloane și localuri din apropiere, prinde oferte și locuri la evenimente și primește recompense când revii. Gratuită pe iPhone și Android. |

The store badges come in Romanian and English from Apple and Google. The picture has no page text, so it works for both languages.

## 7. Search engines and link previews

Every page has these tags in `<head>`:
- `<title>` and meta description (§6), canonical and `hreflang`;
- Open Graph: `og:title`, `og:description`, `og:type=website`, `og:image` = `og-image.jpg` (1200 × 630), `og:locale`;
- Twitter card: `summary_large_image`;
- the Smart App Banner (§3);
- the app icon as the favicon and Apple touch icon.

## 8. Speed, and the backend

- **No calls:** no API and no database. Static HTML and CSS, the pictures and the inline QR.
- **CDN:** served with long cache times (file names with a content hash).
- **Budget on a phone:** under 200 KB in total (HTML + CSS under 30 KB, `hero-phone@2x` about 100 KB, Roboto 500 and 700 subset about 40 KB).
- **Targets:** largest paint under 2 s on 4G; nothing moves while loading (layout shift 0).
- **JavaScript:** none needed. The store choice happens in the `/get` redirect.

## 9. Accessibility

- **Reading order:** top bar → H1 → lead → store buttons → QR card → picture → footer. One H1.
- **Picture:** has its alt text (§4).
- **QR:** the SVG is hidden from screen readers; the card's text says what it is.
- **Touch targets:** every link and button is at least 44 tall (the wordmark link too).
- **Contrast** (all at least 4.5 : 1):
  - lead 11.6;
  - footer and secondary text 6.6;
  - label 5.7;
  - store buttons 17.

## 10. Matched to the app (differences from the canvas)

- **Font:** Roboto 500 / 700 (the canvas used the system font at 600 / 800).
- **Footer text:** `text.secondary` instead of `text.tertiary`, for contrast. The canvas is updated too.
- **Wordmark:** the link is 44 tall (touch target).
- **For businesses:** goes to the download (in the canvas it opens the app's Convert to Business screens, as a prototype link).
- **Picture:** exported as an image; the canvas draws it live.

## 11. Data

None. The page reads no data. Settings for the build (see `properties-per-screen.md`, *Website · Landing page*, and A25):
- `APP_STORE_URL`, `PLAY_STORE_URL`, `IOS_APP_ID`;
- `DOWNLOAD_LINK` (`/get`), `SUPPORT_EMAIL`;
- the Terms and Privacy URLs.

## 12. Definition of done for this page

- [ ] LP1 matches `lp1-landing-desktop.png` at 1440 × 900 with nothing to scroll; LP2 matches `lp2-landing-phone.png` at 360, 390 and 430.
- [ ] Official App Store and Google Play badges, same height, in the page language, linking to the right store pages.
- [ ] The QR is generated from the final download link and opens the right store on an iPhone and on an Android phone.
- [ ] **Get the app:** moves to the buttons on a computer and opens the store on a phone. `/get` redirects by system and keeps `?for=business`.
- [ ] The pictures come from `assets/landing/` with `srcset`, `width` and `height`. Nothing moves while loading.
- [ ] The page makes no API calls and is served from a CDN. On a phone it weighs under 200 KB, and the largest paint takes under 2 s on 4G.
- [ ] Romanian and English pages, with title, description, Open Graph image, `hreflang` and the Smart App Banner.
- [ ] One H1, alt text on the picture, focus rings, targets ≥ 44, contrast ≥ 4.5 : 1.
