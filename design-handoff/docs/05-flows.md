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
3. **First visit**: F3 must be passed (Anyone or a stylist) before the calendar. F4 = R3 layout **plus Choose an offer** (Any time / coupon / event), which switches F4 ↔ F4C ↔ F4E in place.
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
| Food & Beverage | Book now → **TB1 table booking** | — |

## F. Table booking (Food & Beverage)

```mermaid
flowchart LR
  PF1[PF1 F&B profile] -- Book now --> TB1[TB1 Pick a date]
  TB1 -- Choose a time --> TB2[TB2 Guests & time]
  TB1 -- event / coupon row --> TB2
  TB2 -- Continue --> TB3[TB3 Your details]
  TB3 -- Confirm reservation --> TB4[TB4 Booked]
  TB4 -- Done / X --> PF1
  TB3 -- Back / Change --> TB2
  TB2 -- Back --> TB1
```

Rules (details in `11-table-booking.md` §1):
1. Date first (month calendar, months ahead), then guests + offer + time on **one** screen, then details, then the confirmation.
2. The chosen offer (Any time, a coupon or an event) decides which times are shown and is carried to TB3 (summary strip) and the booking request.
3. Back and Change never lose a pick. A row in TB1's list opens TB2 with that day and offer chosen.

## G. Host — team

```mermaid
flowchart LR
  HP[HP Host profile] -- Team tile --> TM1[TM1 Team]
  TM1 -- Invite to team --> TM2[TM2 Invite sheet]
  TM2 -- close --> TM1
  TM1 -- a person --> TM3[TM3 Team member]
  TM3 -- Save changes / Back --> TM1
  TM3 -- Remove from team --> DEL((confirm — not designed))
```
Rules (details in `12-team.md` §1): invites wait under **Invites** until accepted; **Paused** people are hidden from booking (R1, F3, "Can replace", "Anyone") but keep their bookings; TM3 services = "Who does it" on each service; the owner cannot be paused or removed.

## H. Host — customers & rewards

```mermaid
flowchart LR
  HP[HP Host profile] -- Customers tile --> CR1[CR1 People]
  CR1 <-- tabs --> CR4[CR4 Rewards]
  CR1 -- Send reward --> CR2[CR2 New reward] -- Send --> CR3[CR3 Sent]
  CR3 -- See rewards --> CR4
  CR4 -- New automatic reward --> CR5[CR5 When] --> CR6[CR6 Who] --> CR7[CR7 Reward] --> CR8[CR8 Check]
  CR8 -- Turn on --> CR4
  CR4 -- a rule --> CR9[CR9 Edit]
  CR4 -- a sent reward --> CR10[CR10 Details]
```
Rules (details in `13-customers-rewards.md` §1): only people who booked in the app; rewards are single use (one booking); automatic rewards are monthly, Who is decided at each send from visits in the month before; switching off stops future sends only; Stop reward removes it for people who have not used it.

## I. Host — reservations

```mermaid
flowchart LR
  HP[HP Host profile] -- calendar tab --> RV1[RV1 Reservations]
  RV1 -- requests banner --> RV2[RV2 Requests]
  RV2 -- card --> RV3[RV3 Request]
  RV2 & RV3 -- Decline --> RV4[RV4 Reason sheet] -- Decline request --> RV2
  RV2 & RV3 -- Accept --> RV5[RV5 Confirmed]
  RV1 -- confirmed row --> RV5
  RV1 -- past row --> RV6[RV6 Did they come?] -- No-show / Yes, done --> RV1
```
Rules (details in `14-reservations.md` §1): every booking made in the app is a request (**Waiting for you**) until the host answers; oldest first; no answer in 24 hours → declined automatically; Decline needs one of two reasons (Fully booked, Closed that day) and has no message; after the end time a reservation is **Done** unless the host marks **No-show** (done by itself the next day); only done reservations count as visits for customers & rewards (§H). The same screens serve services, tables and events.

Bookings that arrive here come from F4 / R3 (services) and TB3 (tables and events): after **Confirm** / **Confirm reservation** the customer's booking is a request, not yet confirmed (see `10-open-questions.md` #36).

## J. Customer — my activity

