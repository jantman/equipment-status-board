---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories']
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

## Epic 1: Project Foundation, Authentication & User Management

Staff can deploy the system, log in, create and manage user accounts, assign roles, and manage passwords. Core infrastructure (Docker, MySQL, CI/CD, mutation logging, RBAC framework) is in place.

### Story 1.1: Project Scaffolding & Docker Deployment

As a developer,
I want the ESB application scaffolded with Flask, Docker, and CI/CD pipeline,
So that the team has a deployable foundation to build features on.

**Acceptance Criteria:**

**Given** a fresh repository checkout
**When** I run `docker-compose up`
**Then** the Flask app container and MySQL container start successfully
**And** the app serves a basic page on localhost

**Given** the Flask app factory
**When** I inspect the project structure
**Then** it follows the Blueprint-based organization defined in the architecture doc (esb/ package with models/, services/, views/, templates/, static/, utils/ directories)

**Given** the Alembic migration setup
**When** I run `flask db upgrade`
**Then** the database schema is initialized (empty, ready for models)

**Given** the GitHub Actions CI pipeline
**When** code is pushed to the repository
**Then** lint, test, and Docker build stages execute

**Given** the Makefile
**When** I run `make test`
**Then** pytest runs the test suite locally

**Given** the mutation logging utility in utils/logging.py
**When** a service function logs a data-changing operation
**Then** structured JSON with timestamp, event, user, and data fields is written to STDOUT

**Given** the domain exception classes in utils/exceptions.py
**When** a service raises ESBError, EquipmentNotFound, RepairRecordNotFound, UnauthorizedAction, or ValidationError
**Then** the exception hierarchy is properly defined and importable

**Given** the base templates (base.html, base_public.html, base_kiosk.html)
**When** I render any page
**Then** Bootstrap 5 CSS and JS are loaded from bundled local files in static/

**Given** the .env.example file
**When** a developer copies it to .env
**Then** all required environment variables (DATABASE_URL, SECRET_KEY, UPLOAD_PATH, etc.) have documented defaults or placeholders

### Story 1.2: User Authentication System

As a Staff member or Technician,
I want to log in with a username and password,
So that I can access role-appropriate functionality securely.

**Acceptance Criteria:**

**Given** the User model exists with username, email, password_hash, role, slack_handle, and is_active fields
**When** Alembic migration is run
**Then** the users table is created in MySQL

**Given** I am on the login page
**When** I submit valid credentials (username + password)
**Then** I am authenticated via Flask-Login and redirected to a placeholder landing page

**Given** I am logged in
**When** I click logout
**Then** my session is terminated and I am redirected to the login page

**Given** my session is older than 12 hours
**When** I make any request
**Then** I am redirected to the login page with my session expired

**Given** I am not authenticated
**When** I try to access any route decorated with @login_required or @role_required
**Then** I am redirected to the login page

**Given** I am authenticated as a Technician
**When** I try to access a route decorated with @role_required('staff')
**Then** I receive a 403 Forbidden error page

**Given** the auth_service module
**When** authentication is performed
**Then** it goes through the auth_service interface (authenticate(username, password) -> User, load_user(user_id) -> User)

**Given** a user's password
**When** it is stored in the database
**Then** it is hashed using Werkzeug's generate_password_hash (never plaintext)

### Story 1.3: User Account Provisioning & Role Management

As a Staff member,
I want to create user accounts and assign roles,
So that Technicians and other Staff can access the system.

**Acceptance Criteria:**

**Given** I am logged in as Staff
**When** I navigate to the User Management page (/admin/users)
**Then** I see a table listing all users with columns for username, email, role, and status

**Given** I am on the User Management page
**When** I click "Add User" and fill in username, email, Slack handle, select a role (Technician or Staff), and submit
**Then** a new user account is created with a system-generated temporary password

**Given** a new user is created and Slack credentials are configured
**When** the account is created
**Then** the system attempts to deliver the temporary password via Slack direct message to the user's Slack handle

**Given** Slack delivery fails or Slack is not configured
**When** the account is created
**Then** the temporary password is displayed on-screen to the creating Staff member with a one-time visibility warning

**Given** I am logged in as Staff
**When** I change a user's role from Technician to Staff (or vice versa) on the User Management page
**Then** the role change is saved immediately and reflected in the user list

**Given** I am logged in as a Technician
**When** I try to access /admin/users
**Then** I receive a 403 Forbidden error

