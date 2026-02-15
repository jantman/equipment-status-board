# Story 3.4: Technician Repair Queue

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Technician,
I want to see a sortable and filterable repair queue as my default landing page,
so that I can quickly find the highest-impact repair to work on.

## Acceptance Criteria

1. **Default Landing Page:** Given I am logged in as a Technician, when I am redirected after login, then I land on the repair queue page (`/repairs/queue`).

2. **Table Display & Default Sort:** Given I am on the repair queue page, when the page loads, then I see a table with columns: equipment name, severity, area, age (time since creation), status, and assignee. The default sort is by severity (Down first) then age (oldest first).

3. **Column Sorting:** Given I am on the repair queue page, when I click a column header, then the table sorts by that column (toggle ascending/descending).

4. **Area Filtering:** Given I am on the repair queue page, when I select an area from the filter dropdown, then the table shows only repair records for equipment in that area.

5. **Status Filtering:** Given I am on the repair queue page, when I select a status from the filter dropdown, then the table shows only repair records with that status.

6. **Severity Visual Indicators:** Given severity is displayed in the table, when I view a row, then severity is indicated with a color-coded visual indicator (red/`bg-danger` for Down, yellow/`bg-warning` for Degraded and Not Sure).

7. **Mobile Responsive Layout:** Given I am on the repair queue page on a mobile device (viewport < 768px), when the page renders, then table rows are displayed as stacked cards showing equipment name, severity, status, area, and age. There is no horizontal scrolling.

8. **Navigation to Detail:** Given I am on the repair queue page, when I click/tap a row or card, then I navigate to the repair record detail page (`/repairs/<id>`).

9. **Empty State:** Given there are no open repair records, when the page loads, then I see a centered message: "No open repair records. All equipment is operational."

## Tasks / Subtasks

