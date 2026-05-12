---
title: 'Configurable Sort Order for Areas'
slug: 'area-sort-order'
created: '2026-05-12'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - Python 3.14
  - Flask
  - Flask-SQLAlchemy
  - Alembic / Flask-Migrate
  - Flask-WTF / WTForms
  - Jinja2
  - pytest
files_to_modify:
  - esb/models/area.py
  - esb/forms/equipment_forms.py
  - esb/services/equipment_service.py
  - esb/services/status_service.py
  - esb/views/admin.py
  - esb/templates/admin/areas.html
  - esb/templates/admin/area_form.html
  - migrations/versions/<new>_add_area_sort_order.py
  - tests/test_services/test_equipment_service.py
  - tests/test_services/test_status_service.py
  - tests/test_views/test_admin_views.py
code_patterns:
  - Service layer: views never touch ORM; they call equipment_service / status_service.
  - log_mutation(action, actor, details_dict) is called inside service mutations.
  - Admin routes use @role_required('staff').
  - Alembic migrations use op.batch_alter_table for ALTERs (MariaDB-friendly).
  - Forms use Flask-WTF FlaskForm with explicit validators; views render via Jinja templates.
test_patterns:
  - Tests run against SQLite in-memory (TestingConfig).
  - Fixtures: app, client, db, staff_client, tech_client, make_equipment, make_area, make_repair_record (tests/conftest.py).
  - View tests use staff_client/tech_client fixtures; service tests construct via fixtures and assert ORM state.
---

# Tech-Spec: Configurable Sort Order for Areas

**Created:** 2026-05-12
**GitHub Issue:** #45 — "Sorting of areas on status pages"

## Overview

### Problem Statement

Issue #45: All multi-area views in the application — the public status dashboard, the kiosk display, the static status page export, the Areas admin table, and area dropdowns on equipment forms — currently render areas in alphabetical order by name. Staff at Decatur Makers want to control the order so that areas appear in a meaningful sequence (e.g., reflecting the physical layout or priority of the makerspace) rather than the accident of their names.

### Solution

Add a persistent integer `sort_order` column to the `areas` table (default `0`, NOT NULL). Allow staff to edit it through the existing Areas admin form. Replace the two `order_by(Area.name)` clauses in `equipment_service.list_areas()` and `status_service.get_area_status_dashboard()` with `order_by(Area.sort_order, Area.name)`. Because the status dashboard, kiosk view, static page export, and all area dropdowns funnel through one of these two service functions, every multi-area surface inherits the new ordering with no further changes.

### Scope

**In Scope:**
- Schema migration adding `areas.sort_order` (integer, NOT NULL, default 0).
- `Area.sort_order` model attribute.
- `sort_order` field on `AreaCreateForm` and `AreaEditForm`.
- Admin areas list page sorted by `(sort_order, name)` and showing the value.
- Reordering of `equipment_service.list_areas()` and `status_service.get_area_status_dashboard()` queries.
- Audit logging of `sort_order` changes through existing `log_mutation` plumbing.
- Updated tests covering the new ordering, form behavior, and migration default.

**Out of Scope:**
- Drag-and-drop reorder UI. A numeric input is sufficient for this iteration.
- Per-view custom orderings (one global order serves all surfaces).
- Reordering of equipment within an area.
- Reordering of archived areas (admin still lists active areas only; archived areas are not exposed).
- Slack views (Slack does not currently render multi-area lists; no changes needed).

## Context for Development

### Codebase Patterns