**Given** any user management action (create, role change)
**When** the action is performed
**Then** a mutation log entry is written to STDOUT with the action details

### Story 1.4: Password Management

As a user,
I want to change my own password,
So that I can maintain account security.

**Acceptance Criteria:**

**Given** I am logged in
**When** I navigate to Change Password and provide my current password and a valid new password
**Then** my password is updated and I see a success message

**Given** I am on the Change Password page
**When** I submit an incorrect current password
**Then** I see an error message and my password is not changed

**Given** I am on the Change Password page
**When** I submit with the new password fields not matching
**Then** I see a validation error and my password is not changed

**Given** I am logged in as Staff
**When** I click "Reset Password" for a user on the User Management page
**Then** a new temporary password is generated for that user

**Given** a password is reset by Staff
**When** Slack credentials are configured and the user has a Slack handle
**Then** the new temporary password is delivered via Slack direct message, with fallback to on-screen display

**Given** a password is changed or reset
**When** the action completes
**Then** a mutation log entry is written to STDOUT

## Epic 2: Equipment Registry & Area Management

Staff can create and manage the complete equipment catalog with documentation, photos, and links, organized by areas with Slack channel mappings. Technicians can edit documentation when permitted.

### Story 2.1: Area Management

As a Staff member,
I want to create and manage Areas with Slack channel mappings,
So that equipment can be organized by physical location and notifications routed to the right channels.

**Acceptance Criteria:**

**Given** the Area model exists with name, slack_channel, and is_archived fields
**When** Alembic migration is run
**Then** the areas table is created in MySQL

**Given** I am logged in as Staff
**When** I navigate to Area Management (/admin/areas)
**Then** I see a list of all active areas with their Slack channel mappings

**Given** I am on the Area Management page
**When** I click "Add Area" and fill in name and Slack channel
**Then** a new area is created and appears in the area list

**Given** I am on the Area Management page
**When** I edit an existing area's name or Slack channel mapping
**Then** the changes are saved and reflected in the list

**Given** I am on the Area Management page
**When** I soft-delete an area
**Then** the area is marked as archived and no longer appears in active area lists or dropdowns
**And** existing equipment assigned to that area retains its association for historical records

**Given** any area management action (create, edit, archive)
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

### Story 2.2: Equipment Registry CRUD

As a Staff member,
I want to create and manage equipment records with required and optional details,
So that the makerspace has a complete, organized catalog of all equipment.

**Acceptance Criteria:**

**Given** the Equipment model exists with name, manufacturer, model, area_id (required), and optional fields (serial_number, acquisition_date, acquisition_source, acquisition_cost, warranty_expiration, description, is_archived)
**When** Alembic migration is run
**Then** the equipment table is created with proper foreign key to areas

**Given** I am logged in as Staff
**When** I navigate to the Equipment Registry (/equipment)
**Then** I see a list of all active equipment with name, area, and status columns
**And** I can filter the list by area

**Given** I am on the Equipment Registry page
**When** I click "Add Equipment" and fill in name, manufacturer, model, and select an area
**Then** a new equipment record is created and I am redirected to its detail page

**Given** I am creating equipment
**When** I submit without filling in a required field (name, manufacturer, model, or area)
**Then** I see inline validation errors and the record is not created

**Given** I am on an equipment detail page
**When** I click "Edit" and modify any field (required or optional)
**Then** the changes are saved and I see a success message

**Given** I am on the equipment detail page
**When** I view the equipment record
**Then** I see all populated fields, organized with required fields prominently displayed and optional fields in a details section

**Given** any equipment action (create, edit)
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

### Story 2.3: Equipment Documentation & Media

As a Staff member,
I want to upload documents, photos, and add links to equipment records,
So that members and technicians can find manuals, reference materials, and visual documentation.

**Acceptance Criteria:**

**Given** the Document model exists with fields for original_filename, stored_filename, content_type, size_bytes, category, parent_type, parent_id, uploaded_by, and created_at
**When** Alembic migration is run
**Then** the documents table is created in MySQL

**Given** the upload_service module
**When** a file is uploaded
**Then** it validates file size against UPLOAD_MAX_SIZE_MB, generates a safe filename, saves to the correct directory (uploads/equipment/{id}/docs/ or uploads/equipment/{id}/photos/), and creates a Document record

**Given** I am on an equipment detail page
**When** I upload a document and select a category label (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other)
**Then** the document is saved to the filesystem and appears in the equipment's document list with its category label

