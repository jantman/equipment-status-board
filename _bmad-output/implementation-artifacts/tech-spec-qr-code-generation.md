---
title: 'QR Code Generation for Equipment'
slug: 'qr-code-generation'
created: '2026-04-20'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - 'Python 3.14'
  - 'Flask 3.1'
  - 'Flask-WTF (CSRF enforced; disabled in tests)'
  - 'Flask-Login (@login_required, @role_required)'
  - 'SQLAlchemy (via Flask-SQLAlchemy, not used in QR flow)'
  - 'Jinja2 (Bootstrap 5 locally-bundled)'
  - 'qrcode[pil]>=8.0 (already in requirements.txt; pulls Pillow)'
  - 'pytest + pytest factories (make_area, make_equipment; staff_client, tech_client)'
files_to_modify:
  - 'esb/config.py (add ESB_BASE_URL to Config)'
  - '.env.example (add ESB_BASE_URL line)'
  - 'esb/services/qr_service.py (full rewrite)'
  - 'esb/utils/text.py (NEW — slugify_filename)'
  - 'esb/forms/equipment_forms.py (add QRGenerateForm)'
  - 'esb/views/equipment.py (add qr, qr_preview routes)'
  - 'esb/templates/equipment/qr.html (NEW)'
  - 'esb/templates/equipment/detail.html (add button in action row)'
  - 'esb/static/fonts/DejaVuSans-Bold.ttf (NEW — vendored font)'
  - 'esb/static/js/app.js (append preview updater)'
  - 'esb/static/qrcodes/ (DELETE directory)'
  - '.gitignore (remove qrcodes/*.png line)'
  - 'docs/administrators.md (add ESB_BASE_URL env-var row)'
  - 'docs/staff.md (add QR Code Labels section)'
  - 'docs/images/qr-generation.png (NEW screenshot)'
  - 'tests/test_services/test_qr_service.py (replace contents)'
  - 'tests/test_views/test_equipment_views.py (append QR tests)'
  - 'tests/test_utils/test_text.py (NEW)'
code_patterns:
  - 'Service layer: views are thin; business logic in services; dependency flow views → services → models'
  - 'Services imported via module (from esb.services import qr_service); services/__init__.py is empty'
  - 'Forms grouped by domain in esb/forms/{domain}_forms.py; FlaskForm subclasses with explicit validators'
  - 'Views use try/except ValidationError → abort(404) for missing records'
  - 'Flash category is danger (NOT error) per prior story; flash + redirect on configuration error'
  - 'Mutation logging via log_mutation(event, user, data) — NOT called for read-only operations'
  - 'Jinja filters registered in esb/utils/filters.py; CSRF token via {{ csrf_token() }} in templates'
  - 'Single app.css and app.js — no per-page assets'
  - 'snake_case templates; underscore-prefix for partials'
test_patterns:
  - 'pytest with SQLite in-memory (TestingConfig); CSRF disabled in tests (WTF_CSRF_ENABLED=False)'
  - 'Fixtures in tests/conftest.py: app, client, db, make_area, make_equipment, staff_client, tech_client, staff_user, tech_user, capture (mutation logger)'
  - 'Service tests live at tests/test_services/test_{service}.py with TestX class containers per function'
  - 'View tests at tests/test_views/test_{blueprint}_views.py; assert on resp.status_code and resp.data bytes'
  - 'Util tests at tests/test_utils/test_{module}.py'
  - 'No make_user/member_client fixture — use staff_client and tech_client both to prove any-role access'
issue: 14
---

# Tech-Spec: QR Code Generation for Equipment

**Created:** 2026-04-20
**GitHub Issue:** #14

## Overview

### Problem Statement

Makers need printable QR code labels/stickers to attach to physical equipment so that anyone can scan them to reach the equipment's public page (`/public/equipment/<id>`). Today there is no admin UI for generating these images: `esb/services/qr_service.py` only generates a default-size PNG to disk and is not wired to any view. There is also no way to configure the application's externally-accessible base URL — inside a container the request host can be unreliable, so the URL encoded in every QR code needs to come from explicit configuration. Additionally, the labels must support optional equipment-name text above and URL text below the QR image, with text centered and constrained to ≤120% of the image width so the label prints legibly at any size.

### Solution

1. Introduce an `ESB_BASE_URL` environment variable loaded on `esb.config.Config` (same pattern as other env-backed settings such as `UPLOAD_PATH`, `SLACK_BOT_TOKEN`). The QR URL is always `{ESB_BASE_URL}/public/equipment/<id>`.
2. Replace the current on-disk QR service with an in-memory renderer that composes a single PIL image containing optional name text, the QR code, and optional URL text — with text auto-scaled to ≤120% of QR width — and returns the image bytes. No caching; generate on demand.
3. Add a single-source `QR_SIZE_PRESETS` constant listing common print sizes (stickers + US label/page sizes) so future sizes can be added in one place.
4. Add a new authenticated route `GET/POST /equipment/<id>/qr` (any logged-in user) that shows a form with size/name-toggle/URL-toggle, renders a live preview, and provides a PNG download.
5. Add a "Generate QR Code" button on the equipment detail page linking to the new route.
6. Update `docs/administrators.md` with the `ESB_BASE_URL` env var entry and `docs/staff.md` with QR generation instructions plus a new screenshot `docs/images/qr-generation.png`.
7. Comprehensive tests covering: QR payload correctness (scan-decode roundtrip), output image dimensions matching the selected preset at 300 DPI, text inclusion/omission toggles, text-width cap behavior, permission (any logged-in user, anonymous denied), and view integration.

### Scope

**In Scope:**
- `ESB_BASE_URL` config entry + `.env.example` update + administrators-guide entry
- Rewrite of `esb/services/qr_service.py` to return image bytes, with composable name/URL text rendering
- Single-sourced `QR_SIZE_PRESETS` list (label + sticker + page sizes, 300 DPI)
- New WTForm + view + template for `/equipment/<id>/qr` (GET form, POST returns PNG download; preview on GET via `<img>` that POSTs to a separate preview endpoint or via a `preview=1` query — exact shape decided in Step 2)
- "Generate QR Code" button on `equipment/detail.html` (any logged-in user, hidden for archived equipment)
- Font auto-shrink so rendered text width ≤ 120% of QR width; single-line rendering
- Removal of dead code: on-disk QR caching (`get_qr_code_path`, `generate_all_qr_codes`, `esb/static/qrcodes/` usage) — not referenced outside tests
- Unit + view tests (service-level payload/dimensions/text; view-level auth/access/download content-type)
- Staff-guide section + new screenshot
- Commit message + PR description calling out the new env var per issue instructions

