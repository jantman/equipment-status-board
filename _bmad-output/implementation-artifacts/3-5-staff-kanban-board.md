# Story 3.5: Staff Kanban Board

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to see a Kanban board of all open repairs as my default landing page,
so that I can instantly identify what's stuck and needs my attention.

## Acceptance Criteria

1. **Default Landing Page:** Given I am logged in as Staff, when I am redirected after login, then I land on the Kanban board page (`/repairs/kanban`).

2. **Kanban Columns:** Given I am on the Kanban board, when the page loads, then I see columns for: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist. Resolved and Closed statuses are excluded from the Kanban.

3. **Card Ordering:** Given a Kanban column contains cards, when it displays them, then cards are ordered by time-in-column (oldest at top). Each card shows: equipment name, area badge, severity indicator (compact), time-in-column text.

4. **Column Headers:** Given the column header, when I view it, then it shows the status name and count of cards in that column.

5. **Aging — Default (0-2 days):** Given a card has been in its current column for 0-2 days, when I view it, then it has default card styling.

6. **Aging — Warm (3-5 days):** Given a card has been in its current column for 3-5 days, when I view it, then it has a subtle warm background tint indicating it may need attention.

7. **Aging — Hot (6+ days):** Given a card has been in its current column for 6+ days, when I view it, then it has a stronger visual indicator (darker accent border or background) signaling it is stuck.

8. **Card Click-Through:** Given I am on the Kanban board, when I click a card, then I navigate to the full repair record detail page (new page, not modal).

9. **Read-Only Board:** Given I am on the Kanban board, when I try to drag a card, then nothing happens — the board is read-only (no drag-and-drop).

10. **Desktop Layout:** Given I am on the Kanban board on desktop (viewport >= 992px), when the page renders, then columns are displayed horizontally with horizontal scrolling if needed, each column ~250px wide.

11. **Mobile Layout:** Given I am on the Kanban board on mobile (viewport < 992px), when the page renders, then columns stack vertically as collapsible accordion sections.

12. **Empty State:** Given there are no open repair records, when the page loads, then empty columns with headers are visible and a centered message reads: "No open repair records. All equipment is operational."

13. **Accessibility:** Given Kanban column regions, when accessed via keyboard or screen reader, then each column is an ARIA-labeled region and cards are focusable and activatable via Enter key.

## Tasks / Subtasks

