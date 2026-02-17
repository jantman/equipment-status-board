# Technicians Guide

This guide is for volunteer repair technicians. You'll learn how to work with the repair queue, manage repair records, and use Slack commands to stay on top of repairs from anywhere.

## Getting Started

### Logging In

Navigate to the Equipment Status Board URL in your browser and enter the username and password provided to you by a staff member.

### Changing Your Password

If you received a temporary password, change it after your first login:

1. Click your username in the top-right corner of the navigation bar
2. Select "Change Password"
3. Enter your new password and confirm it

### Your Default View

After logging in, you land directly on the **Repair Queue** — a prioritized list of all open repair records. This is your home base.

## Working with the Repair Queue

The repair queue shows all open repair records in a sortable, filterable table.

### Reading the Queue

Each row shows:

| Column | Description |
|--------|-------------|
| Equipment | Name of the equipment with the issue |
| Severity | Down, Degraded, or Not Sure |
| Area | Which area of the makerspace (e.g., Woodshop) |
| Age | How long since the repair was reported |
| Status | Current repair status (New, In Progress, etc.) |
| Assignee | Who is working on it (if anyone) |

By default, the queue is sorted by severity (Down items first), then by age (oldest first). This puts the most urgent, longest-waiting items at the top.

### Sorting

Click any column header to sort by that column. Click again to reverse the sort order.

### Filtering

Use the dropdown filters at the top of the queue to narrow the list:

- **Area** — Show only repairs for a specific area
- **Status** — Show only repairs in a specific status

### Mobile View

On your phone, the table rows display as stacked cards instead of a table. Each card shows the equipment name, severity, status, area, and age. This makes it easy to browse the queue one-handed while you're at the workbench.

![Repair Queue - Desktop](images/placeholder.png)
<!-- SCREENSHOT: Repair queue table on desktop showing columns for equipment, severity, area, age, status, and assignee -->

![Repair Queue - Mobile](images/placeholder.png)
<!-- SCREENSHOT: Repair queue on mobile showing stacked card layout with equipment name, severity, and status -->

## Managing Repair Records

### Opening a Record

Click or tap any row in the repair queue to open the full repair record.

### Reading the Timeline

Every repair record has a timeline — a chronological history of everything that's happened, with the newest entries at the top. The timeline records:

- Notes added by technicians and staff
- Status changes
- Severity changes
- Assignee changes
- ETA updates
- Uploaded diagnostic photos

Each entry includes who made the change and when. This timeline is the institutional memory of the repair — previous diagnostic notes, parts ordered, things already tried — so you don't duplicate work that's already been done.

### Adding a Note

Type your note in the notes field and click Save. Your name and a timestamp are recorded automatically. Use notes to document:

- What you found during diagnosis
- What you tried and whether it worked
- Parts needed or ordered
- Anything the next person should know

### Uploading Diagnostic Photos

Attach photos from the repair record detail page. Photos appear as thumbnails in the timeline. Useful for documenting damage, part numbers, wiring, or the current state of a repair.

### Changing Status

Select a new status from the status dropdown. See [Understanding the Repair Workflow](#understanding-the-repair-workflow) below for when to use each status.

### Setting Severity

Choose the severity that matches the current state of the equipment:

- **Down** — Equipment cannot be used at all
- **Degraded** — Equipment works but has a problem (e.g., accuracy is off, a feature doesn't work)
- **Not Sure** — You haven't assessed it yet, or the impact is unclear

### Assigning

Pick a technician or staff member from the assignee dropdown, or assign the repair to yourself. Assigning helps the team know who's working on what.

### Setting an ETA

Use the date picker to indicate when you expect the repair to be complete. This is especially helpful for repairs waiting on parts — it tells staff and other technicians when to expect the equipment back.

### Batching Changes

You can make multiple changes at once — update the status, add a note, change the assignee, and set an ETA — all before clicking Save. Everything is saved together in a single action.

![Repair Record Detail](images/placeholder.png)
<!-- SCREENSHOT: Repair record detail page showing timeline entries, status dropdown, notes field, and save button -->

## Creating Repair Records

### Via Web

1. Navigate to Repairs > New in the navigation bar
2. Select the equipment from the dropdown
3. Fill in the description, severity, and any other details
4. Click Save

### Via Slack

Use the `/esb-repair` command in Slack:

1. Type `/esb-repair` in any channel
2. Fill out the form that pops up — select equipment, enter description, set severity
3. Submit

## Using Slack Commands

| Command | What It Does |
|---------|-------------|
| `/esb-report` | Quick problem report — same form as the member QR page report |
| `/esb-status` | Check equipment status — see all areas or a specific item |
| `/esb-repair` | Create a new repair record with full details |
| `/esb-update <id>` | Update an existing repair record — change status, add notes, set severity, assignee, or ETA |

## Viewing Equipment Details

### Equipment Registry

Browse all equipment in the system via the navigation bar. You can view equipment details including:

- Equipment name, manufacturer, model, and area
- Uploaded documents (owner's manuals, service manuals, quick start guides)
- Equipment photos
- External links (product pages, support sites, training materials)

### Editing Documentation

If enabled by staff, you can upload documents, photos, and add links to equipment records. This is useful for adding service manuals, wiring diagrams, or other reference material you find during repairs.

## Understanding the Repair Workflow

Each repair record progresses through a series of statuses. Here's when to use each one:

| Status | When to Use |
|--------|-------------|
| **New** | Just reported, not yet assessed by anyone. This is the starting status for all reports. |
| **Assigned** | Someone has taken responsibility for this repair. Use this when you pick up a repair from the queue. |
| **In Progress** | You are actively working on diagnosing or fixing the issue. |
| **Parts Needed** | Diagnosis is complete and you've identified parts that need to be ordered or sourced. |
| **Parts Ordered** | Parts have been ordered. Add a note with order details and expected delivery. |
| **Parts Received** | Parts are in hand and ready to install. |
| **Needs Specialist** | The repair requires expertise or tools beyond what's currently available. Add a note explaining what's needed. |
| **Resolved** | Repair is complete. The equipment is back to working condition. |
| **Closed - No Issue Found** | You investigated and could not reproduce or find a problem. |
| **Closed - Duplicate** | This issue is already tracked in another repair record. Add a note referencing the other record. |