**Out of Scope:**
- PDF output (noted as possible future work)
- Multi-code-per-page sheet layouts (e.g. Avery full-sheet auto-fill)
- Storing generated QR images server-side (always generated on demand)
- AppConfig/DB-backed override of the base URL (env-var only for now)
- Bulk "generate all QR codes" workflows
- Internationalization of the rendered label text

## Context for Development

### Technical Preferences & Constraints

- **Stack:** Python 3.14, Flask, Flask-WTF, Jinja2, SQLAlchemy (unused here), existing `qrcode[pil]>=8.0` dependency (already in `requirements.txt`). Pillow comes via `qrcode[pil]`.
- **Permissions:** Route uses `@login_required` only (no `@role_required`) — any role can generate.
- **Config pattern:** Read env var on the `Config` class (`ESB_BASE_URL = os.environ.get('ESB_BASE_URL', '')`). Accessed via `current_app.config['ESB_BASE_URL']`. No DB override.
- **Base URL normalization & empty-value behavior:** The **view** reads `current_app.config['ESB_BASE_URL']` and `rstrip('/')`s it (so `http://esb.example.com:8080/` → `http://esb.example.com:8080`). If empty/unset, the `/equipment/<id>/qr` view flashes a `danger` message ("ESB_BASE_URL is not configured — contact your administrator.") and redirects back to the equipment detail page. The "Generate QR Code" control on the equipment detail page is rendered as a normal anchor when configured, and as a disabled `<button>` with tooltip "ESB_BASE_URL not configured" when empty. The service does **not** read Flask config — it is pure and takes `base_url` as a keyword argument.
- **Size presets:** Centralized in `esb/services/qr_service.py` — `@dataclass QRSizePreset(key: str, label: str, width_in: float, height_in: float)`, exposed as both `QR_SIZE_PRESETS: tuple[QRSizePreset, ...]` (ordered for the dropdown) and `QR_PRESETS_BY_KEY: dict[str, QRSizePreset]` (for view-side lookup on form submit). Rendering is fixed at **300 DPI** for all presets. Adding a new size is a single-file edit. File-size trade-off acknowledged: 8.5"×11" at 300 DPI = 2550×3300 pixels, ~8 MB PNG — acceptable for occasional admin downloads; no dynamic DPI selection in this change.
- **Rendering pattern:** Use `qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4)`. Build the matrix with `make_image(...).convert('RGB')`, then resize to the target QR pixel dimensions using `Image.NEAREST` — **never LANCZOS** (anti-aliasing blurs module edges and reduces scannability). Compose the final image on a white `Image.new('RGB', (canvas_w_px, canvas_h_px), 'white')`. Dimensions: `canvas_w_px = round(width_in * 300)`, `canvas_h_px = round(height_in * 300)`, `font_px = round(pt * 300 / 72)`.
- **Aspect-ratio / layout rule:** Text rows reserve a fraction of canvas height — 0 if disabled, otherwise 15% for name (top) and 15% for URL (bottom). The QR is rendered as a square sized to `min(canvas_w_px, canvas_h_px - reserved_text_px) - margin` and centered horizontally in the canvas, vertically positioned between the (possibly zero-height) text rows. This rule applies uniformly from 1"×1" stickers up to 8.5"×11" pages and to wide Avery 5160 labels (a legible small square QR with optional text above/below — acceptable for first release; sidebar layouts can follow later if needed).
- **Text constraints:** (a) single line; (b) rendered text pixel width ≤ 120% of the QR pixel width — shrink the font until it fits; (c) minimum font size **12 pt** floor; (d) if the text still exceeds the cap at the minimum size, truncate with an ellipsis (`…`) until it fits. Width is measured via `ImageDraw.textbbox((0,0), text, font=font)`. Both `include_name` and `include_url` default OFF.
- **Vendored font:** Commit `DejaVuSans-Bold.ttf` to `esb/static/fonts/` (Bitstream Vera / DejaVu license — redistributable) to make rendering deterministic across OS images. Service loads via `ImageFont.truetype(os.path.join(current_app.static_folder, 'fonts', 'DejaVuSans-Bold.ttf'), font_px)`. No `load_default()` fallback needed once the font is vendored.
- **Service API (clean break, new names):** Single public function `render_qr_png(equipment, preset, *, include_name=False, include_url=False, base_url) -> bytes` — returns PNG bytes. `preset` is a `QRSizePreset` instance (view does the key→preset lookup via `QR_PRESETS_BY_KEY`). **Delete** `generate_qr_code`, `get_qr_code_path`, and `generate_all_qr_codes`; these are not referenced outside the service and its tests. Also delete the `esb/static/qrcodes/` directory (and its `.gitkeep`).
- **Route shape:** A single route `GET/POST /equipment/<int:id>/qr` handles both the form render (GET) and the PNG download (POST). Preview mechanism — deferred to Step 2.
- **Form placement:** `QRGenerateForm(FlaskForm)` is added to the existing `esb/forms/equipment_forms.py` (matches domain grouping). Fields: `size = SelectField(choices=[(p.key, p.label) for p in QR_SIZE_PRESETS], validators=[DataRequired()])`, `include_name = BooleanField(default=False)`, `include_url = BooleanField(default=False)`.
- **Response:** `flask.send_file(io.BytesIO(png_bytes), mimetype='image/png', as_attachment=True, download_name=f'qr-{equipment.id}-{slugify_filename(equipment.name)}.png')`.
- **Slug helper placement:** Step 2 identifies the best existing module in `esb/utils/` for `slugify_filename(name)` → `re.sub(r'[^A-Za-z0-9-]+', '-', name).strip('-')[:50] or 'equipment'`. If none fits, create `esb/utils/text.py`. Unit-tested.
- **Audit logging:** QR generation is read-only. Explicitly **no** `log_mutation()` call — this is intentional and should be noted in a brief code comment on the view so reviewers don't flag the absence.
- **Architecture rules (from CLAUDE.md + prior story):** service layer holds all business logic; views are thin; no new models; single `app.css`/`app.js` only; Flask-WTF with CSRF.
- **Docs:** Administrators doc table — add `ESB_BASE_URL` with **Required: Yes** (empty value disables the feature). Staff guide gets its own `## QR Code Labels` section with a new screenshot `docs/images/qr-generation.png`.
- **Testing:** pytest with SQLite in-memory. Service tests verify the QR payload by round-tripping: build a fresh `qrcode.QRCode`, add the expected URL, call `get_matrix()`, and compare against `qrcode.QRCode.get_matrix()` extracted from reading back the generated PNG with Pillow + parsing module-to-module. Image-size assertions compare `Image.open(BytesIO(result)).size` against the preset's `(width_in*300, height_in*300)`. `pyzbar` is not used (unavailable per prior story 4.3 experience).
- **Commit convention:** "Issue #14: …" prefix (per project memory).