- [x] Task 1: Add queue service function (AC: #2, #4, #5)
  - [x] 1.1 Add `get_repair_queue()` function to `esb/services/repair_service.py` that returns open repair records (all statuses except "Resolved", "Closed - No Issue Found", "Closed - Duplicate") with eager-loaded equipment and area relationships
  - [x] 1.2 Support optional `area_id` filter parameter
  - [x] 1.3 Support optional `status` filter parameter
  - [x] 1.4 Default ordering: severity (Down=0, Degraded=1, Not Sure=2, NULL=3) then age (oldest first via `created_at` ASC)
  - [x] 1.5 Return list of dicts or model instances with computed `age` field (timedelta from `created_at` to now)

- [x] Task 2: Add queue route and view function (AC: #1, #2, #4, #5, #8, #9)
  - [x] 2.1 Add `queue()` route at `GET /repairs/queue` in `esb/views/repairs.py` with `@role_required('technician')`
  - [x] 2.2 Query all areas for the area filter dropdown
  - [x] 2.3 Query statuses for the status filter dropdown (use `REPAIR_STATUSES` constant, exclude closed statuses from default)
  - [x] 2.4 Call `repair_service.get_repair_queue()` with filter params from query string (`?area=<id>&status=<value>`)
  - [x] 2.5 Pass repair records, areas, statuses, and active filters to template
  - [x] 2.6 Update `index()` to redirect to `repairs.queue` instead of `repairs.create`

- [x] Task 3: Update login redirect for technicians (AC: #1)
  - [x] 3.1 In the login view (`esb/views/auth.py`), after successful login, redirect Technician-role users to `/repairs/queue` instead of the default
  - [x] 3.2 Staff users should also be able to access the queue but their default landing can remain unchanged
  - [x] 3.3 Respect `next` parameter in URL if present (existing Flask-Login behavior)

- [x] Task 4: Update navbar (AC: #1)
  - [x] 4.1 In `esb/templates/base.html`, change the "Repairs" navbar link from `url_for('repairs.create')` to `url_for('repairs.queue')`
  - [x] 4.2 Keep the active class logic: `{% if request.endpoint and request.endpoint.startswith('repairs.') %}`

- [x] Task 5: Create queue template with responsive table/cards (AC: #2, #6, #7, #8, #9)
  - [x] 5.1 Create `esb/templates/repairs/queue.html` extending `base.html`
  - [x] 5.2 Add breadcrumb: Home > Repair Queue
  - [x] 5.3 Add filter dropdowns (area, status) at top, styled with Bootstrap `form-select` inline in a row
  - [x] 5.4 Create responsive table (`d-none d-md-block`) with columns: Equipment Name, Severity, Area, Age, Status, Assignee
  - [x] 5.5 Add severity color indicators: `bg-danger` badge for Down, `bg-warning text-dark` badge for Degraded/Not Sure, `bg-secondary` if null
  - [x] 5.6 Display age as human-readable relative time using `relative_time` Jinja2 filter
  - [x] 5.7 Make each row a clickable link to `url_for('repairs.detail', id=record.id)`
  - [x] 5.8 Create mobile card layout (`d-md-none`) showing equipment name, severity badge, status badge, area, and age per card
  - [x] 5.9 Make each card a clickable link to detail page
  - [x] 5.10 Add empty state message when no records exist
  - [x] 5.11 Add `data-*` attributes on table headers for JS sort functionality
  - [x] 5.12 Add `data-*` attributes on rows/cards for JS filter functionality

- [x] Task 6: Add client-side sorting JavaScript (AC: #3)
  - [x] 6.1 Add table sorting logic to `esb/static/js/app.js`
  - [x] 6.2 Click column header toggles ascending/descending sort
  - [x] 6.3 Add visual sort direction indicator (arrow/caret) on active sort column
  - [x] 6.4 Sorting works on: equipment name (alpha), severity (numeric priority), area (alpha), age (numeric), status (alpha), assignee (alpha)
  - [x] 6.5 Default sort on page load: severity desc (Down first) then age asc (oldest first)

- [x] Task 7: Add client-side filtering JavaScript (AC: #4, #5)
  - [x] 7.1 Add filter logic to `esb/static/js/app.js` that hides/shows table rows and cards based on selected area and status
  - [x] 7.2 Area filter dropdown shows all areas, "All Areas" as default
  - [x] 7.3 Status filter dropdown shows open statuses, "All Statuses" as default
  - [x] 7.4 Filters work together (AND logic: area AND status)
  - [x] 7.5 Update empty state if all rows filtered out
  - [x] 7.6 Filters work on both desktop table and mobile cards

- [x] Task 8: Service tests (AC: #2, #4, #5)
  - [x] 8.1 Add `TestGetRepairQueue` class to `tests/test_services/test_repair_service.py`
  - [x] 8.2 Test returns only open records (excludes Resolved, Closed statuses)
  - [x] 8.3 Test default sort order: severity priority then age
  - [x] 8.4 Test area_id filter
  - [x] 8.5 Test status filter
  - [x] 8.6 Test combined area + status filter
  - [x] 8.7 Test empty result set
  - [x] 8.8 Test includes equipment name, area name, assignee username via relationships

- [x] Task 9: View tests (AC: #1, #2, #4, #5, #8, #9)
  - [x] 9.1 Add `TestRepairQueue` class to `tests/test_views/test_repair_views.py`
  - [x] 9.2 Test queue page loads with 200 for technician
  - [x] 9.3 Test queue page loads with 200 for staff
  - [x] 9.4 Test queue page redirects unauthenticated to login
  - [x] 9.5 Test queue displays repair records with correct columns
  - [x] 9.6 Test queue shows severity badges with correct CSS classes
  - [x] 9.7 Test queue shows empty state message when no open records
  - [x] 9.8 Test area filter parameter works
  - [x] 9.9 Test status filter parameter works
  - [x] 9.10 Test index route redirects to queue
  - [x] 9.11 Test login redirects technician to repair queue
  - [x] 9.12 Test navbar contains link to repair queue

## Dev Notes

### Architecture Compliance (MANDATORY)

- **Service Layer Pattern**: ALL query/filter logic MUST go in `repair_service.py`. The view function calls the service and passes results to the template. Views are thin controllers.
- **Dependency flow**: `views -> services -> models`. Never reverse.
- **Auth decorator**: `@role_required('technician')` on the queue route. Staff can also access (hierarchy: staff > technician).
- **No new models or migrations required**. Story 3.4 is a read-only view over existing `RepairRecord`, `Equipment`, and `Area` data.
- **Single CSS file**: All custom styles go in `esb/static/css/app.css`. No per-page CSS files.
- **Single JS file**: All custom JavaScript goes in `esb/static/js/app.js`. No per-page JS files.
- **Vanilla JavaScript only**: No jQuery, no React, no Vue, no npm packages.

### Critical Implementation Details

#### Severity Sort Priority
The severity column has a business-defined sort priority that differs from alphabetical:
- **Down** = priority 0 (highest/first)
- **Degraded** = priority 1
- **Not Sure** = priority 2
- **NULL/empty** = priority 3 (lowest/last)

For server-side default sort, use a SQL `CASE` expression or Python-level sort. For client-side JS sort, embed `data-severity-priority` attributes on each row.

#### "Open" Repair Records Definition
The queue displays records whose status is NOT one of:
- "Resolved"
- "Closed - No Issue Found"
- "Closed - Duplicate"

This means records with statuses: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist are shown.

Reference constant: `REPAIR_STATUSES` in `esb/models/repair_record.py`

#### Age Calculation
Age = `datetime.now(UTC) - record.created_at`
Display using the existing `relative_time` Jinja2 filter from `esb/utils/filters.py`.
For sorting, use the raw `created_at` timestamp (oldest first = ASC).

#### Login Redirect Behavior
The login view is in `esb/views/auth.py`. After successful authentication:
- If `next` parameter is in the URL query string, redirect there (existing Flask-Login behavior - preserve this)
- If no `next` parameter and user is Technician role: redirect to `/repairs/queue`
- If no `next` parameter and user is Staff role: keep existing default behavior (or also redirect to queue if no other default exists)

#### Navbar Update
In `esb/templates/base.html`, the current Repairs link points to `{{ url_for('repairs.create') }}`. Change to `{{ url_for('repairs.queue') }}`. The active class check already uses `request.endpoint.startswith('repairs.')` which will continue to work.

#### Client-Side Sorting/Filtering Strategy
Given the small dataset size (a makerspace will have at most dozens of open repairs), client-side sorting and filtering provides the best UX (instant, no page reload). Implementation approach:

1. **Data attributes on rows**: Each `<tr>` (and mobile card) should have `data-severity-priority`, `data-area-id`, `data-status`, `data-age-seconds`, `data-equipment-name`, `data-assignee` attributes
2. **Sort by clicking headers**: Toggle between asc/desc, update sort indicator arrow
3. **Filter by dropdowns**: Hide rows that don't match selected area/status using CSS `display: none`
4. **Combined filter+sort**: Apply filters first (hide/show), then sort only visible rows

Server-side also provides initial filter params via query string (`?area=<id>&status=<value>`) for bookmarkable/shareable URLs, but JS provides instant filtering on top.

#### Responsive Table-to-Cards Transformation
- Desktop (>= 768px): Standard Bootstrap table with `<thead>` and `<tbody>`, class `d-none d-md-block`
- Mobile (< 768px): Stacked cards using Bootstrap `card` component, class `d-md-none`
- Both layouts rendered in the same template, toggled by Bootstrap responsive display classes
- Both layouts have the same `data-*` attributes for JS filtering to work on both

### Existing Code to Modify

| File | Action | What Changes |
|------|--------|-------------|
| `esb/services/repair_service.py` | MODIFY | Add `get_repair_queue()` function |
| `esb/views/repairs.py` | MODIFY | Add `queue()` route, update `index()` redirect |
| `esb/views/auth.py` | MODIFY | Add role-based redirect after login |
| `esb/templates/base.html` | MODIFY | Update Repairs navbar link to queue |
| `esb/static/js/app.js` | MODIFY | Add table sort and filter logic |
| `esb/static/css/app.css` | MODIFY | Add queue-specific styles (severity indicators, sort arrows, card layout) |
| `tests/test_services/test_repair_service.py` | MODIFY | Add TestGetRepairQueue tests |
| `tests/test_views/test_repair_views.py` | MODIFY | Add TestRepairQueue tests |

### New Files to Create

| File | Purpose |
|------|---------|
| `esb/templates/repairs/queue.html` | Repair queue page template |

### Existing Patterns to Follow

**Service function pattern** (from `repair_service.py`):
```python
def get_repair_queue(area_id=None, status=None):
    """Get open repair records for technician queue."""
    # Query, filter, sort, return
```

**View route pattern** (from `repairs.py`):
```python
@repairs_bp.route('/queue')
@role_required('technician')
def queue():
    """Technician repair queue page."""
    # Call service, render template
```

**Template pattern** (from existing pages):
- Extends `base.html`
- Bootstrap breadcrumbs
- Bootstrap table with `table-hover` class
- Badge components for severity/status
- Use `relative_time` filter for age display
- Use `format_datetime` filter for tooltips on age column

**Test pattern** (from existing tests):
- Class-based grouping: `TestGetRepairQueue`, `TestRepairQueueView`
- Use `make_repair_record` fixture factory
- Use `staff_client` and `tech_client` fixtures
- Assert HTTP status codes, response body content, redirects

### Previous Story Intelligence (Story 3.3)

**Key learnings from Story 3.3 that apply:**
- Use `capture` fixture for mutation log assertions (NOT `caplog`)
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
- `db.session.get(Model, id)` for PK lookups in assertions
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions if needed to avoid circular imports
- Use existing fixtures from `tests/conftest.py`: `make_repair_record`, `staff_user`, `tech_user`, etc.
- **Story 3.3 left 565 tests passing, 0 lint errors**
- The `repairs.index` route was intentionally left as a redirect placeholder for this story

### Git Intelligence Summary

**Recent commit pattern**: Three-commit cadence per story:
1. Context commit (this file + sprint-status update)
2. Implementation commit (all code, tests, templates)
3. Code review fix commit (addresses review findings)

**File modification patterns from Stories 3.1-3.3:**
- Models in `esb/models/` with constants in the model file
- Services as module-level functions in `esb/services/`
- Views as blueprint routes in `esb/views/`
- Templates extend `base.html`, use Bootstrap 5, include breadcrumbs
- Tests mirror source structure with class-based grouping
- All commits pass `ruff` linting and full test suite

### Project Structure Notes

- Alignment with unified project structure: This story creates the queue view exactly where the architecture specifies (`esb/templates/repairs/queue.html`, `esb/views/repairs.py`)
- The `_repair_queue_row.html` component partial referenced in architecture may be created if the row/card markup warrants extraction, but given it's only used in `queue.html`, inline rendering is acceptable
- No detected conflicts or variances with architecture

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 3, Story 3.4 lines 677-721]
- [Source: _bmad-output/planning-artifacts/architecture.md - Code Structure, Service Layer, View Function Pattern, Template Organization]
- [Source: _bmad-output/planning-artifacts/prd.md - FR35: Technician Repair Queue]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md - Work Queue Pattern, Effortless Interactions, Journey 2: Technician Works the Repair Queue]
- [Source: _bmad-output/implementation-artifacts/3-3-repair-timeline-notes-photos.md - Dev Notes, File List, Completion Notes]
- [Source: esb/views/repairs.py - Current index() redirect, existing route patterns]
- [Source: esb/services/repair_service.py - Existing service functions pattern]
- [Source: esb/models/repair_record.py - REPAIR_STATUSES, REPAIR_SEVERITIES constants]
- [Source: esb/utils/decorators.py - role_required decorator]
- [Source: esb/utils/filters.py - relative_time, format_datetime filters]
- [Source: esb/templates/base.html - Current navbar structure]
- [Source: tests/conftest.py - Available test fixtures]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed timezone mismatch: `now_utc` passed to template as naive datetime (`.replace(tzinfo=None)`) to match naive `created_at` column values from SQLite test DB.

### Completion Notes List

- Task 1+8: Added `get_repair_queue()` service function with SQL CASE severity sort, CLOSED_STATUSES constant, area_id/status filters. 7 service tests pass.
- Task 2: Added `queue()` route with `@role_required('technician')`, updated `index()` redirect to queue.
- Task 3: Updated `auth.py` login redirect — technicians go to `/repairs/queue`, staff keeps default. `next` param preserved.
- Task 4: Updated navbar Repairs link from `repairs.create` to `repairs.queue`. Active class logic unchanged.
- Task 5: Created `queue.html` with responsive table (desktop) + cards (mobile), severity badges, age via `relative_time` filter, empty state, data-* attributes for JS.
- Task 6: Added client-side table sorting JS with click-to-toggle asc/desc, sort indicators, severity numeric priority support.
- Task 7: Added client-side filtering JS for area/status dropdowns with AND logic, works on both table rows and mobile cards, updates empty state.
- Task 9: 12 view tests covering access control, display, filters, redirects, navbar link.
- All 584 tests pass, 0 ruff lint errors.
- Code Review Fix: Added `joinedload()` for equipment/area/assignee in `get_repair_queue()` (was N+1). Added keyboard accessibility (`tabindex`, `keydown` handler) to table rows. Added `aria-label` to filter dropdowns. Fixed `visibleCount` double-counting in JS. Added comment for timezone workaround. Added 3 new view tests (combined filter, assignee display, mobile cards). All 587 tests pass, 0 lint errors.

### Change Log

- 2026-02-15: Implemented Story 3.4 — Technician Repair Queue (all 9 tasks, 19 new tests)
- 2026-02-15: Code review fixes — eager loading, keyboard a11y, aria-labels, JS visibleCount, 3 new tests (22 total new)

### File List

- `esb/services/repair_service.py` (modified) — Added `CLOSED_STATUSES`, `_SEVERITY_PRIORITY`, `get_repair_queue()`
- `esb/views/repairs.py` (modified) — Added `queue()` route, updated `index()` redirect, added datetime import
- `esb/views/auth.py` (modified) — Added technician role-based redirect to `/repairs/queue` after login
- `esb/templates/base.html` (modified) — Changed Repairs navbar link to `repairs.queue`
- `esb/templates/repairs/queue.html` (new) — Repair queue page with responsive table/cards
- `esb/static/js/app.js` (modified) — Added table sorting and filtering JavaScript
- `esb/static/css/app.css` (modified) — Added sortable header styles
- `tests/test_services/test_repair_service.py` (modified) — Added `TestGetRepairQueue` (7 tests)
- `tests/test_views/test_repair_views.py` (modified) — Added `TestRepairQueue` (15 tests)
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Story status updated
- `_bmad-output/implementation-artifacts/3-4-technician-repair-queue.md` (modified) — Story file updated
