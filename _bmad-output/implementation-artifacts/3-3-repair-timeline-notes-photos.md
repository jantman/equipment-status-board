# Story 3.3: Repair Timeline, Notes & Photos

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Technician or Staff member,
I want to add diagnostic notes and photos to repair records,
so that the next person has full context and no effort is duplicated.

## Acceptance Criteria

1. **Inline note addition on detail page:** Given I am viewing a repair record detail page, when I type a note in the text area and click Save, then a note entry is added to the timeline with my username and the current timestamp.

2. **Photo upload with timeline entry:** Given I am viewing a repair record detail page, when I upload a diagnostic photo or video, then the file is saved to `uploads/repairs/{id}/` and a `photo` entry is added to the timeline with a thumbnail.

3. **Chronological timeline display:** Given the repair record timeline, when I view the timeline, then entries are displayed chronologically (newest first) with entry type icons, author name, timestamp, and content.

4. **Status change display:** Given a timeline entry of type `status_change`, when I view it, then it displays "Status changed from [Old] to [New]" with status badges.

5. **Assignee change display:** Given a timeline entry of type `assignee_change`, when I view it, then it displays "Assigned to [name]" or "Unassigned".

6. **Photo thumbnail expansion:** Given a timeline photo entry, when I click the thumbnail, then the photo expands to full size.

7. **Mobile relative timestamps:** Given I am viewing the timeline on mobile, when timestamps are displayed, then they use relative format ("2 hours ago") instead of absolute format.

8. **Append-only timeline:** Given the timeline, when any entry is added, then the timeline is append-only -- no entries can be edited or deleted.

## Tasks / Subtasks

