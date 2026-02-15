# Story 2.1: Area Management

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to create and manage Areas with Slack channel mappings,
so that equipment can be organized by physical location and notifications routed to the right channels.

## Acceptance Criteria

1. **Database Model:** Given the Area model exists with `name`, `slack_channel`, and `is_archived` fields, when Alembic migration is run, then the `areas` table is created in MySQL.

2. **Area listing:** Given I am logged in as Staff, when I navigate to Area Management (`/admin/areas`), then I see a list of all active areas with their Slack channel mappings.

3. **Creating a new area:** Given I am on the Area Management page, when I click "Add Area" and fill in name and Slack channel, then a new area is created and appears in the area list.

4. **Editing an area:** Given I am on the Area Management page, when I edit an existing area's name or Slack channel mapping, then the changes are saved and reflected in the list.

5. **Soft-deleting (archiving) an area:** Given I am on the Area Management page, when I soft-delete an area, then the area is marked as archived and no longer appears in active area lists or dropdowns, and existing equipment assigned to that area retains its association for historical records.

6. **Mutation logging:** Given any area management action (create, edit, archive), when the action is performed, then a mutation log entry is written to STDOUT.

## Tasks / Subtasks

- [x] Task 1: Create Area model and migration (AC: #1)
  - [x] 1.1 Create `esb/models/area.py` with Area model
  - [x] 1.2 Register Area model in `esb/models/__init__.py`
  - [x] 1.3 Generate and apply Alembic migration
  - [x] 1.4 Write model unit tests

- [x] Task 2: Create area service layer (AC: #2, #3, #4, #5, #6)
  - [x] 2.1 Create `esb/services/equipment_service.py` with area management functions
  - [x] 2.2 Implement `list_areas()` -- returns active (non-archived) areas
  - [x] 2.3 Implement `create_area(name, slack_channel, created_by)` with validation and mutation logging
  - [x] 2.4 Implement `get_area(area_id)` for single area retrieval
  - [x] 2.5 Implement `update_area(area_id, name, slack_channel, updated_by)` with validation and mutation logging
  - [x] 2.6 Implement `archive_area(area_id, archived_by)` with mutation logging
  - [x] 2.7 Write service unit tests

- [x] Task 3: Create area forms (AC: #3, #4)
  - [x] 3.1 Create `esb/forms/equipment_forms.py` with `AreaCreateForm` and `AreaEditForm`
  - [x] 3.2 Name field: required, max length
  - [x] 3.3 Slack channel field: required, max length

- [x] Task 4: Create area admin views (AC: #2, #3, #4, #5)
  - [x] 4.1 Add area routes to `esb/views/admin.py`: list, create, edit, archive
  - [x] 4.2 `GET /admin/areas` -- list active areas
  - [x] 4.3 `GET/POST /admin/areas/new` -- create area form
  - [x] 4.4 `GET/POST /admin/areas/<int:id>/edit` -- edit area form
  - [x] 4.5 `POST /admin/areas/<int:id>/archive` -- archive area (with confirmation)
  - [x] 4.6 Write view integration tests

- [x] Task 5: Create area templates (AC: #2, #3, #4, #5)
  - [x] 5.1 Create `esb/templates/admin/areas.html` -- area list page
  - [x] 5.2 Create `esb/templates/admin/area_form.html` -- shared create/edit form
  - [x] 5.3 Include confirmation modal for archive action
  - [x] 5.4 Empty state when no areas exist

- [x] Task 6: RBAC and edge case testing (AC: #2, #3, #4, #5, #6)
  - [x] 6.1 Verify `@role_required('staff')` on all area routes
  - [x] 6.2 Verify technician users get 403 on area routes
  - [x] 6.3 Verify unauthenticated users get redirected to login
  - [x] 6.4 Verify duplicate area name validation
  - [x] 6.5 Verify archived areas excluded from listings

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- All business logic in `esb/services/equipment_service.py` -- views are thin controllers
- Service functions accept primitive types, return model instances, raise domain exceptions
- Service functions handle their own `db.session.commit()`
- Dependency flow: `views -> services -> models` (NEVER reverse)

**File Placement (per architecture doc):**
| File | Purpose |
|------|---------|
| `esb/models/area.py` | Area SQLAlchemy model |
| `esb/services/equipment_service.py` | Area management service (NEW -- will also hold equipment CRUD in Story 2.2) |
| `esb/forms/equipment_forms.py` | Area create/edit forms (NEW -- will also hold equipment forms in Story 2.2) |
| `esb/views/admin.py` | Add area routes to EXISTING admin blueprint |
| `esb/models/__init__.py` | Add Area import for Alembic discovery |
| `esb/templates/admin/areas.html` | Area list page |
| `esb/templates/admin/area_form.html` | Shared create/edit form |

**Routes go in the EXISTING admin blueprint** (`views/admin.py`), NOT a new blueprint. The admin blueprint handles `/admin/*` routes for users, areas, and app config.

### Database Model Specification

```python
class Area(db.Model):
    __tablename__ = 'areas'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False, index=True)
    slack_channel = db.Column(db.String(80), nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))
```

**Key decisions:**
- `name`: unique, not null, indexed -- area names must be unique
- `slack_channel`: nullable -- architecture says nullable even though UX says "required field". Use form-level validation to require it, but the DB column allows NULL for flexibility
- `is_archived`: Boolean soft delete -- archived areas hidden from active lists/dropdowns but retained for FK references
- Follow the EXACT same column patterns as `User` model (see `esb/models/user.py` for reference): `datetime.now(UTC)` lambdas, String lengths, Boolean defaults

**Model registration:** Add `from esb.models.area import Area` and update `__all__` in `esb/models/__init__.py`

### Service Function Contracts

Follow the EXACT same patterns as `esb/services/user_service.py`:

```python
# esb/services/equipment_service.py

def list_areas() -> list[Area]:
    """Return all active (non-archived) areas ordered by name."""

def get_area(area_id: int) -> Area:
    """Get a single area by ID. Raises ValidationError if not found."""

def create_area(name: str, slack_channel: str, created_by: str) -> Area:
    """Create a new area. Raises ValidationError if name already exists."""

def update_area(area_id: int, name: str, slack_channel: str, updated_by: str) -> Area:
    """Update an area. Raises ValidationError if not found or name conflicts."""

def archive_area(area_id: int, archived_by: str) -> Area:
    """Soft-delete an area. Raises ValidationError if not found or already archived."""
```

**Validation rules:**
- `create_area`: Check for duplicate name (case-insensitive recommended)
- `update_area`: Check for duplicate name excluding current area
- `archive_area`: Check area exists and is not already archived

**Mutation logging events:**
- `area.created` -- data: `{id, name, slack_channel}`
- `area.updated` -- data: `{id, name, slack_channel, changes: {field: [old, new]}}`
- `area.archived` -- data: `{id, name}`

### View Route Patterns

Follow the EXACT same patterns as existing admin routes in `esb/views/admin.py`:

```python
@admin_bp.route('/areas')
@role_required('staff')
def list_areas():
    """Area management table listing all active areas."""

@admin_bp.route('/areas/new', methods=['GET', 'POST'])
@role_required('staff')
def create_area():
    """Area creation form and handler."""

@admin_bp.route('/areas/<int:id>/edit', methods=['GET', 'POST'])
@role_required('staff')
def edit_area(id):
    """Area edit form and handler."""

@admin_bp.route('/areas/<int:id>/archive', methods=['POST'])
@role_required('staff')
def archive_area(id):
    """Archive an area (soft delete)."""
```

**Error handling in views:**
- Wrap service calls in `try/except ValidationError` -- flash as `'danger'`, re-render form
- Use `flash('message', 'success')` for success, `flash('message', 'danger')` for errors
- After successful create: redirect to area list with success flash
- After successful edit: redirect to area list with success flash
- After archive: redirect to area list with success flash

### Form Patterns

Follow the EXACT same patterns as `esb/forms/admin_forms.py`:

```python
# esb/forms/equipment_forms.py

class AreaCreateForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Create Area')

class AreaEditForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=80)])
    slack_channel = StringField('Slack Channel', validators=[DataRequired(), Length(max=80)])
    submit = SubmitField('Save Changes')
```

**Note:** Labels do NOT include `*` -- asterisks are added in templates only (lesson from Story 1.4 code review).

### Template Patterns

**Area list page (`templates/admin/areas.html`):**
- Extends `base.html` (authenticated layout)
- Page title: "Area Management"
- "Add Area" primary button (top-right, same pattern as users.html)
- Bootstrap responsive table: Name, Slack Channel, Actions columns
- Actions column: Edit link + Archive button (with confirmation modal)
- Empty state: "No areas have been added yet." with "Add Area" button
- Mobile responsive: table becomes stacked cards at `<768px`

**Area form (`templates/admin/area_form.html`):**
- Extends `base.html`
- Single-column form, labels above fields
- Required fields marked with `*` in template (not in Python form labels)
- Submit button (`btn-primary`) + Cancel link (`btn-outline-secondary` to area list)
- Inline validation errors below fields

**Archive confirmation:**
- Bootstrap modal with danger styling
- "Are you sure you want to archive this area?" message
- Confirm button (`btn-danger`) + Cancel button

### UX Requirements

- **Navigation:** Area management accessible from admin section. Consider adding "Areas" link to navbar for Staff users.
- **Button hierarchy:** "Add Area" = `btn-primary` (one per page), "Edit" = link-style in rows, "Archive" = `btn-danger` with confirmation modal
- **Flash messages:** Use `components/_flash_messages.html` partial (already included in `base.html`)
- **Responsive:** Desktop = Bootstrap table, Mobile (<768px) = stacked cards
- **Empty states:** Centered message with primary action button when no areas exist

### Testing Requirements

**Test files:**
- `tests/test_models/test_area.py` -- Area model tests
- `tests/test_services/test_equipment_service.py` -- area service function tests
- `tests/test_views/test_admin_views.py` -- EXTEND existing file with area route tests

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`

**Add new fixture** to `tests/conftest.py`:
```python
def _create_area(name='Test Area', slack_channel='#test-area'):
    """Helper to create an area in the test database."""
    from esb.models.area import Area
    area = Area(name=name, slack_channel=slack_channel)
    _db.session.add(area)
    _db.session.commit()
    return area
```

**Required test coverage:**
- Model: creation, unique name constraint, defaults, `__repr__`
- Service: `list_areas` (excludes archived), `create_area` (success + duplicate name), `get_area` (success + not found), `update_area` (success + not found + name conflict), `archive_area` (success + not found + already archived), mutation logging for each
- Views: list (staff OK, tech 403, anon redirect), create GET/POST (success, validation error, duplicate name), edit GET/POST (success, not found, validation error), archive POST (success, not found, already archived)
- Mutation logging: use `capture` fixture (NOT `caplog`), verify event names and data fields

**Critical testing notes from previous stories:**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. DB queries: `db.session.get(Area, id)` for PK lookups, `db.session.execute(db.select(Area).filter_by(...)).scalar_one_or_none()` for queries
5. Parse mutation log entries from capture: `json.loads(capture.records[-1].getMessage())`

### Project Structure Notes

- All file placements match the architecture document's directory structure
- Area routes extend the existing admin blueprint -- no new blueprint needed
- `equipment_service.py` is the designated file for BOTH area management AND equipment CRUD (Story 2.2 will add to this file)
- `equipment_forms.py` is the designated file for BOTH area forms AND equipment forms
- No conflicts with existing code -- areas are a net-new feature

### Previous Story Intelligence

**Patterns to follow from Epic 1:**
- Model pattern: copy `User` model structure exactly (timestamps, column types, `__repr__`)
- Service pattern: copy `user_service.py` structure (imports, validation, mutation logging, error handling)
- View pattern: copy admin routes structure (decorator, form validation, flash, redirect)
- Form pattern: copy `admin_forms.py` structure (field definitions, validators)
- Template pattern: copy `users.html` structure (table layout, action buttons, responsive)
- Test pattern: copy `test_user_service.py` and `test_admin_views.py` structures

**Known gotchas from previous stories:**
1. `ruff target-version = "py313"` (NOT py314)
2. Mutation logger `propagate=False` -- use `_CaptureHandler` / `capture` fixture in tests
3. Flash `'danger'` not `'error'` for Bootstrap alert classes
4. Wrap ALL service calls in views with `try/except ValidationError`
5. Labels WITHOUT asterisks in Python form classes -- add `*` in templates only
6. Error templates extend `base_public.html` to avoid `current_user` dependency
7. Import `datetime` from `datetime` module: `from datetime import UTC, datetime`

### Git Intelligence

**Recent commit pattern:** Each story follows a 3-commit cycle:
1. Story context creation (SM agent)
2. Implementation (dev agent)
3. Code review fixes

**Last 5 commits:** Stories 1.3 and 1.4 (user provisioning, password management). 18 files changed, 2,148 insertions. All on linear `main` branch.

**Files most likely to be modified:**
- `esb/views/admin.py` (extend with area routes)
- `esb/models/__init__.py` (add Area import)
- `tests/conftest.py` (add area fixture)
- `tests/test_views/test_admin_views.py` (extend with area tests)

### Library/Framework Requirements

| Package | Version | Notes |
|---------|---------|-------|
| Flask | 3.1.x | Already installed |
| Flask-SQLAlchemy | 3.1.x | Already installed |
| Flask-Migrate/Alembic | Latest | Already installed -- use `flask db migrate` / `flask db upgrade` |
| Flask-WTF | 1.2.x | Already installed |
| Flask-Login | 0.6.3 | Already installed |
| Bootstrap | 5.3.8 | Bundled locally in `esb/static/` |

**No new dependencies required for this story.**

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2, Story 2.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure, Data Model, Service Layer]
- [Source: _bmad-output/planning-artifacts/prd.md#FR8, FR1, FR27, FR29, FR38]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4, Form Patterns, Table Patterns]
- [Source: esb/models/user.py -- Model pattern reference]
- [Source: esb/services/user_service.py -- Service pattern reference]
- [Source: esb/views/admin.py -- View/route pattern reference]
- [Source: esb/forms/admin_forms.py -- Form pattern reference]
- [Source: esb/templates/admin/users.html -- Template pattern reference]
- [Source: tests/conftest.py -- Test fixture pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Required `docker compose up -d db` for Alembic migration generation (MySQL needed for auto-generation)
- Installed `cryptography` package for MySQL caching_sha2_password auth during migration generation (not a runtime dependency -- only needed for dev DB connection)

### Completion Notes List

- Task 1: Area model created following exact User model patterns (timestamps, column types, `__repr__`). Alembic migration auto-generated against live MySQL. 5 model unit tests.
- Task 2: Equipment service with 5 functions (`list_areas`, `get_area`, `create_area`, `update_area`, `archive_area`). Case-insensitive duplicate name validation. Mutation logging for all write operations. 22 service unit tests.
- Task 3: `AreaCreateForm` and `AreaEditForm` with DataRequired + Length validators. Labels without asterisks per code review convention.
- Task 4: 4 area routes added to existing admin blueprint. Thin controller pattern with `try/except ValidationError`. 30 view integration tests covering CRUD, RBAC, error handling, and mutation logging.
- Task 5: `areas.html` list page with table, empty state, and archive confirmation modals. `area_form.html` shared create/edit form with inline validation. Asterisks added in templates only.
- Task 6: All RBAC tests pass -- `@role_required('staff')` on all routes, tech gets 403, anon redirected to login. Duplicate name validation and archived area exclusion tested.

### Implementation Plan

- Followed service layer pattern: views → services → models
- All business logic in `equipment_service.py`, views are thin controllers
- Case-insensitive duplicate name check using `db.func.lower()`
- Archive confirmation via Bootstrap modal with CSRF token
- `_create_area()` helper centralized in `tests/conftest.py` as `make_area` factory fixture

### File List

- `esb/models/area.py` (NEW)
- `esb/models/__init__.py` (MODIFIED -- added Area import)
- `esb/services/equipment_service.py` (NEW)
- `esb/forms/equipment_forms.py` (NEW)
- `esb/views/admin.py` (MODIFIED -- added area routes)
- `esb/templates/admin/areas.html` (NEW)
- `esb/templates/admin/area_form.html` (NEW)
- `migrations/versions/2e0d6d8be171_add_areas_table.py` (NEW)
- `tests/test_models/test_area.py` (NEW)
- `tests/test_services/test_equipment_service.py` (NEW)
- `tests/test_views/test_admin_views.py` (MODIFIED -- added area view tests)
- `esb/templates/components/_admin_nav.html` (NEW -- admin sub-navigation tabs)
- `esb/templates/admin/users.html` (MODIFIED -- added admin nav include)
- `tests/conftest.py` (MODIFIED -- added `make_area` factory fixture)
- `requirements.txt` (MODIFIED -- added cryptography for MySQL 8.4 auth)

## Change Log

- 2026-02-15: Story 2.1 implemented -- Area model, service layer, forms, views, templates, and comprehensive tests (241 total tests, all passing)
- 2026-02-15: Code review completed -- 7 findings (1 HIGH, 3 MEDIUM, 3 LOW). All HIGH/MEDIUM fixed: added admin sub-navigation tabs, differentiated archived vs active area name conflict errors, centralized `_create_area` helper in conftest as `make_area` fixture, updated File List. 4 new tests added (245 total, all passing).
