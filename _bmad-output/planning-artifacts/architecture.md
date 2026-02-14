---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
inputDocuments:
  - '_bmad-output/planning-artifacts/prd.md'
  - '_bmad-output/planning-artifacts/ux-design-specification.md'
  - '_bmad-output/planning-artifacts/product-brief-equipment-status-board-2026-02-08.md'
  - 'docs/original_requirements_doc.md'
workflowType: 'architecture'
project_name: 'equipment-status-board'
user_name: 'Jantman'
date: '2026-02-14'
lastStep: 8
status: 'complete'
completedAt: '2026-02-14'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements:**

55 core functional requirements (FR1-FR55) across 8 categories, plus 16 stretch goals (FR56-FR71):

| Category | FRs | Architectural Significance |
|----------|-----|---------------------------|
| Equipment Registry | FR1-FR10 | Core CRUD entity with document/photo attachments, area relationships, and permission-gated editing |
| Repair Records | FR11-FR21 | 10-status workflow state machine, append-only audit trail, last-write-wins concurrency, photo/video uploads |
| Problem Reporting | FR22-FR26 | Unauthenticated form submission (QR pages + Slack), creates repair records, triggers notifications |
| Status Display & Member Access | FR27-FR33 | Multi-surface read-only views: kiosk (polling), static page (event-driven push), QR pages (on-demand) |
| Role-Based Experiences | FR34-FR37 | Three distinct default landing pages; role determines UI surface, not just permissions |
| Slack Integration | FR38-FR44 | Full Slack App: outbound notifications (configurable triggers), inbound forms (reports, records), status bot |
| User Management & Auth | FR45-FR51 | Local accounts with abstracted auth layer; role assignment; 12-hour sessions; temp password delivery via Slack |
| System & Operations | FR52-FR55 | JSON mutation logging to STDOUT; Docker/MySQL deployment; GitHub Actions CI/CD; unit + Playwright tests |

**Stretch goals (data model accommodated, UI deferred):** Parts inventory (FR56-FR60), Technician-Area assignment (FR61-FR63), consumable workflow (FR64), notification preferences (FR65-FR66), auth providers (FR67-FR68), reporting/analytics (FR69-FR71).

**Non-Functional Requirements:**

| Category | NFRs | Architectural Impact |
|----------|------|---------------------|
| Performance | NFR1-NFR4 | Page load <3s on LAN; kiosk refresh without flicker; static page push <30s; support ~600 concurrent users |
| Security | NFR5-NFR9 | Server-side RBAC enforcement; hashed passwords; secure sessions; no encryption at rest needed |
| Integration | NFR10-NFR13 | Slack independence from core; notification queuing on Slack outage; static page retry with backoff |
| Reliability | NFR14-NFR17 | Local network operation; clean restart recovery; mutation logging for data reconstruction; no HA required |
| Accessibility | NFR18-NFR21 | Semantic HTML; color contrast; keyboard navigation; best practices, not certification |

**Scale & Complexity:**

- Primary domain: Full-stack server-rendered web application (Python + MySQL + Docker)
- Complexity level: Medium
- Estimated architectural components: ~12-15 (web framework, ORM/data layer, auth module, repair workflow engine, file upload handler, QR code generator, static page generator, Slack App client, notification queue, template rendering, kiosk view, admin views, API layer for Slack)

### Technical Constraints & Dependencies

**Hard constraints from PRD and stakeholder requirements:**
- Python backend (framework TBD -- this is an architecture decision)
- MySQL database
- Docker container deployment on local servers within the makerspace
- No public internet exposure for the main application
- Server-rendered HTML multi-page application (no SPA, no JS framework)
- Bootstrap 5 as the design system (via CDN or bundled)
- Local filesystem for photo/video storage
- JSON mutation logging to STDOUT for all data-changing operations
- GitHub Actions CI/CD with locally runnable builds and tests
- Paid Slack plan required (Pro or higher) for Slack App features

**Infrastructure assumptions:**
- On-premises servers with Docker support
- Local network connectivity reliable for core operations
- Internet connectivity available but not required for core web UI
- No HA, no load balancing, no auto-scaling -- single-instance deployment
- "Monday-fix" reliability grade -- downtime is acceptable, data loss is not

### Cross-Cutting Concerns Identified

1. **Role-Based Access Control:** Three roles (Member/Technician/Staff) with hierarchical permissions. Enforced server-side on every request. Affects routing, template rendering, and API access. Members are unauthenticated for public surfaces.

2. **Equipment Status Derivation:** Status is computed, not stored -- derived from open repair records and their severity. This derived status must be consistent across all 5 surfaces (web dashboard, kiosk, QR pages, static page, Slack). Single computation path is critical.

3. **Audit Trail & Mutation Logging:** Dual logging requirement -- application-level audit trail on repair records (FR20) AND infrastructure-level JSON mutation logging to STDOUT (FR52). Both append-only. The STDOUT logging serves as a data reconstruction mechanism.

4. **Multi-Surface Status Delivery:** Five distinct surfaces consuming the same status data with different rendering: authenticated web views, unauthenticated kiosk display, unauthenticated QR code pages, cloud-hosted static page, and Slack messages. Each has different refresh mechanisms (page navigation, 60s polling, on-demand, event-driven push, bot query).

5. **Slack as Parallel Interface:** The Slack App is not a notification add-on -- it's a full CRUD interface for problem reports and repair records. Architecture must ensure Slack operations use the same service/data layer as the web UI, not a separate path.

6. **File Upload Handling:** Photos and videos attached to both equipment records and repair records. Local filesystem storage with configurable size limits. Must handle upload from web forms AND potentially from Slack (image attachments in Slack messages).

7. **Event-Driven Side Effects:** Status changes trigger: static page regeneration and push, Slack notifications to configured channels, and potential future notification expansions. These must be reliable but non-blocking to the triggering action.

8. **Notification Queuing:** When Slack is unreachable, outbound notifications must be queued and delivered when connectivity is restored (NFR11). Static page push must retry with backoff (NFR12). Requires a durable queue or retry mechanism.

## Starter Template Evaluation

### Primary Technology Domain

Full-stack server-rendered web application (Python + MySQL + Docker), based on project requirements analysis. The ESB is a multi-page application with server-rendered HTML -- not an API, not an SPA, not a mobile app.

### Technical Preferences Established

