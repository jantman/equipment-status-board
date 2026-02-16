# Story 4.2: Kiosk Display

Status: review

## Story

As a makerspace visitor,
I want to glance at a large-screen display and see which equipment is operational,
So that I know what's available without checking my phone or asking anyone.

## Acceptance Criteria

1. **Given** I navigate to the status page with `?kiosk=true` parameter, **When** the page loads, **Then** I see a full-width display of all equipment organized by area with no navbar, no footer, and no navigation controls. (AC: #1)

2. **Given** the kiosk display, **When** it renders, **Then** equipment names and area headings use large font sizes for room-distance readability (equipment names ~1.5-2rem, area headings ~2.5rem). (AC: #2)

3. **Given** the kiosk display, **When** an equipment item is degraded or down, **Then** a brief issue description is shown below the equipment name. (AC: #3)

4. **Given** the kiosk display template (`base_kiosk.html`), **When** it renders, **Then** it includes a `<meta http-equiv="refresh" content="60">` tag for auto-refresh every 60 seconds. (AC: #4)

5. **Given** the kiosk display refreshes, **When** the page reloads, **Then** there is no visible flicker or layout shift (content loads quickly on LAN). (AC: #5)

6. **Given** the kiosk display, **When** viewed on a large screen (>= 1400px), **Then** the equipment card grid auto-fills to maximum column density. (AC: #6)

7. **Given** the kiosk display, **When** status indicators are shown, **Then** they use the Compact variant with color, icon, and text label. (AC: #7)

## Tasks / Subtasks

- [x] Task 1: Add kiosk route to `esb/views/public.py` (AC: #1, #4)
  - [x] 1.1: Add `/public/kiosk` route -- NO `@login_required` (unauthenticated, public)
  - [x] 1.2: Route calls `status_service.get_area_status_dashboard()`
  - [x] 1.3: Renders `public/kiosk.html` template
  - [x] 1.4: Also support `?kiosk=true` query parameter on the status dashboard route for FR28 compatibility (redirect to `/public/kiosk` or render kiosk template directly)
- [x] Task 2: Create `esb/templates/public/kiosk.html` template (AC: #1, #2, #3, #6, #7)
  - [x] 2.1: Extends `base_kiosk.html` (already has meta refresh, no navbar, container-fluid)
  - [x] 2.2: Area sections with large headings (~2.5rem)
  - [x] 2.3: Equipment card grid using CSS Grid `auto-fill` for maximum column density on large screens
  - [x] 2.4: Each card shows equipment name (~1.5-2rem) + compact status indicator
  - [x] 2.5: Degraded/down cards show brief issue description below equipment name
  - [x] 2.6: Empty state: centered message "No equipment registered yet."
- [x] Task 3: Add kiosk-specific CSS to `esb/static/css/app.css` (AC: #2, #5, #6)
  - [x] 3.1: Kiosk area headings at ~2.5rem
  - [x] 3.2: Kiosk equipment names at ~1.5-2rem
  - [x] 3.3: CSS Grid `auto-fill` with `minmax()` for maximum column density
  - [x] 3.4: Minimal layout shift on refresh (stable card dimensions)
- [x] Task 4: Write view tests for kiosk route (AC: #1-#7)
  - [x] 4.1: Test kiosk renders without authentication (no login required)
  - [x] 4.2: Test kiosk displays area headings
  - [x] 4.3: Test kiosk displays equipment names
  - [x] 4.4: Test kiosk displays status indicators (compact variant, bg-success/warning/danger)
  - [x] 4.5: Test kiosk displays issue description for degraded/down equipment
  - [x] 4.6: Test kiosk empty state when no areas/equipment
  - [x] 4.7: Test kiosk excludes archived equipment and areas
  - [x] 4.8: Test meta refresh tag present
  - [x] 4.9: Test no navbar elements present
  - [x] 4.10: Test ARIA labels on status indicators
  - [x] 4.11: Test kiosk CSS classes for large fonts
  - [x] 4.12: Test CSS Grid auto-fill class present for responsive layout

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Single CSS/JS files:** All custom styles go in `esb/static/css/app.css`. All custom JS goes in `esb/static/js/app.js`. NO per-page CSS/JS files.
5. **Template naming:** snake_case for templates (`kiosk.html`). Underscore prefix for partials (`_status_indicator.html`).
6. **No new dependencies required** for this story.

### Critical Implementation Details

#### Route Setup

File: `esb/views/public.py`

Add the kiosk route. This route is **unauthenticated** -- no `@login_required`. The module docstring already documents this intent.

```python
@public_bp.route('/kiosk')
def kiosk():
    """Kiosk display -- full-screen equipment status for wall-mounted displays."""
    from esb.services import status_service

    areas = status_service.get_area_status_dashboard()
    return render_template('public/kiosk.html', areas=areas)
```

**FR28 compatibility:** The epics say "kiosk display can be activated via URL parameter." The simplest approach: add the dedicated `/public/kiosk` route (primary access method). The `?kiosk=true` parameter on the dashboard can be handled by detecting it in the `status_dashboard()` view and redirecting to `/public/kiosk`, OR simply document `/public/kiosk` as the URL to configure on kiosk devices. The redirect approach is cleaner for FR28 compliance:

```python
@public_bp.route('/')
@login_required
def status_dashboard():
    """Status dashboard showing all equipment status by area."""
    from flask import request, redirect, url_for
    if request.args.get('kiosk') == 'true':
        return redirect(url_for('public.kiosk'))
    from esb.services import status_service
    areas = status_service.get_area_status_dashboard()
    return render_template('public/status_dashboard.html', areas=areas)
```

#### Reuse from Story 4.1

**DO NOT recreate any of the following -- they already exist and work:**

- `status_service.get_area_status_dashboard()` -- returns areas with equipment and computed statuses. Same data source as the status dashboard. Import from `esb.services.status_service`.
- `components/_status_indicator.html` -- compact variant already fully implemented with color + icon + text label + ARIA label. Just `{% include %}` it.
- `status-card-green`, `status-card-yellow`, `status-card-red` CSS classes -- already in `app.css`.
- `.kiosk-body` CSS class -- already in `app.css` (sets `font-size: 1.25rem` on body).

#### Template: `esb/templates/public/kiosk.html`

Extends `base_kiosk.html` which already provides:
- `<meta http-equiv="refresh" content="60">` (AC #4)
- No navbar, no footer, no navigation controls (AC #1)
- `container-fluid p-3` main container
- Bootstrap CSS/JS bundled locally
- `kiosk-body` class on body element

Template structure:

```jinja2
{% extends "base_kiosk.html" %}

{% block title %}Equipment Status - Kiosk{% endblock %}

{% block content %}
{% if not areas %}
<div class="text-center py-5">
  <p class="fs-3 text-muted">No equipment registered yet.</p>
</div>
{% else %}
  {% for area_data in areas %}
  <section class="mb-4">
    <h2 class="kiosk-area-heading mb-3">{{ area_data.area.name }}</h2>
    {% if area_data.equipment %}
    <div class="kiosk-equipment-grid">
      {% for item in area_data.equipment %}
      <div class="card h-100 status-card status-card-{{ item.status.color }}">
        <div class="card-body">
          <div class="d-flex justify-content-between align-items-start">
            <span class="kiosk-equipment-name fw-bold">{{ item.equipment.name }}</span>
            {% set status = item.status %}
            {% set variant = 'compact' %}
            {% include 'components/_status_indicator.html' %}
          </div>
          {% if item.status.color != 'green' and item.status.issue_description %}
          <p class="card-text text-muted mt-2 mb-0">{{ item.status.issue_description }}</p>
          {% endif %}
        </div>
      </div>
      {% endfor %}
    </div>
    {% endif %}
  </section>
  {% endfor %}
{% endif %}
{% endblock %}
```

#### Kiosk CSS (append to `app.css`)

```css
/* Kiosk display */
.kiosk-area-heading {
    font-size: 2.5rem;
}
.kiosk-equipment-name {
    font-size: 1.5rem;
}
.kiosk-equipment-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 1rem;
}
```

**Key CSS decisions:**
- `auto-fill` with `minmax(280px, 1fr)` means cards fill available width and wrap naturally -- maximum column density on large screens (AC #6)
- Area heading at 2.5rem and equipment name at 1.5rem provide room-distance readability (AC #2)
- No transitions or animations -- page loads with stable layout to minimize flicker (AC #5)
- The existing `.kiosk-body { font-size: 1.25rem; }` already bumps base text size

#### Minimizing Layout Shift on Refresh (AC #5)

The kiosk uses a full page reload every 60 seconds via `<meta http-equiv="refresh">`. To minimize flicker:
- All CSS and JS are served from local filesystem (fast on LAN)
- No external resource loading (no CDN, no web fonts)
- Card grid uses CSS Grid with fixed `minmax` -- stable dimensions
- No JavaScript-driven rendering -- all server-rendered HTML
- Bootstrap CSS is bundled locally in `static/css/bootstrap.min.css`

On a LAN environment, page load should be well under 1 second, making the refresh essentially seamless.

### Project Structure Notes

**New files to create:**
- `esb/templates/public/kiosk.html` -- kiosk display template

**Files to modify:**
- `esb/views/public.py` -- add kiosk route, add `?kiosk=true` redirect on dashboard
- `esb/static/css/app.css` -- add kiosk-specific CSS (~10 lines)
- `tests/test_views/test_public_views.py` -- add kiosk view tests

**Files NOT to modify:**
- `esb/templates/base_kiosk.html` -- already complete with meta refresh, no-nav layout
- `esb/services/status_service.py` -- reuse `get_area_status_dashboard()` as-is
- `esb/templates/components/_status_indicator.html` -- reuse compact variant as-is
- `esb/models/` -- no new models, no migrations
- `esb/templates/base.html` -- no navbar changes needed

### Previous Story Intelligence (from Story 4.1)

**Patterns to follow:**
- Use `capture` fixture for mutation log assertions (NOT `caplog`) -- though this story is read-only, no mutation logging needed
- Flash category is `'danger'` NOT `'error'`
- Test CSRF disabled in test config (`WTF_CSRF_ENABLED = False`)
- `db.session.get(Model, id)` for PK lookups
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside view functions to avoid circular imports
- 639 tests currently passing, 0 lint errors
- Test factories: `make_area`, `make_equipment`, `make_repair_record` in `tests/conftest.py`

**Code review lessons from 4.1:**
- Don't duplicate logic -- reuse `_derive_status_from_records()` via `get_area_status_dashboard()` (already handled)
- Avoid N+1 queries -- `get_area_status_dashboard()` already does efficient batch loading
- Include tests for responsive layout classes and ARIA attributes
- Remove unused fixture parameters from tests

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

- Test file: `tests/test_views/test_public_views.py` (append to existing file)
- Add new test class: `TestKioskView`
- Use existing fixtures: `client` (unauthenticated), `make_area`, `make_equipment`, `make_repair_record`
- The kiosk is unauthenticated -- use `client` NOT `staff_client` or `tech_client`
- Test that authenticated users can ALSO access kiosk (it's public)
- Check for `meta http-equiv="refresh"` in HTML
- Check absence of navbar elements (e.g., no `<nav>` tag or no navbar class)
- Check presence of kiosk CSS classes (`kiosk-area-heading`, `kiosk-equipment-name`, `kiosk-equipment-grid`)
- Check status indicator ARIA labels present
- Check issue descriptions for degraded/down equipment

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 4 Story 4.2]
- [Source: _bmad-output/planning-artifacts/architecture.md#Frontend Architecture - Template Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment]
- [Source: _bmad-output/planning-artifacts/prd.md#FR27-FR28]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR1-NFR2 Performance]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Kiosk Display Grid Component]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Responsive Design Table - Kiosk Display]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Color System - Functional Status Colors]
- [Source: _bmad-output/implementation-artifacts/4-1-equipment-status-derivation-status-dashboard.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

No issues encountered. All tests passed on first run (655 total, 15 new kiosk tests).

### Completion Notes List

- Task 1: Added `/public/kiosk` route (unauthenticated) and `?kiosk=true` redirect on status dashboard for FR28 compatibility. Services imported locally per project convention.
- Task 2: Created `kiosk.html` template extending `base_kiosk.html`. Reuses `_status_indicator.html` compact variant and status card CSS classes from Story 4.1. Shows issue descriptions for degraded/down equipment. Empty state centered message.
- Task 3: Added 3 CSS classes to `app.css`: `.kiosk-area-heading` (2.5rem), `.kiosk-equipment-name` (1.5rem), `.kiosk-equipment-grid` (CSS Grid auto-fill with minmax(280px, 1fr)). No animations for stable layout on refresh.
- Task 4: Added 15 tests in `TestKioskView` class covering all ACs: unauthenticated access, area headings, equipment names, status indicators, issue descriptions, empty state, archived exclusion, meta refresh, no navbar, ARIA labels, CSS classes, grid layout, kiosk parameter redirect, authenticated access.

### Change Log

- 2026-02-16: Implemented Story 4.2 Kiosk Display -- added kiosk route, template, CSS, and 15 tests (655 total passing)

### File List

- esb/views/public.py (modified) -- added kiosk route, kiosk=true redirect
- esb/templates/public/kiosk.html (new) -- kiosk display template
- esb/static/css/app.css (modified) -- kiosk CSS classes
- tests/test_views/test_public_views.py (modified) -- 15 new kiosk tests
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified) -- status update
- _bmad-output/implementation-artifacts/4-2-kiosk-display.md (modified) -- story file updates
