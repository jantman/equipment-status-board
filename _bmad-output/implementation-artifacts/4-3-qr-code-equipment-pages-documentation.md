# Story 4.3: QR Code Equipment Pages & Documentation

Status: review

## Story

As a member,
I want to scan a QR code on a piece of equipment and immediately see its status and documentation,
So that I get instant, machine-specific information without navigating or logging in.

## Acceptance Criteria

1. **Given** the `qr_service` module, **When** QR code generation is triggered for an equipment item, **Then** a QR code image (PNG) is generated linking to the equipment's public page URL on the local network **And** the image is saved to `static/qrcodes/`. (AC: #1)

2. **Given** I scan a QR code on a piece of equipment, **When** my phone browser opens the equipment page (`/public/equipment/<int:id>`), **Then** the page loads without requiring authentication. (AC: #2)

3. **Given** the QR code equipment page, **When** it loads, **Then** I see immediately above the fold: equipment name and area (h1-level), and a Large status indicator (green/yellow/red with icon and text). (AC: #3)

4. **Given** the equipment is degraded or down, **When** I view the QR page, **Then** I see a brief description of the current issue and ETA if available, directly below the status indicator. (AC: #4)

5. **Given** the QR code equipment page, **When** I tap the "Equipment Info" link, **Then** I navigate to a documentation page showing all uploaded manuals, training materials, and external links for that equipment. (AC: #5)

6. **Given** the equipment documentation page (`/public/equipment/<int:id>/info`), **When** I view it, **Then** I see documents organized by category label, photos, and external links **And** documents are downloadable and links open in new tabs. (AC: #6)

7. **Given** the QR code equipment page, **When** viewed on a mobile phone (375px viewport), **Then** the page is single-column, optimized for mobile-first, with no horizontal scrolling **And** all tap targets are minimum 44x44px. (AC: #7)

## Tasks / Subtasks

- [x] Task 1: Create `esb/services/qr_service.py` with QR code generation (AC: #1)
  - [x]1.1: Add `qrcode` and `Pillow` to `requirements.txt` (qrcode[pil])
  - [x]1.2: Implement `generate_qr_code(equipment_id: int, base_url: str) -> str` -- generates PNG QR code, saves to `esb/static/qrcodes/{equipment_id}.png`, returns relative path
  - [x]1.3: Implement `get_qr_code_path(equipment_id: int) -> str | None` -- returns path if QR code exists, None if not
  - [x]1.4: Implement `generate_all_qr_codes(base_url: str) -> int` -- bulk generation for all non-archived equipment, returns count generated
  - [x]1.5: QR code URL format: `{base_url}/public/equipment/{equipment_id}`

- [x] Task 2: Add equipment QR page route to `esb/views/public.py` (AC: #2, #3, #4)
  - [x]2.1: Add `GET /public/equipment/<int:id>` route -- NO `@login_required` (unauthenticated, public)
  - [x]2.2: Route calls `equipment_service.get_equipment(id)` (raise 404 if not found or archived)
  - [x]2.3: Route calls `status_service.compute_equipment_status(id)` for current status
  - [x]2.4: Route queries open repair records for this equipment (status NOT in CLOSED_STATUSES) for "Known Issues" section
  - [x]2.5: Route gets ETA from the highest-severity open repair record (if available)
  - [x]2.6: Renders `public/equipment_page.html` template

- [x] Task 3: Add equipment info/documentation route to `esb/views/public.py` (AC: #5, #6)
  - [x]3.1: Add `GET /public/equipment/<int:id>/info` route -- NO `@login_required`
  - [x]3.2: Route calls `equipment_service.get_equipment(id)` (raise 404 if not found or archived)
  - [x]3.3: Route calls `upload_service.get_documents('equipment_doc', id)` for documents
  - [x]3.4: Route calls `upload_service.get_documents('equipment_photo', id)` for photos
  - [x]3.5: Route calls `equipment_service.get_equipment_links(id)` for external links
  - [x]3.6: Renders `public/equipment_info.html` template

- [x] Task 4: Create `esb/templates/public/equipment_page.html` template (AC: #2, #3, #4, #7)
  - [x]4.1: Extends `base_public.html` (unauthenticated layout, no navbar)
  - [x]4.2: Equipment name + area as `<h1>` (above the fold)
  - [x]4.3: Large status indicator via `{% include 'components/_status_indicator.html' %}` with `variant='large'`
  - [x]4.4: If degraded/down: issue description + ETA below status indicator
  - [x]4.5: "Equipment Info" link navigating to `/public/equipment/{id}/info`
  - [x]4.6: "Known Issues" section (only shown if open repair records exist) with severity + description per issue
  - [x]4.7: Mobile-first single-column layout, minimum 44x44px tap targets
  - [x]4.8: ARIA labels on status indicator and interactive elements

- [x] Task 5: Create `esb/templates/public/equipment_info.html` template (AC: #5, #6)
  - [x]5.1: Extends `base_public.html`
  - [x]5.2: Equipment name as `<h1>`, "Back to status" link
  - [x]5.3: Documents section organized by category (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other)
  - [x]5.4: Each document has download link with original filename displayed
  - [x]5.5: Photos section with thumbnails
  - [x]5.6: External links section with title + URL (open in new tab with `target="_blank" rel="noopener noreferrer"`)
  - [x]5.7: Empty states for each section (hidden if no items, not shown as empty)
  - [x]5.8: Mobile-first layout, minimum 44x44px tap targets

- [x] Task 6: Add QR page CSS to `esb/static/css/app.css` (AC: #7)
  - [x]6.1: QR page hero section styles for above-the-fold status display
  - [x]6.2: Known issues list styling
  - [x]6.3: Documentation page category grouping styles
  - [x]6.4: Mobile-first, no horizontal scroll, full-width elements

- [x] Task 7: Add file serving route for uploads (AC: #6)
  - [x]7.1: Add `GET /uploads/<path:filepath>` route in public.py for serving uploaded documents/photos
  - [x]7.2: Use `send_from_directory` with `app.config['UPLOAD_PATH']` as base directory
  - [x]7.3: Validate path to prevent directory traversal

- [x] Task 8: Write service tests for `qr_service` (AC: #1)
  - [x]8.1: Test QR code generation creates PNG file at correct path
  - [x]8.2: Test QR code contains correct URL
  - [x]8.3: Test `get_qr_code_path` returns path for existing QR code
  - [x]8.4: Test `get_qr_code_path` returns None for missing QR code
  - [x]8.5: Test `generate_all_qr_codes` generates for all non-archived equipment
  - [x]8.6: Test QR code generation skips archived equipment

- [x] Task 9: Write view tests for equipment QR page (AC: #2, #3, #4, #7)
  - [x]9.1: Test equipment page renders without authentication
  - [x]9.2: Test equipment page shows equipment name and area
  - [x]9.3: Test equipment page shows large status indicator
  - [x]9.4: Test equipment page shows issue description for degraded/down
  - [x]9.5: Test equipment page shows ETA when available
  - [x]9.6: Test equipment page shows known issues section when open repairs exist
  - [x]9.7: Test equipment page hides known issues when no open repairs
  - [x]9.8: Test equipment page returns 404 for non-existent equipment
  - [x]9.9: Test equipment page returns 404 for archived equipment
  - [x]9.10: Test equipment page has Equipment Info link
  - [x]9.11: Test ARIA labels present

- [x] Task 10: Write view tests for equipment info/documentation page (AC: #5, #6)
  - [x]10.1: Test info page renders without authentication
  - [x]10.2: Test info page shows documents grouped by category
  - [x]10.3: Test info page shows download links for documents
  - [x]10.4: Test info page shows photos
  - [x]10.5: Test info page shows external links with target="_blank"
  - [x]10.6: Test info page returns 404 for non-existent equipment
  - [x]10.7: Test info page returns 404 for archived equipment
  - [x]10.8: Test info page hides empty sections
  - [x]10.9: Test back-to-status link present

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Single CSS/JS files:** All custom styles go in `esb/static/css/app.css`. All custom JS goes in `esb/static/js/app.js`. NO per-page CSS/JS files.
5. **Template naming:** snake_case for templates (`equipment_page.html`). Underscore prefix for partials (`_status_indicator.html`).
6. **Public routes:** These routes go in `esb/views/public.py` with NO `@login_required` -- they are unauthenticated public pages (like kiosk).
7. **Domain exceptions:** Use `EquipmentNotFound` from `esb/utils/exceptions.py`. Views catch and `abort(404)`.

### Critical Implementation Details

#### New Dependency: `qrcode` Library

The `qrcode` Python library is needed for QR code generation. Add to `requirements.txt`:
```
qrcode[pil]>=8.0
```

This also pulls in `Pillow` for PNG image generation. The architecture doc specifies: "Python `qrcode` library. QR codes generated as PNG or SVG."

#### QR Service (`esb/services/qr_service.py`)

```python
import qrcode
import os
from flask import current_app

def generate_qr_code(equipment_id: int, base_url: str) -> str:
    """Generate a QR code PNG for an equipment item.

    Args:
        equipment_id: The equipment ID to generate QR for.
        base_url: The base URL of the application (e.g., 'http://192.168.1.50:5000').

    Returns:
        Relative path to the generated QR code image (e.g., 'qrcodes/42.png').
    """
    url = f"{base_url}/public/equipment/{equipment_id}"
    qr = qrcode.make(url)

    qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"{equipment_id}.png"
    filepath = os.path.join(qr_dir, filename)
    qr.save(filepath)

    return f"qrcodes/{filename}"
```

**Key decisions:**
- QR codes saved as PNG to `esb/static/qrcodes/{equipment_id}.png`
- The `static/qrcodes/` directory already exists (with `.gitkeep`)
- QR URL format: `{base_url}/public/equipment/{equipment_id}`
- `base_url` is passed in (not hardcoded) -- the URL depends on the local network configuration
- Consider adding a `QR_BASE_URL` environment variable for production configuration

#### Equipment QR Page Route

File: `esb/views/public.py`

```python
@public_bp.route('/equipment/<int:id>')
def equipment_page(id):
    """QR code equipment page -- public status, issues, and documentation link."""
    from esb.services import equipment_service, status_service, repair_service

    try:
        equipment = equipment_service.get_equipment(id)
    except EquipmentNotFound:
        abort(404)

    # Archived equipment should not be publicly visible
    if equipment.is_archived:
        abort(404)

    status = status_service.compute_equipment_status(id)

    # Get open repair records for "Known Issues" section
    from esb.services.repair_service import CLOSED_STATUSES
    open_repairs = [
        r for r in repair_service.list_repair_records(equipment_id=id)
        if r.status not in CLOSED_STATUSES
    ]

    # Get ETA from highest-severity open repair (if any)
    eta = None
    if open_repairs:
        # Sort by severity priority (Down first), take the first with ETA
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
    )
```

**Critical notes:**
- `equipment_service.get_equipment()` raises `EquipmentNotFound` if the ID doesn't exist -- catch it and `abort(404)`
- Additionally check `is_archived` -- archived equipment should return 404 on public pages
- Import `CLOSED_STATUSES` from `repair_service` to filter open records
- The `list_repair_records(equipment_id=id)` function already exists and returns all records for an equipment item, ordered by `created_at desc`

#### Equipment Info/Documentation Route

```python
@public_bp.route('/equipment/<int:id>/info')
def equipment_info(id):
    """Equipment documentation page -- manuals, photos, and links."""
    from esb.services import equipment_service, upload_service

    try:
        equipment = equipment_service.get_equipment(id)
    except EquipmentNotFound:
        abort(404)

    if equipment.is_archived:
        abort(404)

    documents = upload_service.get_documents('equipment_doc', id)
    photos = upload_service.get_documents('equipment_photo', id)
    links = equipment_service.get_equipment_links(id)

    return render_template(
        'public/equipment_info.html',
        equipment=equipment,
        documents=documents,
        photos=photos,
        links=links,
    )
```

#### File Serving Route

Uploaded documents and photos need to be accessible on the public equipment info page. Check if a file serving route already exists. If not, add one:

```python
@public_bp.route('/uploads/<path:filepath>')
def serve_upload(filepath):
    """Serve uploaded files (documents, photos)."""
    from flask import send_from_directory
    upload_path = current_app.config.get('UPLOAD_PATH', 'uploads')
    # Prevent directory traversal
    if '..' in filepath:
        abort(404)
    return send_from_directory(upload_path, filepath)
```

**IMPORTANT:** Check if an upload serving route already exists in other blueprints before creating a duplicate. Look at `esb/views/equipment.py` for existing file serving patterns. If one exists, reuse it by linking to the same URL pattern.

#### Template: `esb/templates/public/equipment_page.html`

Progressive disclosure layout (per UX spec):
1. Equipment name + area (h1) -- above the fold
2. Large status indicator (green/yellow/red with icon + text)
3. If degraded/down: current issue + ETA
4. "Equipment Info" link -> documentation page
5. "Known Issues" section (if open repairs exist)

```jinja2
{% extends "base_public.html" %}

{% block title %}{{ equipment.name }} - {{ equipment.area.name }}{% endblock %}

{% block content %}
<div class="qr-page-hero text-center py-4">
  <h1>{{ equipment.name }}</h1>
  <p class="text-muted fs-5">{{ equipment.area.name }}</p>

  {% set variant = 'large' %}
  {% include 'components/_status_indicator.html' %}

  {% if status.color != 'green' and status.issue_description %}
  <p class="mt-3 fs-5">{{ status.issue_description }}</p>
  {% if eta %}
  <p class="text-muted">ETA: {{ eta.strftime('%b %d, %Y') }}</p>
  {% endif %}
  {% endif %}
</div>

<div class="mt-4">
  <a href="{{ url_for('public.equipment_info', id=equipment.id) }}"
     class="btn btn-outline-primary btn-lg w-100 py-3">
    Equipment Info &amp; Documentation
  </a>
</div>

{% if open_repairs %}
<div class="mt-4">
  <h2>Known Issues</h2>
  <p class="text-muted">If your issue is listed below, it's already being worked on.</p>
  {% for repair in open_repairs %}
  <div class="card mb-2 status-card status-card-{{ 'red' if repair.severity == 'Down' else 'yellow' }}">
    <div class="card-body py-2">
      <div class="d-flex justify-content-between align-items-center">
        <span class="fw-bold">{{ repair.severity or 'Not Sure' }}</span>
      </div>
      <p class="mb-0 mt-1">{{ repair.description }}</p>
    </div>
  </div>
  {% endfor %}
</div>
{% endif %}
{% endblock %}
```

**Key template decisions:**
- Extends `base_public.html` (no navbar, no auth required)
- Uses `status_indicator.html` with `variant='large'` (already implemented in Story 4.1)
- Known Issues section hidden entirely when no open repairs (per UX spec)
- Equipment Info link is a full-width button for easy tap target on mobile
- Status card CSS classes (`status-card-red`, `status-card-yellow`) already exist from Story 4.1

#### Template: `esb/templates/public/equipment_info.html`

```jinja2
{% extends "base_public.html" %}

{% block title %}{{ equipment.name }} - Equipment Info{% endblock %}

{% block content %}
<h1>{{ equipment.name }}</h1>
<p class="text-muted">{{ equipment.area.name }}</p>

<a href="{{ url_for('public.equipment_page', id=equipment.id) }}"
   class="btn btn-outline-secondary mb-4">&larr; Back to Status</a>

{% if documents %}
<h2>Documents</h2>
{% for category, docs in documents_by_category.items() %}
<h3>{{ category }}</h3>
<ul class="list-group mb-3">
  {% for doc in docs %}
  <li class="list-group-item">
    <a href="{{ url_for('public.serve_upload', filepath='equipment/' ~ equipment.id ~ '/docs/' ~ doc.stored_filename) }}"
       download="{{ doc.original_filename }}">
      {{ doc.original_filename }}
    </a>
    <small class="text-muted d-block">{{ (doc.size_bytes / 1024)|int }} KB</small>
  </li>
  {% endfor %}
</ul>
{% endfor %}
{% endif %}

{% if photos %}
<h2>Photos</h2>
<div class="row g-2">
  {% for photo in photos %}
  <div class="col-6 col-md-4">
    <a href="{{ url_for('public.serve_upload', filepath='equipment/' ~ equipment.id ~ '/photos/' ~ photo.stored_filename) }}"
       target="_blank">
      <img src="{{ url_for('public.serve_upload', filepath='equipment/' ~ equipment.id ~ '/photos/' ~ photo.stored_filename) }}"
           alt="{{ photo.original_filename }}"
           class="img-fluid rounded">
    </a>
  </div>
  {% endfor %}
</div>
{% endif %}

{% if links %}
<h2 class="mt-4">External Links</h2>
<ul class="list-group">
  {% for link in links %}
  <li class="list-group-item">
    <a href="{{ link.url }}" target="_blank" rel="noopener noreferrer">
      {{ link.title }}
    </a>
  </li>
  {% endfor %}
</ul>
{% endif %}

{% if not documents and not photos and not links %}
<div class="text-center py-4">
  <p class="text-muted">No documentation available for this equipment yet.</p>
</div>
{% endif %}
{% endblock %}
```

**Key decisions:**
- Documents grouped by category (use a helper in the view to group them before passing to template)
- Category display names map from DB values: `owners_manual` -> "Owner's Manual", etc.
- Documents have download attribute for direct download
- Photos shown as thumbnails in a responsive grid
- External links open in new tabs with `rel="noopener noreferrer"` for security
- Empty state only shown when ALL sections are empty

#### Document Category Display Names

The Document model has `DOCUMENT_CATEGORIES` constant. Map these to user-friendly display names in the view or as a template filter:

```python
CATEGORY_DISPLAY_NAMES = {
    'owners_manual': "Owner's Manual",
    'service_manual': 'Service Manual',
    'quick_start': 'Quick Start Guide',
    'training_video': 'Training Video',
    'manufacturer_page': 'Manufacturer Product Page',
    'manufacturer_support': 'Manufacturer Support',
    'other': 'Other',
}
```

Group documents by category in the view function before passing to template:

```python
from collections import OrderedDict
documents_by_category = OrderedDict()
for doc in documents:
    cat_display = CATEGORY_DISPLAY_NAMES.get(doc.category, doc.category or 'Other')
    documents_by_category.setdefault(cat_display, []).append(doc)
```

### Reuse from Previous Stories (DO NOT recreate)

**From Story 4.1:**
- `status_service.compute_equipment_status(equipment_id)` -- returns `{color, label, issue_description, severity}`. Import from `esb.services.status_service`.
- `components/_status_indicator.html` -- `large` variant already implemented with color + icon + text + ARIA label. Pass `variant='large'` and `status` dict.
- `status-card-green`, `status-card-yellow`, `status-card-red` CSS classes in `app.css`.

**From Story 2.2:**
- `equipment_service.get_equipment(id)` -- returns Equipment instance, raises `EquipmentNotFound`.

**From Story 2.3:**
- `upload_service.get_documents(parent_type, parent_id)` -- returns `list[Document]`.
- `equipment_service.get_equipment_links(equipment_id)` -- returns `list[ExternalLink]`.
- `Document.DOCUMENT_CATEGORIES` -- category constants.

**From Story 3.1-3.2:**
- `repair_service.list_repair_records(equipment_id=id)` -- returns all records for equipment.
- `CLOSED_STATUSES` -- list of closed statuses to filter out.

### Project Structure Notes

**New files to create:**
- `esb/services/qr_service.py` -- QR code generation logic
- `esb/templates/public/equipment_page.html` -- QR code equipment page
- `esb/templates/public/equipment_info.html` -- Equipment documentation page
- `tests/test_services/test_qr_service.py` -- QR service tests
- (view tests added to existing `tests/test_views/test_public_views.py`)

**Files to modify:**
- `esb/views/public.py` -- add 3 routes (equipment_page, equipment_info, serve_upload)
- `esb/static/css/app.css` -- add QR page styles (~15-20 lines)
- `requirements.txt` -- add `qrcode[pil]`
- `tests/test_views/test_public_views.py` -- add view tests

**Files NOT to modify:**
- `esb/services/status_service.py` -- reuse `compute_equipment_status()` as-is
- `esb/services/equipment_service.py` -- reuse `get_equipment()` and `get_equipment_links()` as-is
- `esb/services/upload_service.py` -- reuse `get_documents()` as-is
- `esb/services/repair_service.py` -- reuse `list_repair_records()` and `CLOSED_STATUSES` as-is
- `esb/models/` -- no new models, no migrations
- `esb/templates/base_public.html` -- use as-is
- `esb/templates/components/_status_indicator.html` -- use large variant as-is
- `esb/templates/base.html` -- no navbar changes needed

### Previous Story Intelligence (from Story 4.2)

**Patterns to follow:**
- Use `capture` fixture for mutation log assertions (NOT `caplog`) -- though QR pages are read-only, no mutation logging needed
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
- `db.session.get(Model, id)` for PK lookups
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions to avoid circular imports
- 660 tests currently passing, 0 lint errors
- Test factories: `make_area`, `make_equipment`, `make_repair_record` in `tests/conftest.py`

**Code review lessons from 4.1 and 4.2:**
- Don't duplicate logic -- reuse existing service functions
- Include tests for ARIA attributes and responsive layout classes
- Skip empty areas (no equipment) on public pages
- Include visually-hidden `<h1>` for WCAG if needed
- Use `<h3>` or proper heading elements for equipment names, not `<span>`

### Upload File Serving

**CRITICAL:** Before implementing a new file serving route, check if one already exists. Look at `esb/views/equipment.py` for existing patterns. The equipment detail page (authenticated) already serves uploaded files -- check the exact route pattern used there.

If an existing route like `/uploads/<path:filepath>` or `/equipment/<int:id>/documents/<int:doc_id>/download` already exists, link to that same URL from the public templates. Do NOT create a duplicate file serving mechanism.

If the existing route requires `@login_required`, you'll need to create a public version. The upload path structure is:
- Documents: `{UPLOAD_PATH}/equipment/{id}/docs/{stored_filename}`
- Photos: `{UPLOAD_PATH}/equipment/{id}/photos/{stored_filename}`

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

- Test file: `tests/test_views/test_public_views.py` (append to existing file)
- New test file: `tests/test_services/test_qr_service.py`
- Use existing fixtures: `client` (unauthenticated), `make_area`, `make_equipment`, `make_repair_record`
- QR pages are unauthenticated -- use `client` NOT `staff_client` or `tech_client`
- Check for `status-indicator-large` CSS class on equipment page
- Check for `aria-label` on status indicators
- Check download links have correct `href` and `download` attributes
- Check external links have `target="_blank"` and `rel="noopener noreferrer"`
- Test 404 for non-existent and archived equipment on both routes
- For QR service tests: use `tmp_path` or mock `current_app.static_folder` to avoid writing to actual static directory

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with Jinja2 templates
- **Bootstrap 5** bundled locally (no CDN)
- **Vanilla JS only** -- no npm, no build step
- **SQLAlchemy** via Flask-SQLAlchemy for all queries
- **pytest** for tests
- **NEW dependency: `qrcode[pil]`** for QR code generation (adds `qrcode` + `Pillow`)

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 Story 4.3]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture - QR Code Generation]
- [Source: _bmad-output/planning-artifacts/architecture.md#File System Boundary - qr_service.py]
- [Source: _bmad-output/planning-artifacts/architecture.md#Requirements to Structure Mapping - FR31-FR32]
- [Source: _bmad-output/planning-artifacts/prd.md#FR31-FR32]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#QR Code Equipment Page Template]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Progressive Disclosure Pattern]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 1 Member Checks Status]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Defining Interaction]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design - QR Equipment Page]
- [Source: _bmad-output/implementation-artifacts/4-1-equipment-status-derivation-status-dashboard.md#Dev Notes]
- [Source: _bmad-output/implementation-artifacts/4-2-kiosk-display.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- `get_equipment()` raises `ValidationError` (not `EquipmentNotFound`), caught accordingly in routes
- Existing file-serving routes in equipment.py require `@login_required`, so created public `/uploads/<path:filepath>` route
- `pyzbar` not available for QR decode testing; verified PNG validity with Pillow instead

### Completion Notes List

- Task 1: Created `esb/services/qr_service.py` with `generate_qr_code()`, `get_qr_code_path()`, `generate_all_qr_codes()`; added `qrcode[pil]>=8.0` to requirements.txt
- Task 2: Added `GET /public/equipment/<int:id>` route in public.py — no auth, catches ValidationError → 404, filters archived, gets open repairs + ETA
- Task 3: Added `GET /public/equipment/<int:id>/info` route — documents grouped by category using `DOCUMENT_CATEGORIES`, photos, external links
- Task 4: Created `equipment_page.html` — extends base_public.html, h1 name+area, large status indicator, issue description+ETA, Equipment Info link, Known Issues section
- Task 5: Created `equipment_info.html` — documents by category with download links, photos grid, external links with target=_blank, back-to-status link, empty state
- Task 6: Added QR page CSS to app.css — hero section, 44px tap targets, category grouping
- Task 7: Added `/uploads/<path:filepath>` public route with directory traversal protection
- Task 8: 8 QR service tests (PNG creation, valid image, overwrite, path exists/missing, bulk generation, skip archived, zero count)
- Task 9: 14 equipment page view tests (no auth, name+area, large indicator, degraded/down descriptions, ETA, known issues show/hide, 404 cases, info link, ARIA, closed repairs filtered, hero class)
- Task 10: 9 equipment info view tests (no auth, name, docs by category, download links, photos, external links target=_blank, 404 cases, empty state, back link)

### Change Log

- 2026-02-16: Implemented Story 4.3 — QR code service, equipment page, info page, file serving, CSS, and comprehensive tests (692 total, 0 regressions)

### File List

**New files:**
- esb/services/qr_service.py
- esb/templates/public/equipment_page.html
- esb/templates/public/equipment_info.html
- tests/test_services/test_qr_service.py

**Modified files:**
- esb/views/public.py
- esb/static/css/app.css
- requirements.txt
- tests/test_views/test_public_views.py
- .gitignore
- _bmad-output/implementation-artifacts/sprint-status.yaml
