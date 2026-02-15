# Story 2.3: Equipment Documentation & Media

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to upload documents, photos, and add links to equipment records,
so that members and technicians can find manuals, reference materials, and visual documentation.

## Acceptance Criteria

1. **Document model:** Given the Document model exists with fields for `original_filename`, `stored_filename`, `content_type`, `size_bytes`, `category`, `parent_type`, `parent_id`, `uploaded_by`, and `created_at`, when Alembic migration is run, then the `documents` table is created in MariaDB.

2. **Upload service:** Given the `upload_service` module, when a file is uploaded, then it validates file size against `UPLOAD_MAX_SIZE_MB`, generates a safe filename, saves to the correct directory (`uploads/equipment/{id}/docs/` or `uploads/equipment/{id}/photos/`), and creates a Document record.

3. **Document upload with category:** Given I am on an equipment detail page, when I upload a document and select a category label (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other), then the document is saved to the filesystem and appears in the equipment's document list with its category label.

4. **Photo/video upload:** Given I am on an equipment detail page, when I upload a photo or video, then the file is saved to `uploads/equipment/{id}/photos/` and appears in the equipment's photo gallery.

5. **External links:** Given I am on an equipment detail page, when I add an external link with a title and URL, then the link is saved and appears in the equipment's links section.

6. **File size validation:** Given I upload a file that exceeds the configured size limit, when the upload is processed, then I see a validation error and the file is not saved.

7. **Mutation logging:** Given any documentation action (upload document, upload photo, add link, delete document, delete photo, delete link), when the action is performed, then a mutation log entry is written to STDOUT.

## Tasks / Subtasks