**From PRD (hard constraints):** Python backend, MySQL database, Docker deployment, server-rendered HTML, Bootstrap 5, GitHub Actions CI/CD, Playwright browser tests.

**From user (confirmed):** Flask framework -- existing team familiarity from other projects.

### Starter Options Considered

| Framework | Version | Fit | Verdict |
|-----------|---------|-----|---------|
| **Flask** | 3.1.x | Custom views, explicit code, volunteer-friendly, team familiarity | **Selected** |
| Django | 6.0 | Batteries-included but conventions add overhead, custom views still needed | Rejected -- overhead without proportional benefit for this project's custom UI needs |
| FastAPI | Latest | API-first, poor fit for server-rendered HTML multi-page app | Rejected -- wrong paradigm |

### Selected Stack: Flask 3.1.x with Extensions

**Rationale for Selection:**
- Team has existing Flask experience from other projects
- Flask's explicit, minimal approach matches a project with highly custom views (Kanban, repair queue, QR pages, kiosk)
- Simpler mental model for volunteer maintainers -- less framework "magic"
- Extension ecosystem covers all requirements (ORM, auth, forms, migrations)
- Smaller dependency footprint suits single-container, volunteer-maintained deployment

**Core Framework + Extensions:**

| Component | Package | Version | Purpose |
|-----------|---------|---------|---------|
| Web framework | Flask | 3.1.x | Request handling, routing, Jinja2 templates |
| ORM | Flask-SQLAlchemy | 3.1.x | SQLAlchemy integration, MySQL support |
| Migrations | Alembic (via Flask-Migrate) | Latest | Database schema migrations |
| Auth/Sessions | Flask-Login | 0.7.x | Session management, login/logout, role checking |
| Forms/CSRF | Flask-WTF | 1.2.x | Form validation, CSRF protection |
| Password hashing | Werkzeug (built-in) | Built-in | `generate_password_hash` / `check_password_hash` |

**Architectural Decisions Provided by Stack:**

- **Language & Runtime:** Python 3.14
- **Templating:** Jinja2 (Flask built-in) with Bootstrap 5
- **ORM:** SQLAlchemy via Flask-SQLAlchemy, MySQL backend
- **Routing:** Flask decorator-based routes with Blueprints for modular organization
- **Session management:** Flask-Login with server-side sessions, 12-hour expiry
- **Form handling:** Flask-WTF for CSRF protection and validation
- **Static files:** Flask built-in static file serving (behind reverse proxy in production)

**Development Experience:**