### Codebase Patterns (confirmed)

- Blueprint URL prefix: `/equipment` (registered in `esb/__init__.py` via `equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')`). New routes will be `/equipment/<int:id>/qr` and `/equipment/<int:id>/qr/preview`.
- Views catch `ValidationError` from services (used as a generic "not found / invalid") and `abort(404)`; NO `EquipmentNotFound` class (the story 4.3 context was out-of-date).
- Equipment detail-page action buttons live in a `<div class="d-flex gap-2">` inside `{% if not equipment.is_archived %}` — new QR button goes in that container.
- Gitignore already contains `esb/static/qrcodes/*.png` (line 193). When removing the directory, also remove this line from `.gitignore`.
- Local host has `/usr/share/fonts/TTF/DejaVuSans-Bold.ttf` (Arch), but the production Dockerfile is `python:3.14-slim` which does **not** include DejaVu fonts. Vendored font at `esb/static/fonts/DejaVuSans-Bold.ttf` is the correct approach.
- Existing `esb/static/js/app.js` is the single JS file for the app — append the preview-updater block here (no new JS files).
- Existing `esb/static/qrcodes/` contains stray `1.png`, `2.png`, `3.png` from prior test runs. Directory + files will be removed.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/config.py` | Add `ESB_BASE_URL = os.environ.get('ESB_BASE_URL', '')` on the `Config` class |
| `esb/forms/equipment_forms.py` | Append `QRGenerateForm(FlaskForm)` next to other equipment forms |
| `esb/views/equipment.py` | Add two routes: `GET/POST /qr` (form + attachment download) and `GET /qr/preview` (inline PNG) |
| `esb/services/qr_service.py` | Full rewrite — `@dataclass QRSizePreset`, `QR_SIZE_PRESETS`, `QR_PRESETS_BY_KEY`, `render_qr_png(...)`; delete old functions |
| `esb/utils/text.py` | NEW — `slugify_filename(name)` helper |
| `esb/utils/filters.py` | Reference only (no change) — shows Jinja filter registration pattern |
| `esb/utils/logging.py` | Reference only — confirms QR view should NOT call `log_mutation()` |
| `esb/templates/equipment/detail.html` | Add "Generate QR Code" button in action-row `d-flex gap-2` container; disabled `<button>` if `ESB_BASE_URL` empty |
| `esb/templates/equipment/qr.html` | NEW — extends `base.html`, renders the form + inline preview `<img id="qr-preview">` |
| `esb/static/fonts/DejaVuSans-Bold.ttf` | NEW — vendored TTF for deterministic text rendering (DejaVu/Bitstream Vera license) |
| `esb/static/js/app.js` | Append vanilla-JS preview updater (listens for form `change` events, updates `<img src>`) |
| `esb/static/qrcodes/` | **Delete directory** (no longer used) |
| `.env.example` | Add `ESB_BASE_URL=http://localhost:5000` with explanatory comment |
| `.gitignore` | Remove `esb/static/qrcodes/*.png` line |
| `docs/administrators.md` | Add `ESB_BASE_URL` row to "Environment Variable Reference" table |
| `docs/staff.md` | Add `## QR Code Labels` section with usage steps |
| `docs/images/qr-generation.png` | NEW — screenshot of the QR form page |
| `tests/test_services/test_qr_service.py` | Replace contents — test presets, payload correctness, image dims, text toggles, font-fit shrink/truncate |
| `tests/test_views/test_equipment_views.py` | Append `TestEquipmentQR` class — GET form, POST download, GET preview, auth, empty-config behavior, archived behavior |
| `tests/test_utils/test_text.py` | NEW — `slugify_filename` tests |
| `tests/conftest.py` | Reference only — use existing fixtures `make_area`, `make_equipment`, `staff_client`, `tech_client`, `client` |

### Technical Decisions (resolved in Step 2)

1. **Preview mechanism — two-route split.**
   - `GET/POST /equipment/<int:id>/qr`: GET renders the form page (with an inline preview using sensible defaults); POST validates form and returns PNG as attachment.
   - `GET /equipment/<int:id>/qr/preview?size=KEY&include_name=1&include_url=1`: returns the PNG inline (no attachment). Read-only GET — no CSRF needed.
   - A small vanilla-JS block in `app.js` listens for `change` events on the form controls and updates `document.getElementById('qr-preview').src` to the preview URL with current query params. **Rationale:** clean separation of concerns (attachment download vs. inline preview), no CSRF complications on the preview path, matches the project's "vanilla JS only, single app.js" rule, graceful degradation (without JS, the user just sees the initial preview and submits to download).

2. **Service API signature — pure function, preset object in.**
   - `render_qr_png(equipment: Equipment, preset: QRSizePreset, *, include_name: bool = False, include_url: bool = False, base_url: str) -> bytes`.
   - View does the key→preset lookup via `QR_PRESETS_BY_KEY[form.size.data]`, and reads/normalizes `ESB_BASE_URL`. Service never touches Flask config.