- [ ] Task 1: Create Document model and ExternalLink model with migration (AC: #1)
  - [ ] 1.1 Create `esb/models/document.py` with Document model
  - [ ] 1.2 Create `esb/models/external_link.py` with ExternalLink model
  - [ ] 1.3 Register both models in `esb/models/__init__.py`
  - [ ] 1.4 Generate and apply Alembic migration for both tables
  - [ ] 1.5 Write model unit tests

- [ ] Task 2: Create upload service (AC: #2, #6)
  - [ ] 2.1 Create `esb/services/upload_service.py` (NEW file)
  - [ ] 2.2 Implement `save_upload(file, category, parent_type, parent_id, uploaded_by)` -- validates size, generates safe filename, saves to disk, creates Document record
  - [ ] 2.3 Implement `delete_upload(document_id, deleted_by)` -- deletes file from disk and removes Document record
  - [ ] 2.4 Implement `get_documents(parent_type, parent_id)` -- returns documents for a parent entity
  - [ ] 2.5 Set `MAX_CONTENT_LENGTH` in Flask config for request-level size enforcement
  - [ ] 2.6 Write service unit tests

- [ ] Task 3: Add external link service functions (AC: #5, #7)
  - [ ] 3.1 Add link functions to `esb/services/equipment_service.py` (EXTEND existing file)
  - [ ] 3.2 Implement `add_equipment_link(equipment_id, title, url, created_by)`
  - [ ] 3.3 Implement `delete_equipment_link(link_id, deleted_by)`
  - [ ] 3.4 Implement `get_equipment_links(equipment_id)`
  - [ ] 3.5 Write service unit tests

- [ ] Task 4: Create upload and link forms (AC: #3, #4, #5)
  - [ ] 4.1 Add `DocumentUploadForm`, `PhotoUploadForm`, `ExternalLinkForm` to `esb/forms/equipment_forms.py` (EXTEND existing file)
  - [ ] 4.2 DocumentUploadForm: FileField with category SelectField
  - [ ] 4.3 PhotoUploadForm: FileField only
  - [ ] 4.4 ExternalLinkForm: title StringField + url URLField

- [ ] Task 5: Add equipment document/photo/link routes (AC: #3, #4, #5, #6, #7)
  - [ ] 5.1 Add upload/link routes to `esb/views/equipment.py` (EXTEND existing file)
  - [ ] 5.2 `POST /equipment/<int:id>/documents` -- document upload
  - [ ] 5.3 `POST /equipment/<int:id>/photos` -- photo upload
  - [ ] 5.4 `POST /equipment/<int:id>/links` -- add external link
  - [ ] 5.5 `POST /equipment/<int:id>/documents/<int:doc_id>/delete` -- delete document
  - [ ] 5.6 `POST /equipment/<int:id>/photos/<int:photo_id>/delete` -- delete photo
  - [ ] 5.7 `POST /equipment/<int:id>/links/<int:link_id>/delete` -- delete link
  - [ ] 5.8 `GET /uploads/equipment/<int:id>/docs/<filename>` -- serve document file (or use Flask's `send_from_directory`)
  - [ ] 5.9 `GET /uploads/equipment/<int:id>/photos/<filename>` -- serve photo file
  - [ ] 5.10 Write view integration tests

- [ ] Task 6: Update equipment detail template (AC: #3, #4, #5)
  - [ ] 6.1 Replace Documents placeholder section with document list + upload form
  - [ ] 6.2 Replace Photos placeholder section with photo gallery + upload form
  - [ ] 6.3 Replace Links placeholder section with link list + add link form
  - [ ] 6.4 Add delete buttons (Staff only) for documents, photos, and links
  - [ ] 6.5 Mobile responsive layout for all sections

- [ ] Task 7: RBAC and edge case testing (AC: #2, #3, #4, #5, #6, #7)
  - [ ] 7.1 Verify `@role_required('staff')` on upload/add/delete routes
  - [ ] 7.2 Verify file size rejection works correctly
  - [ ] 7.3 Verify file type validation (document extensions vs photo extensions)
  - [ ] 7.4 Verify deletion removes file from disk AND database record
  - [ ] 7.5 Verify mutation logging for all operations
  - [ ] 7.6 Verify 404 for non-existent equipment on upload routes

## Dev Notes

### Architecture Compliance

**Service Layer Pattern (MANDATORY):**
- All business logic in service modules -- views are thin controllers
- `upload_service.py` handles ALL file I/O -- views never touch the filesystem directly
- Service functions accept primitive types, return model instances, raise domain exceptions
- Service functions handle their own `db.session.commit()`
- Dependency flow: `views -> services -> models` (NEVER reverse)

**File System Boundary (from architecture doc):**
- ONLY `upload_service.py` writes to the filesystem for uploads
- Upload path is configurable via `UPLOAD_PATH` environment variable
- Directory structure: `uploads/equipment/{id}/docs/`, `uploads/equipment/{id}/photos/`
- The `uploads/repairs/{id}/` path will be used later in Epic 3 for repair photos

**File Placement (per architecture doc):**
| File | Purpose |
|------|---------|
| `esb/models/document.py` | Document SQLAlchemy model (NEW) |
| `esb/models/external_link.py` | ExternalLink model (NEW) |
| `esb/services/upload_service.py` | File upload validation, storage, metadata (NEW) |
| `esb/services/equipment_service.py` | Add link management functions (EXTEND) |
| `esb/forms/equipment_forms.py` | Add upload/link forms (EXTEND) |
| `esb/views/equipment.py` | Add upload/link/delete/serve routes (EXTEND) |
| `esb/models/__init__.py` | Add Document, ExternalLink imports (MODIFY) |
| `esb/templates/equipment/detail.html` | Replace placeholder sections (MODIFY) |

**RBAC Rules for Documentation & Media:**
- Upload/add/delete: `@role_required('staff')` -- only Staff can manage documentation
- View/download: `@login_required` -- both Staff AND Technicians can view
- Note: Technician edit permissions are NOT in this story (Story 2.4)
- Public access to documents is NOT in this story (Story 4.3 -- QR code equipment pages)

### Database Model Specifications

**Document Model (`esb/models/document.py`):**

```python
class Document(db.Model):
    """File metadata for uploaded documents and photos."""

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=True)  # Only for documents, NULL for photos
    parent_type = db.Column(db.String(50), nullable=False)  # 'equipment_doc', 'equipment_photo', 'repair_photo'
    parent_id = db.Column(db.Integer, nullable=False, index=True)
    uploaded_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    def __repr__(self):
        return f'<Document {self.original_filename!r}>'
```

**Key design decisions:**
- `parent_type` + `parent_id` = polymorphic association pattern (supports equipment docs, equipment photos, and future repair photos)
- `parent_type` values: `'equipment_doc'`, `'equipment_photo'`, `'repair_photo'` (future)
- `category` is nullable -- only populated for documents (`parent_type='equipment_doc'`), NULL for photos
- `stored_filename` is the UUID-based filename on disk (not the original user filename)
- NO foreign key constraint to equipment table -- polymorphic pattern uses parent_type+parent_id instead
- Composite index on `(parent_type, parent_id)` for efficient queries

**Category values (DOCUMENT_CATEGORIES constant):**
```python
DOCUMENT_CATEGORIES = [
    ('owners_manual', "Owner's Manual"),
    ('service_manual', 'Service Manual'),
    ('quick_start', 'Quick Start Guide'),
    ('training_video', 'Training Video'),
    ('manufacturer_page', 'Manufacturer Product Page'),
    ('manufacturer_support', 'Manufacturer Support'),
    ('other', 'Other'),
]
```

**ExternalLink Model (`esb/models/external_link.py`):**

```python
class ExternalLink(db.Model):
    """External link attached to an equipment record."""

    __tablename__ = 'external_links'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True)
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(2000), nullable=False)
    created_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))

    # Relationships
    equipment = db.relationship('Equipment', backref=db.backref('links', lazy='dynamic'))

    def __repr__(self):
        return f'<ExternalLink {self.title!r}>'
```

**Key decisions:**
- ExternalLink has a direct FK to `equipment.id` (not polymorphic -- links are equipment-only)
- `url` is `String(2000)` to handle long URLs
- `title` is required (max 200 chars)
- Relationship: `equipment.links` gives access to links from equipment instance

**Model registration in `esb/models/__init__.py`:**
```python
from esb.models.area import Area
from esb.models.document import Document
from esb.models.equipment import Equipment
from esb.models.external_link import ExternalLink
from esb.models.user import User

__all__ = ['Area', 'Document', 'Equipment', 'ExternalLink', 'User']
```

### Service Function Contracts

**Upload Service (`esb/services/upload_service.py` -- NEW file):**

```python
def save_upload(
    file: FileStorage,
    parent_type: str,
    parent_id: int,
    uploaded_by: str,
    category: str | None = None,
) -> Document:
    """Save an uploaded file to disk and create a Document record.

    Args:
        file: Werkzeug FileStorage object from the form
        parent_type: 'equipment_doc', 'equipment_photo', or 'repair_photo'
        parent_id: ID of the parent entity (equipment or repair record)
        uploaded_by: Username of the uploader
        category: Document category (required for equipment_doc, ignored for photos)

    Raises:
        ValidationError: if file is empty, exceeds size limit, or has invalid extension

    Returns:
        The created Document instance
    """

def delete_upload(document_id: int, deleted_by: str) -> None:
    """Delete an uploaded file from disk and remove the Document record.

    Raises:
        ValidationError: if document not found
    """

def get_documents(parent_type: str, parent_id: int) -> list[Document]:
    """Get all documents for a parent entity, ordered by created_at desc."""
```

**Implementation details for `save_upload`:**
1. Validate file is not empty (`file.filename` is truthy)
2. Validate file extension against allowed list (per parent_type)
3. Read file content, check `len(content) <= UPLOAD_MAX_SIZE_MB * 1024 * 1024`
4. Generate safe stored filename: `{uuid4_hex}{extension}` using `secure_filename` + `os.path.splitext`
5. Determine storage directory based on parent_type:
   - `equipment_doc` -> `{UPLOAD_PATH}/equipment/{parent_id}/docs/`
   - `equipment_photo` -> `{UPLOAD_PATH}/equipment/{parent_id}/photos/`
   - `repair_photo` -> `{UPLOAD_PATH}/repairs/{parent_id}/` (future)
6. Create directory if it doesn't exist (`os.makedirs(..., exist_ok=True)`)
7. Write file to disk
8. Create Document record in database
9. Call `log_mutation('document.created', uploaded_by, {...})`
10. Return Document instance

**Allowed file extensions:**
```python
ALLOWED_DOC_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx'}
ALLOWED_PHOTO_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'}
```

**External Link functions (add to `esb/services/equipment_service.py`):**

```python
def add_equipment_link(equipment_id: int, title: str, url: str, created_by: str) -> ExternalLink:
    """Add an external link to an equipment record.

    Raises:
        ValidationError: if equipment not found or fields invalid
    """

def delete_equipment_link(link_id: int, deleted_by: str) -> None:
    """Delete an external link.

    Raises:
        ValidationError: if link not found
    """

def get_equipment_links(equipment_id: int) -> list[ExternalLink]:
    """Get all external links for an equipment item, ordered by created_at desc."""
```

**Mutation logging events:**
- `document.created` -- data: `{id, original_filename, category, parent_type, parent_id}`
- `document.deleted` -- data: `{id, original_filename, parent_type, parent_id}`
- `equipment_link.created` -- data: `{id, equipment_id, title, url}`
- `equipment_link.deleted` -- data: `{id, equipment_id, title}`

### View Route Patterns

Add to EXISTING `esb/views/equipment.py`:

```python
# Document upload
@equipment_bp.route('/<int:id>/documents', methods=['POST'])
@role_required('staff')
def upload_document(id):
    """Handle document upload for an equipment item."""

# Photo upload
@equipment_bp.route('/<int:id>/photos', methods=['POST'])
@role_required('staff')
def upload_photo(id):
    """Handle photo upload for an equipment item."""

# Add external link
@equipment_bp.route('/<int:id>/links', methods=['POST'])
@role_required('staff')
def add_link(id):
    """Add an external link to an equipment item."""

# Delete document
@equipment_bp.route('/<int:id>/documents/<int:doc_id>/delete', methods=['POST'])
@role_required('staff')
def delete_document(id, doc_id):
    """Delete a document from an equipment item."""

# Delete photo
@equipment_bp.route('/<int:id>/photos/<int:photo_id>/delete', methods=['POST'])
@role_required('staff')
def delete_photo(id, photo_id):
    """Delete a photo from an equipment item."""

# Delete link
@equipment_bp.route('/<int:id>/links/<int:link_id>/delete', methods=['POST'])
@role_required('staff')
def delete_link(id, link_id):
    """Delete an external link from an equipment item."""
```

**File serving:** Use Flask's `send_from_directory` for serving uploaded files. Add a route or use a separate blueprint:
```python
@equipment_bp.route('/<int:id>/files/<path:filename>')
@login_required
def serve_file(id, filename):
    """Serve an uploaded file for an equipment item."""
    # Determine the correct subdirectory based on filename location
    # Use send_from_directory with the appropriate path
```

**View pattern for uploads:**
```python
@equipment_bp.route('/<int:id>/documents', methods=['POST'])
@role_required('staff')
def upload_document(id):
    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)
    form = DocumentUploadForm()
    if form.validate_on_submit():
        try:
            upload_service.save_upload(
                file=form.file.data,
                parent_type='equipment_doc',
                parent_id=id,
                uploaded_by=current_user.username,
                category=form.category.data,
            )
            flash('Document uploaded successfully.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(f'{error}', 'danger')
    return redirect(url_for('equipment.detail', id=id))
```

**Error handling:**
- All upload/link routes redirect back to equipment detail page
- Use flash messages for success/error feedback
- Catch `ValidationError` from service layer
- Handle `RequestEntityTooLarge` (413) error in the app factory error handler

**Detail view modification:**
The existing `detail` view function needs to be updated to pass documents, photos, links, and forms to the template:
```python
@equipment_bp.route('/<int:id>')
@login_required
def detail(id):
    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)
    documents = upload_service.get_documents('equipment_doc', id)
    photos = upload_service.get_documents('equipment_photo', id)
    links = equipment_service.get_equipment_links(id)
    doc_form = DocumentUploadForm()
    photo_form = PhotoUploadForm()
    link_form = ExternalLinkForm()
    return render_template(
        'equipment/detail.html',
        equipment=equipment,
        documents=documents,
        photos=photos,
        links=links,
        doc_form=doc_form,
        photo_form=photo_form,
        link_form=link_form,
    )
```

### Form Patterns

Add to EXISTING `esb/forms/equipment_forms.py`:

```python
from flask_wtf.file import FileField, FileRequired, FileAllowed

DOCUMENT_CATEGORIES = [
    ('', '-- Select Category --'),
    ('owners_manual', "Owner's Manual"),
    ('service_manual', 'Service Manual'),
    ('quick_start', 'Quick Start Guide'),
    ('training_video', 'Training Video'),
    ('manufacturer_page', 'Manufacturer Product Page'),
    ('manufacturer_support', 'Manufacturer Support'),
    ('other', 'Other'),
]

class DocumentUploadForm(FlaskForm):
    """Form for uploading a document to an equipment record."""
    file = FileField('Document', validators=[
        FileRequired('Please select a file to upload.'),
        FileAllowed(
            ['pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx'],
            'Only document files are allowed.'
        ),
    ])
    category = SelectField('Category', choices=DOCUMENT_CATEGORIES, validators=[DataRequired()])
    submit = SubmitField('Upload Document')


class PhotoUploadForm(FlaskForm):
    """Form for uploading a photo/video to an equipment record."""
    file = FileField('Photo/Video', validators=[
        FileRequired('Please select a file to upload.'),
        FileAllowed(
            ['jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm'],
            'Only image and video files are allowed.'
        ),
    ])
    submit = SubmitField('Upload Photo')


class ExternalLinkForm(FlaskForm):
    """Form for adding an external link to an equipment record."""
    title = StringField('Title', validators=[DataRequired(), Length(max=200)])
    url = StringField('URL', validators=[DataRequired(), Length(max=2000), URL()])
    submit = SubmitField('Add Link')
```

**New imports needed:** `FileField`, `FileRequired`, `FileAllowed` from `flask_wtf.file`, `URL` from `wtforms.validators`

**Note on form template rendering:**
- Each form needs `enctype="multipart/form-data"` in the template
- Forms are inline on the detail page (inside collapsible/accordion sections), NOT on separate pages
- Submit button text matches the action ("Upload Document", "Upload Photo", "Add Link")

### Template Patterns

**Equipment detail page (`templates/equipment/detail.html`) -- replace placeholder sections:**

**Documents section:**
- Card with header "Documents" and "Upload" button (Staff only)
- Upload form (collapsed by default, shown when clicking "Upload") with file input and category dropdown
- Document list as a Bootstrap list group:
  - Each item: category badge + original filename (linked to download) + file size + uploaded by + date + delete button (Staff only)
- Empty state: "No documents attached yet."

**Photos section:**
- Card with header "Photos" and "Upload" button (Staff only)
- Upload form (collapsed by default)
- Photo gallery as a responsive grid of thumbnail cards (using Bootstrap grid, 2-3 columns on desktop, 1-2 on mobile):
  - Each thumbnail: image preview + original filename + delete button (Staff only)
  - Non-image files (video): show a file icon placeholder instead of preview
- Empty state: "No photos attached yet."

**Links section:**
- Card with header "Links" and "Add Link" button (Staff only)
- Add link form (collapsed by default) with title and URL fields
- Link list as a Bootstrap list group:
  - Each item: title (linked, opens in new tab via `target="_blank" rel="noopener noreferrer"`) + delete button (Staff only)
- Empty state: "No links added yet."

**Delete confirmation:** Use a simple `onclick="return confirm('Are you sure?')"` on delete buttons -- no modal needed for individual deletions. Wrap each delete in a small inline form with CSRF token.

**Collapsible upload/add sections:** Use Bootstrap collapse component:
```html
<button class="btn btn-sm btn-primary" type="button" data-bs-toggle="collapse" data-bs-target="#upload-doc-form">
    Upload Document
</button>
<div class="collapse" id="upload-doc-form">
    <form method="post" action="..." enctype="multipart/form-data">
        {{ doc_form.hidden_tag() }}
        ...
    </form>
</div>
```

### Flask Configuration Updates

Add `MAX_CONTENT_LENGTH` to `esb/config.py` in the base `Config` class:
```python
MAX_CONTENT_LENGTH = int(os.environ.get('UPLOAD_MAX_SIZE_MB', 500)) * 1024 * 1024
```

This enforces the upload size limit at the request level. When exceeded, Flask raises a `RequestEntityTooLarge` (413) exception. Add an error handler in the app factory:
```python
@app.errorhandler(413)
def request_entity_too_large(e):
    flash('File is too large. Maximum size is {} MB.'.format(app.config['UPLOAD_MAX_SIZE_MB']), 'danger')
    return redirect(request.referrer or url_for('equipment.list_equipment')), 302
```

### UX Requirements

- **Button hierarchy:** "Upload Document"/"Upload Photo"/"Add Link" = `btn-primary btn-sm` inside card headers (Staff only). Delete = `btn-outline-danger btn-sm` with confirmation.
- **Collapsible forms:** Upload/add forms are hidden by default to keep the page clean. Revealed via Bootstrap collapse on button click.
- **File download:** Documents are downloadable links. Filename in the link is the original filename (not the stored UUID filename).
- **Photo thumbnails:** Equipment photos shown as responsive thumbnail grid. CSS max-height for thumbnails.
- **Links open in new tabs:** `target="_blank" rel="noopener noreferrer"` on all external links.
- **Category badges:** Use Bootstrap badges with `bg-secondary` for document categories.
- **Mobile responsive:** Upload forms go full-width on mobile. Photo grid collapses to single column.
- **Empty states:** Centered `text-muted` message in each section when no items exist.

### Testing Requirements

**Test files:**
- `tests/test_models/test_document.py` -- Document model tests (NEW)
- `tests/test_models/test_external_link.py` -- ExternalLink model tests (NEW)
- `tests/test_services/test_upload_service.py` -- Upload service tests (NEW)
- `tests/test_services/test_equipment_service.py` -- EXTEND with link function tests
- `tests/test_views/test_equipment_views.py` -- EXTEND with upload/link/delete view tests

**Use existing fixtures from `tests/conftest.py`:**
- `app`, `client`, `db`, `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture`
- `make_area`, `make_equipment`

**Add new fixtures to `tests/conftest.py`:**
```python
def _create_document(parent_type='equipment_doc', parent_id=1, category='other',
                     original_filename='test.pdf', stored_filename='abc123.pdf',
                     content_type='application/pdf', size_bytes=1024,
                     uploaded_by='teststaff'):
    """Helper to create a Document record in the test database."""

def _create_external_link(equipment_id=1, title='Test Link',
                           url='https://example.com', created_by='teststaff'):
    """Helper to create an ExternalLink record in the test database."""
```

**Required test coverage:**
- Document model: creation with all fields, defaults, `__repr__`, parent_type values
- ExternalLink model: creation, FK constraint to equipment, defaults, `__repr__`
- Upload service: `save_upload` (success, empty file, oversized file, invalid extension, directory creation), `delete_upload` (success, not found, file removal), `get_documents` (filtering by parent_type+parent_id)
- Equipment service links: `add_equipment_link` (success, invalid equipment, missing fields), `delete_equipment_link` (success, not found), `get_equipment_links` (filtered)
- Views: upload document (staff OK, tech 403, success, validation error), upload photo (staff OK), add link (staff OK, tech 403), delete document/photo/link (staff OK, tech 403), file serving (login required), 413 error handling
- Mutation logging: use `capture` fixture (NOT `caplog`), verify event names and data fields

**Critical testing notes from previous stories:**
1. Use `capture` fixture for mutation log assertions -- `caplog` does NOT work (logger has `propagate=False`)
2. Flash category is `'danger'` NOT `'error'`
3. Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
4. DB queries: `db.session.get(Model, id)` for PK lookups
5. Parse mutation log entries from capture: `json.loads(r.message)` where `r` is from `capture.records`
6. For file upload tests, use `io.BytesIO` to create fake file objects and `(BytesIO(b'content'), 'filename.pdf')` tuple for `data` in test client POST
7. SQLite in tests does NOT enforce FK constraints -- test NOT NULL constraints instead
8. Test the upload directory creation (mock `os.makedirs` or use `tmp_path` fixture)
9. For 413 error testing, set `MAX_CONTENT_LENGTH` to a small value in test config

**File upload test pattern:**
```python
def test_upload_document_success(self, staff_client, make_equipment, db, capture):
    equipment = make_equipment()
    data = {
        'file': (io.BytesIO(b'fake pdf content'), 'manual.pdf'),
        'category': 'owners_manual',
    }
    response = staff_client.post(
        f'/equipment/{equipment.id}/documents',
        data=data,
        content_type='multipart/form-data',
        follow_redirects=True,
    )
    assert response.status_code == 200
    # Verify Document record created
    # Verify mutation log
    # Verify file on disk (or mock)
```

### Project Structure Notes

- Document model uses polymorphic parent_type+parent_id pattern (NOT FK to equipment) -- this enables reuse for repair photos in Epic 3
- ExternalLink model uses direct FK to equipment (links are equipment-only)
- Upload service is a NEW service file -- does NOT go in equipment_service.py because uploads will also be used by repair records in Epic 3
- External link functions go in equipment_service.py because links are equipment-only
- The detail view becomes the central hub -- it now passes 6+ variables to the template (equipment, documents, photos, links, 3 forms)
- Delete routes use POST method with CSRF protection (not GET to prevent CSRF attacks)

### Previous Story Intelligence

**Patterns to follow from Story 2.2 (Equipment Registry CRUD):**
- Service pattern: copy equipment service structure (validation, mutation logging, error handling)
- View pattern: copy equipment view structure (decorator, form validation, flash, redirect)
- Form pattern: copy equipment form structure (validators, no asterisks in Python labels)
- Template pattern: copy detail page card structure for new sections
- Test pattern: copy equipment test structure (class-based grouping, service + view + mutation tests)

**Known gotchas from previous stories:**
1. `ruff target-version = "py313"` (NOT py314)
2. Mutation logger `propagate=False` -- use `_CaptureHandler` / `capture` fixture in tests
3. Flash `'danger'` not `'error'` for Bootstrap alert classes
4. Wrap ALL service calls in views with `try/except ValidationError`
5. Labels WITHOUT asterisks in Python form classes -- add `*` in templates only
6. Error templates extend `base_public.html` to avoid `current_user` dependency
7. Import `datetime` from `datetime` module: `from datetime import UTC, datetime`
8. Case-insensitive duplicate checks use `db.func.lower()`
9. The `make_equipment` fixture already exists in conftest -- creates area automatically if not provided
10. Equipment detail page already has placeholder card sections for Documents, Photos, Links -- REPLACE these, don't add new sections

### Git Intelligence

**Recent commits:**
- `717c384` Fix code review issues for Story 2.2 equipment registry CRUD
- `681337c` Implement Story 2.2: Equipment Registry CRUD
- `927e1cb` Switch database from MySQL 8.4 to MariaDB 12.2.2

**Files most likely to be modified (existing):**
- `esb/services/equipment_service.py` (extend with link functions)
- `esb/forms/equipment_forms.py` (extend with upload/link forms)
- `esb/views/equipment.py` (extend with upload/link/delete/serve routes)
- `esb/models/__init__.py` (add Document, ExternalLink imports)
- `esb/templates/equipment/detail.html` (replace placeholder sections)
- `esb/config.py` (add MAX_CONTENT_LENGTH)
- `esb/__init__.py` (add 413 error handler)
- `tests/conftest.py` (add document/link factory fixtures)
- `tests/test_services/test_equipment_service.py` (extend with link tests)
- `tests/test_views/test_equipment_views.py` (extend with upload/link/delete tests)

**Files to be created (new):**
- `esb/models/document.py`
- `esb/models/external_link.py`
- `esb/services/upload_service.py`
- `migrations/versions/{hash}_add_documents_and_external_links_tables.py`
- `tests/test_models/test_document.py`
- `tests/test_models/test_external_link.py`
- `tests/test_services/test_upload_service.py`

### Library/Framework Requirements

| Package | Version | Notes |
|---------|---------|-------|
| Flask | 3.1.x | Already installed |
| Flask-SQLAlchemy | 3.1.x | Already installed |
| Flask-Migrate/Alembic | Latest | Already installed |
| Flask-WTF | 1.2.x | Already installed -- has `FileField`, `FileAllowed`, `FileRequired` |
| Flask-Login | 0.6.3 | Already installed |
| Werkzeug | 3.1.x | Already installed -- has `secure_filename`, `FileStorage` |
| Bootstrap | 5.3.8 | Bundled locally in `esb/static/` |

**No new pip dependencies required for this story.** Flask-WTF provides `FileField`, `FileRequired`, and `FileAllowed` validators. Werkzeug provides `secure_filename` and `FileStorage`. Standard library provides `uuid`, `os`, `mimetypes`.

**Do NOT add** `python-magic` or other external file validation libraries -- extension-based validation via `FileAllowed` is sufficient for this use case per architecture doc. MIME type validation is a potential future enhancement.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 2, Story 2.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Data Architecture -- File Upload Storage, Document model]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns -- upload_service.py, File System Boundary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Process Patterns -- File Upload Pattern]
- [Source: _bmad-output/planning-artifacts/prd.md#FR3, FR4, FR5]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4 -- Equipment Management, Component Strategy]
- [Source: _bmad-output/implementation-artifacts/2-2-equipment-registry-crud.md -- Previous story patterns and gotchas]
- [Source: esb/models/equipment.py -- Equipment model reference]
- [Source: esb/services/equipment_service.py -- Service pattern reference (extend this file)]
- [Source: esb/forms/equipment_forms.py -- Form pattern reference (extend this file)]
- [Source: esb/views/equipment.py -- View/route pattern reference (extend this file)]
- [Source: esb/templates/equipment/detail.html -- Template reference (modify placeholder sections)]
- [Source: esb/config.py -- UPLOAD_PATH and UPLOAD_MAX_SIZE_MB already configured]
- [Source: tests/conftest.py -- Test fixture pattern reference]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