**Given** I am on an equipment detail page
**When** I upload a photo or video
**Then** the file is saved to uploads/equipment/{id}/photos/ and appears in the equipment's photo gallery

**Given** I am on an equipment detail page
**When** I add an external link with a title and URL
**Then** the link is saved and appears in the equipment's links section

**Given** I upload a file that exceeds the configured size limit
**When** the upload is processed
**Then** I see a validation error and the file is not saved

**Given** any documentation action (upload, add link)
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

### Story 2.4: Equipment Archiving & Technician Permissions

As a Staff member,
I want to archive equipment and control Technician edit permissions,
So that retired equipment is preserved historically and documentation editing is appropriately managed.

**Acceptance Criteria:**

**Given** I am logged in as Staff and viewing an equipment detail page
**When** I click "Archive" and confirm the action in the confirmation modal
**Then** the equipment is soft-deleted (is_archived = true) and no longer appears in active equipment lists
**And** the equipment's full history (repair records, documents, photos) is retained

**Given** an equipment record is archived
**When** I view the archived record via direct URL
**Then** I see a warning banner indicating the equipment is archived

**Given** I am logged in as Staff
**When** I navigate to App Configuration (/admin/config)
**Then** I can set whether Technicians have edit rights for equipment documentation (global toggle)

**Given** the AppConfig model exists with key-value pairs for runtime settings
**When** Alembic migration is run
**Then** the app_config table is created in MySQL

**Given** Technician edit rights are enabled globally
**When** a Technician views an equipment detail page
**Then** they see edit controls for documents, photos, and links (but not for equipment fields like name, manufacturer, model)

**Given** Technician edit rights are disabled
**When** a Technician views an equipment detail page
**Then** they see documentation in read-only mode with no edit controls

**Given** a Technician with edit rights
**When** they upload a document, photo, or add a link to an equipment record
**Then** the action succeeds and is logged with the Technician's username

**Given** any archiving or permission change action
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

## Epic 3: Repair Tracking & Technician Workflow

Technicians and Staff can create, update, and manage repair records through the full 10-status workflow with diagnostic notes, photos, assignees, ETAs, and audit trail. Technicians land on a sortable/filterable repair queue. Staff see a read-only Kanban board with aging indicators.

### Story 3.1: Repair Record Creation & Data Model

As a Technician or Staff member,
I want to create repair records for equipment,
So that problems are tracked from discovery through resolution.

**Acceptance Criteria:**

**Given** the RepairRecord model exists with fields for equipment_id, status (default "New"), severity, description, reporter_name, reporter_email, assignee_id, eta, specialist_description, has_safety_risk, is_consumable, created_at, updated_at
**When** Alembic migration is run
**Then** the repair_records table is created with proper foreign keys to equipment and users

**Given** the RepairTimelineEntry model exists with fields for repair_record_id, entry_type (note, status_change, assignee_change, eta_update, photo, creation), author_id, content, old_value, new_value, created_at
**When** Alembic migration is run
**Then** the repair_timeline_entries table is created

**Given** the AuditLog model exists with fields for entity_type, entity_id, action, user_id, changes (JSON), created_at
**When** Alembic migration is run
**Then** the audit_log table is created

**Given** I am logged in as a Technician or Staff
**When** I navigate to create a new repair record and select an equipment item, enter a description, and submit
**Then** a repair record is created with status "New" and a creation entry is added to the timeline

**Given** a repair record is created
**When** I view the repair record detail page (/repairs/{id})
**Then** I see the equipment name, status, severity, description, and the timeline with the creation entry

**Given** a repair record is created
**When** the service layer processes the creation
**Then** an audit log entry is written and a mutation log is emitted to STDOUT

### Story 3.2: Repair Record Workflow & Updates

As a Technician or Staff member,
I want to update repair records through the full workflow with severity, assignee, and ETA,
So that repairs are tracked accurately and coordinated efficiently.

**Acceptance Criteria:**

**Given** I am viewing a repair record detail page
**When** I change the status using the status dropdown
**Then** I can select any of the 10 statuses: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate
**And** the status transition is not enforced sequentially (any-to-any allowed)

**Given** I change a repair record's status
**When** I save the changes
**Then** a status_change entry is added to the timeline showing old and new status
**And** an audit log entry is created

**Given** I set the status to "Needs Specialist"
**When** I save the changes
**Then** a free-text specialist description field is available and its value is saved with the record

**Given** I am viewing a repair record
**When** I set or change the severity (Down, Degraded, Not Sure)
**Then** the severity is updated and reflected in the record display