3. **Size presets — initial list (keys + display labels + inch dimensions).**
   | key | label | w (in) | h (in) |
   |---|---|---|---|
   | `sticker_1` | 1"×1" sticker | 1.0 | 1.0 |
   | `sticker_1_5` | 1.5"×1.5" sticker | 1.5 | 1.5 |
   | `sticker_2` | 2"×2" sticker | 2.0 | 2.0 |
   | `sticker_3` | 3"×3" sticker | 3.0 | 3.0 |
   | `sticker_4` | 4"×4" sticker | 4.0 | 4.0 |
   | `avery_5160` | Avery 5160 label (2.625"×1") | 2.625 | 1.0 |
   | `avery_5163` | Avery 5163 label (4"×2") | 4.0 | 2.0 |
   | `letter` | US Letter page (8.5"×11") | 8.5 | 11.0 |

4. **Form fields.**
   - `size: SelectField(choices=[(p.key, p.label) for p in QR_SIZE_PRESETS], validators=[DataRequired()], default='sticker_2')`
   - `include_name: BooleanField('Include equipment name above QR', default=False)`
   - `include_url: BooleanField('Include URL below QR', default=False)`
   - `submit: SubmitField('Download QR Code')`

5. **`esb/utils/text.py` location.** No existing string/text helper module in `esb/utils/`. Create `esb/utils/text.py` with `slugify_filename(name: str) -> str`. Tested at `tests/test_utils/test_text.py`.

6. **Button placement and disabled state.**
   - Insert a "Generate QR Code" control in the `d-flex gap-2` action-row container in `detail.html`, before the "Edit"/"Archive" controls, *inside* the `{% if not equipment.is_archived %}` block (so archived equipment hides it, consistent with other actions).
   - When `config['ESB_BASE_URL']` is empty: render a `<button type="button" class="btn btn-outline-secondary btn-sm" disabled title="ESB_BASE_URL not configured">Generate QR Code</button>`. When set: render `<a class="btn btn-outline-secondary btn-sm" href="{{ url_for('equipment.qr', id=equipment.id) }}">Generate QR Code</a>`.

7. **QR decode verification in tests.** Use `qrcode` library's own matrix rebuild (compare matrices of an independently-built QR with the expected URL vs. the rendered PNG parsed back into a matrix via Pillow pixel sampling at the known module grid). `pyzbar` is not used — prior story 4.3 confirmed unavailability.

## Implementation Plan

### Tasks

Ordered by dependency — earlier tasks are prerequisites of later ones.

- [ ] **Task 1: Add `ESB_BASE_URL` to Flask `Config`.**
  - File: `esb/config.py`
  - Action: Add `ESB_BASE_URL = os.environ.get('ESB_BASE_URL', '')` to the `Config` class after `SECRET_KEY`.
  - Notes: Inherited automatically by `DevelopmentConfig`, `TestingConfig`, `ProductionConfig`, etc. No per-env override needed.

- [ ] **Task 2: Document `ESB_BASE_URL` in `.env.example`.**
  - File: `.env.example`
  - Action: After the `SECRET_KEY` block, add:
    ```
    # Base URL of this ESB instance — used as the prefix for QR code targets.
    # Must be the externally-reachable URL that members' phones can hit to open equipment pages.
    # Required to enable QR code generation. No trailing slash is required (it is stripped).
    ESB_BASE_URL=http://localhost:5000
    ```
  - Notes: The default `http://localhost:5000` lets local dev work out-of-the-box; production must set a real URL.

- [ ] **Task 3: Create `slugify_filename` helper.**
  - File: `esb/utils/text.py` (NEW)
  - Action: Create module with:
    ```python
    """Text helpers."""
    import re

    def slugify_filename(name: str) -> str:
        """Produce a filesystem-safe slug from a human name for use in download filenames.

        Collapses any run of non [A-Za-z0-9-] characters to a single hyphen, strips
        leading/trailing hyphens, truncates to 50 chars, and falls back to 'equipment'
        if the result is empty.
        """
        slug = re.sub(r'[^A-Za-z0-9-]+', '-', name or '').strip('-')[:50]
        return slug or 'equipment'
    ```
  - Notes: No existing module in `esb/utils/` fits; create a new one. Keep tiny and focused.

- [ ] **Task 4: Create `tests/test_utils/test_text.py`.**
  - File: `tests/test_utils/test_text.py` (NEW)
  - Action: Write a `TestSlugifyFilename` class with cases: normal alnum name; spaces → hyphens; unicode stripped; multi-run punctuation collapsed; empty string → `'equipment'`; name longer than 50 chars truncated; leading/trailing punctuation stripped; names consisting only of punctuation → `'equipment'`.

- [ ] **Task 5: Vendor the DejaVu Sans Bold font.**
  - File: `esb/static/fonts/DejaVuSans-Bold.ttf` (NEW — binary)
  - Action: Create directory `esb/static/fonts/`. Copy `DejaVuSans-Bold.ttf` into it (either from `/usr/share/fonts/TTF/DejaVuSans-Bold.ttf` on the dev host or the upstream DejaVu release). The DejaVu/Bitstream Vera license permits redistribution.
  - Notes: Required because the `python:3.14-slim` container does not ship DejaVu fonts. Deterministic rendering across OS images.

