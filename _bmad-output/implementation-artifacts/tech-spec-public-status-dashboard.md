---
title: 'Public Status Dashboard Access'
slug: 'public-status-dashboard'
created: '2026-04-12'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'Flask-SQLAlchemy', 'Flask-Login', 'Jinja2', 'pytest']
files_to_modify: ['esb/views/public.py', 'esb/templates/public/status_dashboard.html', 'esb/templates/public/equipment_page.html', 'tests/test_views/test_public_views.py']
code_patterns: ['Service layer pattern — views delegate to services', 'Public templates extend base_public.html', 'current_user.is_authenticated for conditional auth UI', 'Login route is auth.login']
test_patterns: ['pytest classes grouping related tests', 'client fixture for unauthenticated requests', 'staff_client/tech_client for authenticated', 'make_area/make_equipment/make_repair_record factory fixtures']
---

# Tech-Spec: Public Status Dashboard Access

**Created:** 2026-04-12

## Overview

### Problem Statement

The status dashboard (`/public/`) has `@login_required`, so unauthenticated visitors (makerspace members, walk-ins) cannot see equipment status. The root URL (`/`) redirects to `/public/`, which in turn redirects unauthenticated users to `/auth/login` — resulting in a redirect chain (`/` → `/public/` → `/auth/login`) instead of showing the status board.

### Solution

Remove `@login_required` from the dashboard route. Use Jinja2 conditional extends (`{% extends "base.html" if current_user.is_authenticated else "base_public.html" %}`) so authenticated users retain the full navbar, New Relic monitoring, and footer, while unauthenticated users get the clean public layout. Add navigation links (staff login, kiosk view, back-to-dashboard from equipment pages).

### Scope

**In Scope:**
- Remove `@login_required` from `status_dashboard` route
- Use conditional template extends to preserve authenticated UX (navbar, New Relic, footer)
- Add "Staff Login" text link (top-right, only shown to unauthenticated users)
- Add "Kiosk View" link on dashboard for discoverability
- Add "Back to Status Dashboard" link at bottom of equipment QR pages
- Update tests for new unauthenticated access behavior

**Out of Scope:**
- Kiosk view changes
- Authenticated staff/technician/admin views
- RBAC system changes
- Any other public routes
- Caching/rate-limiting (small makerspace app; not needed now)
- Applying conditional extends to other public templates (e.g., `equipment_page.html`) — known limitation; authenticated staff clicking from dashboard to an equipment page will lose the navbar. Can be addressed in a follow-up.
- Eliminating the `/` → `/public/` redirect hop (root URL still 302s to `/public/`; removing `@login_required` breaks the chain to `/auth/login` but the initial hop remains)

## Context for Development

### Codebase Patterns

