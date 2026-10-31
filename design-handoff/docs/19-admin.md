# 19 · Admin dashboard (web)

The full spec of the **Admin · Dashboard** page in the design canvas: the web app the platform team uses to moderate videos, approve hosts, manage the platform and watch the important numbers. It keeps the existing admin's structure and every page name, and cleans up each page.

Unlike the rest of this handoff, it is a **desktop web app**:
- the references are drawn at **1440 × 900**;
- the layout works from 1280 wide;
- the side columns keep their width and the middle column flexes.

It uses the app's tokens and Roboto, plus the admin's red **M** mark (`#E5383B`, a brand asset, not in `tokens.json`).

References: `../screenshots/desktop/<id>.png` (2×) and `../screens/desktop/<id>.html` (exact values).

| Screen | Screen id | Canvas board |
|---|---|---|
| Reviews | `AD1-reviews` | 1 · Reviews: one queue, the video in the middle, decide with A / R |
| Analytics | `AD2-analytics` | 2 · Analytics grouped by category, with a period switch |
| Platform Users · Host Approval | `AD3-host-approval` | 3 · Platform Users: the Super Admin menu in groups; Host Approval |

Decisions, so they are not undone:
- **Three top tabs stay:** **Reviews · Analytics · Platform Users.**
- **Every page keeps its name**, as listed in §1. The group labels in the Super Admin menu ("Approvals", "People", …) are labels only, not pages.
- **Waiting work shows as badges:**
  - Reviews: pending videos;
  - Platform Users and Host Approval: host applications waiting;
  - System Health: a status dot.

---

## 1. Structure (every page, by tab)

```text
Reviews            Video Reviews: Pending Reviews · Approved Videos · Rejected Videos
Analytics          Videos · People · Reservations · System Health   (24h / 7 days / 30 days)
Platform Users     Super Admin menu:
  Approvals          Host Approval
  People             User Management · Host Management
  Bookings & catalog Reservations · Categories
  Platform           General · Platform Settings · System Health
  Audit Log          Audit Log: Overview · Feed · Search · Video Upload · Registration · Reservations · Playback Health
```

The menu shows every page at all times; Audit Log is expanded with its seven pages, as in the existing admin.

## 2. Roles and security

The layout hides what a role cannot use, but **the server is the protection**: every page, list and action checks the admin's role, and refuses the request otherwise.

| Role | Sees |
|---|---|
| **Moderator** | Reviews; Analytics (read only) |
| **Super Admin** | Everything: Reviews, Analytics, Platform Users |

- **Personal data** in Host Approval (email, phone, address, documents) is only for roles that approve hosts. Documents open through short-lived links, and every view is recorded in the Audit Log.
- **Two-factor sign-in** for every admin account. The password is asked again before rejecting a host, changing Platform Settings, or acting on a user in User Management.
- **Every decision is recorded** in the Audit Log: approve or reject a video or a host, with who, when and the reason.
- **Undo** for a few seconds after Approve or Reject (the keyboard makes them fast, and mistakes easy).
- **The Audit Log is read only.** Nobody can edit or delete an entry.
- **Logout** ends the session; an idle session signs out by itself.

## 3. Top bar (AC1)

- 64 tall, white, 1px `line.card` bottom border, padding `0 24`, gap 32.
- **Brand:** M mark 28 (radius 8, `#E5383B`, white 15/700) + "Video Review Playlist" 16/600.
- **Tabs:** 14.5, full bar height. The selected tab is 600 `text.primary` with a 2px `text.primary` underline; the others are 400 `text.secondary`. Badges: **Reviews** ink with white count; **Platform Users** `status.warningBg` / `status.warningText`.
- **Right:** avatar 32 + **Logout** (white, 1px `line.outline`, 36, radius 12, `log-out` 16).

## 4. AD1 · Reviews

Three columns under the top bar.

