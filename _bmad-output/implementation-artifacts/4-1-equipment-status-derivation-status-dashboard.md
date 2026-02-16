# Story 4.1: Equipment Status Derivation & Status Dashboard

Status: done

## Story

As a member,
I want to see a color-coded status dashboard of all equipment organized by area,
So that I can quickly check whether the equipment I need is operational before visiting the space.

## Acceptance Criteria

1. **Given** the `status_service` module with a `compute_equipment_status` function, **When** it is called for an equipment item, **Then** it returns green (operational) if no open repair records exist, yellow (degraded) if the highest severity among open records is "Degraded" or "Not Sure", and red (down) if any open record has severity "Down". (AC: #1)

2. **Given** the `status_service` module, **When** it computes status, **Then** it is the single source of truth called by all surfaces (dashboard, kiosk, QR pages, static page, Slack). (AC: #2)

3. **Given** a repair record with severity "Not Sure", **When** status is derived for that equipment, **Then** it displays as yellow/degraded on all status displays. (AC: #3)

4. **Given** I am logged in as a member (or any authenticated user), **When** I navigate to the Status Dashboard, **Then** I see all areas with their equipment listed in a color-coded grid (green/yellow/red). (AC: #4)

5. **Given** the status dashboard, **When** I view an equipment item that is yellow or red, **Then** I see the equipment name, status color, and a brief description of the current issue. (AC: #5)

6. **Given** the status dashboard on mobile, **When** the page renders, **Then** the area grid displays as 1 column on phone, expanding to 2-3 on tablet and 4+ on desktop. (AC: #6)

7. **Given** the Status Indicator component, **When** it is rendered, **Then** it displays color + icon (checkmark/warning triangle/X-circle) + text label ("Operational"/"Degraded"/"Down") **And** it never relies on color alone for status communication. (AC: #7)

8. **Given** the Status Indicator component, **When** used across different views, **Then** it supports three variants: Large (QR page hero), Compact (table cells, Kanban cards, kiosk grid), Minimal (static page). (AC: #8)

## Tasks / Subtasks

- [x] Task 1: Create `status_service.py` with status derivation logic (AC: #1, #2, #3)
  - [x] 1.1: Implement `compute_equipment_status(equipment_id)` -- returns status dict with `color`, `label`, `severity`, `issue_description`
  - [x] 1.2: Implement `get_area_status_dashboard()` -- returns all non-archived areas with their equipment and computed statuses
  - [x] 1.3: Status derivation rules: no open records = green/Operational; highest severity "Down" = red/Down; highest severity "Degraded" or "Not Sure" = yellow/Degraded
  - [x] 1.4: Include brief issue description from the highest-severity open repair record
- [x] Task 2: Create `_status_indicator.html` component template (AC: #7, #8)
  - [x] 2.1: Large variant -- color background block with icon and text label (for QR pages)
  - [x] 2.2: Compact variant -- badge-sized with color, icon, and short text (for tables, Kanban, kiosk)
  - [x] 2.3: Minimal variant -- color dot + equipment name, no text label (for static page)
  - [x] 2.4: Accessibility -- ARIA label, color + icon + text (three channels), never color alone
- [x] Task 3: Create `status_dashboard.html` template (AC: #4, #5, #6)
  - [x] 3.1: Area grid with responsive layout (1 col phone, 2-3 tablet, 4+ desktop)
  - [x] 3.2: Each equipment item shows name, compact status indicator
  - [x] 3.3: Yellow/red items show brief issue description
  - [x] 3.4: Extends `base.html` (authenticated view, requires login)
- [x] Task 4: Update `views/public.py` with status dashboard route (AC: #4)
  - [x] 4.1: Replace placeholder `/public/` route with actual status dashboard route
  - [x] 4.2: Route calls `status_service.get_area_status_dashboard()`
  - [x] 4.3: Renders `public/status_dashboard.html`
- [x] Task 5: Update navigation and login redirect (AC: #4)
  - [x] 5.1: Add Status Dashboard link to navbar for authenticated users
  - [x] 5.2: Verify member login redirect behavior (members should land on status dashboard)
- [x] Task 6: Write service tests for `status_service` (AC: #1, #2, #3)
  - [x] 6.1: Test green status -- equipment with no open repair records
  - [x] 6.2: Test green status -- equipment with only closed repair records
  - [x] 6.3: Test red status -- equipment with "Down" severity open record
  - [x] 6.4: Test yellow status -- equipment with "Degraded" severity open record
  - [x] 6.5: Test yellow status -- equipment with "Not Sure" severity open record
  - [x] 6.6: Test severity priority -- "Down" wins over "Degraded" and "Not Sure"
  - [x] 6.7: Test issue description returned from highest severity record
  - [x] 6.8: Test `get_area_status_dashboard()` returns areas with equipment and statuses
  - [x] 6.9: Test archived equipment excluded from dashboard
  - [x] 6.10: Test archived areas excluded from dashboard
- [x] Task 7: Write view tests for status dashboard route (AC: #4, #5, #6, #7)
  - [x] 7.1: Test dashboard renders for authenticated user (staff, tech)
  - [x] 7.2: Test dashboard redirects unauthenticated to login
  - [x] 7.3: Test area headings displayed
  - [x] 7.4: Test equipment names displayed
  - [x] 7.5: Test status indicator CSS classes present (green, yellow, red)
  - [x] 7.6: Test issue description displayed for degraded/down equipment
  - [x] 7.7: Test empty state when no areas/equipment exist
  - [x] 7.8: Test archived equipment not shown
  - [x] 7.9: Test status indicator accessibility (ARIA labels present)

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in `esb/services/status_service.py`. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed). Services never import views. Views never import other views.
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Domain exceptions:** Raise `EquipmentNotFound`, `ValidationError` etc. from `esb/utils/exceptions.py`. Views catch these and return appropriate HTTP responses.
5. **Single CSS/JS files:** All custom styles go in `esb/static/css/app.css`. All custom JS goes in `esb/static/js/app.js`. NO per-page CSS/JS files.
6. **Template naming:** snake_case for templates (`status_dashboard.html`). Underscore prefix for partials (`_status_indicator.html`).
7. **Flash categories:** `'success'`, `'danger'`, `'warning'`, `'info'` -- map to Bootstrap `alert-{category}`. Use `'danger'` NOT `'error'`.
8. **Mutation logging:** All data changes must be logged via the mutation logger. (Status derivation is read-only, so no mutation logging needed for this story.)
9. **Service function pattern:** Accept primitive types, return model instances or dicts. Raise domain exceptions on failure. Handle their own `db.session.commit()` if writing (read-only for this story).

### Critical Implementation Details

#### Status Derivation Logic

The status_service MUST implement this exact derivation:

```python
def compute_equipment_status(equipment_id: int) -> dict:
    """
    Compute equipment status from open repair records.

    Returns dict with keys:
        - color: 'green' | 'yellow' | 'red'
        - label: 'Operational' | 'Degraded' | 'Down'
        - issue_description: str | None (brief description from highest severity record)
        - severity: str | None (raw severity value from highest severity record)

    Raises:
        EquipmentNotFound: if equipment_id doesn't exist
    """
```

**Severity priority** (already established in `repair_service.py` as `_SEVERITY_PRIORITY`):
- Down = priority 0 (highest) -> red/Down
- Degraded = priority 1 -> yellow/Degraded
- Not Sure = priority 2 -> yellow/Degraded (FR33: "Not Sure" displays as yellow)
- No severity / no open records -> green/Operational

**"Open" records** = status NOT in `CLOSED_STATUSES` (already defined in `repair_service.py`):
```python
CLOSED_STATUSES = ['Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']
```

Import `CLOSED_STATUSES` from `repair_service` -- do NOT redefine it.

#### Dashboard Service Function

```python
def get_area_status_dashboard() -> list[dict]:
    """
    Get all non-archived areas with their non-archived equipment and computed statuses.

    Returns list of dicts:
        [
            {
                'area': Area instance,
                'equipment': [
                    {
                        'equipment': Equipment instance,
                        'status': {color, label, issue_description, severity}
                    },
                    ...
                ]
            },
            ...
        ]
    """
```

**Performance note:** Use efficient querying -- avoid N+1 by loading repair records with a single query or subquery. Consider using a single query that LEFT JOINs equipment with open repair records and groups by equipment_id.

#### Status Indicator Component

The `_status_indicator.html` partial MUST support three variants via a `variant` parameter:

```jinja2
{% include 'components/_status_indicator.html' with context %}
{# Pass: status (dict with color, label), variant ('large'|'compact'|'minimal') #}
```

**Color mapping to Bootstrap classes:**
- green -> `bg-success` / `text-success` / `badge bg-success`
- yellow -> `bg-warning` / `text-warning` / `badge bg-warning text-dark`
- red -> `bg-danger` / `text-danger` / `badge bg-danger`

**Icon mapping (use Bootstrap Icons via HTML entities or CSS, NOT a separate icon library):**
- green/Operational: checkmark circle (&#10003; or Unicode)
- yellow/Degraded: warning triangle (&#9888;)
- red/Down: X circle (&#10007;)

**Do NOT add Bootstrap Icons library.** Use Unicode characters or simple HTML entities for icons. The project uses vanilla Bootstrap 5 only.

**Accessibility:**
- ARIA label: `aria-label="Equipment status: {label}"`
- Color + icon + text label (three channels, never color alone)
- Sufficient contrast (Bootstrap success/warning/danger meet WCAG AA)

#### Status Dashboard Template

File: `esb/templates/public/status_dashboard.html`
Extends: `base.html` (authenticated view -- this is the member default page)

**Layout:**
- Page title: "Equipment Status"
- Area sections with heading (area name) and equipment card grid
- Responsive grid: Bootstrap `row` with `col-12 col-sm-6 col-lg-4 col-xl-3` for equipment cards
- Each card: equipment name + compact status indicator
- Yellow/red cards show brief issue description below equipment name
- Empty state: "No equipment registered yet." if no areas/equipment

**Important:** The dashboard extends `base.html` (authenticated layout with navbar), NOT `base_public.html`. The architecture spec says members see this as their default view when logged in (FR34). The kiosk display (Story 4.2) will be the unauthenticated version.

#### Route Setup

File: `esb/views/public.py`

Replace the current placeholder route:

```python
@public_bp.route('/')
def status_dashboard():
    """Status dashboard showing all equipment status by area."""
    from esb.services import status_service
    areas = status_service.get_area_status_dashboard()
    return render_template('public/status_dashboard.html', areas=areas)
```

**Authentication:** The status dashboard route at `/public/` should require `@login_required` since it's the member default view (FR34). The unauthenticated kiosk display is a separate route (Story 4.2).

**Wait -- re-reading the architecture:** The architecture says `views/public.py` handles unauthenticated requests with NO `@login_required`. But FR34 says "Members see a status dashboard as their default view" -- members here are authenticated users. Let me reconcile:

- The status dashboard at `/public/` SHOULD be accessible to both authenticated and unauthenticated users (it's public status information)
- Login redirect for members should point to `/public/`
- No `@login_required` on this route -- the dashboard is publicly viewable
- The template should extend `base_public.html` for unauthenticated users and `base.html` for authenticated users, OR simply extend `base.html` and be login-required

**Decision based on architecture doc:** The architecture says `views/public.py` has NO `@login_required`. The status dashboard should be publicly viewable. Use `base_public.html` as the base template. However, if `current_user.is_authenticated`, show the full navbar via `base.html`.

**Simplest correct approach:** Use `base.html` with `@login_required`. The kiosk and static page (Stories 4.2, 5.2) handle the unauthenticated status viewing. FR34 specifically says "Members see a status dashboard as their default view" -- this implies authenticated members, not anonymous users.

**Final decision:** Use `@login_required` and extend `base.html`. This matches FR34 and the role-based experiences pattern.

#### Login Redirect Update

File: `esb/views/auth.py`

Currently the login redirect logic is:
- Staff -> `/repairs/kanban`
- Technician -> `/repairs/queue`
- Others -> `/health`

Update "Others" (which includes unauthenticated members who log in without a technician/staff role) to redirect to `/public/` instead of `/health`. However, based on the current user model, there are only two roles: Technician and Staff. "Members" in the PRD are unauthenticated users -- they don't have accounts.

**Re-reading FR34:** "Members see a status dashboard as their default view (two-tier: summary plus drill-down on internal network)". And the architecture's Role-Based Experiences section says: "Templates: `templates/public/status_dashboard.html` (Member default)."

**But members don't log in.** Members are unauthenticated users on the local network. So the status dashboard should be publicly accessible WITHOUT login. The login redirect for Staff/Technician stays as-is.

**REVISED decision:**
- Status dashboard route at `/public/` has NO `@login_required`
- Template extends `base_public.html` (unauthenticated layout)
- This is the page members see without logging in
- Authenticated users can still access it (they just see it without the authenticated navbar)

### Navbar Update

Add "Status" link to the navbar in `base.html` for authenticated users (Staff and Technicians) so they can navigate to the dashboard from the authenticated interface. Place it as the last nav item.

### Project Structure Notes

**New files to create:**
- `esb/services/status_service.py` -- status derivation logic
- `esb/templates/public/status_dashboard.html` -- dashboard template
- `esb/templates/components/_status_indicator.html` -- reusable status indicator
- `tests/test_services/test_status_service.py` -- service tests
- `tests/test_views/test_public_views.py` -- view tests

**Files to modify:**
- `esb/views/public.py` -- replace placeholder with dashboard route
- `esb/static/css/app.css` -- add status indicator and dashboard styles
- `esb/templates/base.html` -- add Status Dashboard nav link

**Files NOT to modify (no changes needed):**
- `esb/models/` -- no new models, no migrations
- `esb/services/repair_service.py` -- import `CLOSED_STATUSES` from here, don't modify
- `esb/views/__init__.py` -- `public_bp` already registered
- `esb/__init__.py` -- app factory unchanged
- `esb/templates/base_public.html` -- use as-is
- `esb/templates/base_kiosk.html` -- used in Story 4.2, not this story

### Previous Story Intelligence (from Story 3.5)

**Patterns to follow:**
- Use `capture` fixture for mutation log assertions (NOT `caplog`)
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
- `db.session.get(Model, id)` for PK lookups
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions if needed to avoid circular imports
- 610 tests currently passing, 0 lint errors
- `CLOSED_STATUSES` and `_SEVERITY_PRIORITY` already defined in `repair_service.py`
- `relative_time` Jinja2 filter already available
- Test factories: `make_area`, `make_equipment`, `make_repair_record` in `tests/conftest.py`

**Code review issues to avoid (learned from 3.5):**
- Don't duplicate template markup -- use Jinja2 macros if needed
- Ensure title attributes on tooltips use proper Jinja2 expressions
- Match spec'd approach exactly (don't deviate from documented patterns)
- Include tests for responsive layout classes and ARIA attributes
- Remove unused fixture parameters from tests

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

Files typically touched per story implementation:
- Service module (new or modified)
- View module (new route)
- Template(s) (new)
- CSS (append to app.css)
- JS (append to app.js if needed)
- Tests (service + view tests)

### Technology Stack Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with Jinja2 templates
- **Bootstrap 5** bundled locally (no CDN)
- **Vanilla JS only** -- no npm, no build step, no jQuery
- **SQLAlchemy** via Flask-SQLAlchemy for all queries
- **pytest** for tests
- **No new dependencies required** for this story

### Testing Standards

- Test files: `test_{module}.py` in appropriate `tests/` subdirectory
- Use existing fixtures from `tests/conftest.py`: `app`, `client`, `db`, `staff_client`, `tech_client`, `make_area`, `make_equipment`, `make_repair_record`
- Class-based test grouping (e.g., `TestComputeEquipmentStatus`, `TestGetAreaStatusDashboard`, `TestStatusDashboardView`)
- All service logic tested independently
- All view routes tested (status codes, template content, redirects)
- Accessibility assertions: check for ARIA labels in rendered HTML
- No E2E/Playwright tests needed for this story (service + view level sufficient)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 Story 4.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture - Equipment Status Derivation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Cross-Cutting Concerns - Status derivation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping - FR27-FR33]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture]
- [Source: _bmad-output/planning-artifacts/architecture.md#Template Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#Architectural Boundaries - Public/Authenticated]
- [Source: _bmad-output/planning-artifacts/prd.md#FR27-FR34]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR1-NFR4 Performance]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR18-NFR21 Accessibility]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Status Indicator Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Status Grid Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Color System - Functional Status Colors]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design Table]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1 - Member Checks Status]
- [Source: _bmad-output/implementation-artifacts/3-5-staff-kanban-board.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None required.

### Completion Notes List

- Task 1: Created `esb/services/status_service.py` with `compute_equipment_status()` and `get_area_status_dashboard()`. Imports `CLOSED_STATUSES` from `repair_service`. Raises `EquipmentNotFound` for missing equipment. Handles edge case where open records have no severity set (defaults to yellow/Degraded). Dashboard function prefetches open records in one query to avoid N+1.
- Task 2: Created `esb/templates/components/_status_indicator.html` with three variants (large, compact, minimal). Uses Unicode characters for icons (no icon library). All variants include `aria-label` for accessibility. Color + icon + text = three channels.
- Task 3: Created `esb/templates/public/status_dashboard.html` extending `base.html`. Responsive grid with `col-12 col-sm-6 col-lg-4 col-xl-3`. Yellow/red cards show issue description. Empty state message for no equipment.
- Task 4: Replaced placeholder `index()` route in `esb/views/public.py` with `status_dashboard()` using `@login_required`. Calls `status_service.get_area_status_dashboard()`.
- Task 5: Added "Status" nav link to `base.html` for authenticated users. Updated login redirect fallback (non-staff, non-technician users) from `/health` to `/public/`. Updated already-authenticated redirect from `/health` to `/public/`.
- Task 6: 15 service tests covering all status derivation rules, severity priority, archived exclusions, area sorting, empty dashboard, and EquipmentNotFound.
- Task 7: 12 view tests covering auth redirect, staff/tech access, area headings, equipment names, CSS classes, issue descriptions, empty state, archived exclusion, ARIA labels, and responsive layout classes.
- Fixed 1 regression in `test_auth_views.py` (already-authenticated redirect changed from `/health` to `/public/`).
- Fixed 1 lint error (unused variable `green_equip`).

### Senior Developer Review (AI)

**Reviewer:** Claude Opus 4.6 (code-review workflow) — 2026-02-15

**Issues Found:** 2 High, 3 Medium, 2 Low — **All fixed automatically**

- **[H1] FIXED** Duplicated status derivation logic violated AC #2 "single source of truth." Extracted `_derive_status_from_records()` helper used by both `compute_equipment_status()` and `get_area_status_dashboard()`.
- **[H2] FIXED** N+1 equipment query in `get_area_status_dashboard()` (one query per area). Refactored to fetch all non-archived equipment in a single query and group by `area_id` in Python.
- **[M1] FIXED** Missing view test for "Down" severity showing issue description on dashboard. Added `test_issue_description_for_down_equipment`.
- **[M2] FIXED** Missing view test for "Not Sure" displaying as yellow/bg-warning (AC #3). Added `test_not_sure_severity_displays_as_yellow`.
- **[M3] FIXED** `sprint-status.yaml` changed but not documented in story File List. Added to File List.
- **[L1] FIXED** `status-card-green` CSS class generated in HTML but no CSS rule. Added `status-card-green` rule with green left border for visual consistency.
- **[L2] FIXED** Blueprint naming friction (`public_bp` with `@login_required`). Added module-level docstring explaining the intentional `@login_required` for FR34 and that Story 4.2 kiosk routes will not require login.

**Test Results:** 639 passed, 0 lint errors.

### Change Log

- 2026-02-15: Code review fixes — extracted shared derivation helper, fixed N+1 query, added 2 view tests, CSS/doc fixes
- 2026-02-15: Implemented Story 4.1 — Equipment Status Derivation & Status Dashboard

### File List

New files:
- esb/services/status_service.py
- esb/templates/components/_status_indicator.html
- esb/templates/public/status_dashboard.html
- tests/test_services/test_status_service.py
- tests/test_views/test_public_views.py

Modified files:
- esb/views/public.py
- esb/views/auth.py
- esb/templates/base.html
- esb/static/css/app.css
- tests/test_views/test_auth_views.py
- _bmad-output/implementation-artifacts/sprint-status.yaml
