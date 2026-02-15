# Story 2.4: Equipment Archiving & Technician Permissions

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to archive equipment and control Technician edit permissions,
so that retired equipment is preserved historically and documentation editing is appropriately managed.

## Acceptance Criteria

1. **Equipment archiving:** Given I am logged in as Staff and viewing an equipment detail page, when I click "Archive" and confirm the action in the confirmation modal, then the equipment is soft-deleted (`is_archived = true`) and no longer appears in active equipment lists. The equipment's full history (documents, photos, links) is retained.

2. **Archived equipment banner:** Given an equipment record is archived, when I view the archived record via direct URL, then I see a warning banner indicating the equipment is archived, and edit/upload/add controls are hidden.

3. **AppConfig model:** Given the AppConfig model exists with `key` (unique String) and `value` (Text) columns, when Alembic migration is run, then the `app_config` table is created in MariaDB.

4. **App Configuration page:** Given I am logged in as Staff, when I navigate to App Configuration (`/admin/config`), then I can set whether Technicians have edit rights for equipment documentation (global toggle).

5. **Technician edit controls visible:** Given Technician edit rights are enabled globally, when a Technician views an equipment detail page, then they see edit controls for documents, photos, and links (but NOT for equipment core fields like name, manufacturer, model, and NOT the archive button).

6. **Technician edit controls hidden:** Given Technician edit rights are disabled (the default), when a Technician views an equipment detail page, then they see documentation in read-only mode with no edit controls.

7. **Technician upload/link actions succeed:** Given a Technician with edit rights, when they upload a document, photo, or add a link to an equipment record, then the action succeeds and is logged with the Technician's username.

8. **Mutation logging:** Given any archiving or permission change action, when the action is performed, then a mutation log entry is written to STDOUT.

## Tasks / Subtasks