- **Service layer is authoritative.** Views and templates do not touch `db.session` directly — they call functions in `esb/services/*.py`. The two area queries to update both live in services: `equipment_service.list_areas()` (esb/services/equipment_service.py:22) and `status_service.get_area_status_dashboard()` (esb/services/status_service.py:212).
- **One funnel feeds every multi-area surface.** Public dashboard (esb/views/public.py:27), kiosk (esb/views/public.py:36), static page export (esb/services/static_page_service.py:50), and equipment-page rendering (esb/views/public.py:52) all call `status_service.get_area_status_dashboard()`. Admin areas list (esb/views/admin.py:168), equipment-form dropdowns (esb/views/equipment.py:43,79,167), and repair-form dropdowns (esb/views/repairs.py:115) all call `equipment_service.list_areas()`. Reordering the two service queries propagates to every consumer without further template work.
- **All admin mutations go through `log_mutation()`.** `equipment_service.update_area()` (esb/services/equipment_service.py:98-140) computes a `changes` dict (per-field old→new lists) and emits `log_mutation('area.updated', updated_by, {..., 'changes': changes})`. `sort_order` joins this pattern unchanged — append it to the diff calculation.
- **Admin routes are staff-only.** Every route in the Area Management block in `esb/views/admin.py` is decorated with `@role_required('staff')`. No change here.
- **Form classes are minimal and duplicated.** `AreaCreateForm` and `AreaEditForm` (esb/forms/equipment_forms.py:22 and :30) intentionally share field definitions rather than inherit — keep that pattern; add the same `sort_order` field to both. Use `IntegerField` from `wtforms` and a `NumberRange(min=0)` validator from `wtforms.validators`.
- **Templates iterate `areas` directly.** `admin/areas.html`, `public/status_dashboard.html`, `public/kiosk.html`, `public/static_page.html` all loop over an `areas` collection produced by a single service function. Public templates filter out empty areas with `selectattr('equipment')`; that filter is order-preserving, so the new sort flows through unchanged. Only the admin areas template needs a new display column.
- **Migrations use Alembic batch mode.** Existing migrations (e.g., `migrations/versions/2e0d6d8be171_add_areas_table.py`) wrap schema changes in `op.batch_alter_table(...)` for MariaDB compatibility. New migration must use the same pattern when adding the column, and use `server_default='0'` so existing rows backfill before the NOT NULL constraint takes effect.

### Existing Tests Affected (Investigation Findings)

- `tests/test_services/test_equipment_service.py:18-30` (`test_returns_active_areas_ordered`) asserts `list_areas()` returns areas "ordered by name". Default `sort_order=0` on all rows preserves this assertion because the secondary key is still `name`, but the docstring and one extra test must reflect the compound ordering.
- `tests/test_services/test_status_service.py:192-248` covers `get_area_status_dashboard()` but does not assert area ordering — add one positive test for `(sort_order, name)` ordering here.
- `tests/test_views/test_admin_views.py:607-714` covers `/admin/areas/new` and `/admin/areas/<id>/edit` POST flows. Each existing test posts a fixed payload; the new `sort_order` field must be included (or, since the field has a default, the existing payloads must remain valid). Decision: give the form field `default=0` so omitted submissions resolve cleanly and existing tests need no change.
- `tests/test_views/test_admin_views.py:923-959` (`TestAreaMutationLogging`) — extend `test_area_updated_event_logged` with a case that changes only `sort_order` and verifies the `changes` payload reflects it.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| esb/models/area.py | `Area` SQLAlchemy model — add `sort_order` column here. |
| esb/forms/equipment_forms.py | `AreaCreateForm` / `AreaEditForm` — add IntegerField with default 0. |
| esb/services/equipment_service.py | `list_areas()`, `create_area()`, `update_area()` — accept and persist `sort_order`. |
| esb/services/status_service.py | `get_area_status_dashboard()` query reorder. |
| esb/views/admin.py | `create_area` / `edit_area` route handlers — pass `sort_order` through. |
| esb/templates/admin/areas.html | Admin areas table — surface `sort_order` column. |
| esb/templates/admin/area_form.html | Render new form field. |
| migrations/versions/2e0d6d8be171_add_areas_table.py | Reference Alembic style for the new migration. |
| tests/conftest.py | `make_area` fixture; verify signature when extending in tests. |
| CLAUDE.md | "Database Migrations" section — process for generating Alembic migration against the Docker DB container. |

### Technical Decisions

- **Numeric input over drag-and-drop.** A simple `IntegerField` with default `0` keeps the UI scope small and matches the surrounding admin form aesthetic. Ties are broken by `name ASC`, so leaving every area at `0` preserves today's purely-alphabetical ordering for users who don't opt in.
- **NOT NULL with default 0.** Avoids three-valued sort logic. The migration backfills existing rows to `0` so the column can be NOT NULL without further data work.
- **Compound `ORDER BY (sort_order, name)`.** Stable, deterministic, no surprises for areas that share a sort value; alphabetical remains the secondary key so today's behavior is the limit case.
- **No new index for now.** Areas are a small table (handful of rows); a composite index on `(sort_order, name)` adds cost without measurable benefit. Revisit if the table ever grows substantially.
- **Service layer is the single ordering authority.** Touching only the two service queries propagates the new ordering to every consumer (admin list, public dashboard, kiosk, static export, equipment-form dropdowns) without per-template changes.

## Implementation Plan

### Tasks

Tasks are ordered by dependency: schema → model → service signature/queries → forms → views → templates → tests. Within each task, the **File**, **Action**, and **Notes** fields are precise enough for a fresh agent to implement without re-reading conversation history.

