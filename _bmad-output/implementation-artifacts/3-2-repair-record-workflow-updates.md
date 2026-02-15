# Story 3.2: Repair Record Workflow & Updates

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Technician or Staff member,
I want to update repair records through the full workflow with severity, assignee, and ETA,
so that repairs are tracked accurately and coordinated efficiently.

## Acceptance Criteria

1. **Status dropdown with all 10 statuses:** Given I am viewing a repair record detail page, when I change the status using the status dropdown, then I can select any of the 10 statuses: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate. Status transition is not enforced sequentially (any-to-any allowed).

2. **Status change timeline entry:** Given I change a repair record's status, when I save the changes, then a `status_change` entry is added to the timeline showing old and new status, and an audit log entry is created.

3. **Specialist description field:** Given I set the status to "Needs Specialist", when I save the changes, then a free-text specialist description field is available and its value is saved with the record.

4. **Severity update:** Given I am viewing a repair record, when I set or change the severity (Down, Degraded, Not Sure), then the severity is updated and reflected in the record display.

5. **Assignee update with timeline:** Given I am viewing a repair record, when I set or update the assignee by selecting a Technician or Staff user from a dropdown, then an `assignee_change` entry is added to the timeline.

6. **ETA update with timeline:** Given I am viewing a repair record, when I set or update the ETA using a date picker, then an `eta_update` entry is added to the timeline.

7. **Batch save with individual timeline entries:** Given I make multiple changes (status + note + assignee) on a repair record, when I click Save once, then all changes are saved together and individual timeline entries are created for each change type.

8. **Last-write-wins concurrency:** Given two users edit the same repair record concurrently, when both submit their changes, then the last write wins and the audit trail captures both sets of changes with timestamps and authors.

9. **Mutation logging:** Given any repair record update, when the action is performed, then a mutation log entry is written to STDOUT.

## Tasks / Subtasks