```mermaid
flowchart LR
  PR[Customer profile] -- My activity --> MA1[MA1 Upcoming]
  MA1 <-- tabs --> MA2[MA2 Rewards] <-- tabs --> MA3[MA3 History]
  MA1 -- waiting --> MA4[MA4 Reservation · waiting]
  MA1 -- confirmed --> MA5[MA5 Reservation · confirmed]
  MA2 -- ready reward --> MA6[MA6 Reward] -- Book with place --> PROF[PS1 / PF1]
  MA4 & MA5 -- place --> PROF
  MA3 -- Book again --> PROF
```
Rules (details in `15-my-activity.md` §1): Upcoming = WAITING + CONFIRMED; History = DONE, DECLINED (with the reason), CANCELLED; the host's Accept / Decline (§I) moves a row from Waiting to Confirmed or to History; rewards ready to use end soonest first and are used at the last booking step with that place; Rate only on unrated done visits; Book again on declined / cancelled.

## K. Public — search

```mermaid
flowchart LR
  NAV[Bottom nav · Search] --> SR1[SR1 Before you type]
  SR1 -- type / recent --> SR3[SR3 All]
  SR1 -- nothing found --> SR2[SR2 No results]
  SR3 <-- tabs --> SR4[SR4 Videos]
  SR3 <-- tabs --> SR5[SR5 Places]
  SR3 <-- tabs --> SR6[SR6 Deals]
  SR3 & SR5 -- place --> PROF[PS1 / PF1 / PA1]
  SR3 & SR4 -- video --> VID[F2 / PA2]
  SR3 & SR6 -- deal --> BOOK[F4C / F4E / TB2C / TB2E]
```
Rules (details in `16-search.md` §1): one field for places, videos and deals; results replace the start screen while typing, X goes back to SR1; tabs All · Videos · Places · Deals without counts (unselected greyed 0.4), the query stays across tabs; All is one mixed feed, best match first, and every list keeps loading; a place opens its profile by category; a video opens the item's video (services through the first-visit path, F2 → F3, since no team member is picked); a deal opens its booking with the deal already picked, on the first day it applies; deals end soonest first.

## L. Profile — new post

```mermaid
flowchart LR
  NAV[Bottom nav +] --> NP1[NP1 Pick a video]
  NP1 -- Next --> NP2[NP2 On the video, empty]
  NP2 -- type a title --> NP3[NP3 Written]
  NP2 & NP3 -- Tag --> NP4[NP4 Tag a place]
  NP4 -- Done --> NP3
  NP2 & NP3 -- Change video --> NP1
  NP3 -- Publish --> PROF[Own profile]
  POST[Your post · More] -- Edit --> EP1[EP1 Edit post]
  EP1 -- Save --> PROF
  EP1 -- Delete video --> EP2[EP2 Delete video]
  EP2 -- Delete video --> PROF
```
Rules (details in `17-new-post.md` §1): video first, one clip up to 100 MB, no Skip; title required (max 30), description optional (max 100), typing stops at the cap; Publish only with a title; a tag is a place, a service or a room (restaurants: the place only), picked from the person's visits or searched in the same sheet; the tag shows as the Tag icon on the side rail (white + count badge), never as a pill on the video; viewers open the tagged item from that icon; one tag per post. Edit post changes the title, description and tag (not the video); Delete video deletes the video and everything linked to it (title, description, tag, engagement: views and likes) for everyone, after the EP2 confirmation. No hashtags, people tags or location.

## M. Account — create or sign in

```mermaid
flowchart LR
  TAB[Profile tab, signed out] --> AU1[AU1 Your profile]
  AU1 -- Create account / Sign in --> AU2[AU2 Continue with email]
  AU2 -- new email --> AU3[AU3 Create account]
  AU2 -- known email --> SIGNIN((Sign in with password))
  AU3 -- Change on the date --> AU4[AU4 Date of birth]
  AU4 -- Confirm / Cancel --> AU3
  AU3 -- too young --> AU5[AU5 Create account disabled]
  AU3 -- Create account --> PROF[Your profile]
```
Rules (details in `18-account.md` §1): no welcome wall, people browse without an account; the Profile tab shows AU1 while signed out; email only (no Apple / Google); the email decides create or sign in; create needs first and last name, a free username, a date of birth (dialog with Day · Month · Year wheels) and a password of 8+; under the minimum age (16) Create account stays disabled; the date of birth is never shown.
