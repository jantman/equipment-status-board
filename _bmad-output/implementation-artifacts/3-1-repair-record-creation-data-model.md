# Story 3.1: Repair Record Creation & Data Model

Status: review

## Story

As a Technician or Staff member,
I want to create repair records for equipment,
so that problems are tracked from discovery through resolution.

## Acceptance Criteria

1. **RepairRecord model:** Given the RepairRecord model exists with fields for `equipment_id`, `status` (default "New"), `severity`, `description`, `reporter_name`, `reporter_email`, `assignee_id`, `eta`, `specialist_description`, `has_safety_risk`, `is_consumable`, `created_at`, `updated_at` -- when Alembic migration is run, then the `repair_records` table is created with proper foreign keys to `equipment` and `users`.

2. **RepairTimelineEntry model:** Given the RepairTimelineEntry model exists with fields for `repair_record_id`, `entry_type` (note, status_change, assignee_change, eta_update, photo, creation), `author_id`, `content`, `old_value`, `new_value`, `created_at` -- when Alembic migration is run, then the `repair_timeline_entries` table is created.

3. **AuditLog model:** Given the AuditLog model exists with fields for `entity_type`, `entity_id`, `action`, `user_id`, `changes` (JSON), `created_at` -- when Alembic migration is run, then the `audit_log` table is created.

4. **Create repair record:** Given I am logged in as a Technician or Staff, when I navigate to create a new repair record and select an equipment item, enter a description, and submit, then a repair record is created with status "New" and a creation entry is added to the timeline.

5. **View repair record:** Given a repair record is created, when I view the repair record detail page (`/repairs/{id}`), then I see the equipment name, status, severity, description, and the timeline with the creation entry.

6. **Audit and mutation logging:** Given a repair record is created, when the service layer processes the creation, then an audit log entry is written and a mutation log is emitted to STDOUT.

## Tasks / Subtasks