- Hot reloading via Flask debug mode
- Flask CLI for management commands
- Alembic for migration generation and application
- pytest as the test runner (Flask's standard testing approach)
- Playwright for browser tests

**Note:** Project initialization and scaffolding should be the first implementation story.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Service layer pattern (web + Slack share business logic)
- RBAC decorator pattern (defines route security model)
- Database-backed notification queue (enables Slack reliability)
- File upload storage structure (affects all upload features)

**Important Decisions (Shape Architecture):**
- Background processing approach (notification delivery, static page push)
- Template inheritance structure (defines frontend organization)
- Docker Compose topology (defines deployment model)
- Environment configuration approach (defines configuration surface)

**Deferred Decisions (Post-MVP):**
- Caching strategy (add if performance requires it)
- Auth provider integration (Slack OAuth, Neon One SSO -- abstraction layer ready)
- Horizontal scaling (single-instance is sufficient for foreseeable load)

### Data Architecture

**Database:** MySQL (PRD constraint) accessed via SQLAlchemy ORM (Flask-SQLAlchemy 3.1.x).

**Core Entities:**
- `Area` -- organizational grouping with Slack channel mapping
- `Equipment` -- registry entry, belongs to Area, has documents/photos/links
- `RepairRecord` -- tracks a problem from report to resolution, belongs to Equipment
- `RepairTimelineEntry` -- append-only log of notes, status changes, uploads on a RepairRecord
- `User` -- local account with role (Technician/Staff)
- `Document` -- uploaded file metadata (equipment docs, repair photos), references local filesystem path
- `PendingNotification` -- queue table for outbound Slack notifications and static page pushes
- `AuditLog` -- application-level audit trail for repair record changes (FR20)
- `AppConfig` -- key/value store for runtime-configurable settings (notification triggers, Technician edit permissions)

**Equipment Status Derivation:** Status is computed, not stored. A single function queries open RepairRecords for an equipment item and returns green/yellow/red based on the highest severity. This function is the sole source of truth called by all surfaces.

**File Upload Storage:** Organized local filesystem under a configurable base path (`UPLOAD_PATH` env var):
- `uploads/equipment/{id}/docs/` -- manuals, documents
- `uploads/equipment/{id}/photos/` -- equipment photos
- `uploads/repairs/{id}/` -- diagnostic photos and videos
- File metadata (original name, content type, size, uploader, timestamp) stored in the `Document` table.

**Migration Strategy:** Alembic via Flask-Migrate. Auto-generate migrations from model changes. Migrations applied via Flask CLI command (`flask db upgrade`), run as part of container startup or deployment procedure.

**Caching:** None for v1.0. Single-instance deployment on LAN with <600 users and simple queries. Flask-Caching can be added later if needed.

### Authentication & Security

**Session Storage:** Flask's default signed cookie sessions. Flask-Login stores the user ID in the signed cookie; user data loaded from the database on each request. 12-hour session lifetime configured via `PERMANENT_SESSION_LIFETIME`. Sufficient for single-instance deployment with a small authenticated user base.

**RBAC Pattern:** Custom decorators on route functions:
- `@login_required` -- any authenticated user (Technician or Staff)
- `@role_required('staff')` -- Staff only
- `@role_required('technician')` -- Technician or Staff (hierarchical: Staff > Technician)
- Public routes (QR pages, kiosk, static page, problem report form) have no auth requirement

Role is stored on the User model. Decorators check `current_user.role` and return 403 if insufficient. Server-side enforcement on every request (NFR5).

**Password Security:** Werkzeug's `generate_password_hash` / `check_password_hash` using default algorithm (pbkdf2:sha256). No custom crypto.

**Auth Abstraction:** A thin `auth_service` module that Flask-Login's `user_loader` calls. Today it queries the local User table. The interface (`authenticate(username, password) -> User`, `load_user(user_id) -> User`) can be swapped to a Slack OAuth or SSO provider without changing routes or decorators.

**CSRF Protection:** Flask-WTF's CSRF protection on all form submissions. Slack requests validated via Slack signing secret (separate from web CSRF).

### API & Communication Patterns

**Service Layer Pattern:** No separate REST API. Business logic lives in service modules (`equipment_service`, `repair_service`, `notification_service`, `user_service`). Flask views (web UI) and Slack handlers both call the same service functions. This ensures identical behavior regardless of entry point and prevents logic duplication.

```
Web View (Flask route) ──→ Service Layer ──→ SQLAlchemy Models ──→ MySQL
Slack Handler (Bolt)   ──→ Service Layer ──→ SQLAlchemy Models ──→ MySQL
```

**Slack SDK:** `slack_bolt` -- Slack's official modern framework for Slack Apps. Handles event subscriptions, interactive components (modals, forms), and slash commands with a decorator-based API. Integrates with Flask via Bolt's Flask adapter.

**Notification Queue:** Database-backed `PendingNotification` table. When a status change or other trigger event occurs, the service layer inserts a notification row (type, payload, target channel, created_at, status=pending). A background worker polls the table, sends via Slack API, and marks rows as delivered. On Slack API failure: row stays pending, `next_retry_at` set with exponential backoff. Same mechanism handles static page push jobs.

**Static Page Generation:** Jinja2 template rendered to a standalone HTML file. Triggered by equipment status changes (service layer inserts a `static_page_push` job into PendingNotification). The background worker renders the template with current status data, then pushes via a configurable method (S3 upload, SCP, or similar). Retry with backoff on failure (NFR12).

**Error Handling:** Flask error handlers registered for 404, 403, 500 with user-friendly HTML templates. Service layer raises domain-specific exceptions (`EquipmentNotFound`, `RepairRecordNotFound`, `UnauthorizedAction`, `ValidationError`). Flask views catch these and return appropriate HTTP responses. Slack handlers catch the same exceptions and return Slack-formatted error messages.

### Frontend Architecture

**Bootstrap 5 Delivery:** Bundled locally -- Bootstrap CSS and JS files included in Flask's `static/` directory. No CDN dependency. Aligns with on-premises, no-internet-required constraint (NFR14).

**JavaScript Strategy:** Vanilla JS only. No build step, no bundler, no npm for frontend JS. Custom JS limited to:
- Kiosk auto-refresh (via `<meta http-equiv="refresh" content="60">` -- no JS needed)
- Client-side form validation (progressive enhancement)
- Photo upload preview
- Bootstrap JS bundle for modals, dropdowns, tooltips

**Template Organization:** Jinja2 template inheritance with Blueprints:
- `templates/base.html` -- authenticated layout (navbar, Bootstrap, flash messages, footer)
- `templates/base_public.html` -- unauthenticated layout (no navbar, minimal chrome)
- `templates/base_kiosk.html` -- kiosk layout (no nav, full-width, large fonts, meta refresh)
- `templates/{blueprint}/` -- per-blueprint template directories (equipment/, repairs/, admin/, public/)

**QR Code Generation:** Python `qrcode` library. QR codes generated as PNG or SVG when equipment is created or on demand. Stored as static files for download/printing. QR URL points to the equipment's public page on the local network.

### Infrastructure & Deployment

**Python Version:** 3.14 (latest stable).

**Docker Base Image:** `python:3.14-slim`.

**WSGI Server:** Gunicorn -- standard production Flask server. Workers configured based on available CPU (default: 2-4 workers for this workload).

**Docker Compose Topology:** Two primary containers:
- `app` -- Flask application served by Gunicorn
- `db` -- MySQL 8.x

Volumes:
- `mysql_data` -- database persistence
- `uploads` -- file upload storage (bind mount to host path)

Optional: `nginx` container as reverse proxy (recommended for production, serves static files and uploads directly).

**Background Worker:** A separate process (same Docker image, different entrypoint) running a Flask CLI command (`flask worker run`) that polls the `PendingNotification` table every 30 seconds. Handles Slack notification delivery and static page generation/push. Runs as a separate container in Docker Compose or as a second process in the app container via a process manager.

**Environment Configuration:** 12-factor style. All configuration via environment variables:
- `DATABASE_URL` -- MySQL connection string
- `SECRET_KEY` -- Flask session signing key
- `UPLOAD_PATH` -- local filesystem path for uploads
- `UPLOAD_MAX_SIZE_MB` -- configurable upload size limit (default 500)
- `SLACK_BOT_TOKEN` -- Slack App bot token
- `SLACK_SIGNING_SECRET` -- Slack request verification
- `STATIC_PAGE_PUSH_METHOD` -- configurable push mechanism (s3, scp, local)
- `STATIC_PAGE_PUSH_TARGET` -- destination path/URL for static page

`.env` file for local development (loaded by `python-dotenv`). Docker container reads env vars directly or via Docker Compose `env_file`.

**Logging:** Python `logging` module. All output to STDOUT (Docker best practice). Two log streams:
- Application logs: standard Python logging (INFO level default, configurable)
- Mutation logs: structured JSON for all data-changing operations (FR52), written to STDOUT with a distinct logger name for filtering

**CI/CD:** GitHub Actions. Pipeline stages: lint, unit tests (pytest), browser tests (Playwright), Docker image build. All stages runnable locally via `make` targets or shell scripts.

### Decision Impact Analysis

**Implementation Sequence:**
1. Project scaffolding (Flask app factory, Blueprints, configuration)
2. Database models and migrations (SQLAlchemy, Alembic)
3. Auth system (Flask-Login, RBAC decorators, login/logout views)
4. Equipment registry (CRUD views, file uploads)
5. Repair records (workflow state machine, timeline, service layer)
6. Public surfaces (QR pages, kiosk, status dashboard)
7. Notification system (queue, background worker, Slack notifications)
8. Slack App integration (Bolt handlers, forms, bot)
9. Static page generation and push
10. QR code generation
11. User management (provisioning, roles, password management)

**Cross-Component Dependencies:**
- Service layer must exist before Slack integration (Slack handlers depend on it)
- Notification queue must exist before static page push (uses the same mechanism)
- Equipment and RepairRecord models must exist before any view can be built
- Auth system must exist before any authenticated view
- Background worker depends on notification queue schema

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 6 major areas where AI agents could make incompatible choices: naming conventions, project organization, template patterns, service layer contracts, error handling, and logging format.

### Naming Patterns

**Database Naming Conventions:**
- Tables: plural, snake_case (`equipment`, `repair_records`, `users`, `areas`, `pending_notifications`)
- Columns: snake_case (`created_at`, `updated_at`, `equipment_id`, `slack_channel`)
- Foreign keys: `{referenced_table_singular}_id` (`equipment_id`, `user_id`, `area_id`)
- Indexes: `ix_{table}_{column}` (`ix_repair_records_equipment_id`)
- Boolean columns: `is_` or `has_` prefix (`is_archived`, `is_consumable`, `has_safety_risk`)
- Timestamps: `created_at`, `updated_at` on all tables. UTC always. MySQL `DATETIME` type.

**Python Code Naming (PEP 8):**
- Modules/packages: snake_case (`equipment_service.py`, `repair_routes.py`)
- Classes: PascalCase (`Equipment`, `RepairRecord`, `RepairTimelineEntry`)
- Functions/methods: snake_case (`get_equipment_status`, `create_repair_record`)
- Variables: snake_case (`current_user`, `repair_record`)
- Constants: UPPER_SNAKE_CASE (`MAX_UPLOAD_SIZE_MB`, `DEFAULT_SESSION_HOURS`)
- Private: single leading underscore (`_compute_status`, `_validate_severity`)

**Route/URL Naming:**
- All lowercase with hyphens for multi-word segments: `/repair-queue`, `/equipment/<int:id>/edit`
- Resource-oriented: nouns, not verbs (`/equipment/new` not `/create-equipment`)
- Blueprint prefixes match the domain: `/equipment/...`, `/repairs/...`, `/admin/...`, `/public/...`
- Integer IDs in URLs: `<int:id>` (not `<id>` or `<uuid>`)

**Template File Naming:**
- snake_case: `repair_detail.html`, `equipment_list.html`, `kanban_board.html`
- Partials (included fragments): prefix with underscore: `_status_indicator.html`, `_timeline_entry.html`
- Base templates: `base.html`, `base_public.html`, `base_kiosk.html`

**Blueprint Names:**
- Lowercase, singular domain name: `equipment`, `repairs`, `admin`, `public`, `auth`

### Structure Patterns

**Project Organization (Feature-Oriented Blueprints):**
```
esb/                          # Application package
  __init__.py                 # App factory (create_app)
  config.py                   # Configuration classes
  extensions.py               # Flask extension instances (db, login_manager, migrate, csrf)
  models/                     # SQLAlchemy models
    __init__.py               # Imports all models for Alembic discovery
    equipment.py              # Equipment, Area, Document models
    repairs.py                # RepairRecord, RepairTimelineEntry models
    user.py                   # User model
    notifications.py          # PendingNotification model
    audit.py                  # AuditLog model
    config.py                 # AppConfig model
  services/                   # Business logic layer
    equipment_service.py
    repair_service.py
    notification_service.py
    user_service.py
    status_service.py         # Equipment status derivation
    static_page_service.py
    upload_service.py
  views/                      # Flask Blueprints (routes + view logic)
    equipment.py              # Equipment registry routes
    repairs.py                # Repair record routes
    admin.py                  # User management, area management, app config
    public.py                 # QR pages, kiosk, status dashboard, problem report
    auth.py                   # Login, logout, change password
  slack/                      # Slack App handlers
    __init__.py               # Bolt app setup
    handlers.py               # Event and command handlers
    forms.py                  # Slack modal/form definitions
  templates/                  # Jinja2 templates
    base.html
    base_public.html
    base_kiosk.html
    equipment/                # Equipment blueprint templates
    repairs/                  # Repair blueprint templates
    admin/                    # Admin blueprint templates
    public/                   # Public blueprint templates
    auth/                     # Auth blueprint templates
    components/               # Shared partials (_status_indicator.html, etc.)
  static/                     # Static assets
    css/
      bootstrap.min.css
      app.css                 # Single custom stylesheet
    js/
      bootstrap.bundle.min.js
      app.js                  # Single custom JS file
    img/                      # App images (logo, icons)
  utils/                      # Shared utilities
    decorators.py             # @role_required and other custom decorators
    logging.py                # Mutation logger setup
    exceptions.py             # Domain exception classes
tests/                        # Test directory (mirrors app structure)
  conftest.py                 # Shared fixtures (app, db, client, auth helpers)
  test_models/
  test_services/
  test_views/
  test_slack/
  e2e/                        # Playwright browser tests
migrations/                   # Alembic migrations
```

**Key structural rules:**
- Models are data + relationships only. No business logic in models.
- Services contain all business logic. Views and Slack handlers are thin -- they parse input, call a service, render output.
- Views never import other views. Services never import views. Dependencies flow one way: views → services → models.
- Templates never contain Python logic beyond simple conditionals and loops. Complex logic lives in the view or service.
- One custom CSS file (`app.css`), one custom JS file (`app.js`). No per-page CSS/JS files.

**Test Organization:**
- Tests live in `tests/` directory, mirroring `esb/` structure
- Test files: `test_{module}.py` (e.g., `test_equipment_service.py`, `test_repair_routes.py`)
- Shared fixtures in `conftest.py` at the `tests/` root
- Playwright tests in `tests/e2e/` with descriptive names (`test_member_reports_problem.py`, `test_technician_updates_repair.py`)
- Factory functions for test data (e.g., `create_test_equipment()`, `create_test_repair_record()`) in `tests/conftest.py`

### Format Patterns

**Date/Time Handling:**
- All timestamps stored in UTC in the database (`DATETIME` columns)
- Python: `datetime.datetime.now(datetime.UTC)` for current time
- Display: convert to local time in templates using a Jinja2 filter
- Template format: "Feb 14, 2026 2:34 PM" on desktop, "2 hours ago" (relative) on mobile where space is limited
- Forms: HTML `<input type="date">` returns `YYYY-MM-DD`, parsed server-side

**Flash Message Categories:**
- `success` -- operation completed (green alert)
- `danger` -- error occurred (red alert)
- `warning` -- advisory (yellow alert)
- `info` -- informational (blue alert)
- These map directly to Bootstrap alert classes: `alert-{category}`

**Form Validation Pattern:**
- Server-side validation always (Flask-WTF validators)
- Client-side validation as progressive enhancement only (HTML `required` attributes)
- Validation errors rendered inline below the field using Bootstrap's `invalid-feedback` class
- On validation failure: re-render the form with errors and preserved field values
- Flash messages for operation-level feedback (success/error), not field-level

**Pagination Pattern (where applicable):**
- URL parameter: `?page=2`
- Default page size: 25 items
- Use Flask-SQLAlchemy's `paginate()` method
- Render Bootstrap pagination component in templates

### Communication Patterns

**Service Layer Contracts:**

Every service function follows this pattern:
```python
def create_repair_record(equipment_id: int, description: str, reporter_name: str,
                          severity: str = 'not_sure', **kwargs) -> RepairRecord:
    """
    Create a new repair record for an equipment item.

    Raises:
        EquipmentNotFound: if equipment_id doesn't exist
        ValidationError: if required fields are missing/invalid
    """
```

Rules:
- Service functions accept primitive types and return model instances (or lists of them)
- Service functions raise domain exceptions on failure, never return error codes
- Service functions handle their own database commits (`db.session.commit()`)
- Service functions call `notification_service.queue_notification()` for side effects -- never send notifications directly
- Service functions call the mutation logger for all data changes

**Mutation Logging Format (FR52):**
```json
{
  "timestamp": "2026-02-14T14:30:00Z",
  "event": "repair_record.created",
  "user": "marcus",
  "data": {
    "id": 42,
    "equipment_id": 7,
    "description": "Motor makes grinding noise",
    "severity": "down",
    "status": "new"
  }
}
```

Event naming: `{entity}.{action}` in snake_case. Actions: `created`, `updated`, `deleted`, `status_changed`, `archived`.

**Notification Event Types:**
- `new_report` -- new repair record created (from member report or technician)
- `resolved` -- repair record status changed to Resolved
- `severity_changed` -- severity level changed
- `eta_updated` -- ETA set or changed
- These are the configurable trigger types stored in AppConfig

### Process Patterns

**Error Handling:**

Domain exceptions defined in `esb/utils/exceptions.py`:
```python
class ESBError(Exception): """Base exception for all ESB errors."""
class EquipmentNotFound(ESBError): pass
class RepairRecordNotFound(ESBError): pass
class UnauthorizedAction(ESBError): pass
class ValidationError(ESBError): pass
```

View error handling pattern:
```python
@equipment_bp.route('/equipment/<int:id>')
def detail(id):
    try:
        equipment = equipment_service.get_equipment(id)
    except EquipmentNotFound:
        abort(404)
    return render_template('equipment/detail.html', equipment=equipment)
```

Flask error handlers in the app factory:
- 404 → `errors/404.html`
- 403 → `errors/403.html`
- 500 → `errors/500.html`

**View Function Pattern:**

All view functions follow: parse input → call service → render response.
```python
@repairs_bp.route('/repairs/<int:id>/update', methods=['POST'])
@role_required('technician')
def update(id):
    form = RepairUpdateForm()
    if form.validate_on_submit():
        try:
            repair = repair_service.update_repair_record(
                id, status=form.status.data, note=form.note.data,
                current_user=current_user
            )
            flash('Repair record updated.', 'success')
            return redirect(url_for('repairs.detail', id=id))
        except RepairRecordNotFound:
            abort(404)
    return render_template('repairs/edit.html', form=form, id=id)
```

**File Upload Pattern:**
- Use `upload_service.save_upload(file, category, parent_type, parent_id)` -- never handle file I/O in views
- The upload service validates file size, generates a safe filename, saves to the correct directory, and creates a `Document` record
- Return the `Document` instance to the caller
- On failure, raise `ValidationError` with a user-friendly message

**Background Worker Pattern:**
- Worker polls `PendingNotification` table every 30 seconds
- For each pending job: attempt delivery, on success mark `status='delivered'`, on failure set `next_retry_at` with exponential backoff (30s, 1m, 2m, 5m, 15m, max 1h)
- Worker uses the same Flask app context and service layer as the web app
- Worker logs all delivery attempts and failures to STDOUT

### Enforcement Guidelines

**All AI Agents MUST:**
1. Follow PEP 8 naming conventions exactly as specified above
2. Put business logic in services, never in views or models
3. Use domain exceptions from `esb/utils/exceptions.py`, never return error codes or bare strings
4. Call `notification_service.queue_notification()` for all side effects, never send notifications directly from views
5. Write mutation log entries for all data-changing operations via the mutation logger utility
6. Use the shared template partials in `templates/components/` for status indicators, timeline entries, and other reusable UI
7. Include tests for every new service function and view route

**Anti-Patterns to Avoid:**
- Business logic in Jinja2 templates (complex conditionals, data transformations)
- Direct database queries in view functions (bypass service layer)
- Inline SQL (always use SQLAlchemy ORM)
- Per-page CSS or JS files (use the single `app.css` and `app.js`)
- Catching generic `Exception` in views (catch specific domain exceptions)
- Committing database changes in view functions (let service layer handle transactions)
- Hardcoded configuration values (use environment variables via `app.config`)

## Project Structure & Boundaries

### Complete Project Directory Structure

```
equipment-status-board/
├── README.md
├── LICENSE
├── Makefile                          # Local dev commands (test, lint, run, migrate, build)
├── pyproject.toml                    # Python project metadata, dependencies, tool config
├── requirements.txt                  # Pinned production dependencies (generated from pyproject.toml)
├── requirements-dev.txt              # Development/test dependencies
├── .env.example                      # Template for local .env file
├── .gitignore
├── .flake8                           # Linting configuration (or ruff.toml)
├── Dockerfile
├── docker-compose.yml
├── .github/
│   └── workflows/
│       └── ci.yml                    # GitHub Actions: lint, test, build
├── esb/                              # Application package
│   ├── __init__.py                   # App factory (create_app)
│   ├── config.py                     # Configuration classes (Dev, Test, Prod)
│   ├── extensions.py                 # Flask extension instances (db, login_manager, migrate, csrf)
│   ├── models/
│   │   ├── __init__.py               # Imports all models for Alembic discovery
│   │   ├── area.py                   # Area model
│   │   ├── equipment.py              # Equipment model
│   │   ├── document.py               # Document model (file metadata for equipment + repairs)
│   │   ├── repair_record.py          # RepairRecord model
│   │   ├── repair_timeline_entry.py  # RepairTimelineEntry model (append-only)
│   │   ├── user.py                   # User model
│   │   ├── pending_notification.py   # PendingNotification model (queue)
│   │   ├── audit_log.py              # AuditLog model
│   │   └── app_config.py             # AppConfig model (runtime settings)
│   ├── services/
│   │   ├── __init__.py
│   │   ├── equipment_service.py      # Equipment CRUD, area management
│   │   ├── repair_service.py         # Repair record lifecycle, timeline entries
│   │   ├── status_service.py         # Equipment status derivation (single source of truth)
│   │   ├── notification_service.py   # Queue notifications, process delivery
│   │   ├── user_service.py           # User provisioning, role management, password operations
│   │   ├── auth_service.py           # Authentication abstraction (login, user loading)
│   │   ├── upload_service.py         # File upload validation, storage, metadata
│   │   ├── static_page_service.py    # Static page rendering and push
│   │   └── qr_service.py             # QR code generation
│   ├── views/
│   │   ├── __init__.py               # Blueprint registration helper
│   │   ├── equipment.py              # /equipment/* routes (registry CRUD)
│   │   ├── repairs.py                # /repairs/* routes (repair records, timeline)
│   │   ├── admin.py                  # /admin/* routes (users, areas, app config)
│   │   ├── public.py                 # /public/* routes (QR pages, kiosk, status, problem report)
│   │   └── auth.py                   # /auth/* routes (login, logout, change password)
│   ├── forms/
│   │   ├── __init__.py
│   │   ├── equipment_forms.py        # Equipment create/edit, area create/edit
│   │   ├── repair_forms.py           # Repair update, problem report
│   │   ├── admin_forms.py            # User provisioning, role assignment, password reset
│   │   └── auth_forms.py             # Login, change password
│   ├── slack/
│   │   ├── __init__.py               # Bolt app setup, Flask adapter integration
│   │   ├── handlers.py               # Event subscriptions, slash commands, bot queries
│   │   └── forms.py                  # Slack modal/form definitions (problem report, repair update)
│   ├── templates/
│   │   ├── base.html                 # Authenticated layout (navbar, Bootstrap, flash, footer)
│   │   ├── base_public.html          # Unauthenticated layout (no navbar)
│   │   ├── base_kiosk.html           # Kiosk layout (no nav, full-width, meta refresh)
│   │   ├── components/
│   │   │   ├── _status_indicator.html    # Green/yellow/red status (large, compact, minimal variants)
│   │   │   ├── _timeline_entry.html      # Single repair timeline entry
│   │   │   ├── _flash_messages.html      # Flash message rendering
│   │   │   ├── _pagination.html          # Bootstrap pagination
│   │   │   ├── _kanban_card.html         # Single Kanban card
│   │   │   └── _repair_queue_row.html    # Single repair queue table row / mobile card
│   │   ├── equipment/
│   │   │   ├── list.html                 # Equipment registry list (filterable by area)
│   │   │   ├── detail.html               # Equipment detail (docs, photos, links, repair history)
│   │   │   ├── create.html               # Equipment creation form
│   │   │   └── edit.html                 # Equipment edit form
│   │   ├── repairs/
│   │   │   ├── queue.html                # Technician repair queue table
│   │   │   ├── kanban.html               # Staff Kanban board
│   │   │   ├── detail.html               # Repair record detail (timeline, edit form)
│   │   │   └── create.html               # Manual repair record creation
│   │   ├── admin/
│   │   │   ├── users.html                # User management list
│   │   │   ├── user_create.html          # User provisioning form
│   │   │   ├── areas.html                # Area management
│   │   │   └── config.html               # App configuration (notification triggers, permissions)
│   │   ├── public/
│   │   │   ├── equipment_page.html       # QR code landing page (status, issues, report form, docs)
│   │   │   ├── equipment_info.html       # Equipment documentation page (manuals, links)
│   │   │   ├── status_dashboard.html     # Member status dashboard (area grid)
│   │   │   ├── kiosk.html                # Kiosk display (extends base_kiosk.html)
│   │   │   ├── report_confirmation.html  # Post-submission confirmation
│   │   │   └── static_page.html          # Template for generated static status page
│   │   ├── auth/
│   │   │   ├── login.html                # Login page
│   │   │   └── change_password.html      # Change password form
│   │   └── errors/
│   │       ├── 403.html
│   │       ├── 404.html
│   │       └── 500.html
│   ├── static/
│   │   ├── css/
│   │   │   ├── bootstrap.min.css
│   │   │   └── app.css                   # Single custom stylesheet (~140 lines)
│   │   ├── js/
│   │   │   ├── bootstrap.bundle.min.js
│   │   │   └── app.js                    # Single custom JS file
│   │   ├── img/
│   │   │   └── logo.png                  # Decatur Makers logo
│   │   └── qrcodes/                      # Generated QR code images
│   └── utils/
│       ├── __init__.py
│       ├── decorators.py                 # @role_required, other custom decorators
│       ├── logging.py                    # Mutation logger setup (structured JSON to STDOUT)
│       ├── exceptions.py                 # Domain exception classes (ESBError hierarchy)
│       └── filters.py                    # Jinja2 custom filters (date formatting, relative time)
├── worker.py                             # Background worker entrypoint (or flask CLI command)
├── tests/
│   ├── conftest.py                       # App factory, DB fixtures, auth helpers, test data factories
│   ├── test_models/
│   │   ├── test_equipment.py
│   │   ├── test_repair_record.py
│   │   ├── test_user.py
│   │   └── test_pending_notification.py
│   ├── test_services/
│   │   ├── test_equipment_service.py
│   │   ├── test_repair_service.py
│   │   ├── test_status_service.py
│   │   ├── test_notification_service.py
│   │   ├── test_user_service.py
│   │   ├── test_upload_service.py
│   │   └── test_auth_service.py
│   ├── test_views/
│   │   ├── test_equipment_views.py
│   │   ├── test_repair_views.py
│   │   ├── test_admin_views.py
│   │   ├── test_public_views.py
│   │   └── test_auth_views.py
│   ├── test_slack/
│   │   └── test_handlers.py
│   └── e2e/
│       ├── conftest.py                   # Playwright fixtures, live server setup
│       ├── test_member_checks_status.py
│       ├── test_member_reports_problem.py
│       ├── test_technician_repair_queue.py
│       ├── test_staff_kanban.py
│       ├── test_staff_equipment_management.py
│       ├── test_staff_user_management.py
│       └── test_auth_flows.py
└── migrations/                           # Alembic migrations directory
    ├── alembic.ini
    ├── env.py
    └── versions/
```

### Architectural Boundaries

**Public / Authenticated Boundary:**
- `views/public.py` and `views/auth.py` handle unauthenticated requests. No `@login_required`.
- `views/equipment.py`, `views/repairs.py`, `views/admin.py` require authentication. Every route has `@login_required` or `@role_required`.
- Templates in `templates/public/` extend `base_public.html` (no navbar). Templates in other blueprint dirs extend `base.html` (navbar with role-appropriate links).

**Service Layer Boundary:**
- Views and Slack handlers ONLY call service functions. They never query the database directly.
- Services ONLY use SQLAlchemy models for data access. They never import from views or Slack.
- Dependency flow is strictly one-directional: `views/slack → services → models`

**Slack Integration Boundary:**
- `esb/slack/` is a self-contained module. It imports from `esb/services/` but nothing else imports from `esb/slack/`.
- If Slack is disabled (no token configured), the Slack module is not loaded. Core web app is unaffected (NFR10).
- Slack handlers use the same service functions as web views -- no separate business logic path.

**Data Access Boundary:**
- All database access goes through SQLAlchemy models in `esb/models/`.
- No raw SQL anywhere in the codebase.
- All queries happen in service functions, not in views, templates, or utilities.

**File System Boundary:**
- Only `upload_service.py`, `static_page_service.py`, and `qr_service.py` write to the filesystem.
- Upload path is configurable via `UPLOAD_PATH` environment variable.
- QR codes written to `static/qrcodes/`.
- Static page rendered to a temp location, then pushed by the configured method.

### Requirements to Structure Mapping

**Equipment Registry (FR1-FR10):**
- Models: `models/equipment.py`, `models/area.py`, `models/document.py`
- Service: `services/equipment_service.py`
- Views: `views/equipment.py`
- Forms: `forms/equipment_forms.py`
- Templates: `templates/equipment/`
- Tests: `test_models/test_equipment.py`, `test_services/test_equipment_service.py`, `test_views/test_equipment_views.py`

**Repair Records (FR11-FR21):**
- Models: `models/repair_record.py`, `models/repair_timeline_entry.py`, `models/audit_log.py`
- Service: `services/repair_service.py`
- Views: `views/repairs.py`
- Forms: `forms/repair_forms.py`
- Templates: `templates/repairs/`
- Tests: `test_services/test_repair_service.py`, `test_views/test_repair_views.py`

**Problem Reporting (FR22-FR26):**
- Views: `views/public.py` (report form route)
- Forms: `forms/repair_forms.py` (ProblemReportForm)
- Service: `services/repair_service.py` (creates repair record from member report)
- Templates: `templates/public/equipment_page.html`, `templates/public/report_confirmation.html`
- Tests: `test_views/test_public_views.py`, `e2e/test_member_reports_problem.py`

**Status Display & Member Access (FR27-FR33):**
- Service: `services/status_service.py` (status derivation)
- Views: `views/public.py` (kiosk, dashboard, QR pages)
- Templates: `templates/public/kiosk.html`, `templates/public/status_dashboard.html`, `templates/public/equipment_page.html`
- QR generation: `services/qr_service.py`
- Static page: `services/static_page_service.py`, `templates/public/static_page.html`
- Tests: `test_services/test_status_service.py`, `e2e/test_member_checks_status.py`

**Role-Based Experiences (FR34-FR37):**
- Views: `views/auth.py` (post-login redirect based on role)
- Templates: `templates/public/status_dashboard.html` (Member default), `templates/repairs/queue.html` (Technician default), `templates/repairs/kanban.html` (Staff default)
- Tests: `e2e/test_auth_flows.py`

**Slack Integration (FR38-FR44):**
- Slack module: `slack/__init__.py`, `slack/handlers.py`, `slack/forms.py`
- Service: `services/notification_service.py` (outbound notifications)
- Tests: `test_slack/test_handlers.py`

**User Management & Auth (FR45-FR51):**
- Models: `models/user.py`
- Services: `services/user_service.py`, `services/auth_service.py`
- Views: `views/admin.py` (user provisioning), `views/auth.py` (login/logout/password)
- Forms: `forms/admin_forms.py`, `forms/auth_forms.py`
- Templates: `templates/admin/users.html`, `templates/auth/login.html`
- Tests: `test_services/test_user_service.py`, `test_views/test_admin_views.py`, `e2e/test_staff_user_management.py`

**System & Operations (FR52-FR55):**
- Mutation logging: `utils/logging.py`
- Docker: `Dockerfile`, `docker-compose.yml`
- CI/CD: `.github/workflows/ci.yml`
- Tests: `tests/` (entire test suite), `Makefile` (local test commands)

### Cross-Cutting Concerns Mapping

| Concern | Primary Location | Touched By |
|---------|-----------------|------------|
| RBAC | `utils/decorators.py` | All authenticated views |
| Status derivation | `services/status_service.py` | public views, kiosk, static page, Slack bot |
| Mutation logging | `utils/logging.py` | All service functions that change data |
| Audit trail | `models/audit_log.py` + `services/repair_service.py` | Repair record changes |
| Notification queue | `models/pending_notification.py` + `services/notification_service.py` | Any status-changing service function |
| File uploads | `services/upload_service.py` | Equipment views, repair views, Slack handlers |
| Error handling | `utils/exceptions.py` + app factory error handlers | All views, all services |

### Integration Points

**Internal Data Flow:**
```
Member scans QR → public view → equipment_service.get → status_service.compute → render template
Member submits report → public view → repair_service.create → notification_service.queue → DB
Worker polls → notification_service.process → Slack API / static_page_service.push → mark delivered
Technician updates repair → repairs view → repair_service.update → notification_service.queue → DB
```

**External Integrations:**
- **Slack API** (via `slack_bolt`): Inbound events/commands at `/slack/events`, outbound via `WebClient`
- **Cloud hosting** (for static page): S3, SCP, or configurable push target
- **Local filesystem**: Upload storage at configurable `UPLOAD_PATH`

### Development Workflow Integration

**Local Development:**
```bash
make setup          # Create .env from .env.example, install dependencies
make db-up          # Start MySQL via docker-compose (db only)
make migrate        # Run Alembic migrations
make run            # Flask dev server with hot reload
make worker         # Run background worker
make test           # pytest (unit + service + view tests)
make test-e2e       # Playwright browser tests
make lint           # Linting (flake8 or ruff)
make docker-build   # Build Docker image
make docker-up      # Full docker-compose up (app + db + worker)
```

**CI/CD Pipeline (GitHub Actions):**
1. Checkout + Python setup
2. Install dependencies
3. Lint (flake8/ruff)
4. Unit + service + view tests (pytest with MySQL service container)
5. Playwright browser tests (with live Flask server)
6. Docker image build (verify it builds successfully)

**Deployment:**
- `docker-compose up -d` on the makerspace server
- Volumes: `mysql_data` (named volume), `./uploads` (bind mount)
- Environment variables via `.env` file or Docker Compose `env_file`
- Migrations: `docker-compose exec app flask db upgrade`

## Architecture Validation Results

### Coherence Validation

**Decision Compatibility:** All technology choices are compatible. Flask 3.1.x + standard extensions (SQLAlchemy, Login, WTF, Migrate) are a well-tested combination. slack_bolt integrates via official Flask adapter. Python 3.14 + Gunicorn + MySQL 8.x is a standard production stack. Bootstrap 5 bundled locally with Jinja2 requires no build tooling. No version conflicts or contradictory decisions found.

**Pattern Consistency:** PEP 8 naming applied consistently across all layers (models, services, views, templates, routes). Service layer pattern enforced uniformly with one-directional dependency flow. Blueprint organization mirrors template and test directories. Mutation logging format uses consistent `entity.action` naming.

**Structure Alignment:** Project directory structure directly supports all defined Blueprints, services, models, and patterns. Architectural boundaries (public/authenticated, service layer, Slack isolation, data access, filesystem) are structurally enforced by directory organization and import rules.

### Requirements Coverage Validation

**Functional Requirements:** All 55 core FRs (FR1-FR55) are architecturally supported. Each FR category maps to specific models, services, views, and templates as documented in the Requirements to Structure Mapping.

**Non-Functional Requirements:** All 21 NFRs (NFR1-NFR21) are addressed. Performance is handled by LAN deployment and simple architecture. Security by server-side RBAC and standard hashing. Integration by Slack isolation and notification queuing. Reliability by mutation logging and Docker restart recovery. Accessibility by Bootstrap defaults and semantic HTML patterns.

**Stretch Goal Accommodation:** Data model designed to accommodate future parts inventory (FR56-FR60) and Technician-Area assignment (FR61-FR63) without schema redesign.

### Implementation Readiness Validation

**Decision Completeness:** All critical decisions documented with specific package versions. Implementation patterns include concrete code examples for service functions, view functions, error handling, and file uploads. Consistency rules are explicit and enforceable.

**Structure Completeness:** Complete directory tree defined with every file and directory. All integration points specified. Component boundaries clearly defined with import rules.

**Pattern Completeness:** All identified conflict points (naming, structure, format, communication, process) addressed with explicit rules and examples. Anti-patterns documented.

### Implementation Notes

1. **Temp password delivery (FR46):** Direct Slack API call from `user_service`, not routed through the notification queue. Fallback to displaying the temp password to the creator if Slack is unreachable.

2. **Stretch goal data model:** Equipment model should include a placeholder relationship for future parts table. Schema should accommodate `parts`, `equipment_parts`, and stock tracking tables without requiring migration of existing tables.

3. **Static page push default:** `STATIC_PAGE_PUSH_METHOD` defaults to `local` (write to a configurable directory). Additional methods: `s3`, `scp`. This allows the system to work on the local network immediately without cloud credentials.

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (medium complexity, ~600 users)
- [x] Technical constraints identified (Python, MySQL, Docker, on-premises)
- [x] Cross-cutting concerns mapped (8 concerns identified)

**Architectural Decisions**
- [x] Critical decisions documented with versions (Flask 3.1.x, Python 3.14, MySQL 8.x)
- [x] Technology stack fully specified (framework + 5 extensions + Slack SDK)
- [x] Integration patterns defined (service layer, notification queue, Slack adapter)
- [x] Performance considerations addressed (LAN deployment, no caching needed)

**Implementation Patterns**
- [x] Naming conventions established (database, Python, routes, templates)
- [x] Structure patterns defined (service layer, Blueprint organization, test mirroring)
- [x] Communication patterns specified (service contracts, mutation logging, notification events)
- [x] Process patterns documented (error handling, view pattern, file uploads, background worker)

**Project Structure**
- [x] Complete directory structure defined
- [x] Component boundaries established (5 boundaries documented)
- [x] Integration points mapped (internal data flow + external integrations)
- [x] Requirements to structure mapping complete (all 8 FR categories + cross-cutting concerns)

### Architecture Readiness Assessment

**Overall Status:** READY FOR IMPLEMENTATION

**Confidence Level:** High -- all requirements covered, no gaps, well-established technology stack with team familiarity.

**Key Strengths:**
- Service layer pattern ensures Slack and web UI share identical business logic
- Notification queue with retry/backoff handles Slack and static page push reliability
- Clear architectural boundaries prevent AI agent conflicts
- Explicit patterns with code examples reduce ambiguity
- Simple, well-understood technology stack maintainable by volunteers

**Areas for Future Enhancement:**
- Caching layer (add Flask-Caching if query performance becomes an issue)
- Auth provider swap (abstraction layer is ready; implement Slack OAuth or SSO when needed)
- Parts inventory UI and service logic (data model accommodation is in place)
- Monitoring and alerting (not needed for "Monday-fix" reliability grade, but useful if the system grows)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Use implementation patterns consistently across all components
- Respect project structure and boundaries (especially the one-directional dependency flow)
- Refer to this document for all architectural questions
- When in doubt about a pattern, check the Enforcement Guidelines and Anti-Patterns sections

**First Implementation Priority:**
1. Project scaffolding: Flask app factory, Blueprints, configuration classes, extensions
2. Database models and initial Alembic migration
3. Auth system: Flask-Login setup, RBAC decorators, login/logout views
