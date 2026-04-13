# Manual Testing Scenarios

Ten scenarios for manual verification of the Equipment Status Board's core user flows. Each scenario lists preconditions, steps, and expected results.

## Prerequisites

- Application running locally (`make run`) with a seeded database
- At least one area configured with a Slack channel mapping
- At least one piece of equipment in each status (operational, degraded, down)
- User accounts: one Staff, one Technician
- Slack workspace connected with the app installed
- Background worker running (`make worker`)

---

## 1. QR Code Equipment Page — Status Check

**Role:** Unauthenticated member

**Steps:**

1. Open `/public/equipment/<id>` for a piece of equipment that has an open "Down" repair record.
2. Observe the page loads without any login prompt.
3. Verify the equipment name, area, and a large red status indicator are visible above the fold.
4. Verify the issue description and ETA (if set) are displayed.
5. Scroll to "Known Issues" and confirm the open repair record appears.
6. Repeat with an operational (green) equipment — confirm no issues section is shown and the status indicator is green.

**Expected Results:**

- Page loads instantly with no authentication required.
- Status indicator color and text match the equipment's derived status.
- Open repair records are listed under Known Issues.
- Equipment documentation links (manuals, training videos) are accessible from the page.

---

## 2. QR Code Equipment Page — Problem Report Submission

**Role:** Unauthenticated member

**Steps:**

1. Open `/public/equipment/<id>` for any equipment.
2. Scroll to the "Report a Problem" form.
3. Fill in reporter name and problem description (both required).
4. Set severity to "Down" and check the safety risk flag.
5. Submit the form.
6. Observe the confirmation page.

**Expected Results:**

- Form rejects submission if name or description is blank.
- On success, a confirmation page is shown with links to the relevant area Slack channel and #oops.
- A new repair record is created with status "New," severity "Down," and the safety flag set.
- A Slack notification is posted to the area channel and #oops, with a :warning: indicator for the safety flag.
- The equipment's status on the public dashboard updates to red.

---

## 3. Public Status Dashboard and Kiosk Mode

**Role:** Unauthenticated member

**Steps:**

1. Open `/public/` and verify a color-coded grid of all equipment organized by area.
2. Confirm equipment cards show green, yellow, or red indicators matching their current status.
3. Click an equipment card and verify it navigates to the public equipment page (`/public/equipment/<id>`).
4. Open `/public/kiosk` (or `/public/?kiosk=true`).
5. Confirm the kiosk layout is full-width with large fonts and no navigation chrome.
6. Wait 60+ seconds and verify the page auto-refreshes without a full page reload or visible flicker.

**Expected Results:**

- Dashboard accurately reflects all non-archived equipment grouped by area.
- Kiosk mode auto-refreshes and remains readable at room distance.
- No login prompt on any public page.

---

## 4. Technician — Repair Queue Triage and Record Update

**Role:** Technician (authenticated)

**Steps:**

1. Log in as a Technician user. Verify you land on the repair queue (`/repairs/queue`).
2. Confirm the queue shows columns: Equipment, Severity, Area, Age, Status, Assignee.
3. Verify default sort is severity (Down first), then age (oldest first).
4. Use the Area filter dropdown to filter to a single area; confirm only matching records appear.
5. Click a repair record with status "New" to open its detail page.
6. Self-assign the repair (set assignee to yourself).
7. Change status to "In Progress."
8. Add a diagnostic note (e.g., "Motor brushes worn, needs replacement").
9. Save all changes.

**Expected Results:**

- Queue displays correctly on both desktop (table) and mobile (cards).
- Filtering narrows results to the selected area.
- On the detail page, the append-only timeline shows the status change, assignee change, and note — each with timestamp and author.
- The equipment's public status page reflects the updated repair information.

---

## 5. Technician — Full Repair Lifecycle

**Role:** Technician (authenticated)

**Steps:**

1. Open a repair record currently in "In Progress" status.
2. Change status to "Parts Needed" and add a note identifying the part.
3. Save. Then reopen and change status to "Parts Ordered," set an ETA date.
4. Save. Then reopen and change status to "Parts Received."
5. Save. Then reopen and change status to "Resolved," add a closing note.
6. Verify the complete timeline shows all transitions.

**Expected Results:**

- Each status transition is recorded in the timeline with timestamp and author.
- ETA appears on the public equipment page while the repair is open.
- After resolving, the equipment's derived status returns to green (assuming no other open repairs).
- Slack notifications fire for configured events (severity change, ETA update, resolution).

