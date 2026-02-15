# Story 2.2: Equipment Registry CRUD

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to create and manage equipment records with required and optional details,
so that the makerspace has a complete, organized catalog of all equipment.

## Acceptance Criteria

1. **Database Model:** Given the Equipment model exists with `name`, `manufacturer`, `model`, `area_id` (required), and optional fields (`serial_number`, `acquisition_date`, `acquisition_source`, `acquisition_cost`, `warranty_expiration`, `description`, `is_archived`), when Alembic migration is run, then the `equipment` table is created with proper foreign key to `areas`.

2. **Equipment listing:** Given I am logged in as Staff, when I navigate to the Equipment Registry (`/equipment`), then I see a list of all active equipment with name, area, and manufacturer columns.

3. **Area filtering:** Given I am on the Equipment Registry page, when I select an area from the filter dropdown, then the list shows only equipment in that area.

4. **Creating equipment:** Given I am on the Equipment Registry page, when I click "Add Equipment" and fill in name, manufacturer, model, and select an area, then a new equipment record is created and I am redirected to its detail page.

5. **Required field validation:** Given I am creating equipment, when I submit without filling in a required field (name, manufacturer, model, or area), then I see inline validation errors and the record is not created.

6. **Equipment detail page:** Given I am on an equipment detail page, when I view the equipment record, then I see all populated fields organized with required fields prominently displayed and optional fields in a details section.

7. **Editing equipment:** Given I am on an equipment detail page, when I click "Edit" and modify any field (required or optional), then the changes are saved and I see a success message.

8. **Mutation logging:** Given any equipment action (create, edit), when the action is performed, then a mutation log entry is written to STDOUT.

## Tasks / Subtasks