- [ ] **Task 6: Rewrite `esb/services/qr_service.py`.**
  - File: `esb/services/qr_service.py`
  - Action: Replace the entire file with:
    - `@dataclass(frozen=True) class QRSizePreset` with `key, label, width_in, height_in`.
    - `QR_SIZE_PRESETS: tuple[QRSizePreset, ...]` populated with the 8 presets from the Technical Decisions table (in that order).
    - `QR_PRESETS_BY_KEY: dict[str, QRSizePreset] = {p.key: p for p in QR_SIZE_PRESETS}`.
    - `render_qr_png(equipment, preset, *, include_name=False, include_url=False, base_url: str) -> bytes`:
      1. Compute `canvas_w_px = round(preset.width_in * 300)`, `canvas_h_px = round(preset.height_in * 300)`.
      2. Compute `reserved_top = round(canvas_h_px * 0.15) if include_name else 0` and same for `reserved_bottom` with `include_url`.
      3. Compute `qr_px = min(canvas_w_px, canvas_h_px - reserved_top - reserved_bottom) - margin` with a small margin (e.g. `round(canvas_w_px * 0.02)`, min 4 px).
      4. Build the QR: `qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4); qr.add_data(f'{base_url}/public/equipment/{equipment.id}'); qr.make(fit=True); qr_img = qr.make_image(fill_color='black', back_color='white').convert('RGB').resize((qr_px, qr_px), Image.NEAREST)`.
      5. Compose on white canvas: `canvas = Image.new('RGB', (canvas_w_px, canvas_h_px), 'white')`.
      6. Paste QR centered horizontally at `y = reserved_top + ((canvas_h_px - reserved_top - reserved_bottom) - qr_px) // 2`.
      7. If `include_name` or `include_url`: for each text row, compute max row height = `reserved_top` / `reserved_bottom`; call a private `_fit_text(text, max_width_px=int(qr_px * 1.2), max_height_px, font_path)` helper that binary-searches / steps font size from `max_height_px` down to a minimum of `round(12 * 300 / 72) = 50 px` and returns `(ImageFont, truncated_text)`; render centered horizontally and vertically within the row using `ImageDraw.text()`.
      8. Save to `BytesIO` as PNG, return `.getvalue()`.
    - Private helper `_fit_text(text, max_width_px, max_height_px, font_path) -> (ImageFont, str)`:
      - Start at `size = max_height_px`; while `size >= round(12 * 300 / 72)`: build font; measure via `ImageDraw(...).textbbox((0,0), text, font)`; if `width <= max_width_px`: return `(font, text)`; else `size -= round(max_height_px * 0.05)`.
      - At min size: truncate with ellipsis `'…'` — loop reducing text length by 1 char until width fits; return `(font, truncated_or_original)`.
    - **Delete** all prior functions (`generate_qr_code`, `get_qr_code_path`, `generate_all_qr_codes`).
  - Notes: Use `Image.NEAREST` (critical). Font path = `os.path.join(current_app.static_folder, 'fonts', 'DejaVuSans-Bold.ttf')`. No `log_mutation()`.

- [ ] **Task 7: Add `QRGenerateForm` to `equipment_forms.py`.**
  - File: `esb/forms/equipment_forms.py`
  - Action: Append at end:
    ```python
    from esb.services.qr_service import QR_SIZE_PRESETS

    class QRGenerateForm(FlaskForm):
        """Form for QR code generation options."""
        size = SelectField(
            'Size',
            choices=[(p.key, p.label) for p in QR_SIZE_PRESETS],
            validators=[DataRequired()],
            default='sticker_2',
        )
        include_name = BooleanField('Include equipment name above QR', default=False)
        include_url = BooleanField('Include URL below QR', default=False)
        submit = SubmitField('Download QR Code')
    ```
  - Notes: Also add `BooleanField` to the existing `from wtforms import …` import.

- [ ] **Task 8: Add `qr` and `qr_preview` routes to `esb/views/equipment.py`.**
  - File: `esb/views/equipment.py`
  - Action: Add two routes:
    ```python
    @equipment_bp.route('/<int:id>/qr', methods=['GET', 'POST'])
    @login_required
    def qr(id):
        """QR code generation page. Read-only — no mutation logging."""
        try:
            eq = equipment_service.get_equipment(id)
        except ValidationError:
            abort(404)
        if eq.is_archived:
            abort(404)

        base_url = (current_app.config.get('ESB_BASE_URL') or '').rstrip('/')
        if not base_url:
            flash('ESB_BASE_URL is not configured — contact your administrator.', 'danger')
            return redirect(url_for('equipment.detail', id=id))

        form = QRGenerateForm()
        if form.validate_on_submit():
            preset = qr_service.QR_PRESETS_BY_KEY[form.size.data]
            png_bytes = qr_service.render_qr_png(
                eq, preset,
                include_name=form.include_name.data,
                include_url=form.include_url.data,
                base_url=base_url,
            )
            filename = f'qr-{eq.id}-{slugify_filename(eq.name)}.png'
            return send_file(
                io.BytesIO(png_bytes),
                mimetype='image/png',
                as_attachment=True,
                download_name=filename,
            )
        return render_template('equipment/qr.html', equipment=eq, form=form)


    @equipment_bp.route('/<int:id>/qr/preview')
    @login_required
    def qr_preview(id):
        """Inline PNG preview for the QR form. Query params: size, include_name, include_url."""
        try:
            eq = equipment_service.get_equipment(id)
        except ValidationError:
            abort(404)
        if eq.is_archived:
            abort(404)

        base_url = (current_app.config.get('ESB_BASE_URL') or '').rstrip('/')
        if not base_url:
            abort(404)

        size_key = request.args.get('size', 'sticker_2')
        preset = qr_service.QR_PRESETS_BY_KEY.get(size_key)
        if preset is None:
            abort(400)
        include_name = request.args.get('include_name') in ('1', 'true', 'on')
        include_url = request.args.get('include_url') in ('1', 'true', 'on')

        png_bytes = qr_service.render_qr_png(
            eq, preset,
            include_name=include_name,
            include_url=include_url,
            base_url=base_url,
        )
        return send_file(io.BytesIO(png_bytes), mimetype='image/png')
    ```
  - Notes: Add required imports at top of file: `import io`, `from flask import send_file`, `from esb.forms.equipment_forms import QRGenerateForm`, `from esb.services import qr_service`, `from esb.utils.text import slugify_filename`. The `request` import already exists.

- [ ] **Task 9: Create `esb/templates/equipment/qr.html`.**
  - File: `esb/templates/equipment/qr.html` (NEW)
  - Action: Template extending `base.html`:
    - Breadcrumb: Registry → equipment detail → QR Code.
    - `<h1>Generate QR Code — {{ equipment.name }}</h1>`.
    - POST form with CSRF token, size select, include_name checkbox, include_url checkbox, submit button ("Download QR Code").
    - Inline preview block: `<img id="qr-preview" alt="QR preview" src="{{ url_for('equipment.qr_preview', id=equipment.id, size=form.size.data or 'sticker_2') }}" class="img-fluid border" style="max-width: 400px;">`.
    - Data attribute on the `<form>` like `data-preview-base="{{ url_for('equipment.qr_preview', id=equipment.id) }}"` for JS.
  - Notes: Form should have `id="qr-form"` so the JS in `app.js` can select it.

