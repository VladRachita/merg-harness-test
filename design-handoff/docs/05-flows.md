# 05 · Flows and navigation rules

The clickable prototype in `../screens/medium/*.html` follows these flows. `../screens.json` lists every link per screen (`links_to`).

## A. Accommodation (call only)

```mermaid
flowchart LR
  PA1[PA1 Rooms profile] -- play / Details --> PA2[PA2 Room video]
  PA2 -- "+16 more" --> PA3[PA3 What's included]
  PA3 -- close --> PA2
  PA2 -- X --> PA1
  PA1 -- Call --> DIAL((Phone dialer))
  PA2 -- Call --> DIAL
```
Rules: accommodations have **no in-app booking**. The only action is **Call** (profile header and video side rail).

## B. Services booking — the Team filter decides the path

| Team filter on the services list | Path | Taps to book |
|---|---|---|
| A stylist (e.g. Andrei) — "regular customer" | R1 → R2 → R3 → Confirm | 3 (play, Book, Confirm) |
| Everyone — "first visit" | F1 → F2 → F3 → F4 → Confirm | 4–5 (adds Choose a stylist) |

```mermaid
flowchart LR
  subgraph Regular
    R1[R1 Services · Andrei] -- play --> R2[R2 Video]
    R2 -- Book --> R3[R3 Pick a time]
    R3 -- Confirm --> DONE((booking — not designed))
    R1 -- service without video --> R3
  end
  subgraph FirstVisit[First visit]
    F1[F1 Services · Everyone] -- play --> F2[F2 Video]
    F2 -- Book --> F3[F3 Choose a stylist]
    F3 -- Pick a time --> F4[F4 Pick a time]
    F4 -- Confirm --> DONE2((booking — not designed))
    F1 -- service without video --> F3
  end
  R1 -- Everyone --> F1
  F1 -- a stylist --> R1
  R2 -- "+8 more" --> SV[SV What's included]
  F2 -- "+8 more" --> SV
```

Rules:
1. The **side-rail Book** is the only way to book from a video. The info bar on the video is not tappable.
2. **Regular**: R3 opens with the picked stylist highlighted and the **earliest free slot preselected**. The people who can replace that stylist for this service are shown under "Can replace <name>" with their next free time; tapping one switches the calendar to them.
3. **First visit**: F3 must be passed (Anyone or a stylist) before the calendar. F4 = R3 layout.
4. "Anyone" = the earliest free time among everyone who does this service; the summary must then name the assigned stylist.
5. Services without a video skip the video step (go straight to R3/F3).
6. Back navigation returns to the previous screen (video → list, calendar → video or stylist step, sheet → video).
7. A future improvement (not designed): a signed-in returning customer could be treated as "regular" with their last stylist preselected.

## C. Host — add / edit a service or room

```mermaid
flowchart LR
  L[HS1 / HR1 list] -- New --> P[HS2 / HR2 Add a video]
  P -- Next or Skip --> D[HS3 / HR3 Details]
  D -- Save --> L
  L -- edit icon --> E[HS4 / HR4 Edit]
  E -- Add video / Change --> P
  E -- Save changes --> L
  E -- trash --> DEL((Delete — confirm dialog, not designed))
```
Rules: video first (Skip is allowed; the item then shows "No video yet"). Everything entered in Details is what customers see on the video (caption, chips, info bar, What's included sheet).

## D. Coupons & Events tab
Filter tiles (All / Events / Coupons) filter the grid in place. Tapping a ticket opens its video — **not designed** (proposed: same video overlay with **Get coupon** / **Get ticket** on the side rail).

## E. Public profile CTA by business type
| Category | Header CTA | Video side rail |
|---|---|---|
| Accommodation | Call → dialer | Call |
| Services | Book now (target not designed) | Book |
| Food & Beverage | Book now (target not designed) | — |