- [ ] **Task 1: Add `sort_order` column to the `Area` model.**
  - File: `esb/models/area.py`
  - Action: Add `sort_order = db.Column(db.Integer, nullable=False, default=0, server_default='0')` between `is_archived` and `created_at`.
  - Notes: `server_default='0'` is essential — without it, Alembic's added column will not have a default at the DB level, and existing rows on MariaDB will violate NOT NULL during the upgrade. `default=0` covers ORM-level inserts.

- [ ] **Task 2: Generate the Alembic migration.**
  - File: `migrations/versions/<new_revision>_add_area_sort_order.py` (new file; revision auto-generated)
  - Action: Follow the CLAUDE.md "Database Migrations" procedure: ensure DB container is running, inspect its IP, then run `DATABASE_URL=mysql+pymysql://root:esb_dev_password@<ip>/esb flask db migrate -m "Add sort_order to areas"`. After generation, edit the migration so:
    - `upgrade()` uses `op.batch_alter_table('areas', schema=None) as batch_op: batch_op.add_column(sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'))`.
    - `downgrade()` uses `batch_op.drop_column('sort_order')`.
  - Notes: The previous revision identifier should be whichever migration is currently `head`. Apply the migration locally via `flask db upgrade` to verify it runs clean on a populated DB.

- [ ] **Task 3: Reorder `equipment_service.list_areas()`.**
  - File: `esb/services/equipment_service.py:22-28`
  - Action: Change `order_by(Area.name)` to `order_by(Area.sort_order, Area.name)`. Update the docstring from "ordered by name" to "ordered by `(sort_order, name)`".
  - Notes: Do not modify the filter — archived areas remain excluded.

- [ ] **Task 4: Reorder `status_service.get_area_status_dashboard()`.**
  - File: `esb/services/status_service.py:212-220`
  - Action: Change `.order_by(Area.name)` to `.order_by(Area.sort_order, Area.name)`. No other change to the function.
  - Notes: The dashboard's downstream consumers (public dashboard, kiosk, static page export, single-equipment page) all see the new order transitively.

- [ ] **Task 5: Extend `create_area` and `update_area` services to accept `sort_order`.**
  - File: `esb/services/equipment_service.py:71-95` (`create_area`) and `:98-140` (`update_area`)
  - Action:
    - `create_area(name, slack_channel, created_by, sort_order=0)`: persist `sort_order` on the `Area(...)` constructor; include `'sort_order': area.sort_order` in the `log_mutation('area.created', ...)` payload.
    - `update_area(area_id, name, slack_channel, sort_order, updated_by)`: add `sort_order` immediately after `slack_channel` in the signature (no default — the form always supplies a value). Compare to existing `area.sort_order`; on change, append to the `changes` dict and assign `area.sort_order = sort_order` before commit.
  - Notes: Keep parameter ordering consistent with how the form data flows: `name, slack_channel, sort_order`. The `update_area` signature change is intentionally non-defaulted because the only caller (`edit_area` view) is updated in the same patch.

- [ ] **Task 6: Add `sort_order` field to `AreaCreateForm` and `AreaEditForm`.**
  - File: `esb/forms/equipment_forms.py:22-35`
  - Action: Import `IntegerField` from `wtforms` and `NumberRange` from `wtforms.validators`. Add to both classes:
    ```python
    sort_order = IntegerField(
        'Sort Order',
        default=0,
        validators=[NumberRange(min=0, message='Sort order must be zero or positive.')],
    )
    ```
    Place the field between `slack_channel` and `submit` in both forms.
  - Notes: `default=0` plus `IntegerField`'s automatic coercion of `None`/missing input lets pre-existing test POSTs (which omit `sort_order`) continue to validate.

- [ ] **Task 7: Wire `sort_order` through admin view handlers.**
  - File: `esb/views/admin.py:172-222`
  - Action:
    - In `create_area`: pass `sort_order=form.sort_order.data` to `equipment_service.create_area(...)`.
    - In `edit_area`: pass `sort_order=form.sort_order.data` to `equipment_service.update_area(...)`. The `AreaEditForm(obj=area)` instantiation already prefills the field from the model.
  - Notes: No changes to flash messages, redirects, or error handling.

- [ ] **Task 8: Render `sort_order` in the admin area form template.**
  - File: `esb/templates/admin/area_form.html`
  - Action: After the `slack_channel` field block, add an identical block for `sort_order`:
    ```jinja
    <div class="mb-3">
        <label for="sort_order" class="form-label">Sort Order</label>
        {{ form.sort_order(class="form-control" ~ (" is-invalid" if form.sort_order.errors else ""), type="number", min="0", step="1") }}
        <div class="form-text">Lower numbers appear first on status pages. Ties are broken alphabetically.</div>
        {% for error in form.sort_order.errors %}
        <div class="invalid-feedback">{{ error }}</div>
        {% endfor %}
    </div>
    ```
  - Notes: The `type="number"` HTML attribute gets a native spinner in modern browsers; `step="1"` enforces integer-only input client-side.