- [x]Task 1: Add Kanban service function (AC: #2, #3, #4, #5, #6, #7)
  - [x]1.1 Add `get_kanban_data()` function to `esb/services/repair_service.py` that returns open repair records grouped by status column
  - [x]1.2 Exclude CLOSED_STATUSES (Resolved, Closed - No Issue Found, Closed - Duplicate) — reuse existing `CLOSED_STATUSES` constant
  - [x]1.3 Define `KANBAN_COLUMNS` constant as ordered list: `['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered', 'Parts Received', 'Needs Specialist']`
  - [x]1.4 For each column, return records ordered by time-in-current-status (oldest first). Time-in-column = now - last status_change timeline entry timestamp (or `created_at` if status is still "New" with no status changes)
  - [x]1.5 Eager-load equipment (with area) and assignee relationships to avoid N+1
  - [x]1.6 Return a dict of `{status: [records]}` with each record annotated with `time_in_column` (timedelta or seconds)

- [x]Task 2: Add Kanban route and view function (AC: #1, #2, #4, #12)
  - [x]2.1 Add `kanban()` route at `GET /repairs/kanban` in `esb/views/repairs.py` with `@role_required('technician')` (staff inherits access via hierarchy)
  - [x]2.2 Call `repair_service.get_kanban_data()` to get grouped records
  - [x]2.3 Pass kanban data, column definitions, and current UTC time to template
  - [x]2.4 Compute aging tier for each card in the view: 0-2 days = 'default', 3-5 days = 'warm', 6+ days = 'hot'

- [x]Task 3: Update login redirect for Staff (AC: #1)
  - [x]3.1 In `esb/views/auth.py`, after successful login, redirect Staff-role users to `/repairs/kanban`
  - [x]3.2 Technicians continue to redirect to `/repairs/queue` (preserve existing behavior)
  - [x]3.3 Respect `next` parameter in URL if present (existing behavior)

- [x]Task 4: Update navbar for Staff (AC: #1)
  - [x]4.1 In `esb/templates/base.html`, add a "Kanban" navigation link for Staff users pointing to `url_for('repairs.kanban')`
  - [x]4.2 Place the Kanban link before the existing Repairs link in the nav order
  - [x]4.3 Add active class logic: highlight when `request.endpoint == 'repairs.kanban'`

- [x]Task 5: Create Kanban template with responsive layout (AC: #2, #3, #4, #5, #6, #7, #8, #10, #11, #12, #13)
  - [x]5.1 Create `esb/templates/repairs/kanban.html` extending `base.html`
  - [x]5.2 Add breadcrumb: Home > Kanban Board
  - [x]5.3 Desktop layout (>= 992px): horizontal flexbox container with `overflow-x: auto`, each column ~250px min-width
  - [x]5.4 Each column: header with status name + card count badge, then a card list
  - [x]5.5 Each card: equipment name (bold), area badge (`badge bg-secondary`), severity indicator (compact: colored badge), time-in-column text (relative format)
  - [x]5.6 Aging CSS classes: `kanban-card-default` (no extra styling), `kanban-card-warm` (subtle warm background), `kanban-card-hot` (stronger accent border/background)
  - [x]5.7 Each card is an `<a>` tag linking to `url_for('repairs.detail', id=record.id)` for click-through navigation
  - [x]5.8 Mobile layout (< 992px): Bootstrap accordion component with one panel per status column, collapsed by default except columns with cards
  - [x]5.9 Add ARIA attributes: `role="region"` and `aria-label` on each column, `tabindex="0"` and keyboard Enter handler on cards
  - [x]5.10 Empty state: show column headers with "(0)" count and centered message below
  - [x]5.11 Add `title` attribute on time-in-column showing exact datetime

- [x]Task 6: Add Kanban CSS styles (AC: #5, #6, #7, #10)
  - [x]6.1 Add Kanban-specific styles to `esb/static/css/app.css`
  - [x]6.2 `.kanban-container`: flexbox, horizontal scroll on desktop
  - [x]6.3 `.kanban-column`: min-width 250px, flex-shrink 0
  - [x]6.4 `.kanban-card-warm`: subtle warm background tint (e.g., `rgba(255, 193, 7, 0.1)` — Bootstrap warning at 10% opacity)
  - [x]6.5 `.kanban-card-hot`: stronger indicator (e.g., left border `3px solid #fd7e14` or `rgba(255, 193, 7, 0.25)` background)
  - [x]6.6 Responsive: hide horizontal layout below 992px, show accordion instead

- [x]Task 7: Add Kanban JavaScript for keyboard accessibility (AC: #8, #13)
  - [x]7.1 Add keyboard handler to `esb/static/js/app.js` for Kanban cards: Enter key navigates to card href
  - [x]7.2 Reuse the existing clickable-row pattern from queue (data-href + keydown handler)

- [x]Task 8: Service tests (AC: #2, #3, #4, #5, #6, #7)
  - [x]8.1 Add `TestGetKanbanData` class to `tests/test_services/test_repair_service.py`
  - [x]8.2 Test returns only open records (excludes Resolved, Closed statuses)
  - [x]8.3 Test records are grouped by status into correct columns
  - [x]8.4 Test ordering within columns: oldest time-in-column first
  - [x]8.5 Test time-in-column calculation uses last status_change timestamp
  - [x]8.6 Test time-in-column falls back to created_at when no status changes
  - [x]8.7 Test empty columns are included in result dict
  - [x]8.8 Test eager loading includes equipment name, area name, assignee

- [x]Task 9: View tests (AC: #1, #2, #4, #8, #10, #11, #12, #13)
  - [x]9.1 Add `TestKanbanBoard` class to `tests/test_views/test_repair_views.py`
  - [x]9.2 Test kanban page loads with 200 for staff
  - [x]9.3 Test kanban page loads with 200 for technician (accessible via hierarchy)
  - [x]9.4 Test kanban page redirects unauthenticated to login
  - [x]9.5 Test kanban displays column headers with status names
  - [x]9.6 Test kanban shows card count in column headers
  - [x]9.7 Test kanban cards contain equipment name and area
  - [x]9.8 Test kanban cards contain severity badges
  - [x]9.9 Test kanban shows empty state message when no open records
  - [x]9.10 Test kanban card links to repair detail page
  - [x]9.11 Test login redirects staff to kanban
  - [x]9.12 Test navbar contains kanban link for staff
  - [x]9.13 Test aging classes applied correctly (warm for 3-5 days, hot for 6+)

## Dev Notes

### Architecture Compliance (MANDATORY)

- **Service Layer Pattern**: ALL query/grouping logic MUST go in `repair_service.py`. The view function calls the service and passes results to the template. Views are thin controllers.
- **Dependency flow**: `views -> services -> models`. Never reverse.
- **Auth decorator**: `@role_required('technician')` on the kanban route. Staff can also access (hierarchy: staff > technician).
- **No new models or migrations required**. Story 3.5 is a read-only view over existing `RepairRecord`, `RepairTimelineEntry`, `Equipment`, and `Area` data.
- **Single CSS file**: All custom styles go in `esb/static/css/app.css`. No per-page CSS files.
- **Single JS file**: All custom JavaScript goes in `esb/static/js/app.js`. No per-page JS files.
- **Vanilla JavaScript only**: No jQuery, no React, no Vue, no npm packages.

### Critical Implementation Details

#### Kanban Column Definitions
The Kanban displays 7 columns corresponding to open statuses. Use the existing `REPAIR_STATUSES` constant from `esb/models/repair_record.py` but exclude closed statuses. Define:
```python
KANBAN_COLUMNS = [s for s in REPAIR_STATUSES if s not in CLOSED_STATUSES]
```
This yields: `['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered', 'Parts Received', 'Needs Specialist']`

#### Time-in-Column Calculation
This is the most critical computation. For each repair record:
1. Query `RepairTimelineEntry` for the most recent `entry_type='status_change'` where `new_value` matches the record's current status
2. If found: `time_in_column = now_utc - timeline_entry.created_at`
3. If NOT found (record has never had a status change, i.e., still "New"): `time_in_column = now_utc - record.created_at`
4. This must be calculated in the service function, not in the template

**Important**: Use the `RepairTimelineEntry` model's `new_value` field which stores the new status value on status_change entries (confirmed from Story 3.2 implementation).

#### Aging Thresholds
- **Default** (0-2 days): No extra CSS class. Standard Bootstrap card styling.
- **Warm** (3-5 days): CSS class `kanban-card-warm`. Subtle warm tint.
- **Hot** (6+ days): CSS class `kanban-card-hot`. Stronger visual indicator.

Calculate in the view function based on `time_in_column`:
```python
def _aging_tier(seconds):
    days = seconds / 86400
    if days >= 6:
        return 'hot'
    elif days >= 3:
        return 'warm'
    return 'default'
```

#### Login Redirect Behavior
Current behavior in `esb/views/auth.py` (line ~35):
- If `next` parameter exists, redirect there
- If user is Technician: redirect to `/repairs/queue`
- Otherwise: redirect to `health` endpoint

Change to:
- If `next` parameter exists, redirect there
- If user is Staff: redirect to `/repairs/kanban`
- If user is Technician: redirect to `/repairs/queue`
- Otherwise: redirect to `health` endpoint

**Important**: Staff check must come BEFORE Technician check because `@role_required('technician')` allows Staff access. The redirect should distinguish between actual Staff users and actual Technician users based on `current_user.role`.

#### Navbar Update
In `esb/templates/base.html`, add a Kanban link visible to Staff users:
```html
{% if current_user.role == 'staff' %}
<li class="nav-item">
    <a class="nav-link {% if request.endpoint == 'repairs.kanban' %}active{% endif %}" href="{{ url_for('repairs.kanban') }}">Kanban</a>
</li>
{% endif %}
```
Place this BEFORE the existing "Repairs" link. Per UX spec: Staff nav links are "Kanban, Repair Queue, Equipment, Users, Status Dashboard".

#### Desktop Layout Strategy
Use a flexbox container with `overflow-x: auto` for horizontal scrolling when columns exceed viewport width:
```css
.kanban-container {
    display: flex;
    gap: 1rem;
    overflow-x: auto;
    padding-bottom: 1rem;
}
.kanban-column {
    min-width: 250px;
    flex-shrink: 0;
}
```

#### Mobile Layout Strategy (< 992px)
Use Bootstrap 5 Accordion component. Each status column becomes an accordion item:
- Accordion header shows: status name + card count badge
- Accordion body contains the card list
- Columns with 0 cards: show header but collapsed
- Columns with cards: expanded by default (use `show` class)

Use Bootstrap responsive display classes:
- `.d-none .d-lg-flex` on the horizontal kanban container
- `.d-lg-none` on the accordion container

#### Card Content
Each Kanban card should display:
- **Equipment name** (bold, primary text)
- **Area** as a `badge bg-secondary`
- **Severity** as a compact badge: `bg-danger` for Down, `bg-warning text-dark` for Degraded/Not Sure, hidden if null
- **Time-in-column** as relative text (e.g., "3 days") with `title` attribute showing full datetime
- The entire card is wrapped in an `<a>` tag linking to the repair detail page

#### Accessibility Requirements
- Each column container: `role="region"` and `aria-label="Status: {status_name}, {count} items"`
- Each card: `tabindex="0"` for keyboard focus
- JavaScript: Enter key on focused card navigates to detail page (reuse pattern from queue)
- Aging status: include in `aria-label` (e.g., "SawStop #1, Woodshop, Down, in column 7 days - needs attention")

### Existing Code to Modify

| File | Action | What Changes |
|------|--------|-------------|
| `esb/services/repair_service.py` | MODIFY | Add `KANBAN_COLUMNS` constant, `get_kanban_data()` function |
| `esb/views/repairs.py` | MODIFY | Add `kanban()` route, add `_aging_tier()` helper |
| `esb/views/auth.py` | MODIFY | Add Staff role-based redirect to `/repairs/kanban` |
| `esb/templates/base.html` | MODIFY | Add Kanban navbar link for Staff |
| `esb/static/js/app.js` | MODIFY | Add Kanban card keyboard navigation (reuse existing pattern) |
| `esb/static/css/app.css` | MODIFY | Add Kanban container, column, and aging styles |
| `tests/test_services/test_repair_service.py` | MODIFY | Add TestGetKanbanData tests |
| `tests/test_views/test_repair_views.py` | MODIFY | Add TestKanbanBoard tests |

### New Files to Create

| File | Purpose |
|------|---------|
| `esb/templates/repairs/kanban.html` | Kanban board page template |

### Existing Patterns to Follow

**Service function pattern** (from `repair_service.py`):
```python
def get_kanban_data():
    """Get open repair records grouped by status for Kanban board."""
    # Query, group, compute time-in-column, return dict
```

**View route pattern** (from `repairs.py`):
```python
@repairs_bp.route('/kanban')
@role_required('technician')
def kanban():
    """Staff Kanban board page."""
    # Call service, compute aging, render template
```

**Template pattern** (from existing pages):
- Extends `base.html`
- Bootstrap breadcrumbs
- Bootstrap cards for Kanban cards
- Badge components for severity/status/area
- Use `relative_time` filter for time-in-column display
- Use `format_datetime` filter for tooltips

**Test pattern** (from existing tests):
- Class-based grouping: `TestGetKanbanData`, `TestKanbanBoard`
- Use `make_repair_record` fixture factory
- Use `staff_client` and `tech_client` fixtures
- Assert HTTP status codes, response body content, redirects

### Previous Story Intelligence (Story 3.4)

**Key learnings from Story 3.4 that apply:**
- Use `capture` fixture for mutation log assertions (NOT `caplog`)
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
- `db.session.get(Model, id)` for PK lookups in assertions
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions if needed to avoid circular imports
- Use existing fixtures from `tests/conftest.py`: `make_repair_record`, `staff_user`, `tech_user`, etc.
- **Story 3.4 left 587 tests passing, 0 lint errors**
- The `CLOSED_STATUSES` constant and `_SEVERITY_PRIORITY` case expression are already defined in `repair_service.py`
- Client-side sorting/filtering JS is already in `app.js` — extend, don't duplicate
- The `relative_time` Jinja2 filter is already in `esb/utils/filters.py`
- Queue template patterns (responsive table/cards, data-href, severity badges) can be referenced but Kanban has a different layout
- The existing `get_repair_queue()` function does NOT compute time-in-column — the Kanban needs a different query that joins with `RepairTimelineEntry` to find the last status_change entry

### Git Intelligence Summary

**Recent commit pattern**: Three-commit cadence per story:
1. Context commit (this file + sprint-status update)
2. Implementation commit (all code, tests, templates)
3. Code review fix commit (addresses review findings)

**File modification patterns from Stories 3.1-3.4:**
- Services as module-level functions in `esb/services/`
- Views as blueprint routes in `esb/views/`
- Templates extend `base.html`, use Bootstrap 5, include breadcrumbs
- Tests mirror source structure with class-based grouping
- All commits pass `ruff` linting and full test suite
- Eager loading with `joinedload()` is the established pattern for avoiding N+1 queries

### Web Research Notes

**Bootstrap 5 Accordion** (used for mobile Kanban layout):
- Use `accordion` class on container, `accordion-item` per panel
- `accordion-header` contains a button with `data-bs-toggle="collapse"`
- `accordion-collapse` wraps the body content
- Add `show` class to auto-expand panels
- Already included in the bundled Bootstrap JS

**No external libraries needed.** The Kanban is built entirely from Bootstrap 5 cards + flexbox + accordion. No third-party Kanban library.

### Project Structure Notes

- Alignment with unified project structure: This story creates the kanban view exactly where the architecture specifies (`esb/templates/repairs/kanban.html`, `esb/views/repairs.py`)
- The `_kanban_card.html` component partial referenced in architecture may be created if the card markup warrants extraction, but given it's only used in `kanban.html`, inline rendering is acceptable
- No detected conflicts or variances with architecture

### References

- [Source: _bmad-output/planning-artifacts/epics.md - Epic 3, Story 3.5 lines 722-783]
- [Source: _bmad-output/planning-artifacts/architecture.md - Service Layer, View Function Pattern, Template Organization, Kanban section]
- [Source: _bmad-output/planning-artifacts/prd.md - FR36: Staff Kanban board, FR37: Click-through to repair records]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md - Kanban Board component, Journey 3: Staff Manages Operations, Aging Indicators, Mobile Accordion]
- [Source: _bmad-output/implementation-artifacts/3-4-technician-repair-queue.md - Dev Notes, File List, Completion Notes, Previous Story Intelligence]
- [Source: esb/views/repairs.py - Existing route patterns, queue implementation]
- [Source: esb/services/repair_service.py - CLOSED_STATUSES, get_repair_queue() pattern, _SEVERITY_PRIORITY]
- [Source: esb/models/repair_record.py - REPAIR_STATUSES, REPAIR_SEVERITIES constants]
- [Source: esb/models/repair_timeline_entry.py - entry_type values, new_value field]
- [Source: esb/views/auth.py - Current login redirect logic (technician → queue, others → health)]
- [Source: esb/templates/base.html - Current navbar structure, active class logic]
- [Source: esb/templates/repairs/queue.html - Responsive layout patterns, severity badges, data-href cards]
- [Source: esb/static/js/app.js - Existing clickable row/card keyboard handlers]
- [Source: esb/static/css/app.css - Current custom styles]
- [Source: esb/utils/filters.py - relative_time, format_datetime filters]
- [Source: tests/conftest.py - Available test fixtures]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None

### Completion Notes List

- Task 1: Added `KANBAN_COLUMNS` constant and `get_kanban_data()` to `repair_service.py`. Uses a subquery to find the latest `status_change` timeline entry per record, outer-joined to the main query. Falls back to `created_at` for records with no status changes. Annotates each record with `time_in_column` (float seconds). 7 service tests added.
- Task 2: Added `kanban()` route at `/repairs/kanban` with `@role_required('technician')`. Computes aging tier (default/warm/hot) per card. Added `_aging_tier()` helper.
- Task 3: Updated login redirect in `auth.py` — staff redirects to `/repairs/kanban`, technicians to `/repairs/queue`, others to `health`. Updated 4 existing auth tests to expect the new staff redirect target.
- Task 4: Added Kanban nav link in `base.html` for staff users, placed before the Repairs link. Active class logic excludes kanban from repairs active highlight.
- Task 5: Created `kanban.html` template with desktop horizontal flexbox layout (d-none d-lg-flex) and mobile Bootstrap accordion (d-lg-none). Cards show equipment name, area badge, severity badge, time-in-column text. Each card is an `<a>` to detail page. ARIA attributes on columns and cards. Empty state message shown when no cards.
- Task 6: Added Kanban CSS to `app.css`: `.kanban-container` (flex, overflow-x auto), `.kanban-column` (min-width 250px), `.kanban-card-warm` (warm background), `.kanban-card-hot` (orange left border + background).
- Task 7: Added keyboard handler for `a.kanban-card` elements (Enter/Space navigation) in `app.js`.
- Tasks 8-9: 7 service tests in `TestGetKanbanData`, 13 view tests in `TestKanbanBoard`. All 607 tests pass, 0 lint errors.

### Change Log

- 2026-02-15: Implemented Story 3.5 Staff Kanban Board — all 9 tasks complete, 20 new tests added (607 total), 0 regressions, 0 lint errors.

### File List

- `esb/services/repair_service.py` (modified) — Added `KANBAN_COLUMNS`, `get_kanban_data()`
- `esb/views/repairs.py` (modified) — Added `kanban()` route, `_aging_tier()` helper, imported `KANBAN_COLUMNS`
- `esb/views/auth.py` (modified) — Added staff role-based redirect to `/repairs/kanban`
- `esb/templates/base.html` (modified) — Added Kanban navbar link for staff users
- `esb/templates/repairs/kanban.html` (created) — Kanban board template with responsive layout
- `esb/static/css/app.css` (modified) — Added Kanban container, column, and aging styles
- `esb/static/js/app.js` (modified) — Added Kanban card keyboard navigation
- `tests/test_services/test_repair_service.py` (modified) — Added `TestGetKanbanData` (7 tests)
- `tests/test_views/test_repair_views.py` (modified) — Added `TestKanbanBoard` (13 tests)
- `tests/test_views/test_auth_views.py` (modified) — Updated 4 tests for staff redirect change
- `_bmad-output/implementation-artifacts/sprint-status.yaml` (modified) — Story status updated
- `_bmad-output/implementation-artifacts/3-5-staff-kanban-board.md` (modified) — Story file updated