**Given** I am viewing a repair record
**When** I set or update the assignee by selecting a Technician or Staff user from a dropdown
**Then** an assignee_change entry is added to the timeline

**Given** I am viewing a repair record
**When** I set or update the ETA using a date picker
**Then** an eta_update entry is added to the timeline

**Given** I make multiple changes (status + note + assignee) on a repair record
**When** I click Save once
**Then** all changes are saved together and individual timeline entries are created for each change type

**Given** two users edit the same repair record concurrently
**When** both submit their changes
**Then** the last write wins and the audit trail captures both sets of changes with timestamps and authors

**Given** any repair record update
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

### Story 3.3: Repair Timeline, Notes & Photos

As a Technician or Staff member,
I want to add diagnostic notes and photos to repair records,
So that the next person has full context and no effort is duplicated.

**Acceptance Criteria:**

**Given** I am viewing a repair record detail page
**When** I type a note in the text area and click Save
**Then** a note entry is added to the timeline with my username and the current timestamp

**Given** I am viewing a repair record detail page
**When** I upload a diagnostic photo or video
**Then** the file is saved to uploads/repairs/{id}/ and a photo entry is added to the timeline with a thumbnail

**Given** the repair record timeline
**When** I view the timeline
**Then** entries are displayed chronologically (newest first) with entry type icons, author name, timestamp, and content

**Given** a timeline entry of type status_change
**When** I view it
**Then** it displays "Status changed from [Old] to [New]" with status badges

**Given** a timeline entry of type assignee_change
**When** I view it
**Then** it displays "Assigned to [name]" or "Unassigned"

**Given** a timeline photo entry
**When** I click the thumbnail
**Then** the photo expands to full size

**Given** I am viewing the timeline on mobile
**When** timestamps are displayed
**Then** they use relative format ("2 hours ago") instead of absolute format

**Given** the timeline
**When** any entry is added
**Then** the timeline is append-only -- no entries can be edited or deleted

### Story 3.4: Technician Repair Queue

As a Technician,
I want to see a sortable and filterable repair queue as my default landing page,
So that I can quickly find the highest-impact repair to work on.

**Acceptance Criteria:**

**Given** I am logged in as a Technician
**When** I am redirected after login
**Then** I land on the repair queue page (/repairs/queue)

**Given** I am on the repair queue page
**When** the page loads
**Then** I see a table with columns: equipment name, severity, area, age (time since creation), status, and assignee
**And** the default sort is by severity (Down first) then age (oldest first)

**Given** I am on the repair queue page
**When** I click a column header
**Then** the table sorts by that column (toggle ascending/descending)

**Given** I am on the repair queue page
**When** I select an area from the filter dropdown
**Then** the table shows only repair records for equipment in that area

**Given** I am on the repair queue page
**When** I select a status from the filter dropdown
**Then** the table shows only repair records with that status

**Given** severity is displayed in the table
**When** I view a row
**Then** severity is indicated with a color-coded visual indicator (red for Down, yellow for Degraded/Not Sure)

**Given** I am on the repair queue page on a mobile device (viewport < 768px)
**When** the page renders
**Then** table rows are displayed as stacked cards showing equipment name, severity, status, area, and age
**And** there is no horizontal scrolling

**Given** I am on the repair queue page
**When** I click/tap a row or card
**Then** I navigate to the repair record detail page

**Given** there are no open repair records
**When** the page loads
**Then** I see a centered message: "No open repair records. All equipment is operational."

### Story 3.5: Staff Kanban Board

As a Staff member,
I want to see a Kanban board of all open repairs as my default landing page,
So that I can instantly identify what's stuck and needs my attention.

**Acceptance Criteria:**

**Given** I am logged in as Staff
**When** I am redirected after login
**Then** I land on the Kanban board page (/repairs/kanban)

**Given** I am on the Kanban board
**When** the page loads
**Then** I see columns for: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist
**And** Resolved and Closed statuses are excluded from the Kanban

**Given** a Kanban column
**When** it contains cards
**Then** cards are ordered by time-in-column (oldest at top)
**And** each card shows: equipment name, area badge, severity indicator (compact), time-in-column text

**Given** the column header
**When** I view it
**Then** it shows the status name and count of cards in that column

**Given** a card has been in its current column for 0-2 days
**When** I view it
**Then** it has default card styling

**Given** a card has been in its current column for 3-5 days
**When** I view it
**Then** it has a subtle warm background tint indicating it may need attention