- [ ] **Task 10: Add "Generate QR Code" control to `equipment/detail.html`.**
  - File: `esb/templates/equipment/detail.html`
  - Action: Inside the `<div class="d-flex gap-2">` block (within `{% if not equipment.is_archived %}`), insert *before* the "Report Issue" / "Edit" buttons:
    ```jinja2
    {% if config['ESB_BASE_URL'] %}
    <a href="{{ url_for('equipment.qr', id=equipment.id) }}" class="btn btn-outline-secondary btn-sm">Generate QR Code</a>
    {% else %}
    <button type="button" class="btn btn-outline-secondary btn-sm" disabled title="ESB_BASE_URL not configured">Generate QR Code</button>
    {% endif %}
    ```
  - Notes: Control visible to any logged-in user (no role gate), hidden when equipment is archived (enclosing `if`), shown disabled if config empty.

- [ ] **Task 11: Append live-preview JS to `esb/static/js/app.js`.**
  - File: `esb/static/js/app.js`
  - Action: Append a small IIFE:
    ```javascript
    (function () {
      var form = document.getElementById('qr-form');
      if (!form) return;
      var img = document.getElementById('qr-preview');
      var base = form.getAttribute('data-preview-base');
      function update() {
        var size = form.querySelector('[name="size"]').value;
        var incName = form.querySelector('[name="include_name"]').checked ? '1' : '';
        var incUrl = form.querySelector('[name="include_url"]').checked ? '1' : '';
        var params = new URLSearchParams({ size: size });
        if (incName) params.set('include_name', '1');
        if (incUrl) params.set('include_url', '1');
        img.src = base + '?' + params.toString();
      }
      form.addEventListener('change', update);
    })();
    ```
  - Notes: Vanilla JS, no build step. Gracefully no-ops on other pages.

- [ ] **Task 12: Remove the old on-disk cache directory and its gitignore entry.**
  - Files: `esb/static/qrcodes/` (DELETE directory and all contents), `.gitignore` (remove line `esb/static/qrcodes/*.png`).
  - Notes: Use `git rm -r esb/static/qrcodes/`. Edit `.gitignore` with Edit tool.

- [ ] **Task 13: Replace service tests.**
  - File: `tests/test_services/test_qr_service.py`
  - Action: Replace contents with a test module covering:
    - `TestQRSizePresets`: `QR_SIZE_PRESETS` has 8 entries; `QR_PRESETS_BY_KEY[k].key == k` for all; all keys unique; all dimensions positive.
    - `TestRenderQRPng::test_returns_png_bytes`: result is bytes, `Image.open(BytesIO(result)).format == 'PNG'`.
    - `TestRenderQRPng::test_dimensions_match_preset_at_300_dpi`: parametrized over a couple presets (e.g. `sticker_2`, `avery_5160`, `letter`) — `Image.open(...).size == (round(w_in*300), round(h_in*300))`.
    - `TestRenderQRPng::test_payload_contains_expected_url`: render with a known equipment + base_url; decode the QR by re-building a matrix with `qrcode.QRCode().add_data(expected_url).make(); compare to the matrix extracted from the rendered PNG via Pillow pixel sampling at the known module grid.
    - `TestRenderQRPng::test_trailing_slash_handled`: when `base_url` has trailing slash stripped upstream (parametrized `'http://x:5000'` vs `'http://x:5000/'` after rstrip) — the payload is identical; i.e. the service relies on normalized input.
    - `TestRenderQRPng::test_name_disabled_default`: default render vs `include_name=True` differ in pixel output (there is text drawn).
    - `TestRenderQRPng::test_url_toggle`: include_url=True produces different output than include_url=False.
    - `TestRenderQRPng::test_text_width_cap_shrinks_font`: a very long equipment name is rendered at a font smaller than a max-size baseline (compare actual measured text width to `qr_px * 1.2`).
    - `TestRenderQRPng::test_text_truncated_at_min_font`: an equipment name that cannot fit at 12 pt is truncated with `…`. Verify by… (impl detail — could expose `_fit_text` for unit testing with `# noqa`-acceptable private-import, or test via a sentinel like asserting the rendered image's pixel count where text occurs is below some threshold).
    - `TestRenderQRPng::test_qr_uses_nearest_resize`: scan the rendered QR region for only black and white pixels (NEAREST produces no grayscale intermediate values; LANCZOS would). Assert no pixel has R,G,B all in (1..254).
  - Notes: Delete all prior tests (those reference removed functions).

- [ ] **Task 14: Append view tests to `tests/test_views/test_equipment_views.py`.**
  - File: `tests/test_views/test_equipment_views.py`
  - Action: Add `class TestEquipmentQR:` with tests:
    - `test_get_qr_form_staff`: `staff_client.get('/equipment/<id>/qr')` → 200, has size select, name checkbox, url checkbox, preview img.
    - `test_get_qr_form_tech`: same via `tech_client` → 200 (proves any-role access).
    - `test_get_qr_form_unauthenticated`: `client.get(...)` → 302 to login.
    - `test_get_qr_form_not_found`: missing id → 404.
    - `test_get_qr_form_archived_returns_404`: archived equipment → 404.
    - `test_get_qr_form_empty_base_url_redirects`: with `app.config['ESB_BASE_URL']=''`, GET → 302 to equipment.detail with flash.
    - `test_post_qr_download_returns_png_attachment`: POST with valid form → 200, content-type `image/png`, Content-Disposition attachment with filename `qr-<id>-<slug>.png`.
    - `test_post_qr_download_unknown_size_rejected`: POST with invalid size key → 200 with re-rendered form (WTForms SelectField rejects).
    - `test_get_qr_preview_png_inline`: `staff_client.get('/equipment/<id>/qr/preview?size=sticker_2')` → 200, content-type `image/png`, no attachment disposition.
    - `test_get_qr_preview_invalid_size_400`: bad size key → 400.
    - `test_get_qr_preview_empty_base_url_404`: config empty → 404.
    - `test_get_qr_preview_archived_404`: archived equipment → 404.
    - `test_detail_page_shows_generate_qr_button_when_configured`: sets `ESB_BASE_URL`, checks HTML contains link to `/qr`.
    - `test_detail_page_shows_disabled_generate_qr_button_when_unconfigured`: empty `ESB_BASE_URL`, checks HTML contains `disabled` button with `ESB_BASE_URL not configured` title.
    - `test_detail_page_hides_qr_button_when_archived`: archived equipment — no QR control rendered at all.
  - Notes: Use `monkeypatch` or direct `app.config['ESB_BASE_URL'] = 'http://test.example:5000'` on the `app` fixture. Default testing config has `ESB_BASE_URL=''` — set explicitly per test.

