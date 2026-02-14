---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics']
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - '_bmad-output/planning-artifacts/ux-design-specification.md'
---

# Equipment Status Board - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for Equipment Status Board, decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

**Equipment Registry (FR1-FR10):**
- FR1: Staff can create equipment records with name, manufacturer, model, and area assignment (required fields)
- FR2: Staff can add optional equipment details including serial number, acquisition date, acquisition source, acquisition cost, warranty expiration, and description
- FR3: Staff can upload documents to equipment records with category labels (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other)
- FR4: Staff can upload photos and videos to equipment records
- FR5: Staff can add external links to equipment records (product page, support, manuals, training materials)
- FR6: Staff can edit all fields on equipment records
- FR7: Staff can archive equipment (soft delete, full history retained)
- FR8: Staff can manage Areas (add, edit, soft delete) with Slack channel mapping
- FR9: Staff can configure whether Technicians have edit rights for equipment documentation (global setting or per-individual)
- FR10: Technicians can edit equipment documentation when granted permission by Staff

**Repair Records (FR11-FR21):**
- FR11: Technicians and Staff can create repair records associated with an equipment item
- FR12: Members can submit problem reports via QR code page or Slack, which create repair records with status "New"
- FR13: Technicians and Staff can update repair record status through the full workflow: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate
- FR14: Technicians and Staff can set severity on repair records (Down, Degraded, Not Sure)
- FR15: Technicians and Staff can append notes to repair records with automatic author and timestamp logging
- FR16: Technicians and Staff can upload photos and videos to repair records
- FR17: Technicians and Staff can set and update an assignee on repair records
- FR18: Technicians and Staff can set and update an ETA on repair records
- FR19: Technicians and Staff can add free-text specialist description when setting status to Needs Specialist
- FR20: The system maintains an append-only audit trail of all changes to repair records
- FR21: The system resolves concurrent edits via last-write-wins with detailed audit trail