**Given** a card has been in its current column for 6+ days
**When** I view it
**Then** it has a stronger visual indicator (darker accent border or background) signaling it is stuck

**Given** I am on the Kanban board
**When** I click a card
**Then** I navigate to the full repair record detail page (new page, not modal)

**Given** I am on the Kanban board
**When** I try to drag a card
**Then** nothing happens -- the board is read-only (no drag-and-drop)

**Given** I am on the Kanban board on desktop (viewport >= 992px)
**When** the page renders
**Then** columns are displayed horizontally with horizontal scrolling if needed, each column ~250px wide

**Given** I am on the Kanban board on mobile (viewport < 992px)
**When** the page renders
**Then** columns stack vertically as collapsible accordion sections

**Given** there are no open repair records
**When** the page loads
**Then** empty columns with headers are visible and a centered message reads: "No open repair records. All equipment is operational."

**Given** Kanban column regions
**When** accessed via keyboard or screen reader
**Then** each column is an ARIA-labeled region and cards are focusable and activatable via Enter key

## Epic 4: Public Status, QR Codes & Problem Reporting

Anyone can check equipment status via the kiosk display and status dashboard. Members scan QR codes for equipment-specific pages with status, documentation, and existing issues. Members can report problems with duplicate awareness and confirmation.

### Story 4.1: Equipment Status Derivation & Status Dashboard

As a member,
I want to see a color-coded status dashboard of all equipment organized by area,
So that I can quickly check whether the equipment I need is operational before visiting the space.

**Acceptance Criteria:**

**Given** the status_service module with a compute_equipment_status function
**When** it is called for an equipment item
**Then** it returns green (operational) if no open repair records exist, yellow (degraded) if the highest severity among open records is "Degraded" or "Not Sure", and red (down) if any open record has severity "Down"

**Given** the status_service module
**When** it computes status
**Then** it is the single source of truth called by all surfaces (dashboard, kiosk, QR pages, static page, Slack)

**Given** a repair record with severity "Not Sure"
**When** status is derived for that equipment
**Then** it displays as yellow/degraded on all status displays

**Given** I am logged in as a member (or any authenticated user)
**When** I navigate to the Status Dashboard
**Then** I see all areas with their equipment listed in a color-coded grid (green/yellow/red)

**Given** the status dashboard
**When** I view an equipment item that is yellow or red
**Then** I see the equipment name, status color, and a brief description of the current issue

**Given** the status dashboard on mobile
**When** the page renders
**Then** the area grid displays as 1 column on phone, expanding to 2-3 on tablet and 4+ on desktop

**Given** the Status Indicator component
**When** it is rendered
**Then** it displays color + icon (checkmark/warning triangle/X-circle) + text label ("Operational"/"Degraded"/"Down")
**And** it never relies on color alone for status communication

**Given** the Status Indicator component
**When** used across different views
**Then** it supports three variants: Large (QR page hero), Compact (table cells, Kanban cards, kiosk grid), Minimal (static page)

### Story 4.2: Kiosk Display

As a makerspace visitor,
I want to glance at a large-screen display and see which equipment is operational,
So that I know what's available without checking my phone or asking anyone.

**Acceptance Criteria:**

**Given** I navigate to the status page with ?kiosk=true parameter
**When** the page loads
**Then** I see a full-width display of all equipment organized by area with no navbar, no footer, and no navigation controls

**Given** the kiosk display
**When** it renders
**Then** equipment names and area headings use large font sizes for room-distance readability (equipment names ~1.5-2rem, area headings ~2.5rem)

**Given** the kiosk display
**When** an equipment item is degraded or down
**Then** a brief issue description is shown below the equipment name

**Given** the kiosk display template (base_kiosk.html)
**When** it renders
**Then** it includes a `<meta http-equiv="refresh" content="60">` tag for auto-refresh every 60 seconds

**Given** the kiosk display refreshes
**When** the page reloads
**Then** there is no visible flicker or layout shift (content loads quickly on LAN)

**Given** the kiosk display
**When** viewed on a large screen (>= 1400px)
**Then** the equipment card grid auto-fills to maximum column density

**Given** the kiosk display
**When** status indicators are shown
**Then** they use the Compact variant with color, icon, and text label

### Story 4.3: QR Code Equipment Pages & Documentation

As a member,
I want to scan a QR code on a piece of equipment and immediately see its status and documentation,
So that I get instant, machine-specific information without navigating or logging in.