- [ ] **Task 15: Document `ESB_BASE_URL` in `docs/administrators.md`.**
  - File: `docs/administrators.md`
  - Action: Add a row to the "Environment Variable Reference" table near the top (after `SECRET_KEY` / `DATABASE_URL`):
    ```
    | `ESB_BASE_URL` | Externally-reachable base URL of this ESB instance. Used as the prefix for QR code target URLs. Must be set to enable QR code generation. Trailing slash is stripped. | Yes | _(empty)_ | `http://esb.example.com:8080` |
    ```
  - Notes: Also consider adding a short paragraph below the table noting that this cannot be determined inside a container and must be set explicitly.

- [ ] **Task 16: Add `## QR Code Labels` section to `docs/staff.md`.**
  - File: `docs/staff.md`
  - Action: Add a new section (anywhere after the "Using the Kanban Board" section — pick logical placement, e.g. under an "Equipment" heading) with:
    - Purpose of QR labels.
    - Who can generate them (any logged-in user).
    - Step-by-step: open equipment detail page → click "Generate QR Code" → choose a size from the dropdown → optionally toggle "Include equipment name above QR" / "Include URL below QR" → click "Download QR Code".
    - What to do if the button is disabled (contact administrator to set `ESB_BASE_URL`).
    - Brief note about print resolution (300 DPI across all sizes).
    - Embed the new screenshot with `![QR Code Generation](images/qr-generation.png)`.

- [ ] **Task 17: Capture the screenshot `docs/images/qr-generation.png`.**
  - File: `docs/images/qr-generation.png` (NEW)
  - Action: Start the dev server, log in, navigate to `/equipment/<id>/qr`, take a browser screenshot of the form with the preview visible, save as PNG to `docs/images/qr-generation.png`.
  - Notes: Other screenshots in `docs/images/` set the style baseline — match dimensions/aspect.

- [ ] **Task 18: Run `make lint` and `make test`; fix any regressions.**
  - Files: N/A (verification only).
  - Action: Zero lint errors; all tests pass (existing + new). No regressions in unrelated tests.