---

## 6. Staff — Kanban Board and Aging Indicators

**Role:** Staff (authenticated)

**Steps:**

1. Log in as a Staff user. Verify you land on the Kanban board (`/repairs/kanban`).
2. Confirm columns exist for: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist.
3. Verify resolved/closed repairs are not shown on the board.
4. Identify a repair card that has been in its current column for 3+ days — confirm it has a "warm" visual indicator.
5. Identify a repair card in its column for 6+ days — confirm it has a "hot" (urgent) visual indicator.
6. Click a repair card and verify it opens the repair detail page.

**Expected Results:**

- Kanban board accurately reflects all open repairs in their current status columns.
- Aging indicators visually distinguish recent, warm (3-5 days), and hot (6+ days) items.
- On mobile, columns collapse into an accordion layout.

---

## 7. Staff — Equipment and Area Administration

**Role:** Staff (authenticated)

**Steps:**

1. Navigate to `/equipment/new` and create a new piece of equipment with name, area, manufacturer, and model.
2. After creation, navigate to the equipment detail page and verify all fields are shown.
3. Edit the equipment to add a description and documentation link. Save.
4. Navigate to `/admin/areas` and create a new area with a name and Slack channel.
5. Navigate to `/admin/users` and create a new Technician user with a username, email, and Slack handle.
6. Verify the temporary password is delivered via Slack DM.
7. Archive the equipment created in step 1. Verify it no longer appears on the public dashboard.

**Expected Results:**

- Equipment CRUD operations succeed and are reflected on public pages.
- New area appears in area filter dropdowns and equipment forms.
- New user can log in with the temporary password and sees the Technician experience.
- Archived equipment is hidden from active views but its repair history is preserved.

---

## 8. Slack — Status Query and Problem Reporting

**Role:** Any Slack workspace member

**Steps:**

1. In Slack, type `/esb-status` with no arguments. Verify an ephemeral message shows all areas with operational/degraded/down counts.
2. Type `/esb-status SawStop` (or another equipment name). Verify the response includes equipment status, any open issue description, ETA, and assignee.
3. Type `/esb-report`. Verify a modal opens with fields for equipment (dropdown), reporter name, description, severity, safety risk checkbox, and consumable checkbox.
4. Fill in the modal and submit.
5. Verify an ephemeral confirmation message appears.

**Expected Results:**

- `/esb-status` returns accurate, current status information.
- `/esb-report` creates a repair record identical to one submitted via the web form.
- Slack notifications post to the appropriate area channel and #oops.
- The new repair appears in the web repair queue.

---

## 9. Slack — Repair Update via Modal

**Role:** Technician or Staff (with Slack account mapped to ESB user)

**Steps:**

1. Note the ID of an open repair record (e.g., #42).
2. In Slack, type `/esb-update 42`.
3. Verify a modal opens pre-populated with the repair's current status, severity, assignee, and ETA.
4. Change the status to "In Progress," add a note, and assign to yourself.
5. Submit the modal.
6. Open the same repair record in the web UI (`/repairs/42`).

**Expected Results:**

- Modal fields reflect the repair's current state.
- After submission, an ephemeral confirmation appears in Slack.
- The web UI timeline shows the status change, note, and assignee update — attributed to the correct ESB user (mapped from Slack identity).
- Slack notifications fire per configuration.

---

## 10. Authentication and Role-Based Access Control

**Role:** All roles

**Steps:**

1. While logged out, attempt to access `/repairs/queue`. Verify redirect to login page.
2. While logged out, access `/public/` and `/public/equipment/<id>`. Verify no login required.
3. Log in as a Technician. Verify you cannot access `/admin/users` or `/admin/areas` (403 or redirect).
4. Verify the Technician can access `/repairs/queue`, `/repairs/<id>`, and `/equipment/`.
5. Log in as a Staff user. Verify full access to admin pages, Kanban board, equipment management, and repair operations.
6. As Staff, navigate to `/admin/config` and toggle a notification setting (e.g., disable "ETA Updated" notifications). Trigger the event and verify no notification is sent.

**Expected Results:**

- Authenticated routes redirect to login when accessed without a session.
- Public routes are accessible without authentication.
- Technicians are restricted from admin functions but have full repair and equipment view access.
- Staff have unrestricted access to all application features.
- Notification configuration changes take effect immediately.