- [ ] **Task 9: Surface `sort_order` in the admin areas list template.**
  - File: `esb/templates/admin/areas.html`
  - Action:
    - Desktop table (lines 14-36): add a `<th>Sort Order</th>` between `<th>Name</th>` and `<th>Slack Channel</th>`, and a corresponding `<td>{{ area.sort_order }}</td>` in the row body.
    - Mobile card section (lines 39-50): inside each card, after the slack-channel line, add `<p class="card-text text-muted mb-2 small">Sort order: {{ area.sort_order }}</p>`.
  - Notes: Areas in this template already arrive in `(sort_order, name)` order from `list_areas()` after Task 3 — no template-side sorting needed.

- [ ] **Task 10: Update / extend tests for `equipment_service.list_areas()`.**
  - File: `tests/test_services/test_equipment_service.py` (around line 18-30)
  - Action:
    - In `test_returns_active_areas_ordered`, update the docstring to "list_areas() returns active areas ordered by (sort_order, name)".
    - Add new test `test_orders_by_sort_order_then_name`: create three areas with explicit `sort_order` values (e.g., `Area A` with 10, `Area B` with 5, `Area C` with 5) using direct `Area(...)` construction or the `make_area` fixture if extended; assert `[a.name for a in list_areas()] == ['Area B', 'Area C', 'Area A']` (sort_order=5 group sorted alphabetically, then sort_order=10).
  - Notes: Use the existing `_create_area` helper pattern (`tests/conftest.py:77`) for direct ORM inserts when the factory fixture needs extension.

- [ ] **Task 11: Add ordering test for `get_area_status_dashboard()`.**
  - File: `tests/test_services/test_status_service.py` (in `TestGetAreaStatusDashboard`, around line 192)
  - Action: Add `test_orders_areas_by_sort_order_then_name`. Create three areas with mixed sort_order values, each with one piece of equipment so they aren't filtered out, and assert the order of `[r['area'].name for r in status_service.get_area_status_dashboard()]`.
  - Notes: Each area needs at least one non-archived equipment record because the `selectattr('equipment')` filter in public templates would hide empties downstream — but the service itself returns areas regardless of equipment, so the service test only needs the area rows. Verify by reading the service code in case behavior changed.

- [ ] **Task 12: Update service tests for `create_area`/`update_area` to cover `sort_order`.**
  - File: `tests/test_services/test_equipment_service.py` (TestCreateArea class starting line 138; TestUpdateArea starting around line 207)
  - Action:
    - `TestCreateArea`: add `test_creates_area_with_sort_order` that passes `sort_order=42` and asserts `area.sort_order == 42`; verify default behavior (`test_creates_area_with_default_sort_order`) when omitted.
    - `TestUpdateArea`: add `test_updates_sort_order` that mutates `sort_order` and verifies persistence and the `log_mutation` `changes` payload includes `{'sort_order': [old, new]}`.
  - Notes: The capture fixture used elsewhere in the file (look around line 178 for prior usage) is the right tool for asserting on mutation events.

- [ ] **Task 13: Update view tests for admin area routes.**
  - File: `tests/test_views/test_admin_views.py`
  - Action:
    - In `TestCreateArea` (line 607): add `test_creates_area_with_sort_order` that POSTs `{'name': 'X', 'slack_channel': '#x', 'sort_order': '7'}` and asserts the persisted area has `sort_order == 7`.
    - In `TestEditArea` (line 659): add `test_updates_sort_order` that POSTs an edit with a changed `sort_order` and asserts the updated value.
    - In `TestAreaMutationLogging` (line 923): add a test that edits only `sort_order` and asserts the logged `changes` dict contains the `sort_order` key.
    - In `TestEditArea.test_renders_edit_form`: extend assertions to confirm `b'Sort Order'` is present in the form.
  - Notes: No changes required to existing tests because the new form field has a default of 0; existing POSTs that omit it remain valid.

- [ ] **Task 14: Run the full test suite and lint.**
  - File: (commands)
  - Action: Run `make test` and `make lint`. Address any failures before considering the task done.
  - Notes: Per CLAUDE.md, ruff is configured at 120 chars / target py3.13.

### Acceptance Criteria

- [ ] **AC 1 — Migration applies cleanly with backfill:**
  Given the database contains existing area rows from before this change, when `flask db upgrade` runs the new migration, then the `sort_order` column exists, is NOT NULL, and every pre-existing row has `sort_order = 0`.