- [ ] **Task 19: Commit and push in focused commits; open PR.**
  - Files: N/A
  - Action: Follow project commit conventions: prefix all commit subjects with `Issue #14: …`. Suggested split (single-commit-per-concern, final PR ties together):
    1. `Issue #14: add ESB_BASE_URL config and .env.example entry`
    2. `Issue #14: rewrite qr_service with size presets and in-memory renderer`
    3. `Issue #14: add QR generation UI to equipment admin page`
    4. `Issue #14: document ESB_BASE_URL and QR generation in admin/staff guides`
    5. `Issue #14: remove on-disk QR cache directory and gitignore entry`
  - PR description: explicitly call out the new `ESB_BASE_URL` environment variable, its required nature, behavior when unset, and the administrators-guide reference (per the issue's own instructions).

### Acceptance Criteria

- [ ] **AC 1 — Config loaded.** Given `ESB_BASE_URL=http://esb.example.com:8080` is set in the process environment, when the Flask app starts, then `app.config['ESB_BASE_URL']` equals `'http://esb.example.com:8080'`.
- [ ] **AC 2 — Normalization.** Given `ESB_BASE_URL=http://esb.example.com:8080/` (with trailing slash), when a QR is generated, then the encoded URL is exactly `http://esb.example.com:8080/public/equipment/<id>` (no double slash).
- [ ] **AC 3 — Empty-config UI (disabled button).** Given `ESB_BASE_URL=''`, when a logged-in user views `/equipment/<id>`, then the "Generate QR Code" control is rendered as a disabled `<button>` with tooltip "ESB_BASE_URL not configured".
- [ ] **AC 4 — Empty-config view redirect.** Given `ESB_BASE_URL=''`, when a logged-in user GETs `/equipment/<id>/qr`, then the response is a 302 to `/equipment/<id>` with a flash message "ESB_BASE_URL is not configured — contact your administrator.".
- [ ] **AC 5 — Any-role access (staff).** Given a staff user is logged in, when they GET `/equipment/<id>/qr`, then the response is 200 and contains a size `<select>`, an "Include equipment name" checkbox, an "Include URL" checkbox, and an `<img id="qr-preview">`.
- [ ] **AC 6 — Any-role access (technician).** Given a technician user is logged in, when they GET `/equipment/<id>/qr`, then the response is 200 (proving no role gate).
- [ ] **AC 7 — Anonymous denied.** Given no user is logged in, when a client GETs `/equipment/<id>/qr` or `/equipment/<id>/qr/preview`, then the response is a 302 to `/auth/login`.
- [ ] **AC 8 — Missing / archived equipment.** Given an equipment id that does not exist OR is archived, when a logged-in user GETs `/equipment/<id>/qr` or `/equipment/<id>/qr/preview`, then the response is 404.
- [ ] **AC 9 — Preset-size image output.** Given a configured `ESB_BASE_URL` and an existing equipment item, when a user POSTs `/equipment/<id>/qr` with `size=avery_5160`, then the response is a PNG attachment whose `Image.open(...).size == (round(2.625*300), round(1.0*300)) == (788, 300)`.
- [ ] **AC 10 — All presets produce correct dimensions.** For every preset `p` in `QR_SIZE_PRESETS`, when `render_qr_png(eq, p, base_url='http://x:5000')` is called, then the resulting `Image.size == (round(p.width_in*300), round(p.height_in*300))`.
- [ ] **AC 11 — QR payload correctness.** Given `ESB_BASE_URL='http://esb.example.com:8080'` and equipment id `42`, when a QR is generated, then decoding the QR matrix from the rendered PNG yields exactly `http://esb.example.com:8080/public/equipment/42`.
- [ ] **AC 12 — QR resize preserves hard edges.** Given a rendered QR PNG, when scanning all pixels in the QR region, then every pixel is either fully black `(0,0,0)` or fully white `(255,255,255)` — no anti-aliasing intermediates (confirms `Image.NEAREST`).
- [ ] **AC 13 — Text omitted by default.** Given `include_name=False` and `include_url=False`, when a QR is generated, then the top 15% and bottom 15% rows of the canvas contain only white pixels (no text).
- [ ] **AC 14 — Text included on demand.** Given `include_name=True`, when a QR is generated for equipment "Table Saw", then the top 15% of the canvas contains non-white pixels forming rasterized text.
- [ ] **AC 15 — Text width cap (≤ 120% of QR width).** Given an equipment name long enough that at maximum font size the text would exceed 120% of the QR pixel width, when `render_qr_png(..., include_name=True)` is called, then the rendered text's bounding-box width is ≤ 120% of the QR pixel width.
- [ ] **AC 16 — Minimum font floor + ellipsis truncation.** Given an equipment name whose text width at the 12-pt minimum font still exceeds 120% of QR width, when a QR is generated with `include_name=True`, then the rendered text ends with `…` and its bounding-box width is ≤ 120% of QR width.
- [ ] **AC 17 — Preview endpoint returns inline PNG.** Given a logged-in user, when they GET `/equipment/<id>/qr/preview?size=sticker_2&include_name=1&include_url=1`, then the response is 200 with `Content-Type: image/png` and no `Content-Disposition: attachment` header.
- [ ] **AC 18 — Preview endpoint validates size key.** Given a logged-in user, when they GET `/equipment/<id>/qr/preview?size=nonsense`, then the response is 400.
- [ ] **AC 19 — Download attachment naming.** Given equipment id `42` with name "Table Saw #1!", when a user submits the QR form, then the response's `Content-Disposition` filename is `qr-42-Table-Saw-1.png` (matches `slugify_filename`).
- [ ] **AC 20 — slugify_filename fallback.** Given an equipment name consisting only of punctuation (e.g. `"!!!"`), when `slugify_filename` is called, then the result is `'equipment'`.
- [ ] **AC 21 — Detail-page link (configured).** Given `ESB_BASE_URL` set and a non-archived equipment item, when a logged-in user views `/equipment/<id>`, then the page contains an `<a>` with `href="/equipment/<id>/qr"` and text "Generate QR Code".
- [ ] **AC 22 — Detail-page control hidden for archived.** Given an archived equipment item, when a logged-in user views `/equipment/<id>`, then no "Generate QR Code" control is rendered (disabled button or link).
- [ ] **AC 23 — Old service functions removed.** After implementation, grepping the codebase for `generate_qr_code`, `get_qr_code_path`, or `generate_all_qr_codes` yields only references in `_bmad-output/` (historical artifacts), not in `esb/` or `tests/`.
- [ ] **AC 24 — On-disk cache directory removed.** After implementation, `esb/static/qrcodes/` does not exist and `.gitignore` no longer contains the `esb/static/qrcodes/*.png` line.
- [ ] **AC 25 — Font vendored.** After implementation, `esb/static/fonts/DejaVuSans-Bold.ttf` exists in the repo, and `qr_service` loads it via `current_app.static_folder` (not an OS path).
- [ ] **AC 26 — Docs complete.** `docs/administrators.md` contains a row for `ESB_BASE_URL` in the "Environment Variable Reference" table; `docs/staff.md` contains a `## QR Code Labels` section referencing `images/qr-generation.png`; the screenshot file exists.
- [ ] **AC 27 — Lint + tests pass.** `make lint` exits 0; `make test` exits 0 with all new tests passing and zero regressions.

## Additional Context

### Dependencies

- **External libraries:** `qrcode[pil]>=8.0` (already in `requirements.txt` — no new dependency). Pillow (`PIL`) is pulled in transitively.
- **No new DB migrations.** No new models, no schema changes.
- **No new external services.** All generation is in-process.
- **Font license:** Vendoring `DejaVuSans-Bold.ttf` requires redistributing the Bitstream Vera / DejaVu font under its permissive license. Add a brief LICENSE note in `esb/static/fonts/` (a `LICENSE` or `NOTICE` text file alongside the TTF) if the project doesn't already track per-asset licenses.

### Testing Strategy

- **Unit tests (service):** `tests/test_services/test_qr_service.py` — presets, dimensions, QR payload correctness (matrix round-trip), text toggles, font auto-fit, NEAREST-preserves-edges. Tests use `tmp_path` or the in-memory `app` fixture; no on-disk state is needed because the service returns bytes.
- **Unit tests (util):** `tests/test_utils/test_text.py` — `slugify_filename` edge cases.
- **View / integration tests:** `tests/test_views/test_equipment_views.py::TestEquipmentQR` — form render, download response, preview response, auth, permission-by-role, empty-config behavior, archived behavior, detail-page button rendering in both states.
- **Manual testing:** Start dev server, set `ESB_BASE_URL`, visit `/equipment/<id>/qr`, verify live preview updates as options change, download at each size, print a Letter-size page, scan with a phone. Repeat with `ESB_BASE_URL` unset to verify disabled button + redirect behavior.
- **QR scannability (manual):** Print a 1"×1" sticker and scan from 3 inches — confirm the phone camera resolves the URL. (Per issue — correctness of QR generation is explicitly called out.)

### Notes

- **Known limitations:** First release uses a simple stacked layout (name above / QR / URL below). Avery 5160 (wide, short) gets a small central QR with text above/below — legible but not optimal. A sidebar layout variant could come in a follow-up. PDF output is also a noted future enhancement.
- **Pre-mortem risks not covered in-depth:** rate-limiting on QR generation (negligible — authenticated users only, image gen is cheap ~50 ms); potential memory pressure from 8.5"×11" 300-DPI renders under concurrent load (per-request ~8 MB, single-worker gunicorn with 2 threads in current Dockerfile — acceptable for an admin action).
- **Security posture:** `download_name` passes through `slugify_filename` which strips all non-alnum-hyphen characters — no path traversal. `send_file(BytesIO, ...)` does not touch the filesystem; no directory traversal risk. CSRF enforced on the download POST by Flask-WTF. Preview endpoint is read-only GET; no sensitive data is leaked (the generated PNG only encodes a public URL).
- **Future: bulk generation.** If bulk "print all areas" sheets become a need, the `QRSizePreset` list is the right extension point (add sheet presets) and a dedicated view can call `render_qr_png` in a loop. Out of scope for this issue.
- **Future: AppConfig override.** If makerspaces need to change the base URL without redeploying, promote `ESB_BASE_URL` from env-only to env-with-AppConfig-override. The view-side normalization helper would be the single place to extend. Out of scope for this issue.