- [x] Task 1: Add RepairNoteForm and RepairPhotoUploadForm to repair_forms.py (AC: #1, #2)
  - [x] 1.1 Add `RepairNoteForm` with note TextAreaField (DataRequired, max 5000) and submit button
  - [x] 1.2 Add `RepairPhotoUploadForm` with FileField (FileRequired, FileAllowed for image/video) and submit button

- [x] Task 2: Add service functions for notes and photos (AC: #1, #2, #8)
  - [x] 2.1 Add `add_repair_note()` to `esb/services/repair_service.py` -- creates `note` timeline entry, audit log entry, and mutation log
  - [x] 2.2 Add `add_repair_photo()` to `esb/services/repair_service.py` -- calls `upload_service.save_upload()` with `repair_photo` parent_type, creates `photo` timeline entry with document_id reference in content, audit log entry, and mutation log

- [x] Task 3: Add view routes for notes, photos, and file serving (AC: #1, #2, #6)
  - [x] 3.1 Add `POST /repairs/<int:id>/notes` route to handle note form submission
  - [x] 3.2 Add `POST /repairs/<int:id>/photos` route to handle photo upload form submission
  - [x] 3.3 Add `GET /repairs/<int:id>/files/<path:filename>` route to serve uploaded repair photos
  - [x] 3.4 Update `detail()` view to pass note form, photo form, and repair photos to template

- [x] Task 4: Enhance timeline component template (AC: #3, #4, #5, #6, #7)
  - [x] 4.1 Add entry type icons (Bootstrap Icons or Unicode) for each timeline entry type
  - [x] 4.2 Add status badges (colored Bootstrap badges) for status_change old/new values
  - [x] 4.3 Add photo thumbnail display for `photo` entries with click-to-expand (Bootstrap modal or linked full-size view)
  - [x] 4.4 Add responsive timestamps: absolute on desktop (`Feb 15, 2026 2:34 PM`), relative on mobile (`2 hours ago`) using `data-` attributes and CSS media queries or the existing `relative_time` filter with responsive display

- [x] Task 5: Update repair detail page template (AC: #1, #2, #3, #6, #8)
  - [x] 5.1 Add inline note form above the timeline (text area + "Add Note" button)
  - [x] 5.2 Add photo upload form above the timeline (file input + "Upload Photo" button)
  - [x] 5.3 Pass `note_form`, `photo_form`, and `photos` to the template context
  - [x] 5.4 Ensure forms use `enctype="multipart/form-data"` for photo upload
  - [x] 5.5 Ensure timeline remains append-only in the UI (no edit/delete controls on entries)

- [x] Task 6: Write service tests (AC: #1, #2, #8)
  - [x] 6.1 Test `add_repair_note()` creates note timeline entry with content, author_name, author_id
  - [x] 6.2 Test `add_repair_note()` creates audit log entry
  - [x] 6.3 Test `add_repair_note()` emits mutation log
  - [x] 6.4 Test `add_repair_note()` with empty/whitespace note raises ValidationError
  - [x] 6.5 Test `add_repair_note()` with non-existent repair record raises ValidationError
  - [x] 6.6 Test `add_repair_photo()` saves file via upload_service and creates photo timeline entry
  - [x] 6.7 Test `add_repair_photo()` creates audit log entry
  - [x] 6.8 Test `add_repair_photo()` emits mutation log
  - [x] 6.9 Test `add_repair_photo()` with non-existent repair record raises ValidationError

- [x] Task 7: Write view tests (AC: #1, #2, #3, #6)
  - [x] 7.1 Test detail page shows note form and photo upload form (GET 200)
  - [x] 7.2 Test detail page shows timeline entries with all entry types
  - [x] 7.3 Test note POST: staff submits note successfully (302 redirect to detail)
  - [x] 7.4 Test note POST: technician submits note successfully
  - [x] 7.5 Test note POST: unauthenticated redirects to login
  - [x] 7.6 Test note POST: non-existent record returns 404
  - [x] 7.7 Test photo POST: staff uploads photo successfully (302 redirect to detail)
  - [x] 7.8 Test photo POST: technician uploads photo successfully
  - [x] 7.9 Test photo POST: unauthenticated redirects to login
  - [x] 7.10 Test photo POST: non-existent record returns 404
  - [x] 7.11 Test file serving route returns uploaded file
  - [x] 7.12 Test file serving route for non-existent file returns 404

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- Note and photo addition logic in `repair_service.py` -- views are thin controllers
- Photo file I/O delegated to existing `upload_service.save_upload()` -- repair_service orchestrates
- Dependency flow: `views -> repair_service -> upload_service -> models` (NEVER reverse)
- Service handles `db.session.commit()` -- view never commits directly

**RBAC Rules for This Story:**
- Add note / upload photo / view detail: `@role_required('technician')` -- Technicians and Staff can add (Staff > Technician in hierarchy)
- File serving route: `@role_required('technician')` -- only authenticated tech/staff can view repair photos
- All routes require authentication -- no public access to repair timelines

**Append-Only Timeline (AC #8):**
- Timeline entries are NEVER edited or deleted through the UI
- No edit/delete buttons on timeline entries
- The `RepairTimelineEntry` model has no update mechanism by design
- This is enforced at the UI level (no controls) and by convention in the service layer

### File Placement

| File | Action | Purpose |
|------|--------|---------|
| `esb/forms/repair_forms.py` | MODIFY | Add `RepairNoteForm` and `RepairPhotoUploadForm` classes |
| `esb/services/repair_service.py` | MODIFY | Add `add_repair_note()` and `add_repair_photo()` functions |
| `esb/views/repairs.py` | MODIFY | Add `add_note()`, `upload_photo()`, `serve_photo()` routes; update `detail()` |
| `esb/templates/repairs/detail.html` | MODIFY | Add note form, photo upload form, enhanced timeline |
| `esb/templates/components/_timeline_entry.html` | MODIFY | Add icons, status badges, photo thumbnails, responsive timestamps |
| `tests/test_services/test_repair_service.py` | MODIFY | Add note and photo service tests |
| `tests/test_views/test_repair_views.py` | MODIFY | Add note, photo, and file serving view tests |

**No new models or migrations required.** The `RepairTimelineEntry` model already supports `photo` entry type. The `Document` model already supports `repair_photo` parent_type. The `upload_service` already handles `repair_photo` file storage.

### Service Function Contracts

**`add_repair_note()` in `esb/services/repair_service.py`:**

```python
def add_repair_note(
    repair_record_id: int,
    note: str,
    author_name: str,
    author_id: int | None = None,
) -> RepairTimelineEntry:
    """Add a note to a repair record's timeline.

    Args:
        repair_record_id: ID of the repair record.
        note: Text content of the note.
        author_name: Username of the person adding the note.
        author_id: User ID of the author (None for system notes).

    Returns:
        The created RepairTimelineEntry.

    Raises:
        ValidationError: if repair record not found or note is empty.
    """
```

**Implementation approach:**

```python
def add_repair_note(
    repair_record_id: int,
    note: str,
    author_name: str,
    author_id: int | None = None,
) -> RepairTimelineEntry:
    if not note or not note.strip():
        raise ValidationError('Note text is required')

    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    entry = RepairTimelineEntry(
        repair_record_id=record.id,
        entry_type='note',
        author_id=author_id,
        author_name=author_name,
        content=note.strip(),
    )
    db.session.add(entry)

    db.session.add(AuditLog(
        entity_type='repair_record',
        entity_id=record.id,
        action='note_added',
        user_id=author_id,
        changes={'note': note.strip()},
    ))

    db.session.commit()

    log_mutation('repair_record.note_added', author_name, {
        'id': record.id,
        'note': note.strip(),
    })

    return entry
```

**`add_repair_photo()` in `esb/services/repair_service.py`:**

```python
def add_repair_photo(
    repair_record_id: int,
    file,
    author_name: str,
    author_id: int | None = None,
) -> tuple[Document, RepairTimelineEntry]:
    """Upload a photo to a repair record and add a timeline entry.

    Args:
        repair_record_id: ID of the repair record.
        file: Werkzeug FileStorage object from the form.
        author_name: Username of the person uploading.
        author_id: User ID of the uploader.

    Returns:
        Tuple of (Document, RepairTimelineEntry).

    Raises:
        ValidationError: if repair record not found or file invalid.
    """
```

**Implementation approach:**

```python
from esb.services import upload_service

def add_repair_photo(
    repair_record_id: int,
    file,
    author_name: str,
    author_id: int | None = None,
) -> tuple[Document, RepairTimelineEntry]:
    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    # Delegate file handling to upload_service (which commits the Document)
    doc = upload_service.save_upload(
        file=file,
        parent_type='repair_photo',
        parent_id=record.id,
        uploaded_by=author_name,
    )

    # Create timeline entry referencing the document
    entry = RepairTimelineEntry(
        repair_record_id=record.id,
        entry_type='photo',
        author_id=author_id,
        author_name=author_name,
        content=str(doc.id),  # Store document ID as content for linking
    )
    db.session.add(entry)

    db.session.add(AuditLog(
        entity_type='repair_record',
        entity_id=record.id,
        action='photo_added',
        user_id=author_id,
        changes={
            'document_id': doc.id,
            'filename': doc.original_filename,
        },
    ))

    db.session.commit()

    log_mutation('repair_record.photo_added', author_name, {
        'id': record.id,
        'document_id': doc.id,
        'filename': doc.original_filename,
    })

    return doc, entry
```

**Critical implementation notes:**
1. `upload_service.save_upload()` already commits the Document record internally. The timeline entry and audit log are committed in a separate commit. This is acceptable because the upload is the critical operation; the timeline/audit entries enhance the record but do not need to be atomic with the upload.
2. The `content` field on the photo timeline entry stores the `Document.id` as a string. The template uses this to look up the document for thumbnail rendering.
3. `upload_service` validates file type, file size, and generates safe filenames. The repair_service does NOT re-validate these.
4. The `repair_photo` parent_type in `upload_service._PARENT_TYPE_CONFIG` stores files under `repairs/{parent_id}/` with allowed extensions: `jpg, jpeg, png, gif, webp, mp4, mov, avi, webm`.

### Form Design

**`RepairNoteForm` in `esb/forms/repair_forms.py`:**

```python
class RepairNoteForm(FlaskForm):
    """Form for adding a note to a repair record."""

    note = TextAreaField('Note', validators=[DataRequired(), Length(max=5000)])
    submit = SubmitField('Add Note')
```

**`RepairPhotoUploadForm` in `esb/forms/repair_forms.py`:**

```python
from flask_wtf.file import FileAllowed, FileField, FileRequired

class RepairPhotoUploadForm(FlaskForm):
    """Form for uploading a diagnostic photo/video to a repair record."""

    file = FileField('Photo/Video', validators=[
        FileRequired('Please select a file to upload.'),
        FileAllowed(
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'],
            'Only image and video files are allowed.',
        ),
    ])
    submit = SubmitField('Upload Photo')
```

### View Route Patterns

**Note submission route:**

```python
@repairs_bp.route('/<int:id>/notes', methods=['POST'])
@role_required('technician')
def add_note(id):
    """Add a note to a repair record."""
    try:
        repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairNoteForm()
    if form.validate_on_submit():
        try:
            repair_service.add_repair_note(
                repair_record_id=id,
                note=form.note.data,
                author_name=current_user.username,
                author_id=current_user.id,
            )
            flash('Note added.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    return redirect(url_for('repairs.detail', id=id))
```

**Photo upload route:**

```python
@repairs_bp.route('/<int:id>/photos', methods=['POST'])
@role_required('technician')
def upload_photo(id):
    """Upload a diagnostic photo to a repair record."""
    try:
        repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairPhotoUploadForm()
    if form.validate_on_submit():
        try:
            repair_service.add_repair_photo(
                repair_record_id=id,
                file=form.file.data,
                author_name=current_user.username,
                author_id=current_user.id,
            )
            flash('Photo uploaded.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    return redirect(url_for('repairs.detail', id=id))
```

**File serving route (follow equipment pattern from `esb/views/equipment.py:serve_photo`):**

```python
@repairs_bp.route('/<int:id>/files/<path:filename>')
@role_required('technician')
def serve_photo(id, filename):
    """Serve an uploaded repair photo file."""
    upload_path = current_app.config['UPLOAD_PATH']
    directory = os.path.join(upload_path, 'repairs', str(id))
    return send_from_directory(directory, filename)
```

**Updated detail view:**

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

    note_form = RepairNoteForm()
    photo_form = RepairPhotoUploadForm()
    photos = upload_service.get_documents('repair_photo', id)

    return render_template(
        'repairs/detail.html',
        record=record,
        timeline=timeline,
        note_form=note_form,
        photo_form=photo_form,
        photos=photos,
    )
```

**Key additions to imports at top of `esb/views/repairs.py`:**
- `import os`
- `from flask import current_app, send_from_directory`
- `from esb.forms.repair_forms import RepairNoteForm, RepairPhotoUploadForm`
- `from esb.services import upload_service`

### Template Design

**Enhanced `_timeline_entry.html` component:**

The current template is basic. Enhance to include:
1. **Entry type icons** (Unicode characters, no icon library needed):
   - creation: &#x2795; (heavy plus) or simply bold text
   - note: &#x1F4DD; (memo) -- use a simpler approach: just the text with icon-like prefix
   - status_change: &#x1F504; (arrows) -- better: use Bootstrap badge styling
   - assignee_change: &#x1F464; (person)
   - eta_update: &#x1F4C5; (calendar)
   - photo: &#x1F4F7; (camera)

   **IMPORTANT:** Do NOT use emoji characters in templates. Instead, use Bootstrap utility classes for visual distinction. Use `<span class="badge bg-*">` for entry type labels. Keep it simple and accessible.

2. **Status badges for status_change entries:** Use colored Bootstrap badges for old and new status values:
   ```html
   Status changed from <span class="badge bg-secondary">{{ entry.old_value }}</span> to <span class="badge bg-info text-dark">{{ entry.new_value }}</span>
   ```

3. **Photo thumbnails:** For `photo` entries, render an `<img>` thumbnail linking to the full-size photo. The `content` field stores the document ID. The template needs to look up the document's stored_filename to construct the URL.

   **Approach:** Pass a dict of `{doc_id: Document}` to the template for photo timeline entries. The view will pre-load all repair photos and pass them as `photos_by_id`.

4. **Responsive timestamps:** Show both absolute and relative, hide one based on viewport:
   ```html
   <span class="d-none d-md-inline">{{ entry.created_at|format_datetime }}</span>
   <span class="d-md-none">{{ entry.created_at|relative_time }}</span>
   ```

**Updated `repairs/detail.html`:**

Add above the timeline:
```html
{# --- Add Note Form --- #}
<div class="card mb-3">
    <div class="card-body">
        <form method="post" action="{{ url_for('repairs.add_note', id=record.id) }}">
            {{ note_form.hidden_tag() }}
            <div class="mb-2">
                <label for="note" class="form-label">Add a Note</label>
                {{ note_form.note(class="form-control" ~ (" is-invalid" if note_form.note.errors else ""), rows="3", placeholder="Type your diagnostic notes here...") }}
                {% for error in note_form.note.errors %}
                <div class="invalid-feedback">{{ error }}</div>
                {% endfor %}
            </div>
            {{ note_form.submit(class="btn btn-primary") }}
        </form>
    </div>
</div>

{# --- Upload Photo Form --- #}
<div class="card mb-3">
    <div class="card-body">
        <form method="post" action="{{ url_for('repairs.upload_photo', id=record.id) }}" enctype="multipart/form-data">
            {{ photo_form.hidden_tag() }}
            <div class="row g-2 align-items-end">
                <div class="col">
                    <label for="{{ photo_form.file.id }}" class="form-label">Upload Diagnostic Photo</label>
                    {{ photo_form.file(class="form-control") }}
                </div>
                <div class="col-auto">
                    {{ photo_form.submit(class="btn btn-primary") }}
                </div>
            </div>
        </form>
    </div>
</div>
```

### Database Notes

**No new migration required.** All models and columns already exist:
- `RepairTimelineEntry` with `entry_type='photo'` (already in `TIMELINE_ENTRY_TYPES`)
- `Document` model with `parent_type='repair_photo'` support
- `upload_service._PARENT_TYPE_CONFIG` has `'repair_photo'` config

### Testing Requirements

**Add tests to existing files -- do NOT create new test files.**

**Service tests (`tests/test_services/test_repair_service.py` -- ADD to existing):**

```python
class TestAddRepairNote:
    """Tests for add_repair_note()."""

    def test_creates_note_timeline_entry(self, app, make_repair_record, staff_user):
        record = make_repair_record()
        entry = repair_service.add_repair_note(
            record.id, 'Motor bearings look worn', 'staffuser', author_id=staff_user.id,
        )
        assert entry.entry_type == 'note'
        assert entry.content == 'Motor bearings look worn'
        assert entry.author_name == 'staffuser'
        assert entry.author_id == staff_user.id
        assert entry.repair_record_id == record.id

    # ... etc
```

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area`, `make_equipment`, `make_repair_record`

**Service test cases (add to `tests/test_services/test_repair_service.py`):**
1. `test_add_note_creates_timeline_entry` -- verify note entry with content, author
2. `test_add_note_creates_audit_log` -- verify AuditLog with action='note_added'
3. `test_add_note_emits_mutation_log` -- verify via `capture` fixture
4. `test_add_note_empty_raises` -- empty string raises ValidationError
5. `test_add_note_whitespace_raises` -- whitespace-only raises ValidationError
6. `test_add_note_not_found_raises` -- non-existent record raises ValidationError
7. `test_add_note_strips_whitespace` -- leading/trailing whitespace stripped
8. `test_add_photo_creates_document_and_timeline` -- verify Document + photo timeline entry
9. `test_add_photo_creates_audit_log` -- verify AuditLog with action='photo_added'
10. `test_add_photo_emits_mutation_log` -- verify via `capture` fixture
11. `test_add_photo_not_found_raises` -- non-existent record raises ValidationError

**View test cases (add to `tests/test_views/test_repair_views.py`):**
1. `test_detail_shows_note_form` -- GET detail page contains note form elements
2. `test_detail_shows_photo_upload_form` -- GET detail page contains file upload form
3. `test_detail_shows_timeline_entries` -- GET detail page renders timeline with multiple entry types
4. `test_add_note_staff_success` -- POST note returns 302 redirect to detail
5. `test_add_note_tech_success` -- POST note returns 302 redirect to detail
6. `test_add_note_unauthenticated_redirects` -- POST returns 302 to login
7. `test_add_note_not_found` -- POST to non-existent record returns 404
8. `test_upload_photo_staff_success` -- POST with file returns 302 redirect to detail
9. `test_upload_photo_tech_success` -- POST with file returns 302 redirect to detail
10. `test_upload_photo_unauthenticated_redirects` -- POST returns 302 to login
11. `test_upload_photo_not_found` -- POST to non-existent record returns 404
12. `test_serve_photo_returns_file` -- GET file serving route returns the file
13. `test_serve_photo_not_found` -- GET non-existent file returns 404

**Critical testing notes (from Story 3.1/3.2 learnings):**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. `db.session.get(Model, id)` for PK lookups in assertions
5. Parse mutation log entries: `json.loads(r.message)` where `r` is from `capture.records`
6. `ruff target-version = "py313"` (NOT py314)
7. For photo upload tests, use `io.BytesIO` to create fake file data:
   ```python
   from io import BytesIO
   data = {'file': (BytesIO(b'fake image content'), 'test.jpg')}
   response = staff_client.post(f'/repairs/{record.id}/photos', data=data, content_type='multipart/form-data')
   ```
8. For file serving tests, need an actual file on disk -- create via `upload_service.save_upload()` in test setup or mock the filesystem
9. Test config uses `sqlite:///:memory:` -- UPLOAD_PATH needs to be a temp dir for photo tests. Use `tmp_path` fixture.

### Project Structure Notes

- All changes fit within existing file structure -- no new directories needed
- No new files -- all modifications to existing files
- No new models, no new migrations, no new dependencies
- Template component `_timeline_entry.html` is shared -- changes affect the equipment detail page too (but it doesn't use timeline entries, so no impact)

### Previous Story Intelligence

**Patterns established in Story 3.1 and 3.2 (MUST follow):**
- `repair_service.py`: Function signature pattern -- primitive params, return model instances, raise `ValidationError`
- `views/repairs.py`: Route pattern -- `@role_required('technician')`, form handling, `flash()` on success/error, PRG redirect
- `forms/repair_forms.py`: Form pattern -- `FlaskForm`, validators
- `templates/repairs/`: Template pattern -- extends `base.html`, breadcrumbs, Bootstrap classes
- `tests/`: Test pattern -- class-based grouping, fixture usage, `capture` for mutation log

**Upload patterns established in Story 2.3 (MUST follow):**
- `upload_service.save_upload()` for all file uploads -- never handle file I/O in views
- `upload_service.get_documents()` for listing documents by parent_type/parent_id
- Photo upload form uses `enctype="multipart/form-data"`
- File serving via `send_from_directory()` with upload path from config
- `PhotoUploadForm` uses `FileRequired` + `FileAllowed` validators from `flask_wtf.file`

**Key learnings from Story 3.2 code review:**
1. Import services locally inside view functions to avoid circular imports where needed
2. The `repairs.index` route currently redirects to `repairs.create` -- do NOT change it (becomes repair queue in Story 3.4)
3. Use existing fixtures from `tests/conftest.py` -- `make_repair_record`, `staff_user`, `tech_user`, etc.

**Existing code the dev agent MUST use (NOT re-implement):**
- `esb/services/upload_service.py` -- `save_upload()`, `get_documents()` for file operations
- `esb/services/repair_service.py` -- `get_repair_record()` for record lookup
- `esb/utils/logging.py` -- `log_mutation()` for mutation logging
- `esb/utils/exceptions.py` -- `ValidationError` for all validation errors
- `esb/utils/decorators.py` -- `@role_required('technician')` for RBAC
- `esb/utils/filters.py` -- `relative_time`, `format_datetime` filters already registered
- `esb/extensions.py` -- `db` for database access
- `esb/models/repair_record.py` -- `RepairRecord`
- `esb/models/repair_timeline_entry.py` -- `RepairTimelineEntry`, `TIMELINE_ENTRY_TYPES`
- `esb/models/audit_log.py` -- `AuditLog`
- `esb/models/document.py` -- `Document`

### Git Intelligence

**Recent commits (3-commit cadence per story):**
- `1c9e0da` Fix code review issues for Story 3.2 repair record workflow & updates
- `fb132d0` Implement Story 3.2: Repair Record Workflow & Updates
- `d510102` Create Story 3.2: Repair Record Workflow & Updates context for dev agent

**Files most recently modified relevant to this story:**
- `esb/services/repair_service.py` (Story 3.2 -- add `add_repair_note()`, `add_repair_photo()` here)
- `esb/views/repairs.py` (Story 3.2 -- add note, photo, file serving routes here)
- `esb/forms/repair_forms.py` (Story 3.2 -- add `RepairNoteForm`, `RepairPhotoUploadForm` here)
- `esb/templates/repairs/detail.html` (Story 3.2 -- add note/photo forms and enhanced timeline)
- `esb/templates/components/_timeline_entry.html` (Story 3.1 -- enhance with icons, badges, thumbnails)
- `tests/test_services/test_repair_service.py` (Story 3.2 -- add note/photo tests here)
- `tests/test_views/test_repair_views.py` (Story 3.2 -- add note/photo/serving view tests here)

**Current test count:** 537 tests passing. Expect ~20-25 new tests.

### Library/Framework Requirements

| Package | Version | Notes |
|---------|---------|-------|
| Flask | 3.1.x | Already installed |
| Flask-SQLAlchemy | 3.1.x | Already installed |
| Flask-WTF / WTForms | 1.2.x | Already installed -- uses `FileField`, `FileRequired`, `FileAllowed` |
| Flask-Login | 0.6.3 | Already installed |
| Werkzeug | Latest | Already installed -- `send_from_directory()` for file serving |
| Bootstrap | 5.3.8 | Bundled locally in `esb/static/` |

**No new dependencies required for this story.**

### Scope Boundaries

**IN SCOPE for Story 3.3:**
- Add diagnostic notes to repair records (inline on detail page)
- Upload diagnostic photos/videos to repair records (inline on detail page)
- Enhanced timeline display with icons, status badges, photo thumbnails
- Responsive timestamps (relative on mobile, absolute on desktop)
- Photo click-to-expand (full size view)
- File serving route for repair photos
- Append-only enforcement (no edit/delete on timeline entries)

**OUT OF SCOPE (handled in later stories):**
- Repair queue page (Story 3.4)
- Kanban board (Story 3.5)
- Public access to repair records or photos (Epic 4)
- Photo upload from QR code problem report form (Story 4.4)
- Notification queuing on note/photo additions (Story 5.1 -- not a trigger event per current config)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3, Story 3.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern -- repair_service.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#File Upload Storage -- uploads/repairs/{id}/]
- [Source: _bmad-output/planning-artifacts/architecture.md#View Function Pattern -- parse input -> call service -> render]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture -- RepairTimelineEntry, Document]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Repair Timeline Custom Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Append-Only Timeline Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 2: Technician Works the Repair Queue]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Strategy -- mobile timestamps relative]
- [Source: _bmad-output/planning-artifacts/prd.md#FR15 (append notes), FR16 (upload photos/videos), FR20 (audit trail)]
- [Source: esb/services/repair_service.py -- Existing create/update patterns to follow]
- [Source: esb/services/upload_service.py -- save_upload() for repair_photo parent_type]
- [Source: esb/views/equipment.py -- Upload and file serving route patterns]
- [Source: esb/forms/equipment_forms.py -- PhotoUploadForm pattern to follow]
- [Source: esb/templates/equipment/detail.html -- Photo display and upload pattern]
- [Source: esb/templates/components/_timeline_entry.html -- Current timeline component to enhance]
- [Source: esb/utils/filters.py -- relative_time and format_datetime filters]
- [Source: esb/models/repair_timeline_entry.py -- TIMELINE_ENTRY_TYPES includes 'photo']
- [Source: esb/models/document.py -- Document model for file metadata]
- [Source: _bmad-output/implementation-artifacts/3-2-repair-record-workflow-updates.md -- Previous story patterns and learnings]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

None required.

### Completion Notes List

- Task 1: Added `RepairNoteForm` (TextAreaField + DataRequired + Length max 5000) and `RepairPhotoUploadForm` (FileField + FileRequired + FileAllowed for image/video extensions) to `esb/forms/repair_forms.py`.
- Task 2: Added `add_repair_note()` and `add_repair_photo()` to `esb/services/repair_service.py`. Both follow existing service patterns: validate input, create timeline entry, create audit log, commit, emit mutation log. `add_repair_photo()` delegates file I/O to `upload_service.save_upload()`.
- Task 3: Added `add_note()`, `upload_photo()`, and `serve_photo()` routes to `esb/views/repairs.py`. Updated `detail()` to pass note form, photo form, photos list, and photos_by_id dict to template.
- Task 4: Enhanced `_timeline_entry.html` with Bootstrap badge labels for each entry type, status badges for status_change entries, photo thumbnail display with click-to-expand (links to full-size), and responsive timestamps (absolute on desktop via `format_datetime`, relative on mobile via `relative_time`).
- Task 5: Updated `repairs/detail.html` with inline note form and photo upload form (with `enctype="multipart/form-data"`) above the timeline. No edit/delete controls on timeline entries (append-only enforced).
- Task 6: Added 11 service tests covering `add_repair_note()` and `add_repair_photo()` -- timeline entry creation, audit log, mutation log, validation errors, whitespace stripping.
- Task 7: Added 13 view tests covering detail page forms, timeline rendering, note POST (staff/tech/unauth/404), photo POST (staff/tech/unauth/404), and file serving (success/404).
- Total: 561 tests passing (24 new), 0 lint errors.

### Change Log

- 2026-02-15: Implemented Story 3.3 -- repair timeline notes, photos, enhanced timeline display. 24 new tests added.

### File List

- esb/forms/repair_forms.py (MODIFIED) -- Added RepairNoteForm and RepairPhotoUploadForm
- esb/services/repair_service.py (MODIFIED) -- Added add_repair_note() and add_repair_photo()
- esb/views/repairs.py (MODIFIED) -- Added add_note, upload_photo, serve_photo routes; updated detail view
- esb/templates/repairs/detail.html (MODIFIED) -- Added note form, photo upload form above timeline
- esb/templates/components/_timeline_entry.html (MODIFIED) -- Added type badges, status badges, photo thumbnails, responsive timestamps
- tests/test_services/test_repair_service.py (MODIFIED) -- Added TestAddRepairNote (7 tests) and TestAddRepairPhoto (4 tests)
- tests/test_views/test_repair_views.py (MODIFIED) -- Added TestAddNote (7 tests), TestUploadPhoto (4 tests), TestServePhoto (2 tests)