| Column | Spec |
|---|---|
| **Queue** (360, white, right border) | "Video Reviews" 22/600 + "Manage and review submitted videos." 13.5 `text.secondary` |
| | List switch, rows 36, radius 10, 14 (selected: `bg.soft`, 600): **Pending Reviews** with an ink count badge · **Approved Videos** "128 today" · **Rejected Videos** "9 today" |
| | "Oldest first" · `clock` "Oldest: 1 h" 12.5 `text.secondary` |
| | **Queue rows** (AC2): padding 10, radius 14, gap 12. Thumbnail 44 × 64 (radius 8). Title 14/600, 1 line. "@username · 2 min ago" 12.5. Tag chip 22 (`store` 12 + "Place · item"), or "No tag" in `text.tertiary`. Selected: `bg.soft` + 2px `text.primary` ring. |
| **Video** (flexes, centred) | Player 9:16 (338 × 600 at 1440), radius 20, the post as people see it (poster, title, description) with play 56 · **decision bar** (AC3) 18 below |
| **Details** (320) | Three white cards (radius 18, 1px `line.card`), gap 12: |
| | **Uploader:** avatar 40, name 15/600, "@username · role"; then Member since / Approved before / Rejected before |
| | **Post:** Tag, Uploaded, File, Waiting |
| | **If you reject:** "Pick a reason. The person is told why." + reason chips 30 (Not allowed content · Low quality · Wrong tag · Spam or ads) |

**Decision bar (AC3)**, buttons 48 tall, radius 14, gap 10, each with its key in a small `kbd`:
- **Reject** `R`: white, 1.5px `action.danger` border, `x`;
- **Approve** `A`: `status.success` fill, white, `check`;
- **Next** `J`: `bg.soft`.

Rules:
1. Pending is **oldest first**. Opening Reviews selects the oldest.
2. **A** approves. **R** rejects and needs one reason. **J** moves on without deciding.
3. After a decision the next video opens, and **Undo** shows for a few seconds.
4. **Approved Videos** and **Rejected Videos** are read-only history: who decided, when, and the reason for a rejection.
5. The uploader is told the outcome; a rejection includes the reason.

## 5. AD2 · Analytics

- Title "Analytics" 26/600, with a period switch on the right: **24h · 7 days · 30 days**. Labels with "(24h)" follow the period.
- Four sections; each heading (16/600) has an "Open <page>" link on the right:

| Section | Cards | Link |
|---|---|---|
| **Videos** | Pending Videos (24h) · Approved Videos (24h) · Rejected Videos (24h) · Time to review | Open Reviews |
| **People** | New users · New hosts · Host applications waiting | Open User Management |
| **Reservations** | Requests · Confirmed · Declined · No-shows | Open Reservations |
| **System Health** | Playback errors · Upload failures · Uptime | Open System Health |

**KPI card (AC4):** white, radius 18, padding `16 18`. It holds:
- the label, 13.5/500 `text.secondary`;
- the value, 30/600;
- a change line, 12.5/500: `status.successText` when it is good, `action.danger` when it is bad;
- a sparkline 120 × 32 over the period, green or red to match.

## 6. AD3 · Platform Users · Host Approval

**Super Admin menu (AC5):**
- 260 wide, white, right border, padding `20 14`.
- "Super Admin" 16/600.
- Group labels 11.5/600, uppercase, `text.tertiary`.
- Items 36 tall, radius 10, icon 18 + 14. Selected: `bg.soft` and 600.
- Host Approval has the amber count badge. System Health has a status dot: `status.success` when OK, `status.warning` for a warning, `action.danger` when down.
- Audit Log has a chevron, and its seven pages are indented 40 (32 tall).