- [ ] Task 1: Create AppConfig model and migration (AC: #3)
  - [ ] 1.1 Create `esb/models/app_config.py` with AppConfig model
  - [ ] 1.2 Register AppConfig model in `esb/models/__init__.py`
  - [ ] 1.3 Generate and apply Alembic migration for `app_config` table
  - [ ] 1.4 Write model unit tests

- [ ] Task 2: Create config service layer (AC: #4, #8)
  - [ ] 2.1 Create `esb/services/config_service.py` (NEW file)
  - [ ] 2.2 Implement `get_config(key, default='')` -- returns config value or default
  - [ ] 2.3 Implement `set_config(key, value, changed_by)` -- upserts config value with mutation logging
  - [ ] 2.4 Write service unit tests

- [ ] Task 3: Add equipment archiving service function (AC: #1, #8)
  - [ ] 3.1 Add `archive_equipment(equipment_id, archived_by)` to `esb/services/equipment_service.py` (EXTEND existing file)
  - [ ] 3.2 Follow `archive_area()` pattern (lines 108-129): get record, validate not already archived, set `is_archived = True`, commit, log mutation
  - [ ] 3.3 Write service unit tests

- [ ] Task 4: Add equipment archive route (AC: #1, #2)
  - [ ] 4.1 Add `POST /equipment/<int:id>/archive` route to `esb/views/equipment.py` (EXTEND existing file)
  - [ ] 4.2 Require `@role_required('staff')` -- only Staff can archive
  - [ ] 4.3 Redirect to equipment detail page after archive with success flash
  - [ ] 4.4 Update detail view to pass `equipment.is_archived` status to template
  - [ ] 4.5 Block edit route for archived equipment (redirect with warning flash)
  - [ ] 4.6 Write view integration tests

- [ ] Task 5: Add technician doc-edit permission check (AC: #5, #6, #7)
  - [ ] 5.1 Add `_require_doc_edit()` helper to `esb/views/equipment.py` -- checks if user is Staff OR (Technician AND `tech_doc_edit_enabled` config is `'true'`)
  - [ ] 5.2 Add `_can_edit_docs()` helper for template context -- returns boolean
  - [ ] 5.3 Change upload/add/delete doc/photo/link routes from `@role_required('staff')` to `@login_required` + `_require_doc_edit()` call
  - [ ] 5.4 Pass `can_edit_docs` to detail template context
  - [ ] 5.5 Write permission tests (staff always allowed, tech allowed when enabled, tech blocked when disabled, anon blocked)

- [ ] Task 6: Add admin config page (AC: #4, #8)
  - [ ] 6.1 Add `GET/POST /admin/config` route to `esb/views/admin.py` (EXTEND existing file)
  - [ ] 6.2 Create `AppConfigForm` in `esb/forms/admin_forms.py` (EXTEND existing file)
  - [ ] 6.3 Create `esb/templates/admin/config.html` template (NEW)
  - [ ] 6.4 Add "Config" tab to `esb/templates/components/_admin_nav.html` (MODIFY)
  - [ ] 6.5 Write view integration tests

- [ ] Task 7: Update equipment detail template (AC: #1, #2, #5, #6)
  - [ ] 7.1 Add archived warning banner (`alert-warning`) when `equipment.is_archived` is true
  - [ ] 7.2 Add Archive button (danger style, `onclick="return confirm(...)"`) for Staff only, hidden when archived
  - [ ] 7.3 Change doc/photo/link edit control visibility from `current_user.role == 'staff'` to `can_edit_docs and not equipment.is_archived`
  - [ ] 7.4 Keep equipment core Edit button gated to Staff only AND not archived
  - [ ] 7.5 Mobile responsive layout for archive button

- [ ] Task 8: RBAC and edge case testing (AC: #1, #2, #5, #6, #7, #8)
  - [ ] 8.1 Verify only Staff can archive equipment (tech gets 403)
  - [ ] 8.2 Verify archived equipment is excluded from list view
  - [ ] 8.3 Verify archived equipment detail shows warning banner
  - [ ] 8.4 Verify edit/upload/add controls hidden on archived equipment
  - [ ] 8.5 Verify edit route blocked for archived equipment
  - [ ] 8.6 Verify technician can upload/add when permission enabled
  - [ ] 8.7 Verify technician gets 403 on upload/add when permission disabled
  - [ ] 8.8 Verify mutation logging for archive and config change events

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- All business logic in service modules -- views are thin controllers
- `config_service.py` handles ALL AppConfig reads/writes (NEW file)
- `archive_equipment()` goes in existing `equipment_service.py` (follow `archive_area()` pattern exactly)
- Service functions accept primitive types, return model instances, raise domain exceptions
- Service functions handle their own `db.session.commit()`
- Dependency flow: `views -> services -> models` (NEVER reverse)

**File Placement (per architecture doc):**
| File | Purpose |
|------|---------|
| `esb/models/app_config.py` | AppConfig SQLAlchemy model (NEW) |
| `esb/services/config_service.py` | Runtime config get/set with mutation logging (NEW) |
| `esb/services/equipment_service.py` | Add `archive_equipment()` function (EXTEND) |
| `esb/views/equipment.py` | Add archive route + doc-edit permission helpers (EXTEND) |
| `esb/views/admin.py` | Add `/admin/config` route (EXTEND) |
| `esb/forms/admin_forms.py` | Add `AppConfigForm` (EXTEND) |
| `esb/models/__init__.py` | Add AppConfig import (MODIFY) |
| `esb/templates/equipment/detail.html` | Archive button + banner + permission gating (MODIFY) |
| `esb/templates/admin/config.html` | Admin config page (NEW) |
| `esb/templates/components/_admin_nav.html` | Add Config tab (MODIFY) |

**RBAC Rules for This Story:**
- Archive equipment: `@role_required('staff')` -- only Staff can archive
- Edit equipment core fields: `@role_required('staff')` -- unchanged from Story 2.2
- Upload/add/delete docs/photos/links: `@login_required` + `_require_doc_edit()` -- Staff always, Technicians when `tech_doc_edit_enabled` is `'true'`
- View equipment detail: `@login_required` -- unchanged (both roles can view, including archived)
- Admin config page: `@role_required('staff')` -- only Staff can change settings

### Database Model Specification

**AppConfig Model (`esb/models/app_config.py`):**

```python
class AppConfig(db.Model):
    """Key-value store for runtime-configurable settings."""

    __tablename__ = 'app_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default='')
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self):
        return f'<AppConfig {self.key!r}>'
```

**Key design decisions:**
- `key`: Unique String(100) -- identifies the setting (e.g. `'tech_doc_edit_enabled'`)
- `value`: Text -- stores setting value as string (e.g. `'true'`, `'false'`)
- `updated_at`: Tracks when the setting was last changed
- No `created_at` needed -- config entries are upserted, not created/deleted
- Follow the EXACT same timestamp pattern as other models: `from datetime import UTC, datetime`

**Model registration in `esb/models/__init__.py`:**
```python
from esb.models.app_config import AppConfig
# Add to __all__ list
__all__ = ['AppConfig', 'Area', 'Document', 'Equipment', 'ExternalLink', 'User']
```

**Equipment Model -- NO changes needed:**
- `is_archived` field already exists on Equipment model (`esb/models/equipment.py:26`)
- `list_equipment()` already filters by `is_archived=False` (`esb/services/equipment_service.py:141`)
- No migration needed for archiving functionality

### Service Function Contracts

**Config Service (`esb/services/config_service.py` -- NEW file):**

```python
def get_config(key: str, default: str = '') -> str:
    """Get a runtime config value by key.

    Args:
        key: Config key to look up.
        default: Value to return if key not found.

    Returns:
        The config value as a string, or default if not set.
    """

def set_config(key: str, value: str, changed_by: str) -> AppConfig:
    """Set a runtime config value (upsert).

    Args:
        key: Config key to set.
        value: New value.
        changed_by: Username making the change.

    Returns:
        The created or updated AppConfig instance.
    """
```

**Implementation details for `set_config`:**
1. Query for existing AppConfig by key
2. If exists: track old value, update value
3. If not exists: create new AppConfig entry
4. Commit
5. Log mutation: `'app_config.updated'` with `{key, old_value, new_value}`

**Mutation logging events:**
- `app_config.updated` -- data: `{key, old_value, new_value}`

**Archive Equipment -- Add to `esb/services/equipment_service.py`:**

```python
def archive_equipment(equipment_id: int, archived_by: str) -> Equipment:
    """Soft-delete an equipment record.

    Raises:
        ValidationError: if equipment not found or already archived.
    """
```

**Follow `archive_area()` pattern exactly (lines 108-129):**
1. Get equipment by ID, raise if not found
2. Check if already archived, raise if so
3. Set `is_archived = True`
4. Commit
5. Log mutation: `'equipment.archived'` with `{id, name}`

**Mutation logging events:**
- `equipment.archived` -- data: `{id, name}`

### View Route Patterns

**Equipment archive route -- Add to `esb/views/equipment.py`:**

```python
@equipment_bp.route('/<int:id>/archive', methods=['POST'])
@role_required('staff')
def archive(id):
    """Archive an equipment record (soft delete)."""
    try:
        equipment_service.archive_equipment(
            equipment_id=id,
            archived_by=current_user.username,
        )
        flash('Equipment archived successfully.', 'success')
    except ValidationError as e:
        flash(str(e), 'danger')
    return redirect(url_for('equipment.detail', id=id))
```

**Doc-edit permission helpers -- Add to `esb/views/equipment.py`:**

```python
def _can_edit_docs() -> bool:
    """Check if current user can edit equipment documentation.

    Staff always can. Technicians can when tech_doc_edit_enabled is 'true'.
    """
    if current_user.role == 'staff':
        return True
    if current_user.role == 'technician':
        from esb.services import config_service
        return config_service.get_config('tech_doc_edit_enabled', 'false') == 'true'
    return False


def _require_doc_edit():
    """Abort 403 if current user cannot edit equipment documentation."""
    if not _can_edit_docs():
        abort(403)
```

**Change existing doc/photo/link routes:**
- Replace `@role_required('staff')` with `@login_required` on these routes:
  - `upload_document`, `delete_document`
  - `upload_photo`, `delete_photo`
  - `add_link`, `delete_link`
- Add `_require_doc_edit()` as the FIRST call inside each of these view functions (after equipment existence check)

**Update `detail()` view to pass context:**

```python
@equipment_bp.route('/<int:id>')
@login_required
def detail(id):
    ...
    can_edit_docs = _can_edit_docs() and not eq.is_archived
    return render_template(
        'equipment/detail.html',
        equipment=eq,
        documents=documents,
        photos=photos,
        links=links,
        doc_form=doc_form,
        photo_form=photo_form,
        link_form=link_form,
        can_edit_docs=can_edit_docs,
    )
```

**Block edit route for archived equipment:**

```python
@equipment_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@role_required('staff')
def edit(id):
    try:
        eq = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)

    if eq.is_archived:
        flash('Cannot edit archived equipment.', 'danger')
        return redirect(url_for('equipment.detail', id=id))
    ...
```

**Also block archive, upload, add, delete routes for archived equipment:**
- In the archive route: `archive_equipment()` will naturally fail if already archived (service validates)
- In upload/add/delete routes: add check after equipment existence check:
  ```python
  if eq.is_archived:
      flash('Cannot modify archived equipment.', 'danger')
      return redirect(url_for('equipment.detail', id=id))
  ```

**Admin config route -- Add to `esb/views/admin.py`:**

```python
@admin_bp.route('/config', methods=['GET', 'POST'])
@role_required('staff')
def app_config():
    """App configuration page."""
    from esb.services import config_service

    form = AppConfigForm()
    if request.method == 'GET':
        form.tech_doc_edit_enabled.data = (
            config_service.get_config('tech_doc_edit_enabled', 'false') == 'true'
        )

    if form.validate_on_submit():
        config_service.set_config(
            'tech_doc_edit_enabled',
            'true' if form.tech_doc_edit_enabled.data else 'false',
            changed_by=current_user.username,
        )
        flash('Configuration updated successfully.', 'success')
        return redirect(url_for('admin.app_config'))

    return render_template('admin/config.html', form=form)
```

**Note:** Add `from flask import request` to admin.py imports (already has most Flask imports).

### Form Patterns

**Add to `esb/forms/admin_forms.py`:**

```python
class AppConfigForm(FlaskForm):
    """Form for application configuration settings."""

    tech_doc_edit_enabled = BooleanField('Allow Technicians to edit equipment documentation')
    submit = SubmitField('Save Configuration')
```

**New imports needed:** `BooleanField` from `wtforms`

### Template Patterns

**Equipment detail template changes (`esb/templates/equipment/detail.html`):**

Add archived warning banner at the top of `{% block content %}`, after breadcrumb:
```html
{% if equipment.is_archived %}
<div class="alert alert-warning" role="alert">
    This equipment has been archived and is no longer active.
</div>
{% endif %}
```

Add Archive button in the header area (next to Edit button):
```html
{% if current_user.role == 'staff' and not equipment.is_archived %}
<div class="d-flex gap-2">
    <a href="{{ url_for('equipment.edit', id=equipment.id) }}" class="btn btn-outline-secondary">Edit</a>
    <form method="post" action="{{ url_for('equipment.archive', id=equipment.id) }}" class="d-inline">
        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
        <button type="submit" class="btn btn-danger" onclick="return confirm('Are you sure you want to archive this equipment? It will be removed from active lists.')">Archive</button>
    </form>
</div>
{% elif current_user.role == 'staff' and equipment.is_archived %}
{# No edit/archive buttons for archived equipment #}
{% endif %}
```

Change doc/photo/link edit controls from:
```html
{% if current_user.role == 'staff' %}
```
to:
```html
{% if can_edit_docs %}
```

This applies to ALL upload buttons, upload forms, delete buttons, and add link forms across the Documents, Photos, and Links sections.

**Admin config template (`esb/templates/admin/config.html` -- NEW):**

```html
{% extends "base.html" %}

{% block title %}App Configuration - Equipment Status Board{% endblock %}

{% block content %}
<h1>Admin</h1>
{% include 'components/_admin_nav.html' %}

<h2>App Configuration</h2>

<div class="card">
    <div class="card-body">
        <form method="post">
            {{ form.hidden_tag() }}
            <h5>Technician Permissions</h5>
            <div class="form-check mb-3">
                {{ form.tech_doc_edit_enabled(class="form-check-input") }}
                <label class="form-check-label" for="{{ form.tech_doc_edit_enabled.id }}">
                    {{ form.tech_doc_edit_enabled.label.text }}
                </label>
                <div class="form-text">
                    When enabled, Technicians can upload documents, photos, and add links to equipment records.
                    Equipment core fields (name, manufacturer, model, etc.) remain Staff-only.
                </div>
            </div>
            {{ form.submit(class="btn btn-primary") }}
        </form>
    </div>
</div>
{% endblock %}
```

**Admin nav update (`esb/templates/components/_admin_nav.html`):**

Add a Config tab. Add to the endpoint sets at the top:
```html
{% set _config_endpoints = ['admin.app_config'] %}
```

Add new `<li>` element after Areas tab:
```html
<li class="nav-item" role="presentation">
    <a class="nav-link {% if request.endpoint in _config_endpoints %}active{% endif %}" href="{{ url_for('admin.app_config') }}" role="tab" {% if request.endpoint in _config_endpoints %}aria-current="page"{% endif %}>Config</a>
</li>
```

### Testing Requirements

**Test files:**
- `tests/test_models/test_app_config.py` -- AppConfig model tests (NEW)
- `tests/test_services/test_config_service.py` -- Config service tests (NEW)
- `tests/test_services/test_equipment_service.py` -- EXTEND with archive tests
- `tests/test_views/test_equipment_views.py` -- EXTEND with archive + permission tests
- `tests/test_views/test_admin_views.py` -- EXTEND with config page tests

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area`, `make_equipment`

**Required test coverage:**

**Model tests (`test_app_config.py`):**
- Creation with key + value
- Unique constraint on key
- Default empty string for value
- `__repr__` output

**Config service tests (`test_config_service.py`):**
- `get_config`: returns value when key exists
- `get_config`: returns default when key doesn't exist
- `set_config`: creates new entry when key doesn't exist
- `set_config`: updates existing entry when key exists
- `set_config`: mutation logging with old and new values
- `set_config`: mutation logging when creating new (old_value is empty)

**Equipment archive service tests (extend `test_equipment_service.py`):**
- `archive_equipment`: success -- sets `is_archived = True`
- `archive_equipment`: not found -- raises `ValidationError`
- `archive_equipment`: already archived -- raises `ValidationError`
- `archive_equipment`: mutation logging with id and name
- `archive_equipment`: archived equipment excluded from `list_equipment()`

**Equipment view tests (extend `test_equipment_views.py`):**
- Archive route: staff can archive (POST succeeds, equipment.is_archived becomes True)
- Archive route: technician gets 403
- Archive route: anonymous redirects to login
- Detail page: shows archived warning banner when archived
- Detail page: hides edit/archive buttons when archived
- Detail page: hides upload/add/delete controls when archived
- Edit route: redirects with warning for archived equipment
- Upload/add routes: blocked for archived equipment (flash warning, redirect)
- Technician permissions: tech can upload document when permission enabled
- Technician permissions: tech can upload photo when permission enabled
- Technician permissions: tech can add link when permission enabled
- Technician permissions: tech gets 403 on upload when permission disabled (default)
- Technician permissions: tech can delete document when permission enabled
- Technician permissions: tech gets 403 on delete when permission disabled

**Admin view tests (extend `test_admin_views.py`):**
- Config page GET: staff sees form with current config values
- Config page GET: tech gets 403
- Config page POST: staff can update tech_doc_edit_enabled to true
- Config page POST: staff can update tech_doc_edit_enabled to false
- Config page: mutation logging when config changes

**Critical testing notes from previous stories:**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. DB queries: `db.session.get(Model, id)` for PK lookups
5. Parse mutation log entries from capture: `json.loads(r.message)` where `r` is from `capture.records`
6. For technician permission tests, must set config BEFORE making the request:
   ```python
   from esb.services import config_service
   config_service.set_config('tech_doc_edit_enabled', 'true', 'test')
   ```
7. `ruff target-version = "py313"` (NOT py314)
8. Error templates extend `base_public.html` to avoid `current_user` dependency

### Previous Story Intelligence

**Patterns to follow from Stories 2.1-2.3:**
- Service pattern: copy `archive_area()` for `archive_equipment()` (identical structure)
- View pattern: copy admin route structure for config page
- Template pattern: copy area archive button pattern for equipment archive
- Test pattern: copy area archive test structure for equipment archive tests

**Key learnings from Story 2.3 code review:**
1. **IDOR prevention:** All delete routes verify parent ownership (pass `equipment_id` to service for cross-check). Story 2.4 upload/add/delete routes already have this pattern -- do NOT regress it.
2. **Category label filter:** `category_label` Jinja filter already exists in `esb/utils/filters.py`
3. **Filesize filter:** `filesize` Jinja filter already exists
4. **DOCUMENT_CATEGORIES:** Canonical source is `esb/models/document.py`, forms import from there

**Known gotchas from previous stories:**
1. Mutation logger `propagate=False` -- use `capture` fixture in tests, NOT `caplog`
2. Flash `'danger'` not `'error'` for Bootstrap alert classes
3. Wrap ALL service calls in views with `try/except ValidationError`
4. Labels WITHOUT asterisks in Python form classes -- add `*` in templates only
5. Error templates extend `base_public.html`
6. Import `datetime` from `datetime` module: `from datetime import UTC, datetime`
7. Admin nav tabs component at `components/_admin_nav.html` -- add Config tab there
8. `make_area` and `make_equipment` fixtures already exist in conftest -- use them

### Git Intelligence

**Recent commit pattern:** Each story follows:
1. Story context creation (SM agent)
2. Implementation (dev agent)
3. Code review fixes (1-2 rounds)

**Last 5 commits:**
- `55e7ba8` Fix code review issues for Story 2.3 (IDOR prevention, category_label filter, filesize filter)
- `550795f` Add CLAUDE.md with Docker database migration instructions
- `4c44fb7` Implement Story 2.3: Equipment Documentation & Media
- `6b0780a` Create Story 2.3 context for dev agent
- `717c384` Fix code review issues for Story 2.2

**Files most likely to be modified:**
- `esb/services/equipment_service.py` (add `archive_equipment()`)
- `esb/views/equipment.py` (add archive route + permission helpers + change decorators)
- `esb/views/admin.py` (add config route)
- `esb/forms/admin_forms.py` (add `AppConfigForm`)
- `esb/models/__init__.py` (add AppConfig import)
- `esb/templates/equipment/detail.html` (archive button + banner + permission gating)
- `esb/templates/components/_admin_nav.html` (add Config tab)
- `tests/test_services/test_equipment_service.py` (extend with archive tests)
- `tests/test_views/test_equipment_views.py` (extend with archive + permission tests)
- `tests/test_views/test_admin_views.py` (extend with config page tests)

**Files to be created:**
- `esb/models/app_config.py`
- `esb/services/config_service.py`
- `esb/templates/admin/config.html`
- `tests/test_models/test_app_config.py`
- `tests/test_services/test_config_service.py`
- Alembic migration for `app_config` table

### Project Structure Notes

- AppConfig model goes in its own file `esb/models/app_config.py` per architecture doc (which lists `config.py` for AppConfig model -- but use `app_config.py` to avoid confusion with `esb/config.py` Flask config)
- Config service is a NEW file `esb/services/config_service.py` -- separate from equipment_service
- Equipment archive route goes on the **equipment Blueprint** (not admin), matching the UX pattern of archiving from the detail page
- Admin config page goes on the **admin Blueprint** at `/admin/config`, with nav tab addition
- The `_can_edit_docs()` and `_require_doc_edit()` helpers live in `esb/views/equipment.py` (private to the module, not in decorators.py) to keep the scope narrow and avoid import complexity

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

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2, Story 2.4]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture -- AppConfig model]
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns -- Mutation Logging]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure -- app_config.py]
- [Source: _bmad-output/planning-artifacts/prd.md#FR7 (archive equipment), FR9 (technician edit rights), FR10 (technician edit when permitted)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4 -- Staff manages equipment, Archive confirmation]
- [Source: esb/services/equipment_service.py#archive_area() lines 108-129 -- Archive pattern reference]
- [Source: esb/views/admin.py#archive_area route line 194 -- Admin archive pattern reference]
- [Source: esb/views/equipment.py -- Current equipment routes reference]
- [Source: esb/templates/equipment/detail.html -- Current detail template reference]
- [Source: esb/templates/components/_admin_nav.html -- Admin nav tabs reference]
- [Source: esb/utils/decorators.py -- RBAC decorator reference]
- [Source: _bmad-output/implementation-artifacts/2-3-equipment-documentation-media.md -- Previous story patterns]
- [Source: _bmad-output/implementation-artifacts/2-2-equipment-registry-crud.md -- Previous story patterns]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

