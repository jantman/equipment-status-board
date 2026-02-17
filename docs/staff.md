# Staff Guide

This guide is for makerspace managers with the Staff role. You have full access to the Equipment Status Board, including equipment management, user administration, and system configuration. This guide focuses on the capabilities unique to staff — for repair record management, see the [Technicians Guide](technicians.md), which also applies to you.

## Getting Started

### Logging In

Navigate to the Equipment Status Board URL and log in with your username and password. After logging in, you land on the **Kanban Board** — your primary tool for monitoring repair activity.

### Navigation

The navigation bar gives you access to all areas of the system:

| Link | What It Shows |
|------|--------------|
| Kanban | Kanban board overview of all open repairs |
| Repair Queue | Sortable/filterable repair table (same view as Technicians) |
| Equipment | Equipment registry — browse, add, edit equipment |
| Users | User management — add, edit, manage accounts |
| Status | Status dashboard — color-coded equipment grid |

## Using the Kanban Board

The Kanban board gives you an at-a-glance view of all active repairs organized by status. It's designed to answer one question immediately: **what's stuck?**

### Reading the Board

Each column represents a repair status:

- **New** — Reported but not yet assessed
- **Assigned** — Someone has taken responsibility
- **In Progress** — Actively being worked on
- **Parts Needed** — Waiting for parts to be identified or ordered
- **Parts Ordered** — Parts ordered, waiting for delivery
- **Parts Received** — Parts in hand, ready to install
- **Needs Specialist** — Requires expertise beyond current technicians

Resolved and Closed repairs are not shown on the Kanban board — only active repairs appear.

### Card Information

Each card on the board shows:

- Equipment name
- Area (e.g., Woodshop)
- Severity indicator (color-coded)
- Time in current column

Cards within each column are ordered by time-in-column, with the oldest at the top.

### Aging Indicators

The Kanban board uses visual aging indicators so you can spot stuck items without reading details:

| Age in Column | Visual Treatment |
|---------------|-----------------|
| 0-2 days | Default styling — normal |
| 3-5 days | Warm tint — starting to age |
| 6+ days | Strong indicator — needs attention |

If a card has a strong aging indicator, it has been sitting in that status for too long and likely needs intervention — a follow-up with the assigned technician, a parts order, or escalation.

### Taking Action

The Kanban board is a read-only overview. To take action on a repair, click a card to open the full repair record, then make changes there (update status, add notes, reassign, etc.).

### Desktop vs. Mobile

On desktop, columns are displayed side by side with horizontal scrolling if needed. On mobile, columns are stacked vertically as collapsible sections.

![Kanban Board](images/placeholder.png)
<!-- SCREENSHOT: Kanban board showing columns for each repair status with cards displaying equipment name, area, severity, and aging indicators -->

## Managing Equipment

### Viewing the Registry

Click **Equipment** in the navigation bar to see all equipment in the system. Use the area filter to narrow the list.

### Creating Equipment

1. Click the **Add Equipment** button
2. Fill in:
    - **Name** (required) — e.g., "SawStop #1"
    - **Manufacturer** — e.g., "SawStop"
    - **Model** — e.g., "PCS175"
    - **Area** (required) — select the area where the equipment is located
3. Click Save

### Editing Equipment

1. Click on a piece of equipment to open its detail page
2. Click the **Edit** button
3. Update any fields as needed
4. Click Save

### Adding Documentation

From the equipment detail page, you can upload and manage reference materials:

- **Documents** — Upload manuals, guides, and reference PDFs with category labels:
    - Owner's Manual
    - Service Manual
    - Quick Start Guide
    - Training Video
    - Safety Data Sheet
    - Other
- **Photos** — Upload equipment photos for identification
- **Links** — Add external URLs for product pages, support sites, training videos, and other online resources

### Archiving Equipment

When a piece of equipment is retired or removed from the space, archive it instead of deleting it. Archiving is a soft delete that preserves all history (repair records, documents, photos) while removing the equipment from active views.

![Equipment Detail Page](images/placeholder.png)
<!-- SCREENSHOT: Equipment detail page showing name, manufacturer, model, area, documents list, photos, and links sections -->

## Managing Areas

Navigate to **Admin > Areas** to manage the areas (rooms/zones) of the makerspace.

### Creating Areas

1. Click **Add Area**
2. Enter the area **name** (e.g., "Woodshop")
3. Set the **Slack channel** for repair notifications for this area (e.g., `#woodshop-repairs`)
4. Click Save

### Editing Areas

Click an area to change its name or Slack channel mapping.

### Archiving Areas

Archive an area to remove it from active views. Existing equipment retains its area association for historical reference.

## Managing Users

Navigate to **Admin > Users** to manage technician and staff accounts.

### User List

The user list shows:

- Username
- Email
- Role (Technician or Staff)
- Status (Active or Inactive)

### Creating Users

1. Click **Add User**
2. Fill in:
    - **Username** (required)
    - **Email** (required)
    - **Slack handle** — For Slack DM notifications
    - **Role** — Technician or Staff
3. Click Save

The system generates a temporary password. If the user has a Slack handle configured and the Slack integration is active, the temporary password is sent via Slack DM. Otherwise, it is displayed on screen one time — copy it and deliver it to the user securely.

### Changing Roles

Change a user between Technician and Staff roles directly from the user list.

### Resetting Passwords

Generate a new temporary password for a user. The password is delivered via the same mechanism as initial creation (Slack DM if available, otherwise displayed on screen).

![User Management](images/placeholder.png)
<!-- SCREENSHOT: User management page showing user list with username, email, role, and status columns, plus Add User button -->

## Configuring the System

Navigate to **Admin > Config** to adjust system-wide settings.

### Technician Documentation Editing

Toggle whether Technicians can edit equipment documentation (upload documents, photos, and add links). When disabled, only Staff can manage equipment documentation.

### Notification Triggers

Enable or disable which events trigger Slack notifications:

| Setting | When It Fires |
|---------|--------------|
| New Report | A member reports a problem via QR page or Slack |
| Resolved | A repair is marked as Resolved |
| Severity Changed | The severity level of a repair changes |
| ETA Updated | An ETA is set or changed on a repair |

Notifications are sent to the area's configured Slack channel and to the `#oops` channel (configurable via the `SLACK_OOPS_CHANNEL` environment variable).

![App Configuration](images/placeholder.png)
<!-- SCREENSHOT: App configuration page showing toggles for technician doc editing and notification triggers -->

## Working with Repairs

Staff have full access to the Repair Queue (accessible via the **Repair Queue** link in the navigation bar). All repair record management capabilities described in the [Technicians Guide](technicians.md) apply to you as well — viewing the queue, managing records, adding notes, changing status, assigning, and using Slack commands.

## Understanding Status

### Status Dashboard

Click **Status** in the navigation bar to see the color-coded equipment grid organized by area. This is the same view that members see — useful for quickly checking the overall health of the space.

### Static Status Page

The static status page is an externally hosted lightweight version of the status dashboard. It is automatically regenerated and pushed whenever equipment status changes. This allows members to check status from outside the makerspace network. Configuration of the static page push method is handled by an administrator via environment variables.