- [ ] **AC 2 — Default behavior matches today's alphabetical order:**
  Given two or more areas with `sort_order = 0` (the default), when the status dashboard, kiosk, static export, or admin areas page is rendered, then areas appear in alphabetical order by `name`.

- [ ] **AC 3 — Explicit sort_order takes precedence over name:**
  Given areas `Zebra` (`sort_order=1`) and `Alpha` (`sort_order=2`), when any multi-area view is rendered, then `Zebra` appears before `Alpha`.

- [ ] **AC 4 — Ties resolve alphabetically:**
  Given areas `Charlie`, `Alpha`, `Bravo` all with `sort_order = 5`, when any multi-area view is rendered, then the order is `Alpha`, `Bravo`, `Charlie`.

- [ ] **AC 5 — Admin form accepts and persists sort_order:**
  Given a staff user on `/admin/areas/new` or `/admin/areas/<id>/edit`, when they submit the form with `sort_order = 7`, then the area is created/updated with `sort_order == 7` and the user is redirected back to `/admin/areas` with the success flash.

- [ ] **AC 6 — Admin form validates non-negative integers:**
  Given a staff user submits the create or edit form with `sort_order = -3`, when the form is processed, then the form re-renders with a validation error on the `sort_order` field and no DB change occurs.

- [ ] **AC 7 — Admin areas list shows the value:**
  Given multiple areas exist with distinct `sort_order` values, when a staff user loads `/admin/areas`, then the rendered HTML contains each area's `sort_order` value (desktop table column and mobile card line both pass).

- [ ] **AC 8 — Mutation event records the change:**
  Given an area with `sort_order = 0`, when a staff user edits it to `sort_order = 4`, then a JSON-formatted log entry with `event = 'area.updated'` is emitted and its `data.changes` dict contains `sort_order: [0, 4]`.

- [ ] **AC 9 — Static page export reflects the new order:**
  Given areas with explicit `sort_order` values, when `static_page_service.generate()` is invoked, then the resulting HTML lists area sections in `(sort_order, name)` order.

- [ ] **AC 10 — Existing admin POST tests continue to pass without payload changes:**
  Given the test suite's existing POSTs to `/admin/areas/new` and `/admin/areas/<id>/edit` that omit `sort_order`, when those tests run after the change, then they pass (because the form field defaults to 0).

## Additional Context

### Dependencies

- No new Python packages required. `IntegerField` and `NumberRange` are already part of WTForms (already a transitive dependency via Flask-WTF).
- Docker DB container must be running locally to generate the Alembic migration (see CLAUDE.md "Database Migrations").
- Depends on the existing service-layer pattern; no upstream blockers.

### Testing Strategy

- **Unit tests (services):**
  - Ordering: explicit assertions on `list_areas()` and `get_area_status_dashboard()` ordering with mixed `sort_order` values.
  - Mutations: `create_area` and `update_area` persist `sort_order`; `update_area` records the change via `log_mutation`.
- **View tests (admin):**
  - POST flows for create/edit with `sort_order` set and omitted.
  - Validation rejection of negative values.
  - Mutation logging round-trip.
  - Existing tests must remain green without payload changes.
- **Integration / manual verification:**
  - Start dev server (`make run`), log in as staff, create two areas with explicit sort orders, confirm the public status dashboard (`/`), kiosk view, and `/admin/areas` all reflect the order.
  - Trigger a static page export and confirm the same ordering in the generated HTML.
- **Migration verification:** Run `flask db upgrade` against a populated DB and confirm all pre-existing area rows have `sort_order = 0`; run `flask db downgrade` to confirm reversibility.

### Notes

- **Risk: forgotten migration apply.** If a developer runs the test suite (SQLite in-memory rebuilds the schema from models each time) but never applies the migration to MariaDB, the prod schema will lag the code. Mitigation: this is the standard repo workflow — the release workflow runs `flask db upgrade` on container startup.
- **Risk: ordering test flakiness with `make_area` fixture.** The current factory creates areas with `sort_order` defaulting to 0. New tests should construct areas with explicit `sort_order` to make ordering unambiguous; otherwise creation timestamp may suggest a stable order that isn't actually guaranteed.
- **Known limitation:** No bulk-reorder UI. Staff will set values one at a time. Acceptable for the current handful of areas at Decatur Makers.
- **Future considerations (explicitly out of scope):**
  - Drag-and-drop reorder UI on `/admin/areas`.
  - Optional secondary sort for equipment within an area.
  - Exposing `sort_order` to the Slack status bot if/when it ever renders multi-area summaries.