**Acceptance Criteria:**

**Given** the qr_service module
**When** QR code generation is triggered for an equipment item
**Then** a QR code image (PNG or SVG) is generated linking to the equipment's public page URL on the local network
**And** the image is saved to static/qrcodes/

**Given** I scan a QR code on a piece of equipment
**When** my phone browser opens the equipment page (/public/equipment/{id})
**Then** the page loads without requiring authentication

**Given** the QR code equipment page
**When** it loads
**Then** I see immediately above the fold: equipment name and area (h1-level), and a Large status indicator (green/yellow/red with icon and text)

**Given** the equipment is degraded or down
**When** I view the QR page
**Then** I see a brief description of the current issue and ETA if available, directly below the status indicator

**Given** the QR code equipment page
**When** I tap the "Equipment Info" link
**Then** I navigate to a documentation page showing all uploaded manuals, training materials, and external links for that equipment

**Given** the equipment documentation page (/public/equipment/{id}/info)
**When** I view it
**Then** I see documents organized by category label, photos, and external links
**And** documents are downloadable and links open in new tabs

**Given** the QR code equipment page
**When** viewed on a mobile phone (375px viewport)
**Then** the page is single-column, optimized for mobile-first, with no horizontal scrolling
**And** all tap targets are minimum 44x44px

### Story 4.4: Problem Reporting via QR Code Page

As a member,
I want to report an equipment problem from the QR code page in under 90 seconds,
So that issues get tracked and fixed without me needing to figure out who to tell.

**Acceptance Criteria:**

**Given** I am on a QR code equipment page
**When** there are open repair records for this equipment
**Then** a "Known Issues" section is displayed below the Equipment Info link, showing each open issue with severity and description
**And** messaging reads: "If your issue is listed below, it's already being worked on"

**Given** there are no open repair records
**When** I view the QR code equipment page
**Then** the "Known Issues" section is hidden entirely (not shown as empty)

**Given** I am on a QR code equipment page
**When** I scroll below the Known Issues section (or below the Equipment Info link if no issues exist)
**Then** I see a "Report a Problem" form

**Given** the problem report form
**When** I view it
**Then** I see required fields: name and description
**And** optional fields: severity (dropdown, defaults to "Not Sure"), safety risk flag (checkbox), consumable checkbox, email, and photo upload
**And** a large, full-width submit button

**Given** I fill in name and description and tap Submit
**When** validation passes
**Then** a repair record is created with status "New" and the submitted details
**And** a confirmation page is displayed

**Given** I submit without filling in the name or description
**When** validation runs
**Then** inline error messages appear next to the missing required fields and the form is not submitted

**Given** I check the safety risk flag
**When** the repair record is created
**Then** the has_safety_risk field is set to true on the repair record