- [ ] Task 1: Create RepairRecordUpdateForm (AC: #1, #3, #4, #5, #6, #7)
  - [ ] 1.1 Add `RepairRecordUpdateForm` to `esb/forms/repair_forms.py` with status, severity, assignee, ETA, specialist_description, and note fields
  - [ ] 1.2 Import `DateField` from `wtforms` and `REPAIR_STATUSES` from model

- [ ] Task 2: Implement `update_repair_record()` service function (AC: #1-#9)
  - [ ] 2.1 Add `update_repair_record()` to `esb/services/repair_service.py`
  - [ ] 2.2 Detect changed fields by comparing old vs new values
  - [ ] 2.3 Create `status_change` timeline entry for status changes (old_value → new_value)
  - [ ] 2.4 Create `assignee_change` timeline entry for assignee changes
  - [ ] 2.5 Create `eta_update` timeline entry for ETA changes
  - [ ] 2.6 Create `note` timeline entry if note text provided
  - [ ] 2.7 Create AuditLog entry with all changes as JSON
  - [ ] 2.8 Handle specialist_description (save when status is "Needs Specialist")
  - [ ] 2.9 Emit mutation log to STDOUT
  - [ ] 2.10 Validate status is in REPAIR_STATUSES
  - [ ] 2.11 Validate severity is in REPAIR_SEVERITIES (if provided)
  - [ ] 2.12 Validate assignee_id references existing User (if provided)

- [ ] Task 3: Add update route to repairs Blueprint (AC: #1-#9)
  - [ ] 3.1 Add `GET /repairs/<int:id>/edit` route to display edit form pre-populated with current values
  - [ ] 3.2 Add `POST /repairs/<int:id>/edit` route to handle form submission
  - [ ] 3.3 Populate dynamic choices (status, severity, assignee) in view
  - [ ] 3.4 Handle "0" sentinel for assignee (unassigned) and empty string for severity/ETA (cleared)
  - [ ] 3.5 Redirect to detail page on success with flash message

- [ ] Task 4: Create edit template (AC: #1, #3, #4, #5, #6)
  - [ ] 4.1 Create `esb/templates/repairs/edit.html` with pre-populated form fields
  - [ ] 4.2 Include specialist_description field (can be shown always; only saved when status warrants)
  - [ ] 4.3 Include note textarea for optional note addition
  - [ ] 4.4 ETA field uses native HTML date input (`<input type="date">`)

- [ ] Task 5: Update detail page with Edit button (AC: #1)
  - [ ] 5.1 Add "Edit" button to `esb/templates/repairs/detail.html` linking to the edit page

- [ ] Task 6: Write service tests (AC: #1-#9)
  - [ ] 6.1 Test status change creates status_change timeline entry
  - [ ] 6.2 Test assignee change creates assignee_change timeline entry
  - [ ] 6.3 Test ETA change creates eta_update timeline entry
  - [ ] 6.4 Test note creates note timeline entry
  - [ ] 6.5 Test batch changes create individual timeline entries for each change type
  - [ ] 6.6 Test severity change updates record (no specific timeline entry type)
  - [ ] 6.7 Test specialist_description saved with record
  - [ ] 6.8 Test audit log entry created with all changes
  - [ ] 6.9 Test mutation log emitted
  - [ ] 6.10 Test invalid status raises ValidationError
  - [ ] 6.11 Test invalid severity raises ValidationError
  - [ ] 6.12 Test invalid assignee_id raises ValidationError
  - [ ] 6.13 Test non-existent repair record raises ValidationError
  - [ ] 6.14 Test no-op update (no changes) still succeeds but creates no timeline entries
  - [ ] 6.15 Test clearing assignee (set to None) creates timeline entry
  - [ ] 6.16 Test clearing ETA creates timeline entry

- [ ] Task 7: Write view tests (AC: #1-#9)
  - [ ] 7.1 Test edit page GET: staff sees form pre-populated (200)
  - [ ] 7.2 Test edit page GET: technician sees form (200)
  - [ ] 7.3 Test edit page GET: unauthenticated redirects to login (302)
  - [ ] 7.4 Test edit page GET: non-existent record returns 404
  - [ ] 7.5 Test edit page POST: staff updates record successfully (302 redirect to detail)
  - [ ] 7.6 Test edit page POST: technician updates record successfully
  - [ ] 7.7 Test edit page POST: status change reflected in redirect target
  - [ ] 7.8 Test edit page POST: multiple changes at once (status + assignee + note)
  - [ ] 7.9 Test edit page POST: specialist description saved when status is Needs Specialist
  - [ ] 7.10 Test edit page POST: unauthenticated redirects to login

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- All update business logic in `repair_service.py` -- views are thin controllers
- Service function detects changes, creates timeline entries, audit log, and mutation log
- Dependency flow: `views -> services -> models` (NEVER reverse)
- Service handles `db.session.commit()` -- view never commits directly

**RBAC Rules for This Story:**
- Edit/update repair record: `@role_required('technician')` -- Technicians and Staff can update (Staff > Technician in hierarchy)
- All routes require authentication -- no public access to repair updates

**Last-Write-Wins Concurrency (AC #8):**
- NO optimistic locking -- do NOT add a version column or check `updated_at`
- Simply load the record, apply changes, commit
- The audit log and timeline entries provide a full history of all changes by all users
- This is a deliberate architectural decision per the PRD (FR21)

### File Placement

| File | Action | Purpose |
|------|--------|---------|
| `esb/forms/repair_forms.py` | MODIFY | Add `RepairRecordUpdateForm` class |
| `esb/services/repair_service.py` | MODIFY | Add `update_repair_record()` function |
| `esb/views/repairs.py` | MODIFY | Add `edit()` route (GET/POST) |
| `esb/templates/repairs/edit.html` | NEW | Edit form template |
| `esb/templates/repairs/detail.html` | MODIFY | Add "Edit" button |
| `tests/test_services/test_repair_service.py` | MODIFY | Add update service tests |
| `tests/test_views/test_repair_views.py` | MODIFY | Add update view tests |

**No new models or migrations required.** All fields (status, severity, assignee_id, eta, specialist_description) already exist on the RepairRecord model from Story 3.1. All timeline entry types (`status_change`, `assignee_change`, `eta_update`, `note`) already exist in the RepairTimelineEntry model.

### Service Function Contract

**`update_repair_record()` in `esb/services/repair_service.py`:**

```python
def update_repair_record(
    repair_record_id: int,
    updated_by: str,
    author_id: int | None = None,
    **changes,
) -> RepairRecord:
    """Update a repair record and create timeline entries for each change.

    Accepts keyword arguments for any updatable field. Only fields that
    actually differ from the current value will generate timeline entries.

    Updatable fields:
        status (str): New status value. Must be in REPAIR_STATUSES.
        severity (str | None): New severity value. Must be in REPAIR_SEVERITIES or None.
        assignee_id (int | None): New assignee user ID, or None to unassign.
        eta (date | None): New ETA date, or None to clear.
        specialist_description (str | None): Free-text description for specialist needs.
        note (str | None): Optional note text to add to timeline.

    Returns:
        The updated RepairRecord.

    Raises:
        ValidationError: if repair record not found, or invalid field values.
    """
```

**Implementation approach:**

```python
_REPAIR_UPDATABLE_FIELDS = {'status', 'severity', 'assignee_id', 'eta', 'specialist_description'}

def update_repair_record(
    repair_record_id: int,
    updated_by: str,
    author_id: int | None = None,
    **changes,
) -> RepairRecord:
    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    # Validate incoming values
    if 'status' in changes and changes['status'] not in REPAIR_STATUSES:
        raise ValidationError(f'Invalid status: {changes["status"]!r}')
    if 'severity' in changes and changes['severity'] is not None and changes['severity'] not in REPAIR_SEVERITIES:
        raise ValidationError(f'Invalid severity: {changes["severity"]!r}')
    if 'assignee_id' in changes and changes['assignee_id'] is not None:
        assignee = db.session.get(User, changes['assignee_id'])
        if assignee is None:
            raise ValidationError(f'User with id {changes["assignee_id"]} not found')

    # Extract note separately (not a model field)
    note = changes.pop('note', None)

    # Detect changes and create timeline entries
    audit_changes = {}
    for field_name in _REPAIR_UPDATABLE_FIELDS:
        if field_name not in changes:
            continue
        new_value = changes[field_name]
        old_value = getattr(record, field_name)
        if old_value == new_value:
            continue

        # Record the change
        audit_changes[field_name] = [_serialize(old_value), _serialize(new_value)]
        setattr(record, field_name, new_value)

        # Create appropriate timeline entry
        if field_name == 'status':
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='status_change',
                author_id=author_id,
                author_name=updated_by,
                old_value=str(old_value),
                new_value=str(new_value),
            ))
        elif field_name == 'assignee_id':
            # Resolve usernames for timeline display
            old_name = db.session.get(User, old_value).username if old_value else None
            new_name = db.session.get(User, new_value).username if new_value else None
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='assignee_change',
                author_id=author_id,
                author_name=updated_by,
                old_value=old_name,
                new_value=new_name,
            ))
        elif field_name == 'eta':
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='eta_update',
                author_id=author_id,
                author_name=updated_by,
                old_value=str(old_value) if old_value else None,
                new_value=str(new_value) if new_value else None,
            ))
        # severity and specialist_description: no specific timeline entry type,
        # tracked in audit log only

    # Create note timeline entry if note provided
    if note and note.strip():
        db.session.add(RepairTimelineEntry(
            repair_record_id=record.id,
            entry_type='note',
            author_id=author_id,
            author_name=updated_by,
            content=note.strip(),
        ))
        audit_changes['note'] = note.strip()

    # Create audit log entry (even if no model field changes, if there's a note)
    if audit_changes:
        db.session.add(AuditLog(
            entity_type='repair_record',
            entity_id=record.id,
            action='updated',
            user_id=author_id,
            changes=audit_changes,
        ))

    db.session.commit()

    if audit_changes:
        log_mutation('repair_record.updated', updated_by, {
            'id': record.id,
            'changes': audit_changes,
        })

    return record
```

**Critical implementation notes:**
1. Use `db.session.get(RepairRecord, id)` for lookup (not `query.get()`)
2. `db.session.flush()` is NOT needed here since we already have `record.id` from the existing record
3. `db.session.commit()` once at the end for atomic save
4. Timeline entries use `old_value`/`new_value` String(200) columns -- serialize dates and None appropriately
5. The `note` field is NOT a model field on RepairRecord -- it's extracted from `changes` and only creates a timeline entry
6. Severity changes do NOT create a specific timeline entry (no `severity_change` type exists in `TIMELINE_ENTRY_TYPES`). They are tracked in the audit log.
7. `specialist_description` changes do NOT create a timeline entry either -- tracked in audit log
8. For `assignee_change` timeline entries, resolve user IDs to usernames for `old_value`/`new_value` display
9. A helper `_serialize(value)` may be useful: `str(value) if value is not None else None` -- handles date → string conversion for audit log JSON

### Form Design

**`RepairRecordUpdateForm` in `esb/forms/repair_forms.py`:**

```python
from wtforms import DateField

class RepairRecordUpdateForm(FlaskForm):
    """Form for updating a repair record."""

    status = SelectField('Status *', validators=[DataRequired()])
    severity = SelectField(
        'Severity',
        choices=[('', '-- No Severity --')] + [(s, s) for s in REPAIR_SEVERITIES],
        validators=[Optional()],
    )
    assignee_id = SelectField('Assignee', coerce=int, validators=[Optional()])
    eta = DateField('ETA', validators=[Optional()])
    specialist_description = TextAreaField(
        'Specialist Description',
        validators=[Optional(), Length(max=5000)],
    )
    note = TextAreaField('Add Note', validators=[Optional(), Length(max=5000)])
    submit = SubmitField('Save Changes')
```

**Key form decisions:**
- `status` uses `DataRequired()` -- a repair record must always have a status
- `status` choices populated dynamically in the view from `REPAIR_STATUSES`
- `severity` has `('', '-- No Severity --')` as first option to allow clearing severity
- `assignee_id` uses `coerce=int` with `(0, '-- Unassigned --')` sentinel to allow clearing
- `eta` uses `DateField` (WTForms built-in, renders as `<input type="date">`)
- `specialist_description` always present in form, but only saved when relevant
- `note` is optional -- if provided, creates a `note` timeline entry

### View Route Pattern

**Edit route in `esb/views/repairs.py`:**

```python
@repairs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@role_required('technician')
def edit(id):
    """Edit a repair record."""
    try:
        record = repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairRecordUpdateForm(obj=record)

    # Populate dynamic choices
    form.status.choices = [(s, s) for s in REPAIR_STATUSES]

    from esb.services import user_service
    users = user_service.list_users()
    form.assignee_id.choices = [(0, '-- Unassigned --')] + [
        (u.id, u.username) for u in users
    ]

    if request.method == 'GET':
        # Pre-populate form with current record values
        form.status.data = record.status
        form.severity.data = record.severity or ''
        form.assignee_id.data = record.assignee_id or 0
        form.eta.data = record.eta
        form.specialist_description.data = record.specialist_description or ''
        form.note.data = ''  # Always empty on load

    if form.validate_on_submit():
        try:
            repair_service.update_repair_record(
                repair_record_id=id,
                updated_by=current_user.username,
                author_id=current_user.id,
                status=form.status.data,
                severity=form.severity.data or None,
                assignee_id=form.assignee_id.data if form.assignee_id.data != 0 else None,
                eta=form.eta.data,
                specialist_description=form.specialist_description.data or None,
                note=form.note.data or None,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('repairs/edit.html', form=form, record=record)

        flash('Repair record updated successfully.', 'success')
        return redirect(url_for('repairs.detail', id=id))

    return render_template('repairs/edit.html', form=form, record=record)
```

**Key view decisions:**
- Uses `WTForms` `obj=record` for initial form binding, but explicitly sets values on GET for sentinel handling
- `assignee_id=0` sentinel translates to `None` (unassigned) when calling service
- `severity=''` (empty string from form) translates to `None` when calling service
- Always passes `record` to template for display context (breadcrumbs, title)
- Follows PRG pattern: redirect to detail page on success

### Template Design

**Edit template (`esb/templates/repairs/edit.html`):**

Follow the exact pattern from `esb/templates/repairs/create.html`:
- Extends `base.html`
- Breadcrumbs: Repairs > Repair #N > Edit
- Single-column form layout (`col-md-8`, centered)
- Form fields: Status dropdown, Severity dropdown, Assignee dropdown, ETA date input, Specialist Description textarea, Note textarea
- Save Changes button (`btn-primary`) + Cancel link (`btn-outline-secondary`) linking back to detail page
- Validation errors shown inline with `is-invalid` class and `invalid-feedback` div
- `{{ form.hidden_tag() }}` for CSRF
- `novalidate` on form element (server-side validation)

**Detail page modification (`esb/templates/repairs/detail.html`):**

Add an "Edit" button in the page header:
```html
<div class="d-flex justify-content-between align-items-center mb-3">
    <h1>Repair #{{ record.id }}</h1>
    <div>
        <a href="{{ url_for('repairs.edit', id=record.id) }}" class="btn btn-primary">Edit</a>
        <span class="badge bg-{{ ... }}">{{ record.severity or 'No Severity' }}</span>
    </div>
</div>
```

Also add specialist description display to the detail page if present:
```html
{% if record.specialist_description %}
<dt class="col-sm-3">Specialist Description</dt>
<dd class="col-sm-9">{{ record.specialist_description }}</dd>
{% endif %}
```

### Database Notes

**No new migration required.** All fields already exist on RepairRecord from Story 3.1:
- `status` (String(50), default 'New')
- `severity` (String(20), nullable)
- `assignee_id` (Integer FK to users, nullable)
- `eta` (Date, nullable)
- `specialist_description` (Text, nullable)

All timeline entry types already exist:
- `status_change` (with old_value/new_value)
- `assignee_change` (with old_value/new_value for usernames)
- `eta_update` (with old_value/new_value for dates)
- `note` (with content)

### Testing Requirements

**Add tests to existing files -- do NOT create new test files.**

**Service tests (`tests/test_services/test_repair_service.py` -- ADD to existing):**

```python
class TestUpdateRepairRecord:
    """Tests for update_repair_record()."""

    def test_status_change_creates_timeline_entry(self, app, make_repair_record, staff_user):
        record = make_repair_record(status='New')
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, status='In Progress',
        )
        assert updated.status == 'In Progress'
        timeline = RepairTimelineEntry.query.filter_by(
            repair_record_id=record.id, entry_type='status_change',
        ).first()
        assert timeline is not None
        assert timeline.old_value == 'New'
        assert timeline.new_value == 'In Progress'

    # ... etc
```

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area`, `make_equipment`, `make_repair_record`

**Service test cases (add to `tests/test_services/test_repair_service.py`):**
1. `test_status_change_creates_timeline_entry` -- verify status_change entry with old/new values
2. `test_assignee_change_creates_timeline_entry` -- verify assignee_change entry with usernames
3. `test_assignee_clear_creates_timeline_entry` -- set assignee_id to None, verify entry
4. `test_eta_change_creates_timeline_entry` -- verify eta_update entry with date strings
5. `test_eta_clear_creates_timeline_entry` -- clear ETA, verify entry
6. `test_note_creates_timeline_entry` -- verify note entry with content
7. `test_batch_changes_create_individual_entries` -- change status + assignee + note, verify 3 separate timeline entries
8. `test_severity_change_updates_record` -- verify severity updated, no specific timeline entry
9. `test_specialist_description_saved` -- verify specialist_description persisted
10. `test_audit_log_created_with_changes` -- verify AuditLog with changes JSON
11. `test_mutation_log_emitted` -- verify mutation log (use `capture` fixture)
12. `test_invalid_status_raises` -- ValidationError for bad status
13. `test_invalid_severity_raises` -- ValidationError for bad severity
14. `test_invalid_assignee_raises` -- ValidationError for non-existent user
15. `test_not_found_raises` -- ValidationError for non-existent repair record
16. `test_no_changes_no_entries` -- no actual changes = no timeline entries, no audit log
17. `test_any_to_any_status_transition` -- verify can go from any status to any other status

**View test cases (add to `tests/test_views/test_repair_views.py`):**
1. `test_edit_page_staff_sees_form` -- GET returns 200 with pre-populated form
2. `test_edit_page_technician_sees_form` -- GET returns 200
3. `test_edit_page_unauthenticated_redirects` -- GET returns 302 to login
4. `test_edit_page_not_found` -- GET with bad ID returns 404
5. `test_edit_post_staff_updates_successfully` -- POST returns 302 redirect to detail
6. `test_edit_post_technician_updates_successfully` -- POST returns 302
7. `test_edit_post_status_change_saved` -- verify record status changed after POST
8. `test_edit_post_multiple_changes` -- POST with status + assignee + note
9. `test_edit_post_specialist_description` -- POST with status=Needs Specialist + description
10. `test_edit_post_unauthenticated_redirects` -- POST returns 302 to login

**Critical testing notes (from Story 3.1 learnings):**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. `db.session.get(Model, id)` for PK lookups in assertions
5. Parse mutation log entries: `json.loads(r.message)` where `r` is from `capture.records`
6. `ruff target-version = "py313"` (NOT py314)
7. For form POSTs in tests, data keys match form field names exactly
8. For SelectField with `coerce=int`, POST data values are strings (e.g., `'1'` not `1`)
9. DateField expects `YYYY-MM-DD` format in POST data

### Project Structure Notes

- All changes fit within existing file structure -- no new directories needed
- Only one new file: `esb/templates/repairs/edit.html`
- All other changes are modifications to existing files created in Story 3.1
- No new models, no new migrations, no new dependencies

### Previous Story Intelligence

**Patterns established in Story 3.1 (MUST follow):**
- `repair_service.py`: Function signature pattern -- primitive params, return model instances, raise `ValidationError`
- `views/repairs.py`: Route pattern -- `@role_required('technician')`, form handling, `flash()` on success/error, PRG redirect
- `forms/repair_forms.py`: Form pattern -- `FlaskForm`, validators, `coerce=int` for SelectField with FK
- `templates/repairs/`: Template pattern -- extends `base.html`, breadcrumbs, Bootstrap classes
- `tests/`: Test pattern -- class-based grouping, fixture usage, `capture` for mutation log

**Key learnings from Story 3.1 code review:**
1. Navbar already has Repairs link with auth guard and active class -- no changes needed
2. Blueprint already registered in `esb/views/__init__.py` -- no changes needed
3. `make_repair_record` fixture exists in `tests/conftest.py` -- use it
4. The `repairs.index` route currently redirects to `repairs.create` -- this is a placeholder. Do NOT change it in this story; it will become the repair queue in Story 3.4.
5. Import `user_service` locally inside view functions (not at module top) to avoid circular imports -- follow existing pattern in `create()` view

**Existing code the dev agent MUST use (NOT re-implement):**
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` for mutation logging
- `esb/utils/exceptions.py` -- `ValidationError` for all validation errors
- `esb/utils/decorators.py` -- `@role_required('technician')` for RBAC
- `esb/extensions.py` -- `db` for database access
- `esb/models/repair_record.py` -- `REPAIR_STATUSES`, `REPAIR_SEVERITIES`, `RepairRecord`
- `esb/models/repair_timeline_entry.py` -- `RepairTimelineEntry`, `TIMELINE_ENTRY_TYPES`
- `esb/models/audit_log.py` -- `AuditLog`
- `esb/services/user_service.py` -- `list_users()` for assignee dropdown population

### Git Intelligence

**Recent commits (3-commit cadence per story):**
- `9ad4fd7` Fix code review issues for Story 3.1 repair record creation & data model
- `7cbdfe6` Implement Story 3.1: Repair Record Creation & Data Model
- `59002c9` Create Story 3.1 context for dev agent

**Files most recently modified relevant to this story:**
- `esb/services/repair_service.py` (Story 3.1 -- add `update_repair_record()` here)
- `esb/views/repairs.py` (Story 3.1 -- add `edit()` route here)
- `esb/forms/repair_forms.py` (Story 3.1 -- add `RepairRecordUpdateForm` here)
- `esb/templates/repairs/detail.html` (Story 3.1 -- add "Edit" button here)
- `tests/test_services/test_repair_service.py` (Story 3.1 -- add update tests here)
- `tests/test_views/test_repair_views.py` (Story 3.1 -- add update view tests here)

**Current test count:** 508 tests passing. Expect ~25-30 new tests.

### Library/Framework Requirements

| Package | Version | Notes |
|---------|---------|-------|
| Flask | 3.1.x | Already installed |
| Flask-SQLAlchemy | 3.1.x | Already installed |
| Flask-WTF / WTForms | 1.2.x | Already installed -- uses `DateField` from wtforms |
| Flask-Login | 0.6.3 | Already installed |
| Bootstrap | 5.3.8 | Bundled locally in `esb/static/` |

**No new dependencies required for this story.**

### Scope Boundaries

**IN SCOPE for Story 3.2:**
- Update repair record via edit form (status, severity, assignee, ETA, specialist description)
- Optional note during update (creates `note` timeline entry)
- Timeline entries for status, assignee, and ETA changes
- Audit logging for all changes
- Mutation logging for all changes
- Any-to-any status transitions (no enforced sequence)
- Last-write-wins concurrency (no optimistic locking)
- Edit page template and "Edit" button on detail page

**OUT OF SCOPE (handled in later stories):**
- Standalone note addition without other changes (Story 3.3 covers the full timeline/notes/photos experience)
- Photo/video uploads (Story 3.3)
- Repair queue page (Story 3.4)
- Kanban board (Story 3.5)
- Problem reporting from QR pages (Story 4.4)
- Notification queuing on status changes (Story 5.1)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3, Story 3.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern -- repair_service.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#View Function Pattern -- parse input → call service → render]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture -- RepairRecord, RepairTimelineEntry, AuditLog]
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns -- Route/URL, Template File, Python Code]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 2: Technician Works the Repair Queue]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns, Feedback Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Repair Timeline Custom Component]
- [Source: _bmad-output/planning-artifacts/prd.md#FR13 (10 status workflow), FR14 (severity), FR17 (assignee), FR18 (ETA), FR19 (specialist desc), FR20 (audit trail), FR21 (last-write-wins)]
- [Source: esb/services/repair_service.py -- Existing create pattern to follow for update]
- [Source: esb/services/equipment_service.py#update_equipment -- Update pattern reference with change detection]
- [Source: esb/views/repairs.py -- Existing view pattern to follow]
- [Source: esb/forms/repair_forms.py -- Existing form pattern to follow]
- [Source: esb/templates/repairs/create.html -- Template pattern reference for edit.html]
- [Source: esb/templates/repairs/detail.html -- Modify to add Edit button]
- [Source: esb/models/repair_record.py -- REPAIR_STATUSES, REPAIR_SEVERITIES constants]
- [Source: esb/models/repair_timeline_entry.py -- TIMELINE_ENTRY_TYPES, entry model]
- [Source: esb/utils/logging.py -- log_mutation() function]
- [Source: _bmad-output/implementation-artifacts/3-1-repair-record-creation-data-model.md -- Previous story patterns and learnings]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### Change Log

### File List