- Public routes live in `esb/views/public.py` on the `public_bp` blueprint with URL prefix `/public`
- Public-facing templates extend `base_public.html` (minimal layout: no nav bar, no footer, no New Relic)
- Authenticated templates extend `base.html` (includes nav bar, New Relic browser monitoring, footer)
- `flask_login.current_user` is available in Jinja2 templates to check authentication state (`current_user.is_authenticated`)
- Jinja2 supports conditional extends as the first tag: `{% extends "base.html" if condition else "base_public.html" %}`
- Login route is `auth.login` (URL: `/auth/login`)
- Tests use `client` fixture (unauthenticated), `staff_client` and `tech_client` (authenticated)
- The dashboard route has existing logic for `?kiosk=true` query param that redirects to the kiosk view — this continues to work unchanged after removing `@login_required`

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/views/public.py` | Public blueprint — `status_dashboard` route has `@login_required` to remove |
| `esb/templates/public/status_dashboard.html` | Dashboard template — needs conditional extends and nav links |
| `esb/templates/public/equipment_page.html` | Equipment QR page — needs "Back to Status Dashboard" link |
| `esb/templates/base_public.html` | Base template for public pages (no nav bar, no New Relic, no footer) — read-only reference, no changes needed |
| `esb/templates/base.html` | Base template for authenticated pages (navbar, New Relic, footer) — read-only reference, no changes needed |
| `tests/test_views/test_public_views.py` | Test file with `TestStatusDashboardView` class |

### Technical Decisions

- **Conditional extends** (`{% extends "base.html" if current_user.is_authenticated else "base_public.html" %}`) preserves navbar, New Relic monitoring, and footer for authenticated users while giving unauthenticated users the clean public layout. This avoids the regression of losing these features for staff/technicians. `current_user` is available at render time via Flask-Login's context processor, so this pattern works correctly.
- **Block compatibility verified:** Both `base.html` and `base_public.html` define `{% block title %}`, `{% block content %}`, `{% block extra_css %}`, and `{% block extra_js %}` — the conditional extends will work with either base.
- "Staff Login" link positioned via `<div class="text-end mb-2">` at the top of `{% block content %}`, only rendered when using `base_public.html` (i.e., unauthenticated). Since conditional extends guarantees `base_public.html` only loads for unauthenticated users, the check `{% if not current_user.is_authenticated %}` is sufficient.
- "Back to Status Dashboard" link placed at bottom of equipment page (after report form)
- `base_public.html` is NOT modified — the Staff Login link lives in the dashboard template's content block

## Implementation Plan

### Tasks

- [ ] Task 1: Remove `@login_required` from status dashboard route
  - File: `esb/views/public.py`
  - Action: Remove the `@login_required` decorator from `status_dashboard()`. Remove the `login_required` import from `flask_login` — no other routes in this file currently use it, so the import can be removed. (If a future route needs it, the import would be re-added at that time.) Update the module docstring to reflect that the dashboard is now public (currently references FR34 requiring login).

- [ ] Task 2: Switch dashboard template to conditional extends and add navigation links
  - File: `esb/templates/public/status_dashboard.html`
  - Action:
    1. Change `{% extends "base.html" %}` to `{% extends "base.html" if current_user.is_authenticated else "base_public.html" %}`
    2. At the top of `{% block content %}`, add a "Staff Login" text link for unauthenticated users:
       ```html
       {% if not current_user.is_authenticated %}
       <div class="text-end mb-2">
         <a href="{{ url_for('auth.login') }}">Staff Login</a>
       </div>
       {% endif %}
       ```
    3. Add a "Kiosk View" link immediately after the `<h1>` and before the areas loop, right-aligned below the heading. **This link must be outside/below the `{% if not current_user.is_authenticated %}` block** so it is visible to all users (AC 4):
       ```html
       <div class="text-end mb-3">
         <a href="{{ url_for('public.kiosk') }}" class="btn btn-sm btn-outline-secondary">Kiosk View</a>
       </div>
       ```

- [ ] Task 3: Add "Back to Status Dashboard" link on equipment pages
  - File: `esb/templates/public/equipment_page.html`
  - Action: Add a link at the bottom of `{% block content %}` (after the report form div) pointing back to the dashboard:
    ```html
    <div class="mt-4 text-center">
      <a href="{{ url_for('public.status_dashboard') }}">Back to Status Dashboard</a>
    </div>
    ```

- [ ] Task 4: Update tests for public dashboard access
  - File: `tests/test_views/test_public_views.py`
  - Action:
    1. Modify `test_dashboard_redirects_unauthenticated` → rename to `test_dashboard_accessible_unauthenticated`, assert `200` status and `b'Equipment Status'` in response data
    2. Add `test_dashboard_shows_login_link_when_unauthenticated` using `client` — assert response contains `b'Staff Login'` and `/auth/login`
    3. Add `test_dashboard_hides_login_link_when_authenticated` using `staff_client` — assert `b'Staff Login'` is NOT in response data
    4. Add `test_dashboard_shows_kiosk_link` using `client` — assert response contains `/public/kiosk`
    5. Add `test_equipment_page_links_to_dashboard` using `client`, `make_area`, and `make_equipment` fixtures — create an equipment item, GET its public page, assert response contains `/public/` and `b'Back to Status Dashboard'`
    6. Add `test_dashboard_authenticated_has_navbar` using `staff_client`, `make_area`, `make_equipment` — assert response contains navbar markers (e.g., `b'navbar'` and nav links like `b'Equipment'`, `b'Repairs'`) and footer text (e.g., `b'Decatur Makers'`). Note: New Relic is verified by the conditional extends mechanism — `newrelic_browser_header` may not be set in test config, so test the footer as a proxy for `base.html` being used.
    7. Modify `test_kiosk_param_unauthenticated_redirects_to_login` → rename to `test_kiosk_param_unauthenticated_redirects_to_kiosk`, change assertion from 302 to `/auth/login` to 302 to `/public/kiosk` (removing `@login_required` means the view now processes the `?kiosk=true` param and redirects to the kiosk route instead of bouncing to login)
    8. Verify existing `staff_client`/`tech_client` tests still pass unchanged

### Acceptance Criteria

- [ ] AC 1: Given an unauthenticated user, when they visit `/public/`, then they see the equipment status dashboard with HTTP 200 (no redirect to login).
- [ ] AC 2: Given an unauthenticated user viewing the dashboard, when the page renders, then a "Staff Login" text link is visible in the top-right area linking to `/auth/login`.
- [ ] AC 3: Given an authenticated user viewing the dashboard, when the page renders, then the "Staff Login" link is NOT shown.
- [ ] AC 4: Given any user viewing the dashboard, when the page renders, then a "Kiosk View" link is visible linking to `/public/kiosk`.
- [ ] AC 5: Given a user viewing an equipment QR page (`/public/equipment/<id>`), when the page renders, then a "Back to Status Dashboard" link is visible at the bottom linking to `/public/`.
- [ ] AC 6: Given the existing authenticated dashboard tests, when the test suite runs, then all existing tests still pass (staff and technician access unchanged).
- [ ] AC 7: Given an authenticated user viewing the dashboard, when the page renders, then the full navbar (Equipment, Repairs, Admin, etc.), footer, and New Relic monitoring are present (no regression from `base.html`).

## Additional Context

### Dependencies

None — all changes are within existing code. No new packages or migrations required.

### Testing Strategy

- **Modified test:** `test_dashboard_redirects_unauthenticated` → `test_dashboard_accessible_unauthenticated` (assert 200 instead of 302)
- **New tests:**
  - `test_dashboard_shows_login_link_when_unauthenticated` — Staff Login link visible for anonymous users
  - `test_dashboard_hides_login_link_when_authenticated` — Staff Login link hidden for logged-in users
  - `test_dashboard_shows_kiosk_link` — Kiosk View link present
  - `test_equipment_page_links_to_dashboard` — Back link present on equipment QR pages (covers AC 5)
  - `test_dashboard_authenticated_has_navbar` — Authenticated users get navbar/footer (covers AC 7)
  - `test_kiosk_param_unauthenticated_redirects_to_kiosk` — Updated existing test for new behavior
- **Existing tests:** All `staff_client`/`tech_client` dashboard tests pass unchanged
- **Manual verification:** Visit `/public/` in incognito to confirm public access; visit logged in to confirm navbar/footer/New Relic intact

### Notes

- The module docstring in `public.py` references FR34 for `@login_required` — update when removing the decorator.
- The `login_required` import can be removed from `public.py` as no other routes currently use it. If a future route needs it, the import would be re-added at that time.
- The `?kiosk=true` query param redirect on the dashboard route continues to work unchanged — it fires before template rendering and is unaffected by the `@login_required` removal. Note: previously, unauthenticated users hitting `/public/?kiosk=true` would be redirected to login (never reaching the kiosk check); after this change they will be properly redirected to `/public/kiosk`. This is a beneficial behavior change.
- `base_public.html` is not modified. The Staff Login link is positioned within the dashboard template's own content block using `<div class="text-end mb-2">`.