**Host Applications** (AC6), main area padding `28 32`:
- **List card:**
  - `shield-check` + "Host Applications" 20/600 + "Review and approve/reject business host applications." 13.5;
  - **Refresh** (white outline, 36);
  - **Pending · Approved · Rejected** switch, Pending with its count;
  - table columns **Business** (avatar 36, name 14/600, "Category · type"), **City**, **Applied**, **Owner** (name + email);
  - rows separated by `line.rowSeparator`; the selected row on `bg.soft`.
- **Application card** (340, beside the list):
  - avatar 44 + name 16/600 + "Category · type · City";
  - Owner, Email, Phone, Address, Applied;
  - **Documents** as file links;
  - **Reject** (danger outline) · **Approve** (`status.success`).

Rules:
- **Approve** makes the business a host, and the owner is told.
- **Reject** asks for a reason, in the same way as Reviews.
- Both are recorded in the Audit Log (§2).

## 7. Pages without their own board yet

User Management, Host Management, Reservations, Categories, General, Platform Settings, System Health and the seven Audit Log pages are in the menu with their names and places as in §1. They use the same shell (top bar + Super Admin menu + main area) and follow §2. Their content is designed next.

## 8. Components (admin)

| # | Component | Spec |
|---|---|---|
| AC1 | **Admin top bar** | §3 — M mark, product name, three tabs with badges, avatar, Logout |
| AC2 | **Queue row** | §4 — thumbnail 44 × 64, title, @username · age, tag chip; selected ring |
| AC3 | **Decision bar** | §4 — Reject (R) · Approve (A) · Next (J), 48 tall, keyboard hints |
| AC4 | **KPI card** | §5 — label, value 30/600, change line, sparkline |
| AC5 | **Super Admin menu** | §6 — grouped items, badges, status dot, Audit Log with its seven pages |
| AC6 | **Applications table + detail card** | §6 — Business / City / Applied / Owner, selected row, detail with documents and Approve / Reject |

## 9. Copy (EN)

| Where | Copy |
|---|---|
| Top bar | "Video Review Playlist" · "Reviews" · "Analytics" · "Platform Users" · **Logout** |
| AD1 | "Video Reviews" · "Manage and review submitted videos." · "Pending Reviews" · "Approved Videos" · "Rejected Videos" · "<n> today" · "Oldest first" · "Oldest: <age>" · "No tag" · **Reject** · **Approve** · **Next** · "Member since" · "Approved before" · "Rejected before" · "Post" · "Tag" · "Uploaded" · "File" · "Waiting" · "If you reject" · "Pick a reason. The person is told why." · "Not allowed content" · "Low quality" · "Wrong tag" · "Spam or ads" |
| AD2 | "Analytics" · "24h" · "7 days" · "30 days" · "Videos" · "People" · "Reservations" · "System Health" · card labels as in §5 · "Open <page>" |
| AD3 | "Super Admin" · group labels · page names as in §1 · "Host Applications" · "Review and approve/reject business host applications." · **Refresh** · "Pending" · "Approved" · "Rejected" · "Business" · "City" · "Applied" · "Owner" · "Documents" · **Reject** · **Approve** |

## 10. Data

See `06-data-model.md` → *Admin*: the review queue and decisions, the analytics summary, host applications and decisions, and admin roles.

## 11. Definition of done for this page

- [ ] AD1–AD3 match their screenshots at 1440 × 900 (overlay at 50 %), and work from 1280 wide.
- [ ] Three tabs, and every page name exactly as in §1. Badges for pending reviews and host applications, and a status dot on System Health.
- [ ] Reviews: oldest first; Reject (R) needs a reason, Approve (A), Next (J); Undo after a decision; Approved Videos and Rejected Videos are history.
- [ ] Analytics: four sections with a period switch; each card shows its value, change and sparkline; each section links to its page.
- [ ] Host Approval: grouped menu; Pending / Approved / Rejected; the table and the detail card with documents and Approve / Reject.
- [ ] §2 holds on the server: role checks on every request, personal data only for host approvers, two-factor sign-in, password again for the risky actions, every decision in the read-only Audit Log.