- [x] Task 1: Create Equipment model and migration (AC: #1)
  - [x] 1.1 Create `esb/models/equipment.py` with Equipment model
  - [x] 1.2 Register Equipment model in `esb/models/__init__.py`
  - [x] 1.3 Generate and apply Alembic migration
  - [x] 1.4 Write model unit tests

- [x] Task 2: Create equipment service layer (AC: #2, #3, #4, #5, #7, #8)
  - [x] 2.1 Add equipment functions to `esb/services/equipment_service.py` (EXTEND existing file)
  - [x] 2.2 Implement `list_equipment(area_id=None)` -- returns active equipment, with optional area filter
  - [x] 2.3 Implement `get_equipment(equipment_id)` for single equipment retrieval
  - [x] 2.4 Implement `create_equipment(name, manufacturer, model, area_id, created_by, **optional_fields)` with validation and mutation logging
  - [x] 2.5 Implement `update_equipment(equipment_id, updated_by, **fields)` with validation and mutation logging
  - [x] 2.6 Write service unit tests

- [x] Task 3: Create equipment forms (AC: #4, #5, #7)
  - [x] 3.1 Add `EquipmentCreateForm` and `EquipmentEditForm` to `esb/forms/equipment_forms.py` (EXTEND existing file)
  - [x] 3.2 Required fields: name, manufacturer, model, area (SelectField)
  - [x] 3.3 Optional fields: serial_number, acquisition_date, acquisition_source, acquisition_cost, warranty_expiration, description

- [x] Task 4: Create equipment views/routes (AC: #2, #3, #4, #5, #6, #7)
  - [x] 4.1 Create `esb/views/equipment.py` with equipment Blueprint (NEW file)
  - [x] 4.2 `GET /equipment` -- list active equipment with optional area filter
  - [x] 4.3 `GET/POST /equipment/new` -- create equipment form
  - [x] 4.4 `GET /equipment/<int:id>` -- equipment detail page
  - [x] 4.5 `GET/POST /equipment/<int:id>/edit` -- edit equipment form
  - [x] 4.6 Register equipment Blueprint in app factory
  - [x] 4.7 Write view integration tests

- [x] Task 5: Create equipment templates (AC: #2, #3, #4, #5, #6, #7)
  - [x] 5.1 Create `esb/templates/equipment/list.html` -- equipment list with area filter
  - [x] 5.2 Create `esb/templates/equipment/detail.html` -- equipment detail page
  - [x] 5.3 Create `esb/templates/equipment/form.html` -- shared create/edit form
  - [x] 5.4 Empty state when no equipment exists
  - [x] 5.5 Mobile responsive card layout for list view

- [x] Task 6: RBAC and edge case testing (AC: #2, #4, #5, #7, #8)
  - [x] 6.1 Verify `@role_required('staff')` on create/edit routes
  - [x] 6.2 Verify `@login_required` on list and detail routes (Technicians can view)
  - [x] 6.3 Verify unauthenticated users get redirected to login
  - [x] 6.4 Verify area dropdown only shows active (non-archived) areas
  - [x] 6.5 Verify archived equipment excluded from listings

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
| `esb/models/equipment.py` | Equipment SQLAlchemy model (NEW) |
| `esb/services/equipment_service.py` | Equipment CRUD functions (EXTEND existing -- area functions already here) |
| `esb/forms/equipment_forms.py` | Equipment create/edit forms (EXTEND existing -- area forms already here) |
| `esb/views/equipment.py` | Equipment Blueprint with all equipment routes (NEW) |
| `esb/models/__init__.py` | Add Equipment import for Alembic discovery (MODIFY) |
| `esb/__init__.py` | Register equipment Blueprint in app factory (MODIFY) |
| `esb/templates/equipment/list.html` | Equipment list page (NEW) |
| `esb/templates/equipment/detail.html` | Equipment detail page (NEW) |
| `esb/templates/equipment/form.html` | Shared create/edit form (NEW) |

**Equipment routes go in a NEW equipment Blueprint** (`views/equipment.py`) with URL prefix `/equipment`. This is a separate Blueprint from admin -- per architecture doc, the equipment Blueprint handles `/equipment/*` routes.

**RBAC Rules for Equipment:**
- List and detail views: `@login_required` -- both Staff AND Technicians can view equipment
- Create and edit views: `@role_required('staff')` -- only Staff can create/edit
- Archiving is NOT in this story (Story 2.4)

### Database Model Specification

```python
class Equipment(db.Model):
    """Equipment registry entry."""

    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False, index=True)
    manufacturer = db.Column(db.String(200), nullable=False)
    model = db.Column(db.String(200), nullable=False)
    area_id = db.Column(db.Integer, db.ForeignKey('areas.id'), nullable=False, index=True)
    serial_number = db.Column(db.String(200), nullable=True)
    acquisition_date = db.Column(db.Date, nullable=True)
    acquisition_source = db.Column(db.String(200), nullable=True)
    acquisition_cost = db.Column(db.Numeric(10, 2), nullable=True)
    warranty_expiration = db.Column(db.Date, nullable=True)
    description = db.Column(db.Text, nullable=True)
    is_archived = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False,
                           default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))

    # Relationships
    area = db.relationship('Area', backref=db.backref('equipment', lazy='dynamic'))

    def __repr__(self):
        return f'<Equipment {self.name!r}>'
```

**Key decisions:**
- `name`: NOT unique -- multiple equipment items can have the same name (e.g., "3D Printer")
- `area_id`: NOT NULL with FK constraint to `areas.id`, indexed for filtering
- `acquisition_cost`: `Numeric(10, 2)` for currency precision
- `acquisition_date` and `warranty_expiration`: `Date` type (not DateTime)
- `description`: `Text` type for long descriptions
- `is_archived`: Boolean soft delete column (used in Story 2.4 but define now for schema stability)
- Follow the EXACT same timestamp patterns as `Area` and `User` models

**Model registration:** Add `from esb.models.equipment import Equipment` and update `__all__` in `esb/models/__init__.py`

### Service Function Contracts

Add to the EXISTING `esb/services/equipment_service.py` (which already has area management functions):

```python
# Equipment CRUD functions -- add below existing area functions

def list_equipment(area_id: int | None = None) -> list[Equipment]:
    """Return all active (non-archived) equipment, optionally filtered by area.

    Args:
        area_id: If provided, filter to equipment in this area only.
    """

def get_equipment(equipment_id: int) -> Equipment:
    """Get a single equipment record by ID.

    Raises:
        ValidationError: if equipment not found.
    """

def create_equipment(
    name: str,
    manufacturer: str,
    model: str,
    area_id: int,
    created_by: str,
    serial_number: str | None = None,
    acquisition_date: date | None = None,
    acquisition_source: str | None = None,
    acquisition_cost: Decimal | None = None,
    warranty_expiration: date | None = None,
    description: str | None = None,
) -> Equipment:
    """Create a new equipment record.

    Raises:
        ValidationError: if area_id is invalid or required fields are missing.
    """

def update_equipment(
    equipment_id: int,
    updated_by: str,
    **fields,
) -> Equipment:
    """Update an equipment record.

    Raises:
        ValidationError: if equipment not found or validation fails.
    """
```

**Validation rules:**
- `create_equipment`: Verify area_id references an active (non-archived) area
- `create_equipment`: Verify name, manufacturer, model are non-empty strings
- `update_equipment`: Verify area_id (if changed) references an active area
- `update_equipment`: Track changes for mutation logging (like `update_area` pattern)

**Mutation logging events:**
- `equipment.created` -- data: `{id, name, manufacturer, model, area_id, ...populated_optional_fields}`
- `equipment.updated` -- data: `{id, name, changes: {field: [old, new]}}`

### View Route Patterns

Create NEW file `esb/views/equipment.py`:

```python
equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')

@equipment_bp.route('/')
@login_required
def list_equipment():
    """Equipment registry list with optional area filter."""

@equipment_bp.route('/new', methods=['GET', 'POST'])
@role_required('staff')
def create_equipment():
    """Equipment creation form and handler."""

@equipment_bp.route('/<int:id>')
@login_required
def detail(id):
    """Equipment detail page."""

@equipment_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@role_required('staff')
def edit_equipment(id):
    """Equipment edit form and handler."""
```

**Blueprint registration:** Add to `esb/__init__.py` app factory:
```python
from esb.views.equipment import equipment_bp
app.register_blueprint(equipment_bp)
```

**Error handling in views:**
- Wrap service calls in `try/except ValidationError` -- flash as `'danger'`, redirect or re-render
- After successful create: redirect to equipment detail page with success flash
- After successful edit: redirect to equipment detail page with success flash
- Use `flash('message', 'success')` for success, `flash('message', 'danger')` for errors

**Area filter on list page:**
- Accept `area_id` as URL query parameter: `/equipment?area_id=3`
- Pass active areas to template for the filter dropdown
- Selected area persists in the dropdown after filter

### Form Patterns

Add to EXISTING `esb/forms/equipment_forms.py`:

```python
class EquipmentCreateForm(FlaskForm):
    """Form for creating a new equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Create Equipment')


class EquipmentEditForm(FlaskForm):
    """Form for editing an existing equipment record."""

    name = StringField('Name', validators=[DataRequired(), Length(max=200)])
    manufacturer = StringField('Manufacturer', validators=[DataRequired(), Length(max=200)])
    model = StringField('Model', validators=[DataRequired(), Length(max=200)])
    area_id = SelectField('Area', coerce=int, validators=[DataRequired()])
    serial_number = StringField('Serial Number', validators=[Length(max=200)])
    acquisition_date = DateField('Acquisition Date', validators=[Optional()])
    acquisition_source = StringField('Acquisition Source', validators=[Length(max=200)])
    acquisition_cost = DecimalField('Acquisition Cost', places=2, validators=[Optional()])
    warranty_expiration = DateField('Warranty Expiration', validators=[Optional()])
    description = TextAreaField('Description')
    submit = SubmitField('Save Changes')
```

**Area dropdown choices:**
- Populate `area_id.choices` dynamically in the view before rendering:
```python
form.area_id.choices = [(a.id, a.name) for a in equipment_service.list_areas()]
```
- Add an empty default option: `[(0, '-- Select Area --')] + area_choices` and validate `area_id != 0`

**New imports needed:** `DateField`, `DecimalField`, `TextAreaField` from `wtforms`, `Optional` from `wtforms.validators`

**Note:** Labels do NOT include `*` -- asterisks are added in templates only (lesson from Story 1.4 code review).

### Template Patterns

**Equipment list page (`templates/equipment/list.html`):**
- Extends `base.html` (authenticated layout)
- Page title: "Equipment Registry"
- "Add Equipment" primary button (top-right) -- only shown to Staff users via `{% if current_user.role == 'staff' %}`
- Area filter dropdown above the table (Bootstrap `form-select` with onchange to reload page)
- Responsive table (desktop) / cards (mobile) pattern matching `areas.html`:
  - Desktop columns: Name, Manufacturer, Model, Area
  - Mobile cards: Name (title), Manufacturer/Model, Area badge
- Each row/card links to the equipment detail page
- Empty state: "No equipment has been added yet." with "Add Equipment" button (Staff only)
- If filtered and no results: "No equipment found in this area." with "Clear Filter" link

**Equipment detail page (`templates/equipment/detail.html`):**
- Extends `base.html`
- Page title: equipment name
- Breadcrumb: Equipment Registry > Equipment Name
- "Edit" button (Staff only) in header area
- Required fields displayed prominently: Name, Manufacturer, Model, Area
- Optional fields in a "Details" section (only show fields that have values):
  - Serial Number, Acquisition Date, Acquisition Source, Acquisition Cost, Warranty Expiration, Description
- Use Bootstrap description list (`<dl>`) for field display
- Placeholder sections for future stories: Documents (Story 2.3), Photos (Story 2.3), Links (Story 2.3)

**Equipment form (`templates/equipment/form.html`):**
- Extends `base.html`
- Shared for create/edit (uses `title` variable like `area_form.html`)
- Single-column form layout with labels above fields
- Required fields marked with `*` in template labels
- Required fields section: Name, Manufacturer, Model, Area dropdown
- Optional fields section with a visual separator or heading "Additional Details"
- Date fields use HTML `<input type="date">`
- Cost field use HTML `<input type="number" step="0.01">`
- Description uses a textarea (3+ rows)
- Submit button + Cancel link pattern matching `area_form.html`

### UX Requirements

- **Navigation:** Add "Equipment" link to navbar for both Staff and Technician roles
- **Button hierarchy:** "Add Equipment" = `btn-primary` (one per page, Staff only), row click = navigate to detail, "Edit" on detail = `btn-outline-secondary`
- **Area filter:** Bootstrap `form-select` inline with the page header area, auto-submits on change (simple JS `onchange="this.form.submit()"` or link-based filter)
- **Responsive:** Desktop = Bootstrap table with clickable rows, Mobile (<768px) = stacked cards
- **Empty states:** Centered message with primary action button when no equipment exists
- **Detail page layout:** Required fields in a card header area, optional details in card body, use `text-muted` for empty optional fields or hide them

### Testing Requirements

**Test files:**
- `tests/test_models/test_equipment.py` -- Equipment model tests (NEW)
- `tests/test_services/test_equipment_service.py` -- EXTEND existing file with equipment service tests
- `tests/test_views/test_equipment_views.py` -- Equipment view tests (NEW)

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area` -- needed to create areas for equipment FK

**Add new fixture** to `tests/conftest.py`:
```python
def _create_equipment(name='Test Equipment', manufacturer='TestCo', model='Model X',
                      area=None, **kwargs):
    """Helper to create an equipment record in the test database."""
    from esb.models.equipment import Equipment
    if area is None:
        area = _create_area()
    equipment = Equipment(
        name=name, manufacturer=manufacturer, model=model,
        area_id=area.id, **kwargs,
    )
    _db.session.add(equipment)
    _db.session.commit()
    return equipment
```

**Required test coverage:**
- Model: creation with required fields, optional fields, FK constraint to area, defaults, `__repr__`
- Service: `list_equipment` (excludes archived, area filter), `get_equipment` (success + not found), `create_equipment` (success, invalid area, missing required fields), `update_equipment` (success + not found + change tracking), mutation logging for each
- Views: list (staff OK, tech OK, anon redirect, area filter works), create GET/POST (staff OK, tech 403, validation error), detail GET (staff OK, tech OK, not found 404), edit GET/POST (staff OK, tech 403, success, validation error)
- Mutation logging: use `capture` fixture (NOT `caplog`), verify event names and data fields

**Critical testing notes from previous stories:**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. DB queries: `db.session.get(Equipment, id)` for PK lookups
5. Parse mutation log entries from capture: `json.loads(r.message)` where `r` is from `capture.records`
6. Area FK: tests must create an Area first (use `make_area` fixture) before creating equipment

### Project Structure Notes

- Equipment routes use a NEW `equipment` Blueprint -- separate from admin
- `equipment_service.py` is EXTENDED (area functions already exist here)
- `equipment_forms.py` is EXTENDED (area forms already exist here)
- The equipment Blueprint must be registered in the app factory `esb/__init__.py`
- Add "Equipment" to the navbar links for Staff and Technician roles in `base.html`
- Equipment detail page will serve as the anchor for future Stories 2.3 (documents/media) and 2.4 (archiving/permissions)

### Previous Story Intelligence

**Patterns to follow from Story 2.1 (Area Management):**
- Model pattern: copy `Area` model structure exactly (timestamps, column types, `__repr__`)
- Service pattern: copy area service functions structure (imports, validation, mutation logging, error handling, change tracking in updates)
- View pattern: copy admin routes structure (decorator, form validation, flash, redirect)
- Form pattern: copy area forms structure (field definitions, validators, no asterisks in labels)
- Template pattern: copy `areas.html` responsive table/card pattern
- Test pattern: copy area test structure (class-based grouping, service + view + mutation tests)

**Known gotchas from previous stories:**
1. `ruff target-version = "py313"` (NOT py314)
2. Mutation logger `propagate=False` -- use `_CaptureHandler` / `capture` fixture in tests
3. Flash `'danger'` not `'error'` for Bootstrap alert classes
4. Wrap ALL service calls in views with `try/except ValidationError`
5. Labels WITHOUT asterisks in Python form classes -- add `*` in templates only
6. Error templates extend `base_public.html` to avoid `current_user` dependency
7. Import `datetime` from `datetime` module: `from datetime import UTC, datetime`
8. Case-insensitive duplicate checks use `db.func.lower()`
9. Admin nav tabs component already exists at `components/_admin_nav.html` -- do NOT use for equipment pages (equipment has its own blueprint)
10. The `make_area` fixture already exists in conftest -- use it to create areas for equipment FK in tests

### Git Intelligence

**Recent commit pattern:** Each story follows a cycle:
1. Story context creation (SM agent)
2. Implementation (dev agent)
3. Code review fixes (1-2 rounds)

**Last relevant commits:**
- `927e1cb` Switch database from MySQL 8.4 to MariaDB 12.2.2
- `c239fb2` Fix second code review issues for Story 2.1 area management
- `6d78cde` Fix code review issues for Story 2.1 area management
- `cf3d861` Implement Story 2.1: Area management (CRUD with soft-delete)

**Files most likely to be modified:**
- `esb/services/equipment_service.py` (extend with equipment functions)
- `esb/forms/equipment_forms.py` (extend with equipment forms)
- `esb/models/__init__.py` (add Equipment import)
- `esb/__init__.py` (register equipment Blueprint)
- `esb/templates/base.html` (add Equipment nav link)
- `tests/conftest.py` (add `make_equipment` factory fixture)
- `tests/test_services/test_equipment_service.py` (extend with equipment tests)

**Files to be created:**
- `esb/models/equipment.py`
- `esb/views/equipment.py`
- `esb/templates/equipment/list.html`
- `esb/templates/equipment/detail.html`
- `esb/templates/equipment/form.html`
- `tests/test_models/test_equipment.py`
- `tests/test_views/test_equipment_views.py`

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

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2, Story 2.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture, Project Structure, Service Layer]
- [Source: _bmad-output/planning-artifacts/prd.md#FR1, FR2, FR6]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4, Form Patterns, Table Patterns]
- [Source: _bmad-output/implementation-artifacts/2-1-area-management.md -- Previous story patterns]
- [Source: esb/models/area.py -- Model pattern reference]
- [Source: esb/services/equipment_service.py -- Service pattern reference (extend this file)]
- [Source: esb/forms/equipment_forms.py -- Form pattern reference (extend this file)]
- [Source: esb/views/admin.py -- View/route pattern reference]
- [Source: esb/templates/admin/areas.html -- Template responsive table pattern reference]
- [Source: tests/conftest.py -- Test fixture pattern reference]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- SQLite test DB does not enforce FK constraints; FK enforcement test replaced with NOT NULL test for area_id
- `_create_equipment` helper needed explicit area param to avoid duplicate "Test Area" unique constraint violations in multi-equipment tests

### Completion Notes List

- Task 1: Created Equipment model (`esb/models/equipment.py`) with all required/optional fields matching spec. Registered in `__init__.py`. Generated and applied Alembic migration `fe564f1c4920`. 9 model unit tests passing.
- Task 2: Extended `esb/services/equipment_service.py` with `list_equipment`, `get_equipment`, `create_equipment`, `update_equipment`. Validation for required fields, area existence/archived checks, mutation logging with change tracking. 23 equipment service tests passing.
- Task 3: Extended `esb/forms/equipment_forms.py` with `EquipmentCreateForm` and `EquipmentEditForm`. Required fields with DataRequired validators, optional fields with Optional validators.
- Task 4: Replaced equipment Blueprint stub in `esb/views/equipment.py` with full CRUD routes. `@login_required` on list/detail, `@role_required('staff')` on create/edit. Area filter via query param. 404 for not-found equipment.
- Task 5: Created three templates: `list.html` (responsive table/cards, area filter dropdown, empty states), `detail.html` (breadcrumb, required/optional field sections), `form.html` (shared create/edit with required/optional field sections).
- Task 6: RBAC tests confirm staff-only create/edit (403 for technicians), login_required on all routes, area dropdown excludes archived areas, archived equipment excluded from listings. Mutation logging verified via `capture` fixture.

### File List

**New files:**
- `esb/models/equipment.py`
- `esb/templates/equipment/list.html`
- `esb/templates/equipment/detail.html`
- `esb/templates/equipment/form.html`
- `migrations/versions/fe564f1c4920_add_equipment_table.py`
- `tests/test_models/test_equipment.py`
- `tests/test_views/test_equipment_views.py`

**Modified files:**
- `esb/models/__init__.py` (added Equipment import)
- `esb/services/equipment_service.py` (added equipment CRUD functions)
- `esb/forms/equipment_forms.py` (added EquipmentCreateForm, EquipmentEditForm)
- `esb/views/equipment.py` (replaced placeholder with full implementation)
- `tests/conftest.py` (added make_equipment fixture)
- `tests/test_services/test_equipment_service.py` (added equipment service tests)

### Change Log

- 2026-02-15: Implemented Story 2.2 Equipment Registry CRUD - model, service, forms, views, templates, tests (311 total tests passing, lint clean)