**Problem Reporting (FR22-FR26):**
- FR22: Members can report equipment problems via QR code page with required fields (name, description) and optional fields (severity defaulting to "Not Sure", safety risk flag, consumable checkbox, email, photo)
- FR23: Members can report equipment problems via Slack forms with the same field set
- FR24: The QR code equipment page displays existing open issues before the report form, with messaging to report only if the member's issue isn't already listed
- FR25: The system displays a confirmation after problem submission with links to relevant Slack channels (#area and #oops)
- FR26: Members can flag a safety risk on problem reports, which is highlighted in all notifications

**Status Display & Member Access (FR27-FR33):**
- FR27: Anyone can view the in-space kiosk display showing equipment status organized by area with color coding (green/yellow/red) and 60-second auto-refresh
- FR28: The kiosk display can be activated via URL parameter with stripped-down navigation
- FR29: Anyone can view the public static status page showing a summary of all areas and equipment status
- FR30: The system regenerates and pushes the static status page to cloud hosting whenever equipment status changes
- FR31: Anyone can view equipment information pages (manuals, training materials, educational links) via QR code or direct link
- FR32: The system generates QR codes for each equipment item linking to its equipment page
- FR33: "Not Sure" severity displays as yellow (degraded) on all status displays

**Role-Based Experiences (FR34-FR37):**
- FR34: Members see a status dashboard as their default view (two-tier: summary plus drill-down on internal network)
- FR35: Technicians see a sortable and filterable repair queue table as their default landing page (columns: equipment name, severity, area, age, status, assignee)
- FR36: Staff see a read-only Kanban board as their default landing page with columns by status, cards ordered by duration in column, and visual aging indicators
- FR37: Staff can click through from Kanban cards to full repair records

**Slack Integration (FR38-FR44):**
- FR38: The system sends notifications to area-specific Slack channels and #oops for configurable trigger events (defaults: new report, resolved, severity change, ETA update)
- FR39: The system highlights safety risk flags in Slack notifications
- FR40: Members can report equipment problems via Slack App forms
- FR41: Technicians and Staff can create repair records via Slack App with rich forms
- FR42: Technicians and Staff can update repair records via Slack App (status, notes, severity, assignee, ETA)
- FR43: Members can query equipment status via Slack bot
- FR44: Staff can configure notification triggers

**User Management & Authentication (FR45-FR51):**
- FR45: Staff can provision user accounts with username, email, Slack handle, and temporary password
- FR46: The system delivers temporary passwords via Slack message, with fallback to visible display for the account creator
- FR47: Staff can assign and change user roles (Technician/Staff)
- FR48: Staff can reset user passwords
- FR49: Users can change their own password
- FR50: The system authenticates users via local accounts with an abstracted auth layer for future provider integration
- FR51: Authenticated sessions last 12 hours

**System & Operations (FR52-FR55):**
- FR52: The system logs all mutation requests in JSON to STDOUT for data reconstruction
- FR53: The system deploys as a Docker container with MySQL backend
- FR54: The system supports CI/CD via GitHub Actions with locally runnable builds and tests
- FR55: The system includes comprehensive unit tests and Playwright browser tests covering all user flows

### NonFunctional Requirements

**Performance:**
- NFR1: Web UI pages load within standard web application response times (under 3 seconds on local network)
- NFR2: Kiosk display refreshes without visible flicker or layout shift during 60-second polling cycle
- NFR3: Static status page generation and push completes within 30 seconds of a status change event
- NFR4: The system supports concurrent usage by all active users (up to ~600 members, handful of Technicians/Staff) without degradation

**Security:**
- NFR5: Role-based access control enforced server-side -- unauthenticated users cannot access Technician or Staff functionality
- NFR6: Passwords stored using industry-standard hashing (never plaintext or reversible encryption)
- NFR7: Session tokens are not predictable or reusable after expiration
- NFR8: Public-facing pages (QR code pages, kiosk, static page) do not expose internal system details, user credentials, or administrative functionality
- NFR9: No encryption at rest required -- data is not sensitive and the server is on a private local network

**Integration:**
- NFR10: The Slack App integration operates independently from core web UI functionality -- Slack outages do not prevent web-based operations
- NFR11: When Slack is unreachable (API errors, network outage), the system queues outbound notifications for delivery when connectivity is restored
- NFR12: The static page push mechanism handles cloud hosting unavailability gracefully (retry with backoff, log failures)
- NFR13: The Slack App requires a paid Slack plan (Pro or higher)

**Reliability:**
- NFR14: Core application (web UI, database) operates fully on the local network with no internet dependency
- NFR15: The system recovers cleanly from restart (Docker container restart, server reboot) without data loss or corrupted state
- NFR16: All data-mutating operations are logged to STDOUT in sufficient detail to reconstruct data if the database is corrupted or lost
- NFR17: The system does not require high availability infrastructure, monitoring, or on-call support -- "Monday-fix" reliability grade

**Accessibility:**
- NFR18: Follow semantic HTML best practices (proper heading hierarchy, form labels, alt text)
- NFR19: Maintain sufficient color contrast for status indicators (green/yellow/red must be distinguishable; do not rely solely on color)
- NFR20: Support keyboard navigation for all authenticated workflows
- NFR21: No formal WCAG compliance target -- best practices, not certification

### Additional Requirements

**From Architecture:**
- Starter template: Flask 3.1.x with extensions (Flask-SQLAlchemy, Alembic/Flask-Migrate, Flask-Login, Flask-WTF). Project scaffolding is the first implementation step.
- Python 3.14, Gunicorn WSGI server, Docker Compose (app + db containers)
- Service layer pattern: business logic in service modules, shared by web views and Slack handlers. Dependency flow: views/slack -> services -> models.
- Database-backed notification queue (PendingNotification table) with background worker polling every 30 seconds, exponential backoff on failure
- File upload storage: organized local filesystem under configurable UPLOAD_PATH (uploads/equipment/{id}/docs/, uploads/equipment/{id}/photos/, uploads/repairs/{id}/)
- Equipment status is computed (not stored) -- derived from open repair records via a single status_service function
- RBAC decorator pattern: @login_required, @role_required('staff'), @role_required('technician')
- Mutation logging: structured JSON to STDOUT with entity.action naming (e.g., repair_record.created)
- Blueprint-based project organization: equipment, repairs, admin, public, auth
- Error handling: domain exceptions (ESBError hierarchy) caught by views, Flask error handlers for 404/403/500
- Environment configuration: 12-factor style via environment variables (DATABASE_URL, SECRET_KEY, UPLOAD_PATH, SLACK_BOT_TOKEN, etc.)
- Implementation sequence: scaffolding -> models/migrations -> auth -> equipment registry -> repair records -> public surfaces -> notification system -> Slack App -> static page -> QR codes -> user management

**From UX Design:**
- Bootstrap 5 bundled locally (no CDN dependency, aligns with on-premises deployment)
- Custom components: Status Indicator (3 variants: Large, Compact, Minimal), Kanban Board, Repair Timeline, Kiosk Display Grid, QR Code Equipment Page
- Total custom CSS budget: ~140 lines on top of Bootstrap
- Single custom CSS file (app.css) and single custom JS file (app.js)
- Mobile-first for public surfaces (QR pages, problem reporting, status dashboard), desktop-optimized for management (Kanban, equipment registry, user admin)
- Responsive pattern: tables become stacked cards on mobile (<768px breakpoint)
- Kanban aging indicators: 0-2 days (default), 3-5 days (warm tint), 6+ days (stronger indicator)
- Progressive disclosure on QR pages: status -> known issues -> report form -> documentation
- Kiosk mode via URL parameter (?kiosk=true), meta refresh, no nav
- Form patterns: single-column, labels above fields, validate on submit, required fields marked with asterisk
- Button hierarchy: Primary (btn-primary, one per page), Secondary (btn-outline-secondary), Danger (btn-danger with confirmation)
- Empty states defined for all views
- Accessibility: axe-core integration in Playwright tests, WCAG 2.1 AA best practices, status communicated via color + icon + text label
- Navigation: sticky top navbar, role-appropriate links, breadcrumbs on detail pages 2+ levels deep

### FR Coverage Map

- FR1: Epic 2 - Staff can create equipment records
- FR2: Epic 2 - Staff can add optional equipment details
- FR3: Epic 2 - Staff can upload documents with category labels
- FR4: Epic 2 - Staff can upload photos and videos to equipment
- FR5: Epic 2 - Staff can add external links to equipment
- FR6: Epic 2 - Staff can edit all equipment fields
- FR7: Epic 2 - Staff can archive equipment
- FR8: Epic 2 - Staff can manage Areas with Slack channel mapping
- FR9: Epic 2 - Staff can configure Technician edit rights
- FR10: Epic 2 - Technicians can edit documentation when permitted
- FR11: Epic 3 - Technicians and Staff can create repair records
- FR12: Epic 3 - Members can submit problem reports creating repair records (web form implemented in Epic 4, Slack form in Epic 6)
- FR13: Epic 3 - Repair record status workflow (10 statuses)
- FR14: Epic 3 - Set severity on repair records
- FR15: Epic 3 - Append notes with author and timestamp
- FR16: Epic 3 - Upload photos and videos to repair records
- FR17: Epic 3 - Set and update assignee
- FR18: Epic 3 - Set and update ETA
- FR19: Epic 3 - Specialist description on Needs Specialist status
- FR20: Epic 3 - Append-only audit trail
- FR21: Epic 3 - Last-write-wins concurrent edit resolution
- FR22: Epic 4 - Problem reporting via QR code page
- FR23: Epic 6 - Problem reporting via Slack forms
- FR24: Epic 4 - Display existing open issues before report form
- FR25: Epic 4 - Confirmation after submission with Slack channel links
- FR26: Epic 4 - Safety risk flag on problem reports
- FR27: Epic 4 - Kiosk display with color coding and auto-refresh
- FR28: Epic 4 - Kiosk mode via URL parameter
- FR29: Epic 5 - Public static status page
- FR30: Epic 5 - Static page regeneration and push on status change
- FR31: Epic 4 - Equipment information pages via QR code or direct link
- FR32: Epic 4 - QR code generation for equipment pages
- FR33: Epic 4 - "Not Sure" displays as yellow on all status displays
- FR34: Epic 4 - Member status dashboard as default view
- FR35: Epic 3 - Technician repair queue as default landing page
- FR36: Epic 3 - Staff Kanban board as default landing page
- FR37: Epic 3 - Staff click-through from Kanban cards to repair records
- FR38: Epic 6 - Notifications to area-specific Slack channels and #oops
- FR39: Epic 6 - Safety risk highlighting in Slack notifications
- FR40: Epic 6 - Problem reporting via Slack App forms
- FR41: Epic 6 - Create repair records via Slack App
- FR42: Epic 6 - Update repair records via Slack App
- FR43: Epic 6 - Query equipment status via Slack bot
- FR44: Epic 5 - Staff can configure notification triggers
- FR45: Epic 1 - Staff can provision user accounts
- FR46: Epic 1 - Temp password delivery via Slack with fallback
- FR47: Epic 1 - Staff can assign and change user roles
- FR48: Epic 1 - Staff can reset user passwords
- FR49: Epic 1 - Users can change their own password
- FR50: Epic 1 - Local account authentication with abstracted auth layer
- FR51: Epic 1 - 12-hour authenticated sessions
- FR52: Epic 1 - JSON mutation logging to STDOUT
- FR53: Epic 1 - Docker container deployment with MySQL
- FR54: Epic 1 - CI/CD via GitHub Actions
- FR55: Epic 1 - Comprehensive unit tests and Playwright browser tests (cross-cutting, each epic adds tests)

**Cross-cutting NFR mapping:**
- NFR1-NFR4 (Performance): Addressed by architecture choices, validated across all epics
- NFR5-NFR9 (Security): Foundation in Epic 1 (RBAC, password hashing, sessions), enforced in all epics
- NFR10-NFR13 (Integration): Epic 5 (notification queue, static page retry), Epic 6 (Slack independence)
- NFR14-NFR17 (Reliability): Foundation in Epic 1 (Docker, mutation logging, clean restart), cross-cutting
- NFR18-NFR21 (Accessibility): Cross-cutting, every epic's UI follows semantic HTML and accessibility best practices

## Epic List

### Epic 1: Project Foundation, Authentication & User Management
Staff can deploy the system, log in, create and manage user accounts, assign roles, and manage passwords. Core infrastructure (Docker, MySQL, CI/CD, mutation logging, RBAC framework) is in place.
**FRs covered:** FR45-FR51, FR52-FR55

### Epic 2: Equipment Registry & Area Management
Staff can create and manage the complete equipment catalog with documentation, photos, and links, organized by areas with Slack channel mappings. Technicians can edit documentation when permitted.
**FRs covered:** FR1-FR10

### Epic 3: Repair Tracking & Technician Workflow
Technicians and Staff can create, update, and manage repair records through the full 10-status workflow with diagnostic notes, photos, assignees, ETAs, and audit trail. Technicians land on a sortable/filterable repair queue. Staff see a read-only Kanban board with aging indicators.
**FRs covered:** FR11-FR21, FR35-FR37

### Epic 4: Public Status, QR Codes & Problem Reporting
Anyone can check equipment status via the kiosk display and status dashboard. Members scan QR codes for equipment-specific pages with status, documentation, and existing issues. Members can report problems with duplicate awareness and confirmation.
**FRs covered:** FR22, FR24-FR28, FR31-FR34

### Epic 5: Notification System & Static Status Page
Background worker and notification queue operational with retry and backoff. Status changes trigger static page generation and push to cloud hosting. Staff can configure notification triggers.
**FRs covered:** FR29-FR30, FR44

### Epic 6: Slack Integration
Full Slack App: outbound notifications to area channels with safety risk highlighting, inbound problem reports and repair record management via rich forms, and status bot queries.
**FRs covered:** FR23, FR38-FR43