**Given** the confirmation page
**When** it is displayed after successful submission
**Then** it shows a confirmation message and links to the relevant Slack channels (#area-channel and #oops)
**And** a "Report another issue" link is available

**Given** I upload a photo with my problem report
**When** the form is submitted
**Then** the photo is saved to uploads/repairs/{id}/ and attached to the repair record

**Given** the problem report form
**When** viewed on mobile
**Then** form fields are full-width, the submit button is full-width with minimum 48px height, and the photo upload triggers the native camera/gallery picker

## Epic 5: Notification System & Static Status Page

Background worker and notification queue operational with retry and backoff. Status changes trigger static page generation and push to cloud hosting. Staff can configure notification triggers.

### Story 5.1: Notification Queue & Background Worker

As a system administrator,
I want a reliable notification queue with background processing,
So that outbound notifications and static page pushes are delivered even when external services are temporarily unavailable.

**Acceptance Criteria:**

**Given** the PendingNotification model exists with fields for notification_type (slack_message, static_page_push), target (channel or push destination), payload (JSON), status (pending, delivered, failed), created_at, next_retry_at, retry_count, delivered_at, error_message
**When** Alembic migration is run
**Then** the pending_notifications table is created in MySQL

**Given** the notification_service module
**When** a service function calls notification_service.queue_notification(type, target, payload)
**Then** a new row is inserted into pending_notifications with status "pending"

**Given** the background worker process
**When** it starts via `flask worker run` CLI command
**Then** it runs within the Flask app context with access to the database and all services

**Given** the background worker is running
**When** it polls the pending_notifications table every 30 seconds
**Then** it picks up all rows where status is "pending" and next_retry_at is null or in the past

**Given** a pending notification is processed successfully
**When** the delivery completes
**Then** the row is updated to status "delivered" with delivered_at timestamp

**Given** a pending notification fails to deliver
**When** the delivery attempt errors
**Then** the row's retry_count is incremented, error_message is recorded, and next_retry_at is set with exponential backoff (30s, 1m, 2m, 5m, 15m, max 1h)

**Given** the background worker
**When** it processes jobs
**Then** all delivery attempts and failures are logged to STDOUT

**Given** the Docker Compose configuration
**When** `docker-compose up` is run
**Then** the worker runs as a separate container (same image, different entrypoint) alongside the app and db containers

**Given** the system restarts (container restart, server reboot)
**When** the worker starts up
**Then** it resumes processing any pending notifications that were not delivered before the restart

### Story 5.2: Static Status Page Generation & Push

As a remote member,
I want to view an up-to-date static status page online,
So that I can check equipment status without being on the makerspace local network.

**Acceptance Criteria:**

**Given** the static_page_service module
**When** it is called to generate the static page
**Then** it renders the static_page.html Jinja2 template with current status data for all areas and equipment into a standalone HTML file

**Given** the static status page
**When** it is rendered
**Then** it shows a summary of all areas with equipment names and status indicators (Minimal variant: color dot + equipment name)
**And** it is a self-contained HTML file with no external dependencies (CSS inlined or bundled)

**Given** an equipment status changes (repair record created, status updated, severity changed, repair resolved)
**When** the status_service detects the change
**Then** the service layer inserts a static_page_push job into the PendingNotification table

**Given** the background worker picks up a static_page_push job
**When** it processes the job
**Then** it calls static_page_service to render the template and push the file via the configured method

**Given** STATIC_PAGE_PUSH_METHOD is set to "local"
**When** the static page is pushed
**Then** the rendered HTML file is written to the directory specified by STATIC_PAGE_PUSH_TARGET

**Given** STATIC_PAGE_PUSH_METHOD is set to "s3"
**When** the static page is pushed
**Then** the rendered HTML file is uploaded to the S3 bucket/path specified by STATIC_PAGE_PUSH_TARGET

**Given** the static page push fails (network error, permission denied, service unavailable)
**When** the delivery attempt errors
**Then** the notification queue retries with exponential backoff per Story 5.1's retry logic

**Given** the static page generation and push
**When** triggered by a status change
**Then** the entire process completes within 30 seconds under normal conditions

### Story 5.3: Notification Trigger Configuration

As a Staff member,
I want to configure which events trigger notifications,
So that the team gets notified about important changes without being overwhelmed by noise.

**Acceptance Criteria:**

**Given** I am logged in as Staff
**When** I navigate to App Configuration (/admin/config)
**Then** I see a "Notification Triggers" section with toggles for each trigger event type

**Given** the notification trigger settings
**When** I view them
**Then** the available trigger types are: new_report, resolved, severity_changed, eta_updated
**And** all four are enabled by default

**Given** I toggle a notification trigger off (e.g., disable eta_updated)
**When** I save the configuration
**Then** the setting is stored in the AppConfig table

**Given** a trigger event occurs (e.g., a new problem report is submitted)
**When** the service layer processes the event
**Then** it checks the AppConfig trigger settings before queuing any notification
**And** if the trigger type is disabled, no notification is queued

**Given** a trigger event occurs and the trigger type is enabled
**When** the service layer processes the event
**Then** a notification is queued in PendingNotification for future delivery (Slack delivery implemented in Epic 6)

**Given** the notification trigger configuration
**When** I change settings
**Then** the changes take effect immediately for subsequent events without requiring a restart

**Given** any configuration change
**When** the action is performed
**Then** a mutation log entry is written to STDOUT

## Epic 6: Slack Integration

Full Slack App: outbound notifications to area channels with safety risk highlighting, inbound problem reports and repair record management via rich forms, and status bot queries.

### Story 6.1: Slack App Setup & Outbound Notifications

As a makerspace community member,
I want equipment status changes and new problem reports posted to the relevant Slack channels,
So that the community stays informed without checking the web app.

**Acceptance Criteria:**

**Given** the esb/slack/ module with slack_bolt and Flask adapter
**When** the app starts with SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET configured
**Then** the Slack App initializes and registers event handlers at the /slack/events endpoint

**Given** SLACK_BOT_TOKEN is not configured (empty or missing)
**When** the app starts
**Then** the Slack module is not loaded and the core web application functions normally without any Slack-related errors

**Given** the Slack App is initialized
**When** incoming requests arrive at /slack/events
**Then** they are validated using the Slack signing secret before processing

**Given** a notification is queued with type "slack_message"
**When** the background worker processes it
**Then** it sends the message to the target Slack channel via the Slack WebClient API

**Given** a new problem report is created and the "new_report" trigger is enabled
**When** the notification is delivered to Slack
**Then** the message is posted to the equipment's area-specific Slack channel AND to #oops
**And** the message includes: equipment name, area, severity, description, and reporter name

**Given** a repair record is resolved and the "resolved" trigger is enabled
**When** the notification is delivered to Slack
**Then** the message is posted to the area channel and #oops indicating the equipment is back in service

**Given** a severity change occurs and the "severity_changed" trigger is enabled
**When** the notification is delivered to Slack
**Then** the message is posted with old and new severity levels

**Given** an ETA is set or updated and the "eta_updated" trigger is enabled
**When** the notification is delivered to Slack
**Then** the message includes the new ETA date

**Given** a problem report or notification has the safety risk flag set
**When** the Slack message is composed
**Then** the safety risk is prominently highlighted in the message (bold text, warning emoji, or distinct formatting)

**Given** the Slack API is unreachable
**When** the background worker attempts delivery
**Then** the notification remains in the queue and retries with exponential backoff per the notification queue logic in Epic 5

### Story 6.2: Problem Reporting & Repair Records via Slack

As a member,
I want to report equipment problems directly from Slack,
So that I can flag issues without leaving the conversation I'm already in.

**Acceptance Criteria:**

**Given** the Slack App is installed in the workspace
**When** a member uses the problem report slash command (e.g., /esb-report)
**Then** a Slack modal opens with fields matching the web form: equipment selector, name, description (required), severity (defaults to "Not Sure"), safety risk flag, consumable checkbox

**Given** a member fills out the Slack problem report modal and submits
**When** the submission is processed
**Then** the Slack handler calls repair_service.create_repair_record() -- the same service function used by the web form
**And** a repair record is created with status "New"
**And** a confirmation message is posted to the member in the channel or as an ephemeral message

**Given** a Technician or Staff member uses a repair record creation command (e.g., /esb-repair)
**When** the slash command is invoked
**Then** a Slack modal opens with rich form fields: equipment selector, description, severity, assignee, status

**Given** a Technician or Staff member submits a repair record creation modal
**When** the submission is processed
**Then** the Slack handler calls the same repair_service functions as the web UI
**And** the repair record is created with all provided details

**Given** a Technician or Staff member wants to update an existing repair record from Slack
**When** they use an update command (e.g., /esb-update [repair-id])
**Then** a Slack modal opens pre-populated with the current record data and editable fields: status, notes, severity, assignee, ETA

**Given** a repair record update is submitted via Slack
**When** the submission is processed
**Then** the Slack handler calls repair_service.update_repair_record() with the changes
**And** timeline entries are created for each change, with the Slack user identified as the author

**Given** a Slack handler encounters a service layer error (EquipmentNotFound, ValidationError, etc.)
**When** the error is caught
**Then** a Slack-formatted error message is returned to the user (not a web HTML error page)

### Story 6.3: Slack Status Bot

As a member,
I want to ask a Slack bot about equipment status,
So that I can get a quick answer without leaving Slack or opening a browser.

**Acceptance Criteria:**

**Given** the Slack App is installed
**When** a member uses the status query command (e.g., /esb-status)
**Then** the bot responds with a summary of all areas showing equipment counts by status (e.g., "Woodshop: 5 operational, 1 degraded, 0 down")

**Given** a member uses the status query command with an equipment name (e.g., /esb-status SawStop)
**When** the command is processed
**Then** the bot responds with that specific equipment's status, current issue description if not green, and ETA if available

**Given** a member queries for an equipment name that doesn't exist
**When** the command is processed
**Then** the bot responds with "Equipment not found" and suggests checking the spelling or using the full name

**Given** a member queries for an equipment name that matches multiple items
**When** the command is processed
**Then** the bot responds with a list of matching equipment items and asks the member to be more specific

**Given** the status bot query
**When** it computes equipment status
**Then** it calls status_service.compute_equipment_status() -- the same single source of truth used by all other surfaces

**Given** the Slack App is not configured (no token)
**When** a member tries to use a slash command
**Then** Slack shows its own "app not installed" behavior -- the ESB web app is unaffected
