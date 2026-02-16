# Story 4.4: Problem Reporting via QR Code Page

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a member,
I want to report an equipment problem from the QR code page in under 90 seconds,
So that issues get tracked and fixed without me needing to figure out who to tell.

## Acceptance Criteria

1. **Given** I am on a QR code equipment page, **When** there are open repair records for this equipment, **Then** a "Known Issues" section is displayed below the Equipment Info link, showing each open issue with severity and description **And** messaging reads: "If your issue is listed below, it's already being worked on." (AC: #1 -- already implemented in Story 4.3)

2. **Given** there are no open repair records, **When** I view the QR code equipment page, **Then** the "Known Issues" section is hidden entirely (not shown as empty). (AC: #2 -- already implemented in Story 4.3)

3. **Given** I am on a QR code equipment page, **When** I scroll below the Known Issues section (or below the Equipment Info link if no issues exist), **Then** I see a "Report a Problem" form. (AC: #3)

4. **Given** the problem report form, **When** I view it, **Then** I see required fields: name and description **And** optional fields: severity (dropdown, defaults to "Not Sure"), safety risk flag (checkbox), consumable checkbox, email, and photo upload **And** a large, full-width submit button. (AC: #4)

5. **Given** I fill in name and description and tap Submit, **When** validation passes, **Then** a repair record is created with status "New" and the submitted details **And** a confirmation page is displayed. (AC: #5)

6. **Given** I submit without filling in the name or description, **When** validation runs, **Then** inline error messages appear next to the missing required fields and the form is not submitted. (AC: #6)

7. **Given** I check the safety risk flag, **When** the repair record is created, **Then** the `has_safety_risk` field is set to true on the repair record. (AC: #7)

8. **Given** the confirmation page, **When** it is displayed after successful submission, **Then** it shows a confirmation message and links to the relevant Slack channels (#area-channel and #oops) **And** a "Report another issue" link is available. (AC: #8)

9. **Given** I upload a photo with my problem report, **When** the form is submitted, **Then** the photo is saved to `uploads/repairs/{id}/` and attached to the repair record. (AC: #9)

10. **Given** the problem report form, **When** viewed on mobile, **Then** form fields are full-width, the submit button is full-width with minimum 48px height, and the photo upload triggers the native camera/gallery picker. (AC: #10)

## Tasks / Subtasks

- [x] Task 1: Create `ProblemReportForm` in `esb/forms/repair_forms.py` (AC: #4, #6)
  - [x] 1.1: Add `ProblemReportForm` class with fields: `reporter_name` (StringField, required), `description` (TextAreaField, required), `severity` (SelectField, choices: Down/Degraded/Not Sure, default "Not Sure"), `has_safety_risk` (BooleanField), `is_consumable` (BooleanField), `reporter_email` (StringField, optional, email validation if provided), `photo` (FileField, optional, allowed extensions: jpg/jpeg/png/gif/webp/mp4/mov/avi/webm)
  - [x] 1.2: Use existing `ALLOWED_PHOTO_EXTENSIONS` pattern from `RepairPhotoUploadForm` for file validation
  - [x] 1.3: Import `REPAIR_SEVERITIES` from `esb.models.repair_record` for severity choices

- [x] Task 2: Add problem report form to `esb/templates/public/equipment_page.html` (AC: #3, #4, #10)
  - [x] 2.1: Add "Report a Problem" section below Known Issues (or below Equipment Info link if no issues)
  - [x] 2.2: Form action posts to `url_for('public.report_problem', id=equipment.id)`
  - [x] 2.3: Include `enctype="multipart/form-data"` for photo upload support
  - [x] 2.4: Render required fields: reporter_name (label "Your Name"), description (textarea, min 3 rows)
  - [x] 2.5: Render optional fields: severity (dropdown defaulting to "Not Sure"), has_safety_risk (checkbox "This is a safety risk"), is_consumable (checkbox "This is a consumable item"), reporter_email (label "Email (optional)"), photo (file input with `accept="image/*,video/*"` and `capture="environment"`)
  - [x] 2.6: Large, full-width submit button (`btn-primary btn-lg w-100` with min-height 48px)
  - [x] 2.7: Inline validation error display using Bootstrap `invalid-feedback` pattern
  - [x] 2.8: Hidden CSRF token field (Flask-WTF handles this)
  - [x] 2.9: ARIA labels on all form fields

- [x] Task 3: Add `report_problem` POST route to `esb/views/public.py` (AC: #5, #7, #9)
  - [x] 3.1: Add `POST /public/equipment/<int:id>/report` route -- NO `@login_required`
  - [x] 3.2: Instantiate `ProblemReportForm` from request data
  - [x] 3.3: On validation failure: re-render `equipment_page.html` with form errors, preserving all page context (equipment, status, open_repairs, eta, form)
  - [x] 3.4: On validation pass: call `repair_service.create_repair_record()` with form data
  - [x] 3.5: Pass `has_safety_risk=form.has_safety_risk.data` and `is_consumable=form.is_consumable.data`
  - [x] 3.6: If photo uploaded: call `upload_service.save_upload(file=form.photo.data, parent_type='repair_photo', parent_id=record.id, uploaded_by=form.reporter_name.data)`
  - [x] 3.7: On success: redirect to `url_for('public.report_confirmation', id=equipment.id, record_id=record.id)`
  - [x] 3.8: On `ValidationError` from service: flash error message with category `'danger'`, re-render form

- [x] Task 4: Add `report_confirmation` GET route to `esb/views/public.py` (AC: #8)
  - [x] 4.1: Add `GET /public/equipment/<int:id>/report-confirmation` route -- NO `@login_required`
  - [x] 4.2: Accept `record_id` as query parameter
  - [x] 4.3: Load equipment (404 if not found/archived) and repair record
  - [x] 4.4: Load equipment's area for Slack channel display
  - [x] 4.5: Render `public/report_confirmation.html` with equipment, repair record, and area info

- [x] Task 5: Create `esb/templates/public/report_confirmation.html` (AC: #8)
  - [x] 5.1: Extends `base_public.html` (no navbar, public page)
  - [x] 5.2: Success heading and confirmation message ("Thank you for reporting this issue!")
  - [x] 5.3: Display submitted issue summary (description, severity)
  - [x] 5.4: Display Slack channel links: area-specific channel (from `equipment.area.slack_channel`) and `#oops`
  - [x] 5.5: "Report another issue" link back to equipment page with form anchor
  - [x] 5.6: "Back to equipment status" link to equipment page
  - [x] 5.7: Mobile-friendly, single-column layout

- [x] Task 6: Update `equipment_page` GET route in `esb/views/public.py` to pass empty form (AC: #3)
  - [x] 6.1: Import and instantiate `ProblemReportForm()` (empty) in the existing `equipment_page()` view
  - [x] 6.2: Pass `form=form` to the template context

- [x] Task 7: Add problem report form CSS to `esb/static/css/app.css` (AC: #10)
  - [x] 7.1: Submit button min-height 48px styling
  - [x] 7.2: Form section spacing consistent with rest of QR page
  - [x] 7.3: File input touch-friendly sizing

- [x] Task 8: Write view tests for problem report form display (AC: #3, #4)
  - [x] 8.1: Test equipment page shows report form without authentication
  - [x] 8.2: Test form has required fields (name, description)
  - [x] 8.3: Test form has optional fields (severity, safety risk, consumable, email, photo)
  - [x] 8.4: Test form has submit button
  - [x] 8.5: Test form has CSRF token (rendered, but disabled in test config)
  - [x] 8.6: Test form has `enctype="multipart/form-data"`

- [x] Task 9: Write view tests for problem report submission (AC: #5, #6, #7, #9)
  - [x] 9.1: Test valid submission creates repair record with status "New"
  - [x] 9.2: Test submission sets reporter_name and reporter_email on record
  - [x] 9.3: Test submission with severity sets severity on record
  - [x] 9.4: Test submission without severity defaults to "Not Sure"
  - [x] 9.5: Test submission with safety risk flag sets has_safety_risk=True
  - [x] 9.6: Test submission with consumable flag sets is_consumable=True
  - [x] 9.7: Test missing name shows validation error (no record created)
  - [x] 9.8: Test missing description shows validation error (no record created)
  - [x] 9.9: Test submission with photo saves photo to uploads/repairs/{id}/
  - [x] 9.10: Test submission redirects to confirmation page
  - [x] 9.11: Test submission for archived equipment returns 404
  - [x] 9.12: Test submission for non-existent equipment returns 404
  - [x] 9.13: Test valid submission creates timeline entry

- [x] Task 10: Write view tests for confirmation page (AC: #8)
  - [x] 10.1: Test confirmation page renders without authentication
  - [x] 10.2: Test confirmation page shows success message
  - [x] 10.3: Test confirmation page shows Slack channel links (area channel + #oops)
  - [x] 10.4: Test confirmation page has "Report another issue" link
  - [x] 10.5: Test confirmation page has "Back to status" link
  - [x] 10.6: Test confirmation page returns 404 for non-existent equipment

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Single CSS/JS files:** All custom styles go in `esb/static/css/app.css`. All custom JS goes in `esb/static/js/app.js`. NO per-page CSS/JS files.
5. **Template naming:** snake_case for templates (`report_confirmation.html`). Underscore prefix for partials (`_status_indicator.html`).
6. **Public routes:** These routes go in `esb/views/public.py` with NO `@login_required` -- they are unauthenticated public pages.
7. **Domain exceptions:** Use `ValidationError` from `esb/utils/exceptions.py`. Views catch and flash `'danger'` or `abort(404)`.
8. **Flash category:** Use `'danger'` NOT `'error'` for error flash messages.
9. **Form handling:** Flask-WTF for CSRF protection and validation. Validate on submit, not on blur.
10. **Import pattern:** Import services locally inside view functions to avoid circular imports.

### Critical Implementation Details

#### ProblemReportForm (`esb/forms/repair_forms.py`)

Add this form to the EXISTING file. Do NOT create a new file.

```python
class ProblemReportForm(FlaskForm):
    """Public problem report form -- no authentication required."""
    reporter_name = StringField('Your Name', validators=[
        DataRequired(message='Name is required'),
        Length(max=200),
    ])
    description = TextAreaField('Description', validators=[
        DataRequired(message='Description is required'),
        Length(max=5000),
    ])
    severity = SelectField('Severity', choices=[
        ('Not Sure', 'Not Sure'),
        ('Degraded', 'Degraded'),
        ('Down', 'Down'),
    ], default='Not Sure')
    has_safety_risk = BooleanField('This is a safety risk')
    is_consumable = BooleanField('This is a consumable item (e.g., filament, sandpaper)')
    reporter_email = StringField('Email (optional)', validators=[
        Optional(),
        Email(message='Please enter a valid email address'),
        Length(max=255),
    ])
    photo = FileField('Photo (optional)')
    submit = SubmitField('Submit Report')
```

**Key decisions:**
- `reporter_name` and `description` are the ONLY required fields (per FR22)
- `reporter_email` is OPTIONAL with email validation only when provided (use `Optional()` validator)
- `severity` defaults to "Not Sure" (per FR22)
- `has_safety_risk` and `is_consumable` are BooleanField (checkboxes)
- `photo` is FileField -- validation of allowed extensions done in upload_service, not in form
- Import `Optional` from `wtforms.validators` and `Email` from `wtforms.validators`

#### Report Problem Route (`esb/views/public.py`)

```python
@public_bp.route('/equipment/<int:id>/report', methods=['POST'])
def report_problem(id):
    """Handle problem report form submission -- public, no auth required."""
    from esb.forms.repair_forms import ProblemReportForm
    from esb.services import equipment_service, repair_service, status_service, upload_service
    from esb.services.repair_service import CLOSED_STATUSES

    form = ProblemReportForm()

    # Load equipment context (needed for re-rendering on validation failure)
    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)
    if equipment.is_archived:
        abort(404)

    if form.validate_on_submit():
        try:
            record = repair_service.create_repair_record(
                equipment_id=id,
                description=form.description.data,
                created_by=form.reporter_name.data,
                severity=form.severity.data,
                reporter_name=form.reporter_name.data,
                reporter_email=form.reporter_email.data or None,
                has_safety_risk=form.has_safety_risk.data,
                is_consumable=form.is_consumable.data,
                author_id=None,  # Anonymous -- no user account
            )

            # Handle optional photo upload
            if form.photo.data and hasattr(form.photo.data, 'filename') and form.photo.data.filename:
                try:
                    upload_service.save_upload(
                        file=form.photo.data,
                        parent_type='repair_photo',
                        parent_id=record.id,
                        uploaded_by=form.reporter_name.data,
                    )
                except ValidationError as e:
                    # Photo upload failed but record was created -- flash warning, don't fail
                    flash(f'Report submitted but photo upload failed: {e}', 'warning')

            return redirect(url_for('public.report_confirmation', id=id, record_id=record.id))

        except ValidationError as e:
            flash(str(e), 'danger')

    # Validation failed or service error -- re-render equipment page with form errors
    status = status_service.compute_equipment_status(id)
    open_repairs = [
        r for r in repair_service.list_repair_records(equipment_id=id)
        if r.status not in CLOSED_STATUSES
    ]
    eta = None
    if open_repairs:
        for repair in sorted(open_repairs, key=lambda r: {'Down': 0, 'Degraded': 1, 'Not Sure': 2}.get(r.severity or '', 3)):
            if repair.eta:
                eta = repair.eta
                break

    return render_template(
        'public/equipment_page.html',
        equipment=equipment,
        status=status,
        open_repairs=open_repairs,
        eta=eta,
        form=form,
    )
```

**Critical notes:**
- `equipment_service.get_equipment()` raises `ValidationError` (NOT `EquipmentNotFound`) -- learned from Story 4.3 dev notes
- On validation failure, must re-render the ENTIRE equipment page with all context (equipment, status, open_repairs, eta, form with errors)
- Photo upload is best-effort -- if it fails, the report is still created with a warning
- `form.photo.data` check must verify `filename` exists (empty file inputs still have a FileStorage object)
- `reporter_email` passed as `None` if empty string (to avoid storing empty strings)

#### Confirmation Route (`esb/views/public.py`)

```python
@public_bp.route('/equipment/<int:id>/report-confirmation')
def report_confirmation(id):
    """Display confirmation after successful problem report submission."""
    from esb.services import equipment_service

    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)
    if equipment.is_archived:
        abort(404)

    record_id = request.args.get('record_id', type=int)

    return render_template(
        'public/report_confirmation.html',
        equipment=equipment,
        record_id=record_id,
    )
```

#### Update Equipment Page GET Route

Modify the existing `equipment_page()` function to also pass an empty form:

```python
@public_bp.route('/equipment/<int:id>')
def equipment_page(id):
    # ... existing code ...
    from esb.forms.repair_forms import ProblemReportForm
    form = ProblemReportForm()

    return render_template(
        'public/equipment_page.html',
        equipment=equipment,
        status=status,
        open_repairs=open_repairs,
        eta=eta,
        form=form,  # NEW: pass empty form for problem reporting
    )
```

#### Template: Report Form on `equipment_page.html`

Add AFTER the Known Issues section (`{% endif %}` on line 46), BEFORE `{% endblock %}`:

```jinja2
{# Problem Report Form #}
<div class="mt-4">
  <h2>Report a Problem</h2>
  <p class="text-muted">Don't see your issue listed above? Let us know.</p>

  <form method="POST" action="{{ url_for('public.report_problem', id=equipment.id) }}"
        enctype="multipart/form-data" novalidate>
    {{ form.hidden_tag() }}

    <div class="mb-3">
      {{ form.reporter_name.label(class="form-label") }}
      <span class="text-danger">*</span>
      {{ form.reporter_name(class="form-control" ~ (" is-invalid" if form.reporter_name.errors else ""),
                             placeholder="Your name") }}
      {% for error in form.reporter_name.errors %}
      <div class="invalid-feedback">{{ error }}</div>
      {% endfor %}
    </div>

    <div class="mb-3">
      {{ form.description.label(class="form-label") }}
      <span class="text-danger">*</span>
      {{ form.description(class="form-control" ~ (" is-invalid" if form.description.errors else ""),
                           rows="3", placeholder="Describe the problem...") }}
      {% for error in form.description.errors %}
      <div class="invalid-feedback">{{ error }}</div>
      {% endfor %}
    </div>

    <div class="mb-3">
      {{ form.severity.label(class="form-label") }}
      {{ form.severity(class="form-select") }}
    </div>

    <div class="mb-3 form-check">
      {{ form.has_safety_risk(class="form-check-input") }}
      {{ form.has_safety_risk.label(class="form-check-label") }}
    </div>

    <div class="mb-3 form-check">
      {{ form.is_consumable(class="form-check-input") }}
      {{ form.is_consumable.label(class="form-check-label") }}
    </div>

    <div class="mb-3">
      {{ form.reporter_email.label(class="form-label") }}
      {{ form.reporter_email(class="form-control" ~ (" is-invalid" if form.reporter_email.errors else ""),
                              placeholder="your@email.com") }}
      {% for error in form.reporter_email.errors %}
      <div class="invalid-feedback">{{ error }}</div>
      {% endfor %}
    </div>

    <div class="mb-3">
      {{ form.photo.label(class="form-label") }}
      {{ form.photo(class="form-control", accept="image/*,video/*", capture="environment") }}
    </div>

    <button type="submit" class="btn btn-primary btn-lg w-100 report-submit-btn">
      Submit Report
    </button>
  </form>
</div>
```

#### Template: `esb/templates/public/report_confirmation.html`

```jinja2
{% extends "base_public.html" %}

{% block title %}Report Submitted - {{ equipment.name }}{% endblock %}

{% block content %}
<div class="text-center py-4" style="max-width: 600px; margin: 0 auto;">
  <h1 class="text-success">Report Submitted</h1>
  <p class="fs-5">Thank you for reporting this issue with <strong>{{ equipment.name }}</strong>.</p>
  <p class="text-muted">Your report has been received and a technician will review it.</p>

  {% if equipment.area.slack_channel %}
  <div class="card mt-4">
    <div class="card-body">
      <h2 class="h5">Stay Updated</h2>
      <p>Follow progress on Slack:</p>
      <ul class="list-unstyled">
        <li class="mb-2">
          <strong>{{ equipment.area.slack_channel }}</strong> &mdash; {{ equipment.area.name }} channel
        </li>
        <li>
          <strong>#oops</strong> &mdash; All equipment issues
        </li>
      </ul>
    </div>
  </div>
  {% endif %}

  <div class="mt-4">
    <a href="{{ url_for('public.equipment_page', id=equipment.id) }}#report-form"
       class="btn btn-outline-primary btn-lg w-100 mb-2">
      Report Another Issue
    </a>
    <a href="{{ url_for('public.equipment_page', id=equipment.id) }}"
       class="btn btn-outline-secondary w-100">
      &larr; Back to {{ equipment.name }}
    </a>
  </div>
</div>
{% endblock %}
```

**Key decisions:**
- Shows Slack channel links only if `equipment.area.slack_channel` is populated
- "Report another issue" links back to equipment page with `#report-form` anchor
- "Back to status" links to the equipment page top
- Clean, mobile-friendly centered layout matching QR page hero pattern

### Reuse from Previous Stories (DO NOT recreate)

**From Story 4.3 (DO NOT modify these):**
- `GET /public/equipment/<int:id>` route -- EXISTS, only needs `form` added to context
- `equipment_page.html` -- EXISTS, add form section below Known Issues
- `GET /public/equipment/<int:id>/info` route -- EXISTS, no changes needed
- `equipment_info.html` -- EXISTS, no changes needed
- `GET /public/uploads/<path:filepath>` route -- EXISTS, no changes needed

**From Story 4.1:**
- `status_service.compute_equipment_status(equipment_id)` -- returns `{color, label, issue_description, severity}`
- `components/_status_indicator.html` -- `large` variant, pass `variant='large'` and `status` dict
- Status card CSS classes (`status-card-green`, `status-card-yellow`, `status-card-red`)

**From Story 2.2:**
- `equipment_service.get_equipment(id)` -- returns Equipment instance, raises `ValidationError` if not found

**From Story 2.3:**
- `upload_service.save_upload(file, parent_type, parent_id, uploaded_by)` -- saves file, returns Document
- `upload_service.get_documents(parent_type, parent_id)` -- lists documents

**From Story 3.1-3.2:**
- `repair_service.create_repair_record(...)` -- creates record with status "New", timeline entry, audit log, mutation log
- `repair_service.list_repair_records(equipment_id=id)` -- lists all records for equipment
- `CLOSED_STATUSES` -- `['Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']`

**From Story 3.3:**
- `RepairPhotoUploadForm` pattern in `esb/forms/repair_forms.py` -- follow for file upload field pattern

### `create_repair_record()` Exact Signature (from `esb/services/repair_service.py`)

```python
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
```

**For anonymous problem reports:**
- `equipment_id`: from URL path `id`
- `description`: `form.description.data`
- `created_by`: `form.reporter_name.data` (used as the "author" string for anonymous reports)
- `severity`: `form.severity.data` (defaults "Not Sure" from form)
- `reporter_name`: `form.reporter_name.data`
- `reporter_email`: `form.reporter_email.data or None`
- `assignee_id`: `None` (no assignment on public reports)
- `has_safety_risk`: `form.has_safety_risk.data`
- `is_consumable`: `form.is_consumable.data`
- `author_id`: `None` (anonymous, no user account)

### `save_upload()` Exact Signature (from `esb/services/upload_service.py`)

```python
def save_upload(
    file,
    parent_type: str,
    parent_id: int,
    uploaded_by: str,
    category: str | None = None,
) -> Document:
```

**For problem report photo:**
- `file`: `form.photo.data` (Werkzeug FileStorage)
- `parent_type`: `'repair_photo'`
- `parent_id`: `record.id` (the newly created repair record)
- `uploaded_by`: `form.reporter_name.data`
- `category`: `None` (not used for repair photos)

**Allowed photo extensions:** jpg, jpeg, png, gif, webp, mp4, mov, avi, webm
**Storage path:** `{UPLOAD_PATH}/repairs/{parent_id}/{uuid_filename}.{ext}`
**Max size:** `UPLOAD_MAX_SIZE_MB` (default 500MB)

### Notification Service

**IMPORTANT:** `esb/services/notification_service.py` **DOES NOT EXIST**. The Slack notification queue (Epic 5) and Slack App (Epic 6) have not been implemented yet. Do NOT attempt to send Slack notifications or queue notifications in this story.

The `repair_service.create_repair_record()` function already handles all side effects:
- Creates timeline entry (type: 'creation')
- Creates audit log entry
- Emits mutation log to STDOUT
- Commits database transaction

No additional notification logic is needed for Story 4.4.

### Project Structure Notes

**New files to create:**
- `esb/templates/public/report_confirmation.html` -- Confirmation page template

**Files to modify:**
- `esb/forms/repair_forms.py` -- Add `ProblemReportForm` class
- `esb/views/public.py` -- Add `report_problem` POST route, `report_confirmation` GET route; modify `equipment_page` to pass form
- `esb/templates/public/equipment_page.html` -- Add problem report form section
- `esb/static/css/app.css` -- Add submit button and form styling (~5-10 lines)
- `tests/test_views/test_public_views.py` -- Add problem report and confirmation tests

**Files NOT to modify:**
- `esb/services/repair_service.py` -- reuse `create_repair_record()` as-is
- `esb/services/upload_service.py` -- reuse `save_upload()` as-is
- `esb/services/status_service.py` -- reuse `compute_equipment_status()` as-is
- `esb/services/equipment_service.py` -- reuse `get_equipment()` as-is
- `esb/models/` -- no new models, no migrations (all fields already exist)
- `esb/templates/base_public.html` -- use as-is
- `esb/templates/components/_status_indicator.html` -- use large variant as-is
- `esb/templates/public/equipment_info.html` -- no changes needed

### Previous Story Intelligence (from Story 4.3)

**Patterns to follow:**
- `get_equipment()` raises `ValidationError` (NOT `EquipmentNotFound`) -- handle accordingly
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`) -- form submissions work in tests without CSRF token
- `db.session.get(Model, id)` for PK lookups
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions to avoid circular imports
- Test factories: `make_area`, `make_equipment`, `make_repair_record` in `tests/conftest.py`
- 692 tests currently passing, 0 lint errors

**Code review lessons from 4.1, 4.2, 4.3:**
- Don't duplicate logic -- reuse existing service functions
- Include tests for ARIA attributes and responsive layout classes
- Include visually-hidden `<h1>` for WCAG if needed
- Use proper heading elements, not `<span>`
- Include `novalidate` on form to prevent browser native validation (server-side is authoritative)

### Upload File Handling for Problem Reports

The existing `/public/uploads/<path:filepath>` route (created in Story 4.3) serves files from `UPLOAD_PATH`. Repair photos uploaded via problem reports will be stored at `{UPLOAD_PATH}/repairs/{record_id}/{filename}` and served via this existing route.

Photo upload is OPTIONAL. The view must check that `form.photo.data` has an actual file before attempting to save:

```python
if form.photo.data and hasattr(form.photo.data, 'filename') and form.photo.data.filename:
    # Only process if user actually selected a file
    upload_service.save_upload(...)
```

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

- Test file: `tests/test_views/test_public_views.py` (append to existing file)
- No new test files needed (form tests covered via view tests)
- Use existing fixtures: `client` (unauthenticated), `make_area`, `make_equipment`, `make_repair_record`
- Problem report pages are unauthenticated -- use `client` NOT `staff_client` or `tech_client`
- For POST tests: use `client.post(url, data={...}, content_type='multipart/form-data')` for photo uploads
- For file upload tests: create `FileStorage` objects from `io.BytesIO`
- Check form renders with required field indicators
- Check `enctype="multipart/form-data"` on form tag
- Check inline validation errors appear on missing required fields
- Check repair record is created in database after valid submission
- Check photo is saved to correct path after submission with photo
- Check redirect to confirmation page on success
- Check confirmation page has Slack channel info and "Report another" link

**Test data patterns:**

```python
# Valid form submission
data = {
    'reporter_name': 'Sarah Member',
    'description': 'Motor making grinding noise',
    'severity': 'Down',
    'has_safety_risk': True,
    'is_consumable': False,
    'reporter_email': 'sarah@example.com',
}
response = client.post(f'/public/equipment/{equip.id}/report', data=data)
assert response.status_code == 302  # Redirect to confirmation

# File upload test
from io import BytesIO
from werkzeug.datastructures import FileStorage
data['photo'] = (BytesIO(b'fake image content'), 'problem.jpg')
response = client.post(f'/public/equipment/{equip.id}/report', data=data,
                       content_type='multipart/form-data')
```

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with Jinja2 templates
- **Flask-WTF** for form handling and CSRF
- **Bootstrap 5** bundled locally (no CDN)
- **Vanilla JS only** -- no npm, no build step
- **SQLAlchemy** via Flask-SQLAlchemy for all queries
- **pytest** for tests
- No new dependencies needed (qrcode already added in Story 4.3; Flask-WTF already in project)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 Story 4.4]
- [Source: _bmad-output/planning-artifacts/prd.md#FR22-FR26 Problem Reporting]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#File Upload Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Form Validation Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#QR Code Equipment Page Template]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Progressive Disclosure Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Minimal Form Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1 Member Checks Status & Reports Problem]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- [Source: _bmad-output/implementation-artifacts/4-3-qr-code-equipment-pages-documentation.md#Dev Notes]
- [Source: esb/services/repair_service.py#create_repair_record]
- [Source: esb/services/upload_service.py#save_upload]
- [Source: esb/views/public.py#equipment_page]
- [Source: esb/forms/repair_forms.py]
- [Source: esb/models/repair_record.py#RepairRecord]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- CSRF hidden_tag renders empty in test config (WTF_CSRF_ENABLED=False); adjusted test to verify form action/method instead
- RepairTimelineEntry model is in `esb/models/repair_timeline_entry.py` (not `repair_timeline.py`)

### Completion Notes List

- Task 1: Added `ProblemReportForm` class to `esb/forms/repair_forms.py` with required fields (reporter_name, description), optional fields (severity, has_safety_risk, is_consumable, reporter_email, photo), severity defaults "Not Sure"
- Task 2: Added problem report form section to `equipment_page.html` below Known Issues, with ARIA labels, inline validation errors, multipart enctype, novalidate
- Task 3: Added `report_problem` POST route -- validates form, creates repair record via service, handles optional photo upload, re-renders on validation failure with full page context
- Task 4: Added `report_confirmation` GET route -- loads equipment (404 if archived/missing), renders confirmation template with record_id
- Task 5: Created `report_confirmation.html` -- success message, Slack channel links (conditional on area.slack_channel), "Report Another Issue" and "Back to" links
- Task 6: Updated `equipment_page` GET route to instantiate and pass empty `ProblemReportForm` to template
- Task 7: Added CSS for `.report-submit-btn` min-height 48px and file input touch-friendly sizing
- Tasks 8-10: Added 26 tests covering form display (7), submission (13), confirmation (6) -- all AC verified

### Change Log

- 2026-02-16: Implemented Story 4.4 - Problem Reporting via QR Code Page (all 10 tasks, 26 new tests, 718 total passing)

### File List

- esb/forms/repair_forms.py (modified -- added ProblemReportForm class)
- esb/views/public.py (modified -- added report_problem POST, report_confirmation GET, updated equipment_page to pass form)
- esb/templates/public/equipment_page.html (modified -- added problem report form section)
- esb/templates/public/report_confirmation.html (new -- confirmation page template)
- esb/static/css/app.css (modified -- added report form styling)
- tests/test_views/test_public_views.py (modified -- added 26 tests in 3 test classes)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified -- updated story status)
- _bmad-output/implementation-artifacts/4-4-problem-reporting-via-qr-code-page.md (modified -- updated status, tasks, dev record)