- [x] Task 1: Create RepairRecord model and migration (AC: #1)
  - [x] 1.1 Create `esb/models/repair_record.py` with RepairRecord model
  - [x] 1.2 Register RepairRecord in `esb/models/__init__.py`
  - [x] 1.3 Write model unit tests

- [x] Task 2: Create RepairTimelineEntry model (AC: #2)
  - [x] 2.1 Create `esb/models/repair_timeline_entry.py` with RepairTimelineEntry model
  - [x] 2.2 Register RepairTimelineEntry in `esb/models/__init__.py`
  - [x] 2.3 Write model unit tests

- [x] Task 3: Create AuditLog model (AC: #3)
  - [x] 3.1 Create `esb/models/audit_log.py` with AuditLog model
  - [x] 3.2 Register AuditLog in `esb/models/__init__.py`
  - [x] 3.3 Write model unit tests

- [x] Task 4: Generate and apply Alembic migration for all three tables (AC: #1, #2, #3)
  - [x] 4.1 Generate migration with `flask db migrate -m "Add repair_records, repair_timeline_entries, and audit_log tables"`
  - [x] 4.2 Apply migration with `flask db upgrade`
  - [x] 4.3 Verify tables created correctly

- [x] Task 5: Create repair service layer (AC: #4, #6)
  - [x] 5.1 Create `esb/services/repair_service.py` (NEW file)
  - [x] 5.2 Implement `create_repair_record()` -- creates record + timeline creation entry + audit log + mutation log
  - [x] 5.3 Implement `get_repair_record()` -- get by ID with validation
  - [x] 5.4 Implement `list_repair_records()` -- list with optional equipment_id filter
  - [x] 5.5 Write service unit tests

- [x] Task 6: Create repair forms (AC: #4)
  - [x] 6.1 Create `esb/forms/repair_forms.py` (NEW file)
  - [x] 6.2 Implement `RepairRecordCreateForm` with equipment selector, description, severity, safety risk, assignee
  - [x] 6.3 Write form validation tests (if needed)

- [x] Task 7: Create repair views and routes (AC: #4, #5)
  - [x] 7.1 Create `esb/views/repairs.py` (NEW file) with repairs Blueprint
  - [x] 7.2 Implement `GET /repairs/new` -- create repair record form
  - [x] 7.3 Implement `POST /repairs/new` -- handle form submission
  - [x] 7.4 Implement `GET /repairs/<int:id>` -- repair record detail page
  - [x] 7.5 Register Blueprint in `esb/views/__init__.py`
  - [x] 7.6 Write view integration tests

- [x] Task 8: Create repair templates (AC: #4, #5)
  - [x] 8.1 Create `esb/templates/repairs/create.html` -- repair record creation form
  - [x] 8.2 Create `esb/templates/repairs/detail.html` -- repair record detail with timeline
  - [x] 8.3 Create `esb/templates/components/_timeline_entry.html` -- reusable timeline entry partial

- [x] Task 9: Add navigation links for repairs (AC: #5)
  - [x] 9.1 Add "Repairs" link to navbar in `base.html` for Technician and Staff users
  - [x] 9.2 Add "Create Repair Record" action link from equipment detail page

- [x] Task 10: Comprehensive testing (AC: #1-#6)
  - [x] 10.1 Model unit tests for all three models
  - [x] 10.2 Service tests for create, get, list with mutation log verification
  - [x] 10.3 View tests for access control, creation, detail view
  - [x] 10.4 Verify audit log entries created on repair record creation
  - [x] 10.5 Verify timeline entries created correctly

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- All business logic in service modules -- views are thin controllers
- `repair_service.py` handles ALL repair record operations (NEW file)
- Service functions accept primitive types, return model instances, raise domain exceptions
- Service functions handle their own `db.session.commit()`
- Dependency flow: `views -> services -> models` (NEVER reverse)

**File Placement (per architecture doc):**
| File | Purpose |
|------|---------|
| `esb/models/repair_record.py` | RepairRecord SQLAlchemy model (NEW) |
| `esb/models/repair_timeline_entry.py` | RepairTimelineEntry SQLAlchemy model (NEW) |
| `esb/models/audit_log.py` | AuditLog SQLAlchemy model (NEW) |
| `esb/services/repair_service.py` | Repair record lifecycle, timeline entries (NEW) |
| `esb/forms/repair_forms.py` | Repair record creation form (NEW) |
| `esb/views/repairs.py` | /repairs/* routes (NEW) |
| `esb/views/__init__.py` | Register repairs Blueprint (MODIFY) |
| `esb/models/__init__.py` | Add RepairRecord, RepairTimelineEntry, AuditLog imports (MODIFY) |
| `esb/templates/repairs/create.html` | Repair creation form template (NEW) |
| `esb/templates/repairs/detail.html` | Repair detail + timeline template (NEW) |
| `esb/templates/components/_timeline_entry.html` | Reusable timeline entry partial (NEW) |
| `esb/templates/base.html` | Add Repairs nav link (MODIFY) |
| `esb/templates/equipment/detail.html` | Add "Create Repair Record" link (MODIFY) |

**RBAC Rules for This Story:**
- Create repair record: `@role_required('technician')` -- Technicians and Staff can create (Staff > Technician in hierarchy)
- View repair record detail: `@role_required('technician')` -- Technicians and Staff can view
- List repair records: `@role_required('technician')` -- Technicians and Staff can view
- Public problem reporting (QR page): handled in Epic 4, NOT this story

### Database Model Specifications

**RepairRecord Model (`esb/models/repair_record.py`):**

```python
from datetime import UTC, datetime

from esb.extensions import db


class RepairRecord(db.Model):
    """Tracks an equipment problem from report through resolution."""

    __tablename__ = 'repair_records'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(
        db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True,
    )
    status = db.Column(db.String(50), nullable=False, default='New', index=True)
    severity = db.Column(db.String(20), nullable=True)
    description = db.Column(db.Text, nullable=False)
    reporter_name = db.Column(db.String(200), nullable=True)
    reporter_email = db.Column(db.String(255), nullable=True)
    assignee_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True, index=True,
    )
    eta = db.Column(db.Date, nullable=True)
    specialist_description = db.Column(db.Text, nullable=True)
    has_safety_risk = db.Column(db.Boolean, nullable=False, default=False)
    is_consumable = db.Column(db.Boolean, nullable=False, default=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
    )
    updated_at = db.Column(
        db.DateTime,
        nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    # Relationships
    equipment = db.relationship('Equipment', backref=db.backref('repair_records', lazy='dynamic'))
    assignee = db.relationship('User', backref=db.backref('assigned_repairs', lazy='dynamic'))

    def __repr__(self):
        return f'<RepairRecord {self.id} [{self.status}]>'
```

**Key design decisions for RepairRecord:**
- `status`: String(50) NOT an enum -- allows any-to-any transitions without DB constraint. Valid values enforced in service layer.
- `severity`: Nullable -- member reports default to "Not Sure", but internal records may not have severity initially.
- `reporter_name` / `reporter_email`: Nullable -- only populated for member-submitted reports (QR/Slack). When Staff/Technician creates, use their username.
- `assignee_id`: Nullable FK to users -- can be unassigned.
- `eta`: Date type (not DateTime) -- ETA is a target date.
- `has_safety_risk` / `is_consumable`: Boolean defaults to False.
- `specialist_description`: Nullable Text -- only populated when status is "Needs Specialist".
- Index on `equipment_id`, `status`, `assignee_id` for common query patterns.

**Valid Status Values (enforce in service, not DB):**
```python
REPAIR_STATUSES = [
    'New',
    'Assigned',
    'In Progress',
    'Parts Needed',
    'Parts Ordered',
    'Parts Received',
    'Needs Specialist',
    'Resolved',
    'Closed - No Issue Found',
    'Closed - Duplicate',
]
```

**Valid Severity Values:**
```python
REPAIR_SEVERITIES = ['Down', 'Degraded', 'Not Sure']
```

Define these as module-level constants in `esb/models/repair_record.py` (following the pattern of `DOCUMENT_CATEGORIES` in `esb/models/document.py`).

**RepairTimelineEntry Model (`esb/models/repair_timeline_entry.py`):**

```python
from datetime import UTC, datetime

from esb.extensions import db


TIMELINE_ENTRY_TYPES = [
    'creation',
    'note',
    'status_change',
    'assignee_change',
    'eta_update',
    'photo',
]


class RepairTimelineEntry(db.Model):
    """Append-only log entry for a repair record's timeline."""

    __tablename__ = 'repair_timeline_entries'

    id = db.Column(db.Integer, primary_key=True)
    repair_record_id = db.Column(
        db.Integer, db.ForeignKey('repair_records.id'), nullable=False, index=True,
    )
    entry_type = db.Column(db.String(30), nullable=False)
    author_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True,
    )
    author_name = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=True)
    old_value = db.Column(db.String(200), nullable=True)
    new_value = db.Column(db.String(200), nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
    )

    # Relationships
    repair_record = db.relationship(
        'RepairRecord',
        backref=db.backref('timeline_entries', lazy='dynamic', order_by='RepairTimelineEntry.created_at.desc()'),
    )
    author = db.relationship('User', backref=db.backref('timeline_entries', lazy='dynamic'))

    def __repr__(self):
        return f'<RepairTimelineEntry {self.id} [{self.entry_type}]>'
```

**Key design decisions for RepairTimelineEntry:**
- `entry_type`: String, not enum. Values: `'creation'`, `'note'`, `'status_change'`, `'assignee_change'`, `'eta_update'`, `'photo'`.
- `author_id`: Nullable FK to users -- nullable for system-generated entries or anonymous member reports.
- `author_name`: String -- stores display name for entries from anonymous reporters (QR code submissions). When author_id is set, this can be derived from the User, but storing it denormalized ensures timeline entries are self-contained even if users are deleted later.
- `content`: Nullable text -- used for notes, specialist descriptions, photo filenames.
- `old_value` / `new_value`: Used for status_change, assignee_change, eta_update entries.
- `created_at`: Required timestamp, no `updated_at` (entries are append-only, never modified).
- Timeline entries are APPEND-ONLY -- no update or delete operations.
- Default ordering by `created_at DESC` (newest first) in the backref.

**AuditLog Model (`esb/models/audit_log.py`):**

```python
from datetime import UTC, datetime

from esb.extensions import db


class AuditLog(db.Model):
    """Application-level audit trail for entity changes."""

    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True,
    )
    changes = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
    )

    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<AuditLog {self.entity_type}:{self.entity_id} [{self.action}]>'
```

**Key design decisions for AuditLog:**
- `entity_type`: String identifying the entity type (e.g., `'repair_record'`).
- `entity_id`: Integer referencing the entity's ID (not a FK -- works across all entity types).
- `action`: String describing the action (e.g., `'created'`, `'status_changed'`, `'updated'`).
- `user_id`: Nullable FK to users -- nullable for system or anonymous actions.
- `changes`: JSON column -- stores a dict of field changes `{field: [old_value, new_value]}`.
- `created_at`: Timestamp only (no `updated_at` -- audit entries are immutable).
- This is the application-level audit trail (FR20). Separate from the STDOUT mutation logging (FR52).
- Index on `entity_type` + `entity_id` for efficient per-entity queries.

**Model Registration in `esb/models/__init__.py`:**
```python
from esb.models.audit_log import AuditLog
from esb.models.repair_record import RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
```
Add all three to the `__all__` list.

### Service Function Contracts

**Repair Service (`esb/services/repair_service.py` -- NEW file):**

```python
"""Repair record lifecycle management."""

from esb.extensions import db
from esb.models.audit_log import AuditLog
from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES, RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation


def create_repair_record(
    equipment_id: int,
    description: str,
    created_by: str,
    severity: str | None = None,
    reporter_name: str | None = None,
    reporter_email: str | None = None,
    assignee_id: int | None = None,
    has_safety_risk: bool = False,
    is_consumable: bool = False,
    author_id: int | None = None,
) -> RepairRecord:
    """Create a new repair record with initial timeline entry.

    Args:
        equipment_id: ID of the equipment this repair is for.
        description: Description of the problem.
        created_by: Username of the person creating the record.
        severity: Optional severity level (Down, Degraded, Not Sure).
        reporter_name: Name of the person reporting (for member reports).
        reporter_email: Email of the reporter (for member reports).
        assignee_id: Optional user ID to assign the repair to.
        has_safety_risk: Whether this is a safety risk.
        is_consumable: Whether this involves consumables.
        author_id: User ID of the creator (None for anonymous reports).

    Returns:
        The created RepairRecord.

    Raises:
        ValidationError: if equipment not found, archived, or invalid input.
    """
```

**Implementation details for `create_repair_record`:**
1. Validate `description` is not empty/whitespace
2. Validate `equipment_id` references existing, non-archived Equipment
3. Validate `severity` is in `REPAIR_SEVERITIES` if provided
4. Validate `assignee_id` references existing User if provided
5. Create RepairRecord with status='New'
6. Create RepairTimelineEntry with `entry_type='creation'`, `content=description`
7. Create AuditLog entry with `entity_type='repair_record'`, `action='created'`
8. `db.session.commit()`
9. Log mutation: `'repair_record.created'` with `{id, equipment_id, status, severity, description}`

```python
def get_repair_record(repair_record_id: int) -> RepairRecord:
    """Get a repair record by ID.

    Raises:
        ValidationError: if not found.
    """
```

```python
def list_repair_records(
    equipment_id: int | None = None,
    status: str | None = None,
) -> list[RepairRecord]:
    """List repair records, optionally filtered.

    Args:
        equipment_id: Filter by equipment ID.
        status: Filter by status.

    Returns:
        List of RepairRecord instances ordered by created_at desc.
    """
```

**Follow the exact same patterns as `equipment_service.py`:**
- Use `db.session.get(Model, id)` for PK lookups
- Use `db.select(Model).filter_by(...)` for queries
- Raise `ValidationError` for all error cases
- Call `log_mutation()` for all data changes
- Service handles `db.session.commit()`

**Mutation logging events for this story:**
- `repair_record.created` -- data: `{id, equipment_id, status, severity, description, reporter_name}`

### View Route Patterns

**Repairs Blueprint (`esb/views/repairs.py` -- NEW file):**

```python
"""Repair record routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from esb.forms.repair_forms import RepairRecordCreateForm
from esb.services import equipment_service, repair_service
from esb.utils.decorators import role_required
from esb.utils.exceptions import ValidationError

repairs_bp = Blueprint('repairs', __name__, url_prefix='/repairs')
```

**Create route:**
```python
@repairs_bp.route('/new', methods=['GET', 'POST'])
@role_required('technician')
def create():
    """Create a new repair record."""
    form = RepairRecordCreateForm()

    # Populate equipment choices (active only)
    equipment_list = equipment_service.list_equipment()
    form.equipment_id.choices = [(0, '-- Select Equipment --')] + [
        (e.id, f'{e.name} ({e.area.name})') for e in equipment_list
    ]

    # Populate assignee choices (all active users who are tech or staff)
    from esb.services import user_service
    users = user_service.list_users()
    form.assignee_id.choices = [(0, '-- Unassigned --')] + [
        (u.id, u.username) for u in users
    ]

    if form.validate_on_submit():
        if form.equipment_id.data == 0:
            flash('Please select an equipment item.', 'danger')
            return render_template('repairs/create.html', form=form)

        try:
            record = repair_service.create_repair_record(
                equipment_id=form.equipment_id.data,
                description=form.description.data,
                created_by=current_user.username,
                severity=form.severity.data or None,
                assignee_id=form.assignee_id.data if form.assignee_id.data != 0 else None,
                has_safety_risk=form.has_safety_risk.data,
                is_consumable=form.is_consumable.data,
                author_id=current_user.id,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('repairs/create.html', form=form)

        flash('Repair record created successfully.', 'success')
        return redirect(url_for('repairs.detail', id=record.id))

    return render_template('repairs/create.html', form=form)
```

**Detail route:**
```python
@repairs_bp.route('/<int:id>')
@role_required('technician')
def detail(id):
    """Repair record detail page with timeline."""
    try:
        record = repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    timeline = record.timeline_entries.order_by(
        RepairTimelineEntry.created_at.desc()
    ).all()

    return render_template(
        'repairs/detail.html',
        record=record,
        timeline=timeline,
    )
```

**Blueprint Registration -- Add to `esb/views/__init__.py`:**
Follow the existing pattern. Import `repairs_bp` and register it with the app in `register_blueprints()`.

**Pre-selected equipment route (from equipment detail page):**
```python
@repairs_bp.route('/new', methods=['GET', 'POST'])
@role_required('technician')
def create():
    """Create a new repair record."""
    form = RepairRecordCreateForm()

    # Support pre-selected equipment from query param
    preselected_equipment_id = request.args.get('equipment_id', type=int)

    # ...populate choices...

    if request.method == 'GET' and preselected_equipment_id:
        form.equipment_id.data = preselected_equipment_id

    # ...rest of handler...
```

### Form Patterns

**Repair Forms (`esb/forms/repair_forms.py` -- NEW file):**

```python
"""Repair record forms."""

from flask_wtf import FlaskForm
from wtforms import BooleanField, SelectField, StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Optional

from esb.models.repair_record import REPAIR_SEVERITIES


class RepairRecordCreateForm(FlaskForm):
    """Form for creating a new repair record."""

    equipment_id = SelectField('Equipment *', coerce=int, validators=[DataRequired()])
    description = TextAreaField(
        'Description *', validators=[DataRequired(), Length(max=5000)],
    )
    severity = SelectField(
        'Severity',
        choices=[('', '-- Select Severity --')] + [(s, s) for s in REPAIR_SEVERITIES],
        validators=[Optional()],
    )
    assignee_id = SelectField('Assignee', coerce=int, validators=[Optional()])
    has_safety_risk = BooleanField('Safety Risk')
    is_consumable = BooleanField('Consumable Issue')
    submit = SubmitField('Create Repair Record')
```

**Key form decisions:**
- `equipment_id` uses `coerce=int` and `DataRequired()`. Choices populated in view.
- `severity` uses Optional() with empty default -- technicians may not know severity immediately.
- `assignee_id` uses `coerce=int` with Optional(). `0` means unassigned (checked in view).
- No `reporter_name` / `reporter_email` fields -- those are for member QR/Slack reports (Epic 4).
- Labels follow project convention: asterisk for required fields added in templates, NOT in Python label text (per previous story learnings).

**CORRECTION on labels:** Looking at the existing codebase, labels in forms DO include ` *` suffix for required fields (e.g., `'Name *'` in equipment_forms.py). Follow this existing convention.

### Template Patterns

**Repair Create Template (`esb/templates/repairs/create.html`):**

Follow the pattern from `equipment/form.html`:
- Extends `base.html`
- Breadcrumbs: Repairs > Create Repair Record
- Single-column form layout (`col-md-8`, centered)
- Required Information section header
- Equipment selector dropdown
- Description textarea (3 rows min)
- Optional Details section (below `<hr>`)
- Severity dropdown, assignee dropdown
- Checkboxes for safety risk and consumable
- Submit button (`btn-primary`) + Cancel link (`btn-outline-secondary`)
- Validation errors shown inline with `is-invalid` class and `invalid-feedback` div

**Repair Detail Template (`esb/templates/repairs/detail.html`):**

```html
{% extends "base.html" %}

{% block title %}Repair #{{ record.id }} - Equipment Status Board{% endblock %}

{% block content %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{{ url_for('repairs.create') }}">Repairs</a></li>
        <li class="breadcrumb-item active" aria-current="page">Repair #{{ record.id }}</li>
    </ol>
</nav>

<div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Repair #{{ record.id }}</h1>
    <span class="badge bg-{{ 'danger' if record.severity == 'Down' else ('warning text-dark' if record.severity in ['Degraded', 'Not Sure'] else 'secondary') }}">
        {{ record.severity or 'No Severity' }}
    </span>
</div>

<!-- Repair Information Card -->
<div class="card mb-4">
    <div class="card-header"><h5 class="mb-0">Repair Information</h5></div>
    <div class="card-body">
        <dl class="row mb-0">
            <dt class="col-sm-3">Equipment</dt>
            <dd class="col-sm-9">
                <a href="{{ url_for('equipment.detail', id=record.equipment.id) }}">
                    {{ record.equipment.name }}
                </a>
                ({{ record.equipment.area.name }})
            </dd>
            <dt class="col-sm-3">Status</dt>
            <dd class="col-sm-9"><span class="badge bg-info text-dark">{{ record.status }}</span></dd>
            <dt class="col-sm-3">Severity</dt>
            <dd class="col-sm-9">{{ record.severity or 'Not set' }}</dd>
            <dt class="col-sm-3">Assignee</dt>
            <dd class="col-sm-9">{{ record.assignee.username if record.assignee else 'Unassigned' }}</dd>
            {% if record.eta %}
            <dt class="col-sm-3">ETA</dt>
            <dd class="col-sm-9">{{ record.eta.strftime('%Y-%m-%d') }}</dd>
            {% endif %}
            {% if record.has_safety_risk %}
            <dt class="col-sm-3">Safety Risk</dt>
            <dd class="col-sm-9"><span class="badge bg-danger">SAFETY RISK</span></dd>
            {% endif %}
            <dt class="col-sm-3">Created</dt>
            <dd class="col-sm-9">{{ record.created_at.strftime('%Y-%m-%d %H:%M') }}</dd>
        </dl>
    </div>
</div>

<!-- Timeline Section -->
<h3>Timeline</h3>
<ol class="list-group mb-4">
    {% for entry in timeline %}
    {% include 'components/_timeline_entry.html' %}
    {% endfor %}
</ol>
{% endblock %}
```

**Timeline Entry Partial (`esb/templates/components/_timeline_entry.html`):**

```html
<li class="list-group-item">
    <div class="d-flex justify-content-between align-items-start">
        <div>
            {% if entry.entry_type == 'creation' %}
            <strong>Repair record created</strong>
            {% elif entry.entry_type == 'note' %}
            <strong>Note added</strong>
            {% elif entry.entry_type == 'status_change' %}
            <strong>Status changed from {{ entry.old_value }} to {{ entry.new_value }}</strong>
            {% elif entry.entry_type == 'assignee_change' %}
            <strong>{% if entry.new_value %}Assigned to {{ entry.new_value }}{% else %}Unassigned{% endif %}</strong>
            {% elif entry.entry_type == 'eta_update' %}
            <strong>ETA {% if entry.new_value %}set to {{ entry.new_value }}{% else %}removed{% endif %}</strong>
            {% elif entry.entry_type == 'photo' %}
            <strong>Photo uploaded</strong>
            {% endif %}
            {% if entry.content %}
            <p class="mb-0 mt-1">{{ entry.content }}</p>
            {% endif %}
        </div>
        <small class="text-muted text-nowrap ms-2">
            {{ entry.author_name or (entry.author.username if entry.author else 'System') }}
            &middot;
            {{ entry.created_at.strftime('%Y-%m-%d %H:%M') }}
        </small>
    </div>
</li>
```

**Navbar Update (`esb/templates/base.html`):**

Add a "Repairs" link for Technician and Staff roles. Look at the existing navbar structure and add between Equipment and Admin links:
```html
{% if current_user.is_authenticated %}
<li class="nav-item">
    <a class="nav-link {% if request.endpoint and request.endpoint.startswith('repairs.') %}active{% endif %}"
       href="{{ url_for('repairs.create') }}">Repairs</a>
</li>
{% endif %}
```

**Equipment Detail Link:**

Add a "Create Repair Record" button/link on the equipment detail page to pre-populate the equipment selector:
```html
<a href="{{ url_for('repairs.create', equipment_id=equipment.id) }}"
   class="btn btn-outline-primary btn-sm">Report Issue</a>
```

### Testing Requirements

**Test files:**
- `tests/test_models/test_repair_record.py` -- RepairRecord model tests (NEW)
- `tests/test_models/test_repair_timeline_entry.py` -- RepairTimelineEntry model tests (NEW)
- `tests/test_models/test_audit_log.py` -- AuditLog model tests (NEW)
- `tests/test_services/test_repair_service.py` -- Repair service tests (NEW)
- `tests/test_views/test_repair_views.py` -- Repair view tests (NEW)

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area`, `make_equipment`

**Add new fixtures to `tests/conftest.py`:**
```python
@pytest.fixture
def make_repair_record(app, make_equipment):
    """Factory fixture to create test repair records."""
    def _create(equipment=None, status='New', description='Test issue', **kwargs):
        if equipment is None:
            area = make_area('Test Area')
            equipment = make_equipment('Test Equipment', area_id=area.id)
        record = RepairRecord(
            equipment_id=equipment.id,
            status=status,
            description=description,
            **kwargs,
        )
        _db.session.add(record)
        _db.session.commit()
        return record
    return _create
```

**Required test coverage:**

**Model tests (`test_repair_record.py`):**
- Creation with required fields (equipment_id, description)
- Default status is 'New'
- Default has_safety_risk is False
- Default is_consumable is False
- Timestamps auto-set
- Equipment relationship works
- Assignee relationship works (nullable)
- `__repr__` output

**Model tests (`test_repair_timeline_entry.py`):**
- Creation with required fields (repair_record_id, entry_type)
- Optional fields nullable (content, old_value, new_value, author_id)
- author_name stored
- Timestamp auto-set
- Repair record relationship works
- `__repr__` output

**Model tests (`test_audit_log.py`):**
- Creation with required fields (entity_type, entity_id, action)
- JSON changes column stores/retrieves correctly
- User relationship works (nullable)
- Timestamp auto-set
- `__repr__` output

**Service tests (`test_repair_service.py`):**
- `create_repair_record`: success with minimal fields
- `create_repair_record`: success with all optional fields
- `create_repair_record`: creates timeline creation entry
- `create_repair_record`: creates audit log entry
- `create_repair_record`: mutation log emitted (use `capture` fixture)
- `create_repair_record`: raises ValidationError for missing description
- `create_repair_record`: raises ValidationError for non-existent equipment
- `create_repair_record`: raises ValidationError for archived equipment
- `create_repair_record`: raises ValidationError for invalid severity
- `create_repair_record`: raises ValidationError for non-existent assignee
- `get_repair_record`: returns record by ID
- `get_repair_record`: raises ValidationError when not found
- `list_repair_records`: returns all records ordered by created_at desc
- `list_repair_records`: filters by equipment_id
- `list_repair_records`: returns empty list when none exist

**View tests (`test_repair_views.py`):**
- Create page GET: staff sees form (200)
- Create page GET: technician sees form (200)
- Create page GET: unauthenticated redirects to login (302)
- Create page POST: staff creates record successfully (302 redirect)
- Create page POST: technician creates record successfully (302 redirect)
- Create page POST: missing required field shows validation error (200)
- Create page POST: invalid equipment shows error flash (200)
- Create page POST: pre-selected equipment via query param works
- Detail page GET: staff sees record detail (200)
- Detail page GET: technician sees record detail (200)
- Detail page GET: unauthenticated redirects to login (302)
- Detail page GET: non-existent record returns 404
- Detail page: shows timeline entries
- Detail page: shows equipment name and link

**Critical testing notes from previous stories:**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. DB queries: `db.session.get(Model, id)` for PK lookups
5. Parse mutation log entries from capture: `json.loads(r.message)` where `r` is from `capture.records`
6. `ruff target-version = "py313"` (NOT py314)
7. Error templates extend `base_public.html` to avoid `current_user` dependency

### Previous Story Intelligence

**Patterns established in Stories 1.1-2.4:**
- Service functions: follow `equipment_service.py` patterns exactly (validation, mutation logging, commit pattern)
- View functions: follow `views/equipment.py` patterns (decorator order, form handling, error catching)
- Models: follow `equipment.py` pattern (imports, timestamp lambdas, relationships)
- Forms: follow `equipment_forms.py` pattern (validators, field types, choices)
- Tests: follow `test_equipment_service.py` pattern (fixture usage, assertion patterns)
- Templates: follow `equipment/detail.html` pattern (breadcrumbs, cards, Bootstrap classes)

**Key learnings from Story 2.3-2.4 code reviews:**
1. **IDOR prevention:** Validate parent ownership in delete/update routes (e.g., verify equipment_id matches)
2. Mutation logger `propagate=False` -- use `capture` fixture in tests, NOT `caplog`
3. Flash `'danger'` not `'error'` for Bootstrap alert classes
4. Labels in Python form classes include ` *` suffix for required fields
5. Error templates extend `base_public.html`
6. Import `datetime` from datetime module: `from datetime import UTC, datetime`
7. `make_area` and `make_equipment` fixtures already exist in conftest -- use them
8. Service functions accept primitive types, return model instances

**Existing utility/service references the dev agent MUST use:**
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` for mutation logging
- `esb/utils/exceptions.py` -- `ValidationError` for all validation errors
- `esb/utils/decorators.py` -- `@role_required('technician')` for RBAC
- `esb/extensions.py` -- `db` for database access
- `esb/services/equipment_service.py` -- `get_equipment()`, `list_equipment()` for equipment lookups

### Git Intelligence

**Recent commit pattern:** Each story follows:
1. Story context creation (SM agent)
2. Implementation (dev agent)
3. Code review fixes (1-2 rounds)

**Last 5 commits:**
- `3a64a1c` Fix code review issues for Story 2.4 equipment archiving & technician permissions
- `4d02d4c` Implement Story 2.4: Equipment Archiving & Technician Permissions
- `cd29a92` Create Story 2.4 context for dev agent
- `55e7ba8` Fix code review issues for Story 2.3 equipment documentation & media
- `550795f` Add CLAUDE.md with Docker database migration instructions

**Codebase state:** Epic 2 complete. All Equipment models, services, views, templates, and tests are established and working. The dev agent will be building ON TOP of this foundation. The RepairRecord model has a FK to Equipment, so the Equipment model must already be working (it is).

**Files most likely to be modified:**
- `esb/models/__init__.py` (add 3 new model imports)
- `esb/views/__init__.py` (register repairs Blueprint)
- `esb/templates/base.html` (add Repairs nav link)
- `esb/templates/equipment/detail.html` (add "Report Issue" link)
- `tests/conftest.py` (add `make_repair_record` fixture)

**Files to be created:**
- `esb/models/repair_record.py`
- `esb/models/repair_timeline_entry.py`
- `esb/models/audit_log.py`
- `esb/services/repair_service.py`
- `esb/forms/repair_forms.py`
- `esb/views/repairs.py`
- `esb/templates/repairs/create.html`
- `esb/templates/repairs/detail.html`
- `esb/templates/components/_timeline_entry.html`
- `tests/test_models/test_repair_record.py`
- `tests/test_models/test_repair_timeline_entry.py`
- `tests/test_models/test_audit_log.py`
- `tests/test_services/test_repair_service.py`
- `tests/test_views/test_repair_views.py`
- Alembic migration file

### Project Structure Notes

- All three new models go in their own files under `esb/models/` per the architecture doc
- RepairRecord is the core entity; RepairTimelineEntry and AuditLog are supporting entities
- The `repairs` Blueprint follows the same pattern as `equipment` Blueprint
- Templates go in `esb/templates/repairs/` directory (NEW)
- Timeline entry partial goes in `esb/templates/components/` (shared reusable component)
- Tests mirror the `esb/` structure under `tests/`

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

### Alembic Migration Instructions

The MariaDB database runs in a Docker container. To generate/apply the migration:

```bash
source venv/bin/activate
docker compose up -d db
CONTAINER_IP=$(docker inspect equipment-status-board-db-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}')
DATABASE_URL="mysql+pymysql://root:esb_dev_password@${CONTAINER_IP}/esb" flask db migrate -m "Add repair_records, repair_timeline_entries, and audit_log tables"
DATABASE_URL="mysql+pymysql://root:esb_dev_password@${CONTAINER_IP}/esb" flask db upgrade
```

The container IP changes on restart, so always inspect it fresh. The DB port (3306) is NOT mapped to the host.

### Scope Boundaries

**IN SCOPE for Story 3.1:**
- RepairRecord, RepairTimelineEntry, AuditLog models + migration
- `repair_service.py` with `create_repair_record()`, `get_repair_record()`, `list_repair_records()`
- Create repair record form + route (for authenticated Staff/Technician)
- Repair record detail page with timeline
- Nav link to Repairs
- "Report Issue" link on equipment detail page
- Unit tests for all new code

**OUT OF SCOPE (handled in later stories):**
- Repair record updates/status changes (Story 3.2)
- Adding notes, uploading photos to repairs (Story 3.3)
- Technician repair queue page (Story 3.4)
- Staff Kanban board (Story 3.5)
- Member problem reporting via QR page (Story 4.4)
- Notification queuing on repair creation (Story 5.1)
- Slack integration (Story 6.x)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3, Story 3.1]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture -- RepairRecord, RepairTimelineEntry, AuditLog models]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern -- repair_service.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#Communication Patterns -- Mutation Logging Format]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure -- models/repair_record.py, models/repair_timeline_entry.py, models/audit_log.py]
- [Source: _bmad-output/planning-artifacts/prd.md#FR11 (create repair records), FR13 (10 status workflow), FR14 (severity), FR15 (notes), FR17 (assignee), FR18 (ETA), FR19 (specialist desc), FR20 (audit trail), FR21 (last-write-wins)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Repair Record Detail Page, Timeline Component, Form Patterns]
- [Source: esb/services/equipment_service.py -- Service pattern reference]
- [Source: esb/views/equipment.py -- View/route pattern reference]
- [Source: esb/models/equipment.py -- Model pattern reference]
- [Source: esb/forms/equipment_forms.py -- Form pattern reference]
- [Source: esb/templates/equipment/detail.html -- Template pattern reference]
- [Source: esb/utils/logging.py -- Mutation logging reference]
- [Source: esb/utils/exceptions.py -- Domain exception reference]
- [Source: esb/utils/decorators.py -- RBAC decorator reference]
- [Source: _bmad-output/implementation-artifacts/2-4-equipment-archiving-technician-permissions.md -- Previous story patterns]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed `DataRequired()` on `equipment_id` SelectField: `coerce=int` with `DataRequired` rejects sentinel value 0 (falsy). Removed validator; validation handled in view.
- Fixed `selected` attribute assertion: WTForms renders `<option selected value="X">` not `<option value="X" selected>`.

### Completion Notes List

- Task 1-3: Created RepairRecord, RepairTimelineEntry, AuditLog models with full field specs per AC #1-#3. Constants (REPAIR_STATUSES, REPAIR_SEVERITIES, TIMELINE_ENTRY_TYPES) defined as module-level lists.
- Task 4: Generated and applied Alembic migration `7bd5caedf749`. All three tables verified in MariaDB.
- Task 5: Implemented repair_service.py with create_repair_record (validates equipment, severity, assignee; creates timeline entry + audit log + mutation log), get_repair_record, list_repair_records.
- Task 6: Created RepairRecordCreateForm with equipment selector, description, severity, assignee, safety risk, consumable fields.
- Task 7: Implemented repairs Blueprint with /repairs/new (GET/POST) and /repairs/<id> (GET) routes. Pre-selected equipment via query param supported.
- Task 8: Created create.html, detail.html, and _timeline_entry.html templates following existing Bootstrap patterns.
- Task 9: Navbar already had Repairs link. Added "Report Issue" button on equipment detail page (visible to all authenticated users for non-archived equipment).
- Task 10: 507 tests passing (0 failures). 55 new tests: 12 model (RepairRecord), 8 model (RepairTimelineEntry), 6 model (AuditLog), 15 service, 14 view. Ruff clean.

### Change Log

- 2026-02-15: Implemented Story 3.1 — RepairRecord, RepairTimelineEntry, AuditLog models + migration + service + forms + views + templates + tests

### File List

**New files:**
- esb/models/repair_record.py
- esb/models/repair_timeline_entry.py
- esb/models/audit_log.py
- esb/services/repair_service.py
- esb/forms/repair_forms.py
- esb/templates/repairs/create.html
- esb/templates/repairs/detail.html
- esb/templates/components/_timeline_entry.html
- tests/test_models/test_repair_record.py
- tests/test_models/test_repair_timeline_entry.py
- tests/test_models/test_audit_log.py
- tests/test_services/test_repair_service.py
- tests/test_views/test_repair_views.py
- migrations/versions/7bd5caedf749_add_repair_records_repair_timeline_.py

**Modified files:**
- esb/models/__init__.py
- esb/views/repairs.py
- esb/templates/equipment/detail.html
- tests/conftest.py
