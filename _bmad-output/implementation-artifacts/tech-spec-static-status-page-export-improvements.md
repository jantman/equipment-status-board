---
title: 'Static status page export improvements'
slug: 'static-status-page-export-improvements'
created: '2026-05-11'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'Jinja2', 'pytest']
files_to_modify:
  - 'esb/services/static_page_service.py'
  - 'esb/services/status_service.py'
  - 'esb/templates/public/static_page.html'
  - 'tests/test_services/test_static_page_service.py'
  - 'tests/test_services/test_status_service.py'
  - 'docker-compose.yml'
  - 'docs/administrators.md'
code_patterns:
  - 'esb.services.status_service.get_area_status_dashboard() returns areas with computed status only — needs extension to expose ALL open repair records per equipment'
  - 'esb.templates.components._footer.html is the site copyright footer used on live pages; references current_year context var (injected in esb/__init__.py)'
  - 'esb.utils.filters.format_date is a registered Jinja filter'
  - 'esb.slack.forms.format_status_summary and format_area_status_detail consume the dashboard dict shape'
test_patterns:
  - 'tests/test_services/test_static_page_service.py uses make_area, make_equipment, make_repair_record fixtures; asserts on substrings in generated HTML'
  - 'fixtures: make_repair_record(equipment, status, description, **kwargs) — kwargs become RepairRecord column values (severity, eta, created_at, etc.)'
revision_history:
  - '2026-05-11 — initial spec'
  - '2026-05-11 — applied 20 adversarial-review findings (F1–F20)'
---

# Tech-Spec: Static status page export improvements

**Created:** 2026-05-11
**Revised:** 2026-05-11 (post-adversarial-review)

GitHub Issue: [#44](https://github.com/jantman/equipment-status-board/issues/44)

## Overview

### Problem Statement

The static status page (`esb/services/static_page_service.py` → `esb/templates/public/static_page.html`) — exported to local disk / S3 / GCS for public-facing display when the live Flask site is unavailable — has two presentation gaps:

1. **No repair detail for non-green equipment.** It lists each equipment item by area with a status dot (green/yellow/red), a label, and (for the highest-severity record only) an ETA. When equipment is Degraded or Down, the page does not enumerate the **open repair records** with their per-record status, ETA, and description, so a reader cannot see *why* equipment is impaired or *what is being done about it*.
2. **Generation metadata is inconsistent and visually weak.** A small "Generated: YYYY-MM-DD HH:MM UTC" line at the very bottom is the only branding/footer content. The live site uses a richer copyright/license footer (`esb/templates/components/_footer.html`). The static export should match the live look-and-feel, and the generation timestamp should be more prominent and in local/system timezone (not UTC).

### Solution

Update `static_page_service.generate()` to pass through (a) the open repair records per non-green equipment item (sorted by severity priority, then `created_at` ASC) and (b) a generation timestamp in the system's local timezone (with seconds). Update `esb/templates/public/static_page.html` to (i) render a list of open repair records — with each record's status, severity, ETA, and description — nested under each non-green equipment item; (ii) add a generation-time sub-heading immediately under the `<h1>Equipment Status</h1>` title, right-aligned, in local timezone; (iii) replace the bottom "Generated:" line with the site's copyright/license footer text (inlined — the static page must remain CSP-locked and have no external **sub-resources**, though anchor links to external sites are permitted). Configure the `worker` container to use `America/New_York` as the default timezone via `docker-compose.yml`, with deployment instructions added to `docs/administrators.md`.

**Note on scope additions beyond issue #44's literal text:** The issue lists status, ETA, and description as required per-record fields. This spec additionally includes (a) a textual severity badge `[Down]` / `[Degraded]` / `[Not Sure]` per record — for accessibility, since color alone (the left-border indicator) is a WCAG concern; (b) sort-by-severity-priority — so the most urgent records bubble to the top at a glance, since this is the fallback view when the live site is down. These are explicitly called out as enhancements.

### Scope

**In Scope:**
- `esb/services/status_service.py` — extend `get_area_status_dashboard()` to include per-equipment `open_records` list, sorted by severity priority then `created_at` ASC.
- `esb/services/static_page_service.py` — compute local-tz generation timestamp (with seconds), pass local-tz year to the template.
- `esb/templates/public/static_page.html` — repair-record list under non-green items, top sub-heading with generated time, replace bottom footer with inlined copyright text.
- Inline the copyright footer markup/text into the static template (the static page must have no external sub-resources — same self-contained / `default-src 'none'` CSP rule).
- `docker-compose.yml` — set `TZ=America/New_York` as the default `worker`-service environment variable (overridable via `.env` for non-EST/EDT deployments).
- `docs/administrators.md` — document the `TZ` environment variable in the Environment Variable Reference table.
- `tests/test_services/test_static_page_service.py` — cover the new repair list, footer, generation-time placement, XSS escape, and CSP directive integrity.
- `tests/test_services/test_status_service.py` — regression test for the new `open_records` key in `get_area_status_dashboard()`.

**Out of Scope:**
- Live `public/status_dashboard.html`, kiosk views, or equipment-info pages.
- Database schema changes.
- Push delivery backends (`_push_local`, `_push_s3`, `_push_gcs`) — unchanged.
- Changes to `status_service` status derivation (color/label/severity logic stays as-is).
- Reuse of `_footer.html` via `{% include %}` — static export must remain self-contained.
- Pagination / cap on the number of open records displayed per equipment (explicit decision — see Notes).
- `get_single_area_status_dashboard()` extension (per-area kiosk static export).

## Context for Development

### Codebase Patterns

- **Self-contained static page.** `static_page.html` declares `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'` and uses only inline `<style>`. The page must continue to render with no external **sub-resources** — no `<link>`, no `<script src=>`, no `<img src=…>` to external hosts. Anchor links (`<a href="…">`) to external sites are user-initiated navigation, not auto-fetched sub-resources, and are permitted under this CSP (which has no `connect-src` / `navigate-to` restrictions). Existing test `test_produces_self_contained_html` enforces no `<link>` / `<script src=>`.
- **Status derivation lives in `esb/services/status_service.py`.** `get_area_status_dashboard()` currently emits one `status` dict per equipment (computed from the highest-severity open record). The new requirement needs **all open repair records** per non-green equipment. Approach: extend `get_area_status_dashboard()` to additionally include the per-equipment list of `RepairRecord` instances in each entry (e.g., `open_records: list[RepairRecord]`). The records are already prefetched and grouped by `equipment_id` in the existing implementation (`records_by_equipment` dict). The new key is sorted by `(severity priority ASC, created_at ASC)` using `_SEVERITY_STATUS`; the prefetch query is already ordered by `(created_at ASC, id ASC)` so the secondary sort is stable. Existing callers ignoring the new key continue to work.
- **Consumers of `get_area_status_dashboard()` return value** (audited 2026-05-11):
  - `esb/templates/public/status_dashboard.html` — iterates `area_data.equipment[*].equipment` and `.status` only.
  - `esb/templates/public/kiosk.html` — same.
  - `esb/views/public.py:40-54` `kiosk_area()` route — passes a single-area dict (from `get_single_area_status_dashboard()`, not changed here) into `public/kiosk.html`.
  - `esb/slack/forms.py` `format_status_summary(dashboard_data)` and `format_area_status_detail(area_data)` — iterate `equipment` and `status` only.
  - `esb/slack/handlers.py:288` — calls `format_status_summary()` from the `/esb-status` command path.
  - None of the above reference `open_records`, so the additive key change does not require any caller updates. The full test suite (Task 6) is the regression net.
- **`current_year` is injected via `app.context_processor` in `esb/__init__.py`** (`esb/__init__.py:75-76`); that processor works for `render_template()` calls so it is available to the static template without explicit kwargs. **However**, it is derived from `datetime.now(timezone.utc).year`, which can disagree with the static page's local-tz generation timestamp for a few hours either side of midnight Dec 31. Spec passes a local-tz year as a separate template var (`generated_year`) and the footer uses that, not `current_year`, to keep the two timestamps consistent (see Decision #7).
- **Jinja filter `format_date`** (in `esb/utils/filters.py:13-30`) is registered on the app's Jinja env and usable from any template, including the static one.
- **`RepairRecord` model fields** (confirmed in `esb/models/repair_record.py`):
  - `status: str` from `REPAIR_STATUSES = ['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered', 'Parts Received', 'Needs Specialist', 'Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']`. Non-closed = anything not in `CLOSED_STATUSES = ('Resolved', 'Closed - No Issue Found', 'Closed - Duplicate')`.
  - `severity: str | None` from `REPAIR_SEVERITIES = ['Down', 'Degraded', 'Not Sure']`.
  - `description: str` (Text, non-null). Can be multi-line and effectively unbounded.
  - `eta: date | None`.
  - `created_at: datetime` (UTC).
- **Severity → color map** (`status_service._SEVERITY_STATUS`): `Down`→red (priority 0), `Degraded`→yellow (priority 1), `Not Sure`→yellow (priority 2), no severity → gray (priority 3, treated as last for sort purposes). Use this same mapping for per-record styling AND per-record sort.
- **Local-timezone formatting.** No existing helper. Place the implementation in a module-level helper `_compute_generated_at()` (NOT inline in `generate()`) so tests can monkey-patch it directly. Format: `'%Y-%m-%d %H:%M:%S %Z'` → `2026-05-11 14:32:15 EDT`. If `dt.tzname()` returns `None` or an empty string (fixed-offset zone), fall back to `'%Y-%m-%d %H:%M:%S %z'` → `2026-05-11 14:32:15 -0400`. **Detect the fallback by inspecting `dt.tzname()` directly**, not by parsing the result of `strftime('%Z')` for trailing whitespace.
- **Reference precedent.** `esb/templates/public/equipment_page.html:29-46` already renders an `open_repairs` list with severity-derived `status-card-*` styling. Static page repair list follows the same conceptual layout (record per `<li>`, severity styling, description visible, ETA shown when set) but using *inline* CSS classes defined within `static_page.html` (Bootstrap is unavailable in the export).
- **Test fixtures** (`tests/conftest.py:118-160`):
  - `make_area(name=…)` → `Area` (the only accepted kwarg shape).
  - `make_equipment(name=…, area=…, **kwargs)` → `Equipment` (extra kwargs forwarded to model constructor).
  - `make_repair_record(equipment=…, status='New', description='X', **kwargs)` → `RepairRecord`. Extra kwargs (`severity`, `eta`, `created_at`, `assignee_id`, `reporter_name`, etc.) are forwarded to the `RepairRecord` constructor; **the fixture does NOT accept `area` or `name`**.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/services/static_page_service.py` | Modify `generate()`; add `_compute_generated_at()` module-level helper. |
| `esb/services/status_service.py` | Extend `get_area_status_dashboard()` with the new `open_records` key. |
| `esb/templates/public/static_page.html` | Render repair list, top-right generation timestamp, inline copyright footer. |
| `esb/templates/components/_footer.html` | Source of truth for the copyright/license text and link targets (used as reference; not included). |
| `esb/__init__.py` | `inject_current_year` context processor (already wired; not modified — local-tz year is passed separately). |
| `esb/utils/filters.py` | `format_date` Jinja filter. |
| `esb/slack/forms.py`, `esb/slack/handlers.py` | Existing consumers of `get_area_status_dashboard()`; verified not affected by the additive `open_records` key. |
| `docker-compose.yml` | Add `TZ=America/New_York` to the `worker` service. |
| `docs/administrators.md` | Document the `TZ` env var in the Environment Variable Reference section. |
| `tests/test_services/test_static_page_service.py` | Existing test class `TestGenerate`; add cases for repair list, top-right timestamp, inline footer, footer-drift pin, XSS escape, CSP directive integrity. |
| `tests/test_services/test_status_service.py` | Add regression test for `open_records` key. |
| `tests/conftest.py` | Fixture definitions (`make_area`, `make_equipment`, `make_repair_record`). |

### Technical Decisions

1. **Extend `get_area_status_dashboard()` to include an `open_records` list per equipment.** Records are already prefetched and grouped in `records_by_equipment`; threading the list through is a one-line change. Rejected the "new helper" option to avoid duplicating ~40 lines of prefetch code. Existing callers (live dashboard, kiosk, Slack formatters) ignore the new key (verified — see "Consumers" bullet above).
2. **Sort open records by severity priority, then `created_at` ASC.** Rationale: the static page is the fallback at-a-glance view. Sorting by severity ensures `Down` records bubble above `Degraded`/`Not Sure`/no-severity within each equipment's record list, supporting quick triage. Sort key: `(_SEVERITY_STATUS.get(rec.severity, (..., ..., 999))[2], rec.created_at, rec.id)`. The `999` default places no-severity records last. Apply the sort inside `get_area_status_dashboard()` after grouping by equipment.
3. **Local-timezone generation timestamp.** Implemented in module-level helper `_compute_generated_at()` in `static_page_service.py` (so tests can patch it). Uses `datetime.now().astimezone()` (no `tzinfo` argument) — Python picks up the host system's TZ from `TZ` env / `/etc/localtime`. Format: `'%Y-%m-%d %H:%M:%S %Z'` → `2026-05-11 14:32:15 EDT`. **Seconds are included** for debugging value when multiple pushes happen within a minute. If `dt.tzname()` returns `None` or `''`, fall back to `'%Y-%m-%d %H:%M:%S %z'` → `2026-05-11 14:32:15 -0400`. Detection is via `dt.tzname()`, not via post-hoc string inspection of the formatted output.
4. **Footer text is inlined verbatim** from `_footer.html` (copyright line + GitHub link + MIT license link) into `static_page.html`, NOT included via `{% include %}`. Reasons: (a) the static page must remain self-contained (no external sub-resources); (b) an include couples the export to a fragment used by the live site, which is brittle if that fragment later pulls in Bootstrap classes or external icons; (c) copyright text is short and stable. **Drift mitigation:** Task 4 adds a unit test that reads `_footer.html` and asserts its three key substrings (owner name, GitHub URL, MIT URL) appear verbatim in the rendered static page. The test fails loudly when either file diverges, forcing the implementer to keep the static-page footer in sync. Footer markup uses inline styles defined in `static_page.html` (no Bootstrap class dependency).
5. **Per-record styling**. Repair-record `<li>` items use a small inline left-border indicator color-coded by severity using the same mapping as the equipment-level dot (`Down`→red, `Degraded`/`Not Sure`→yellow, no severity → gray). Display order within the record: `[status badge] [severity badge if set] description …ETA: …`. Severity text badge is **retained** (e.g., `[Down]`) as an accessibility/redundancy feature — color alone is a WCAG concern, and the text badge gives the same information non-visually. This is called out as a spec-added enhancement beyond issue #44's literal ask.
6. **Description wrap, not truncate.** `RepairRecord.description` is unbounded Text. Apply inline CSS `white-space: pre-wrap; overflow-wrap: anywhere;` to `.record-description` so multi-line descriptions render correctly and long un-broken strings (URLs, etc.) wrap rather than overflow the page. **No truncation** — the static page is a fallback view and full text is more useful than an ellipsis; visual clutter from a long description is acceptable for that rare case.
7. **Local-tz year for the footer.** Compute the footer year from the same `datetime` used by `_compute_generated_at()` and pass it to the template as a separate kwarg `generated_year`. The footer renders `&copy; {{ generated_year }} Jason Antman`. The `current_year` context processor (UTC) is left alone so the live site is unaffected. This avoids the ~5-hour disagreement window around midnight Dec 31 where footer year and generation-timestamp year could differ by one.
8. **Generation sub-heading placement.** Below the `<h1>Equipment Status</h1>` block, right-aligned via `text-align: right` on a `.generated-at` div (new CSS rule).
9. **Equipment-row layout wrapper.** Existing `.equipment-item` uses `display: flex` to lay out dot/name/label/eta on one line. Adding a nested `<ul>` for open records inside the same `<li>` would make the `<ul>` a flex sibling. Spec wraps the existing four spans into a new `<div class="equipment-row">` (with `display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem;`) and changes `.equipment-item` to `display: block`. The new `<ul class="open-records-list">` lays out beneath the row naturally. The full template diff is spelled out in Task 3.
10. **TZ default in `docker-compose.yml`.** Set `TZ=${TZ:-America/New_York}` in the `worker` service `environment:` block so the makerspace timezone is the out-of-the-box default. Operators in other zones override via `TZ=...` in `.env`. The `app` service does not need `TZ` because it does not invoke `generate()`; the worker is the sole producer of static pages via `generate_and_push()`.
11. **Module-level datetime import in `static_page_service.py`.** Hoist `from datetime import datetime` to module top (it is currently function-scoped). This is required for the `_compute_generated_at()` helper to exist at module scope, and it lets tests patch `static_page_service._compute_generated_at` directly.

## Implementation Plan

### Tasks

- [ ] **Task 1: Extend `get_area_status_dashboard()` to include sorted per-equipment open repair records.**
  - File: `esb/services/status_service.py`
  - Action:
    1. In `_SEVERITY_STATUS` (line 17-21), the priority for each known severity is the third tuple element. Add a module-level constant `_NO_SEVERITY_SORT_PRIORITY = 999` (or inline `999` with a comment) to use for records with `severity=None`.
    2. Inside `get_area_status_dashboard()`, after the `records_by_equipment` grouping (lines 232-235), add a sort: for each list of records in `records_by_equipment.values()`, sort in place by `(severity_priority, created_at, id)`. Helper:
       ```python
       def _sort_key(rec):
           sev = _SEVERITY_STATUS.get(rec.severity)
           priority = sev[2] if sev else _NO_SEVERITY_SORT_PRIORITY
           return (priority, rec.created_at, rec.id)
       for records in records_by_equipment.values():
           records.sort(key=_sort_key)
       ```
    3. In the loop that builds `equip_statuses` (currently lines 238-246), add `'open_records': equip_records` to the dict appended for each equipment.
    4. Update the function's docstring (lines 170-186) to document the new `open_records` key — list of `RepairRecord` instances, sorted by `(severity priority, created_at, id)` so highest-severity oldest-first.
  - Notes: Existing live-page templates (`public/status_dashboard.html`, `public/kiosk.html`) and Slack formatters (`esb/slack/forms.py`) iterate `area_data.equipment` but reference only `item.equipment` and `item.status` — none touch `open_records`. The additive key is safe. `get_single_area_status_dashboard()` is **not** changed (out of scope per Scope section).

- [ ] **Task 2: Add `_compute_generated_at()` helper and hoist `datetime` import in `static_page_service.py`.**
  - File: `esb/services/static_page_service.py`
  - Action:
    1. Move `from datetime import UTC, datetime` from inside `generate()` (line 22) to the module-level imports at the top of the file. Remove the now-unused `UTC` if not referenced elsewhere in the module.
    2. Add a module-level helper function:
       ```python
       def _compute_generated_at() -> tuple[str, int]:
           """Compute the generation timestamp string and year in the system's local timezone.

           Returns:
               (timestamp_str, year) where timestamp_str is formatted like
               '2026-05-11 14:32:15 EDT' (or '2026-05-11 14:32:15 -0400' when
               the local tz has no tzname). year is the local-tz year of the
               same instant.
           """
           dt = datetime.now().astimezone()
           tzname = dt.tzname()
           if tzname:
               timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S ') + tzname
           else:
               timestamp_str = dt.strftime('%Y-%m-%d %H:%M:%S %z')
           return timestamp_str, dt.year
       ```
       (Note: build `timestamp_str` via concatenation, not `%Z`, because some Python builds emit a trailing space when `tzname()` is non-empty — being explicit avoids the ambiguity.)
    3. Update `generate()`:
       ```python
       def generate() -> str:
           from esb.services import status_service
           areas = status_service.get_area_status_dashboard()
           generated_at, generated_year = _compute_generated_at()
           return render_template(
               'public/static_page.html',
               areas=areas,
               generated_at=generated_at,
               generated_year=generated_year,
           )
       ```
       (Remove the docstring "Uses status_service.get_area_status_dashboard() for data" line about `generated_at` format being UTC.)
  - Notes: No new external deps. Tests patch `esb.services.static_page_service._compute_generated_at` to inject deterministic timestamps regardless of host TZ.

- [ ] **Task 3: Update `static_page.html` template structure.**
  - File: `esb/templates/public/static_page.html`
  - Below is the full intended template (replace the file's contents). Read the existing file first to confirm no other recent edits.

    ```html
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline';">
        <title>Equipment Status</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; color: #212529; background: #f8f9fa; padding: 1rem; }
            h1 { font-size: 1.5rem; margin-bottom: 0.25rem; text-align: center; }
            .generated-at { text-align: right; font-size: 0.85rem; color: #6c757d; margin-bottom: 1rem; }
            .area { margin-bottom: 1.5rem; }
            .area h2 { font-size: 1.1rem; border-bottom: 2px solid #dee2e6; padding-bottom: 0.3rem; margin-bottom: 0.5rem; }
            .equipment-list { list-style: none; }
            .equipment-item { display: block; padding: 0.25rem 0; }
            .equipment-row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem; }
            .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
            .status-green { background-color: #198754; }
            .status-yellow { background-color: #ffc107; }
            .status-red { background-color: #dc3545; }
            .equipment-name { font-size: 0.95rem; }
            .status-label { font-size: 0.8rem; color: #6c757d; }
            .eta-label { font-size: 0.8rem; color: #6c757d; margin-left: 0.25rem; }
            .no-equipment { color: #6c757d; font-size: 0.9rem; }
            .open-records-list { list-style: none; margin: 0.4rem 0 0.6rem 1.5rem; }
            .open-record { font-size: 0.85rem; padding: 0.25rem 0.4rem; margin-bottom: 0.2rem; border-left: 3px solid #6c757d; background: #fff; }
            .open-record-red { border-left-color: #dc3545; }
            .open-record-yellow { border-left-color: #ffc107; }
            .open-record-gray { border-left-color: #6c757d; }
            .record-status { font-weight: 600; }
            .record-severity { color: #6c757d; }
            .record-description { white-space: pre-wrap; overflow-wrap: anywhere; }
            .record-eta { color: #6c757d; margin-left: 0.25rem; }
            .site-footer { text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #dee2e6; font-size: 0.8rem; color: #6c757d; }
            .site-footer a { color: #6c757d; }
        </style>
    </head>
    <body>
        <h1>Equipment Status</h1>
        <div class="generated-at">Generated: {{ generated_at }}</div>
        {% for area_data in areas %}
        <div class="area">
            <h2>{{ area_data.area.name }}</h2>
            {% if area_data.equipment %}
            <ul class="equipment-list">
                {% for item in area_data.equipment %}
                <li class="equipment-item">
                    <div class="equipment-row">
                        <span class="status-dot status-{{ item.status.color }}" aria-hidden="true"></span>
                        <span class="equipment-name">{{ item.equipment.name }}</span>
                        <span class="status-label">{{ item.status.label }}</span>
                        {% if item.status.eta %}<span class="eta-label">ETA: {{ item.status.eta|format_date }}</span>{% endif %}
                    </div>
                    {% if item.status.color != 'green' and item.open_records %}
                    <ul class="open-records-list">
                        {% for rec in item.open_records %}
                        <li class="open-record open-record-{{ 'red' if rec.severity == 'Down' else 'yellow' if rec.severity in ('Degraded', 'Not Sure') else 'gray' }}">
                            <span class="record-status">{{ rec.status }}</span>{% if rec.severity %} <span class="record-severity">[{{ rec.severity }}]</span>{% endif %} <span class="record-description">{{ rec.description }}</span>{% if rec.eta %} <span class="record-eta">ETA: {{ rec.eta|format_date }}</span>{% endif %}
                        </li>
                        {% endfor %}
                    </ul>
                    {% endif %}
                </li>
                {% endfor %}
            </ul>
            {% else %}
            <p class="no-equipment">No equipment in this area.</p>
            {% endif %}
        </div>
        {% endfor %}
        <footer class="site-footer" role="contentinfo">&copy; {{ generated_year }} Jason Antman. <a href="https://github.com/jantman/equipment-status-board" rel="noopener noreferrer">github.com/jantman/equipment-status-board</a> <a href="https://opensource.org/license/mit" rel="noopener noreferrer">MIT licensed</a>.</footer>
    </body>
    </html>
    ```

  - Key changes vs. previous template: `.equipment-item` becomes `display: block`; the existing dot/name/label/eta row is wrapped in `<div class="equipment-row">`; new `<ul class="open-records-list">` rendered only when equipment is non-green AND has open records; old `<div class="footer">Generated: …</div>` replaced by `<footer class="site-footer">` with copyright/license; new `.generated-at` sub-heading directly under the `<h1>`. The footer uses `generated_year` (local-tz, from `_compute_generated_at()`), NOT `current_year`. The CSP directive is unchanged.

- [ ] **Task 4: Add tests in `tests/test_services/test_static_page_service.py`.**
  - File: `tests/test_services/test_static_page_service.py`
  - Add the following tests (inside `class TestGenerate` unless noted):

    1. `test_generated_at_subheading_renders_above_areas` — Given an area with one equipment item, when `generate()` runs, then the HTML contains `<div class="generated-at">` and that string's `find()` index is less than the index of the first `<div class="area">` AND greater than the index of `</h1>`.

    2. `test_generated_at_uses_local_timezone_helper` (covers AC 7) — Monkey-patch `esb.services.static_page_service._compute_generated_at` to return `('2026-05-11 14:32:15 EDT', 2026)`. Call `generate()`. Assert HTML contains `Generated: 2026-05-11 14:32:15 EDT`. This bypasses the host TZ entirely and verifies the wiring between the helper and the template.

    3. `test_compute_generated_at_uses_tzname_when_present` (covers AC 7, helper-level) — Use `unittest.mock.patch` on `esb.services.static_page_service.datetime` to make `datetime.now().astimezone()` return a real `datetime` with `tzinfo=ZoneInfo('America/New_York')` set to a specific UTC instant (e.g., `2026-07-15 14:32:15` US Eastern). Call `_compute_generated_at()` directly. Assert returned timestamp ends with ` EDT` and year is `2026`.

    4. `test_compute_generated_at_falls_back_to_offset_when_tzname_empty` (covers AC 8) — Patch `datetime.now().astimezone()` to return a `datetime` whose `tzinfo` is a `timezone(timedelta(hours=-4))` (anonymous offset; `tzname()` returns `'UTC-04:00'` by default in newer Python, but `timezone(timedelta(hours=-4), name=None)` then `tzname()` returns the offset string — verify behavior; if needed, build a custom `tzinfo` subclass whose `tzname()` returns `None`). Assert the returned timestamp ends with `-0400` (i.e., `%z` format), not an empty trailing space.

    5. `test_open_records_listed_for_non_green_equipment` (covers AC 1) — Create equipment with one record `make_repair_record(equipment=eq, status='In Progress', severity='Down', description='Belt slipping', eta=date(2026, 6, 1))`. Call `generate()`. Assert HTML contains `'In Progress'`, `'[Down]'`, `'Belt slipping'`, and `'ETA: ' + date(2026, 6, 1).strftime('%b %d, %Y')`, AND contains the substring `class="open-record open-record-red"`.

    6. `test_open_records_omitted_for_green_equipment` (covers AC 2) — Create equipment with no repair records. Assert HTML does NOT contain `'open-records-list'`.

    7. `test_open_records_uses_yellow_class_for_degraded_and_not_sure` (covers AC 4) — Create two equipment items in the same area, one with `severity='Degraded'`, one with `severity='Not Sure'`. Assert HTML contains at least two occurrences of `'open-record-yellow'`.

    8. `test_open_records_uses_gray_class_for_no_severity` (covers AC 4 None branch) — Create a repair record passing `severity=None` (note: this requires inserting via the fixture; the model column is nullable). Assert HTML contains `'open-record-gray'` AND does NOT contain `'<span class="record-severity">'` for that record.

    9. `test_open_records_omits_eta_when_unset` (covers AC 5) — Create a repair record with `eta=None`. Within its `<li class="open-record …">` block, the rendered HTML must not contain `'record-eta'`. Use a sliced substring (e.g., split on `open-record open-record-`) to isolate the relevant `<li>` for the assertion.

    10. `test_open_records_sorted_by_severity_priority_then_created_at` (covers AC 3) — Create one equipment with three records: `(severity='Down', created_at=datetime(2026, 5, 1, tzinfo=UTC), description='down-newer')`, `(severity='Not Sure', created_at=datetime(2026, 4, 1, tzinfo=UTC), description='notsure-older')`, `(severity='Degraded', created_at=datetime(2026, 4, 15, tzinfo=UTC), description='degraded-mid')`. Insert in mixed insertion order. Call `generate()`. Assert the HTML substring index of `'down-newer'` < `'degraded-mid'` < `'notsure-older'` (severity priority order: Down(0) < Degraded(1) < Not Sure(2)).

    11. `test_site_footer_replaces_old_generated_line` (covers AC 9) — Call `generate()`. Assert HTML contains `'Jason Antman'`, `'github.com/jantman/equipment-status-board'`, and `'MIT licensed'`, AND contains `'<footer class="site-footer"'`, AND does NOT contain `'<div class="footer">'` (the old class).

    12. `test_footer_renders_local_tz_year` (covers AC 10) — Monkey-patch `_compute_generated_at` to return `(..., 2027)`. Assert HTML footer contains `'&copy; 2027 Jason Antman'` (or `'© 2027 Jason Antman'` after Jinja unescaping — use the literal-byte form Jinja emits; in practice `&copy;` is emitted verbatim because the template uses the entity).

    13. `test_footer_pins_to_live_footer_text` (covers F9 drift mitigation) — Read `esb/templates/components/_footer.html` from disk. Extract the three load-bearing substrings: `'Jason Antman'`, the GitHub URL `https://github.com/jantman/equipment-status-board`, and the MIT URL `https://opensource.org/license/mit`. Assert each appears in the rendered static page HTML. If the live footer ever changes its owner name or link targets, this test fails and forces the static page to be updated in lockstep.

    14. `test_description_is_html_escaped` (covers F11 XSS defense) — Create a repair record with `description='<script>alert(1)</script><img src=x onerror=y>'`. Call `generate()`. Assert HTML contains `'&lt;script&gt;'` (escaped) AND does NOT contain the literal `'<script>alert(1)</script>'`.

    15. `test_csp_meta_tag_directive_unchanged` (covers AC 11; strengthen existing test) — Update existing `test_includes_csp_meta_tag` (or add a sibling) to assert the verbatim substring `"default-src 'none'; style-src 'unsafe-inline'"` appears in the HTML, not just `'Content-Security-Policy'`.

    16. `test_equipment_row_keeps_dot_name_label_on_one_line` (covers AC re. F8 layout) — Assert HTML contains `<div class="equipment-row">` and within that wrapper, the order of substrings is `status-dot`, `equipment-name`, `status-label` (i.e., the existing single-line composition is preserved structurally).

    17. **Update existing `test_includes_generated_timestamp`** (covers AC 12) — Replace `assert 'UTC' in html` with `assert 'Generated:' in html`. The timezone token now depends on host TZ / patched helper; pinning to `UTC` is no longer correct.

  - Notes:
    - Use `from datetime import UTC, datetime` (Python 3.11+) for the `created_at` kwarg values.
    - The fixture `make_repair_record(equipment, status='New', description='X', **kwargs)` — pass `created_at`, `severity`, `eta` via kwargs.
    - For `test_compute_generated_at_falls_back_to_offset_when_tzname_empty`, the cleanest approach is a tiny custom `tzinfo` subclass: `class _NamelessTZ(tzinfo): utcoffset = lambda self, dt: timedelta(hours=-4); tzname = lambda self, dt: None; dst = lambda self, dt: timedelta(0)`. Then patch `datetime.now().astimezone()` to return a datetime with that `tzinfo`.

- [ ] **Task 5: Add a regression test for the new `open_records` key in `tests/test_services/test_status_service.py`.**
  - File: `tests/test_services/test_status_service.py`
  - Add (in an existing `TestGetAreaStatusDashboard` class, or create one if missing):

    1. `test_includes_open_records_list_per_equipment` — Create one area with one equipment item and two non-closed repair records and one closed record (`status='Resolved'`). Call `get_area_status_dashboard()`. Assert `result[0]['equipment'][0]` has key `'open_records'` whose value is a `list` of length 2 (the two non-closed). Assert the closed record is excluded. Assert each entry is a `RepairRecord` instance.

    2. `test_open_records_sorted_by_severity_then_created_at` — Create one equipment with `Down/2026-05-01`, `Not Sure/2026-04-01`, `Degraded/2026-04-15`, `None/2026-03-01`. Call the dashboard. Assert the `open_records` list order is: `Down`, `Degraded`, `Not Sure`, `None`-severity (severity-priority sort, ties broken by `created_at`).

    3. `test_empty_open_records_list_for_green_equipment` — Create equipment with zero non-closed records. Assert `equipment[0]['open_records'] == []`.

  - Notes: Verify existing tests in the file still pass — the new key is additive but make sure no existing assertion uses `set(equipment[0].keys())` style equality.

- [ ] **Task 6: Configure default TZ in `docker-compose.yml` worker service.**
  - File: `docker-compose.yml`
  - Action: In the `worker:` service's `environment:` block (lines 53-60), add a new line: `      - TZ=${TZ:-America/New_York}`. Place it adjacent to the existing `PYTHONUNBUFFERED=1` and `WORKER_HEARTBEAT_PATH=…` entries.
  - Notes: The `${TZ:-America/New_York}` syntax means "use the `TZ` env var if set in `.env` or shell, otherwise default to `America/New_York`." This matches the makerspace location (Decatur Makers) while letting other deployments override. The `app` service does **not** need TZ — only the worker calls `generate()`.

- [ ] **Task 7: Document the `TZ` environment variable in `docs/administrators.md`.**
  - File: `docs/administrators.md`
  - Action: In the Environment Variable Reference table (line 72 onward), add a new row:
    ```markdown
    | `TZ` | IANA timezone name for the worker container. Controls the timezone displayed in the static status page's generation timestamp (sub-heading near top of page and the copyright year in the footer). Set this to your local timezone for accurate display. The `app` service does not use this variable. | No | `America/New_York` | `America/Chicago` |
    ```
  - Notes: Place the row alphabetically or near other deployment-configuration variables. The default reflects what's in `docker-compose.yml`. Also add a short paragraph in the "Static Status Page Setup" section (line 245+) noting that the static page's generation timestamp reflects the `worker` container's `TZ`, and that operators should set `TZ` in `.env` to match their local timezone.

- [ ] **Task 8: Run lint and full test suite.**
  - Commands: `make lint` then `make test`.
  - Expected: All green. Existing test `test_includes_generated_timestamp` was updated in Task 4 case 17; `test_produces_self_contained_html` continues to pass (no new `<link>` or `<script src=>`); existing `test_includes_csp_meta_tag` may need rename/strengthen per Task 4 case 15. The full suite covers Slack formatter tests (`tests/test_slack/`) which exercise consumers of `get_area_status_dashboard()` — confirms no regression.

### Acceptance Criteria

- [ ] **AC 1 (happy path — repair list rendered):** Given a non-archived area with one equipment item whose only open repair record has `status='In Progress'`, `severity='Down'`, `description='Belt slipping'`, `eta=date(2026, 6, 1)`, when `static_page_service.generate()` is called, then the returned HTML contains a `<ul class="open-records-list">` nested under that equipment's `<li class="equipment-item">` whose single `<li>` includes the substrings `In Progress`, `[Down]`, `Belt slipping`, and `ETA: Jun 01, 2026`, and has the CSS class substring `open-record-red`.

- [ ] **AC 2 (green equipment — no list):** Given a non-archived equipment item with zero open repair records, when `generate()` is called, then the HTML for that equipment contains no `open-records-list` element.

- [ ] **AC 3 (severity-priority sort):** Given one equipment item with three open repair records (`severity='Down', created_at=2026-05-01`; `severity='Not Sure', created_at=2026-04-01`; `severity='Degraded', created_at=2026-04-15`), when `generate()` is called, then in the HTML the `Down` record appears before the `Degraded` record, which appears before the `Not Sure` record (severity-priority ascending; ties broken by older `created_at` first).

- [ ] **AC 4 (severity color mapping):** Given open repair records with severities `'Down'`, `'Degraded'`, `'Not Sure'`, and `None`, when `generate()` is called, then their `<li class="open-record …">` elements receive classes `open-record-red`, `open-record-yellow`, `open-record-yellow`, and `open-record-gray` respectively, and the `None`-severity record does **not** render a `<span class="record-severity">[…]</span>` badge.

- [ ] **AC 5 (ETA optional):** Given an open repair record with `eta=None`, when `generate()` is called, then its rendered `<li class="open-record …">` does not include a `record-eta` span and contains no `ETA:` substring within that record's `<li>`.

- [ ] **AC 6 (top sub-heading present and positioned):** Given any non-empty status dashboard, when `generate()` is called, then the HTML contains exactly one element matching `<div class="generated-at">` whose `find()` position in the document is greater than the position of `</h1>` and less than the position of the first `<div class="area">`. Its inner text starts with `Generated: ` followed by a `YYYY-MM-DD HH:MM:SS ` (including seconds) and a non-empty timezone token.

- [ ] **AC 7 (local-timezone helper, monkey-patchable):** Given the helper `_compute_generated_at()` is patched to return `('2026-05-11 14:32:15 EDT', 2026)`, when `generate()` is called, then the HTML contains the exact substring `Generated: 2026-05-11 14:32:15 EDT` in the `<div class="generated-at">`. The helper's source uses `datetime.now().astimezone()` with no explicit `UTC` argument, and detects the no-tzname case via `dt.tzname()` (not via string inspection of the formatted output).

- [ ] **AC 8 (timezone fallback for unnamed offsets):** Given a `datetime` whose `tzinfo.tzname(dt)` returns `None` or `''`, when `_compute_generated_at()` is called, then the returned timestamp string contains an ISO offset like `+0000` or `-0400` (no empty trailing space, no `None` token).

- [ ] **AC 9 (site footer replaces "Generated:" line):** Given any rendering, when `generate()` is called, then the HTML contains a `<footer class="site-footer">` element whose text includes `© <YEAR> Jason Antman`, an anchor to `https://github.com/jantman/equipment-status-board`, and an anchor to `https://opensource.org/license/mit` (text `MIT licensed`), AND the HTML does NOT contain the old `<div class="footer">` element.

- [ ] **AC 10 (footer year matches generation timestamp year):** Given the helper `_compute_generated_at()` is patched to return year `2027`, when `generate()` is called, then the rendered footer contains `© 2027 Jason Antman` (the local-tz year, not `current_year` UTC).

- [ ] **AC 11 (still self-contained — no external sub-resources):** When `generate()` is called, then the HTML contains no `<link …>`, no `<script src="…">`, and no `<img src="http…">` or other external sub-resource references. Anchor (`<a href="…">`) links to external sites are permitted. The meta CSP tag's full directive `default-src 'none'; style-src 'unsafe-inline'` is unchanged.

- [ ] **AC 12 (existing tests preserved):** Existing tests in `tests/test_services/test_static_page_service.py` continue to pass after Task 4 case 17's adjustment (drop the `'UTC' in html` assertion in `test_includes_generated_timestamp`; replace with `'Generated:' in html`).

- [ ] **AC 13 (XSS defense — description is HTML-escaped):** Given a repair record with `description='<script>alert(1)</script><img src=x onerror=y>'`, when `generate()` is called, then the HTML contains `&lt;script&gt;` (escaped) and does NOT contain the literal `<script>alert(1)</script>` as a tag.

- [ ] **AC 14 (description preserves newlines and wraps long text):** Given a repair record with a multi-line `description` containing `\n`, when `generate()` is called, then the rendered `.record-description` span carries inline CSS `white-space: pre-wrap; overflow-wrap: anywhere;` (verified by asserting the rule appears in the page's `<style>` block — no DOM rendering check required).

- [ ] **AC 15 (footer-text drift detector):** Given the source file `esb/templates/components/_footer.html`, when `generate()` is called, then the three load-bearing substrings from `_footer.html` (`Jason Antman`, `https://github.com/jantman/equipment-status-board`, `https://opensource.org/license/mit`) all appear in the rendered static page HTML. If the live footer changes any of these, this AC fails and the static page must be updated.

- [ ] **AC 16 (single-line equipment row preserved):** When `generate()` is called for an area with at least one equipment item, then the HTML contains a `<div class="equipment-row">` wrapper, and within that wrapper the substrings `status-dot`, `equipment-name`, and `status-label` appear in that order. The new `<ul class="open-records-list">` (when rendered) is outside this wrapper but inside the parent `<li class="equipment-item">`.

- [ ] **AC 17 (`get_area_status_dashboard()` returns `open_records`):** Given an equipment item with two non-closed repair records and one record with `status='Resolved'`, when `get_area_status_dashboard()` is called, then `result[0]['equipment'][0]['open_records']` is a `list` of exactly 2 `RepairRecord` instances (the non-closed ones), in `(severity priority ASC, created_at ASC, id ASC)` order.

- [ ] **AC 18 (deployment-default TZ wired):** Given `docker-compose.yml` defines the `worker` service, when the file is read, then its `environment:` block includes a `TZ=${TZ:-America/New_York}` entry. (Verified by reading the YAML in a test or by visual inspection during code review; not a Python unit test.)

- [ ] **AC 19 (admin docs include TZ row):** Given `docs/administrators.md`, when grepped for `| \`TZ\` |`, then a row exists in the Environment Variable Reference table documenting the variable, its default, and an example value.

## Additional Context

### Dependencies

None new — uses existing `datetime`, `zoneinfo` (stdlib), Flask, Jinja2. No DB migration. No new Python packages.

### Testing Strategy

**Unit tests (pytest, SQLite in-memory per `TestingConfig`):**

All new tests live in `tests/test_services/test_static_page_service.py` (HTML-level) and `tests/test_services/test_status_service.py` (service-level). Use the existing fixtures: `app`, `make_area`, `make_equipment`, `make_repair_record`. The `make_repair_record(equipment, status='New', description='X', **kwargs)` signature accepts `RepairRecord` column kwargs (`severity`, `eta`, `created_at`, etc.); it does NOT accept `area` or `name`.

Strategy for tz-sensitive tests: **never** assert on the unpatched host clock. Either patch `_compute_generated_at()` to return a known string, or patch `datetime.now().astimezone()` to return a fixed `datetime` with a known `tzinfo`. This keeps tests deterministic on UTC CI runners.

| Test | Covers AC |
| ---- | --------- |
| `test_open_records_listed_for_non_green_equipment` | AC 1 |
| `test_open_records_omitted_for_green_equipment` | AC 2 |
| `test_open_records_sorted_by_severity_priority_then_created_at` | AC 3 |
| `test_open_records_uses_yellow_class_for_degraded_and_not_sure` | AC 4 |
| `test_open_records_uses_gray_class_for_no_severity` | AC 4 (None branch) |
| `test_open_records_omits_eta_when_unset` | AC 5 |
| `test_generated_at_subheading_renders_above_areas` | AC 6 |
| `test_generated_at_uses_local_timezone_helper` | AC 7 |
| `test_compute_generated_at_uses_tzname_when_present` | AC 7 (helper) |
| `test_compute_generated_at_falls_back_to_offset_when_tzname_empty` | AC 8 |
| `test_site_footer_replaces_old_generated_line` | AC 9 |
| `test_footer_renders_local_tz_year` | AC 10 |
| (modified) `test_produces_self_contained_html` and `test_csp_meta_tag_directive_unchanged` | AC 11 |
| (modified) `test_includes_generated_timestamp` | AC 12 |
| `test_description_is_html_escaped` | AC 13 |
| (assert CSS rule in `<style>`) `test_description_has_prewrap_styles` | AC 14 |
| `test_footer_pins_to_live_footer_text` | AC 15 |
| `test_equipment_row_keeps_dot_name_label_on_one_line` | AC 16 |
| `test_status_service.test_includes_open_records_list_per_equipment` | AC 17 |
| `test_status_service.test_open_records_sorted_by_severity_then_created_at` | AC 17 (sort) |

AC 18 and AC 19 are configuration/documentation criteria verified by code review (or trivially by `grep` in a CI step).

**Manual / smoke testing:**

1. Apply the changes locally.
2. `make db-up && make migrate && make run` and create at least one Area, two Equipment items, and one open `RepairRecord` per equipment (one `Down`, one `Degraded`, one `Not Sure` or `None`) via the staff UI. Include one long-text description and one multi-line description to verify wrap behavior.
3. Set `TZ=America/New_York` in shell before running `flask shell`, then `from esb.services import static_page_service; print(static_page_service.generate())` (or hit the export path on disk via `STATIC_PAGE_PUSH_METHOD=local`).
4. Open the resulting `index.html` in a browser. Verify:
   - Top right under the title: `Generated: 2026-05-11 14:32:15 EDT` (or local zone).
   - Equipment header (dot + name + label + ETA) on a single line under each area.
   - Under each non-green equipment item: a list with one row per open record, colored by severity, showing status + `[severity]` badge + description (multi-line / long text wrapping correctly) + ETA (when set). Records sorted with `Down` records on top.
   - Bottom: centered copyright footer with the GitHub and MIT license links; year matches the generation sub-heading year.
   - View source: no `<link>`, no `<script src=...>`, no external `<img>`; CSP meta tag value is `default-src 'none'; style-src 'unsafe-inline'` verbatim.
5. Repeat with `TZ=UTC` to verify the UTC fallback rendering matches expectations.

### Notes

**Production timezone configuration.** The default `docker-compose.yml` now sets `TZ=America/New_York` on the `worker` service to match the makerspace's location. Operators in other zones override via the `TZ` env var in `.env` (e.g., `TZ=America/Chicago`). Documented in `docs/administrators.md` Environment Variable Reference. `app` service does not need TZ (does not render the static page).

**Risk: timezone test flakiness.** Mitigated. All tz-sensitive tests patch either `_compute_generated_at()` or `datetime.now().astimezone()`. No test depends on the runner's `TZ` env var. Avoid asserting raw `EDT`/`EST` against an unpatched clock.

**Risk: live dashboard / Slack regression.** Task 1 adds an `open_records` key to the dict returned by `get_area_status_dashboard()`. Audited consumers: `public/status_dashboard.html`, `public/kiosk.html`, `public/equipment_page.html` (different route, not affected), `esb/slack/forms.py::format_status_summary`, `esb/slack/forms.py::format_area_status_detail`, `esb/slack/handlers.py:288`. None iterate or reference `open_records`. Task 8 runs the full suite — including `tests/test_slack/` — to confirm.

**Risk: severity-priority sort change.** Spec changes the sort from "created_at ASC oldest-first" to "severity priority then created_at ASC." This is the right call for the static fallback view but is a visible behavior change vs. the previously-shipped behavior of the highest-severity-only display. The change affects only the static page's repair list (a new feature), not the equipment-level status dot which was already severity-derived. No callers depend on the old "created_at order" because the `open_records` list itself is new.

**Risk: footer drift detector test could become flaky.** AC 15 / Task 4 case 13 reads `_footer.html` from disk and asserts substrings. If someone edits `_footer.html` to change the owner name, the test fails. That is **intentional** — the failure prompts the implementer to also update the static-page footer. Not a flake; it's a coupling alarm.

**Risk: `severity=None` repair records.** Repair creation paths set severity by default, but the column is nullable. Spec handles `None` explicitly in (a) sort key (priority `999` → sorted last), (b) template class mapping (`open-record-gray`), (c) severity-badge rendering (`{% if rec.severity %}…{% endif %}` guards the `[…]` text). Tests cover this branch.

**Explicit non-decisions:**
- **No cap on records displayed per equipment.** Static page is the fallback view; full information takes priority over visual tidiness in the rare worst case. (F20 decision.)
- **Severity text badge `[Down]` retained** as accessibility/redundancy for color-coding. (F19 decision.)

**Future / out of scope (do not implement now):**
- Per-area kiosk static export (would require extending `get_single_area_status_dashboard()` similarly).
- Showing `specialist_description` or `assignee` on the static page (privacy / clutter concerns).
- Localizing the timestamp into a non-system timezone via an app-level config var (currently driven by OS `TZ`).

GitHub issue #44 text:
> 1. The static status page currently just shows a list of equipment by area and operational/degraded/down state. For degraded or down equipment this should also include a list of the open repair records, their status, ETA if set, and description.
> 2. There is currently a small unobtrusive "Generated:" line at the bottom of the static page. Let's replace that with the copyright footer used on the live site, and add a sub-heading near the top right under "Equipment Status" that gives the generated date and time in the local/system timezone.

### Adversarial Review Resolution

Findings F1–F20 from the 2026-05-11 adversarial review applied:

| ID | Resolution |
| --- | --- |
| F1 (AC 7 unenforceable) | Rewrote AC 7 to assert via monkey-patched `_compute_generated_at()`, not host env. |
| F2 (function-scoped `datetime` defeats patch) | Hoisted import to module top; added `_compute_generated_at()` helper at module scope (Task 2). |
| F3 (worker TZ broken by default) | Added `TZ=${TZ:-America/New_York}` to `docker-compose.yml` worker (Task 6); documented in `docs/administrators.md` (Task 7). |
| F4 (hallucinated `kiosk_area.html`) | Removed; corrected consumer list to actual files audited. |
| F5 (Slack consumers missed) | Audited and listed: `esb/slack/forms.py`, `esb/slack/handlers.py`. None affected by additive key. |
| F6 (trailing-space fallback brittle) | Detect fallback via `dt.tzname()` directly; build timestamp by concatenation, not `%Z` format. |
| F7 (description wrap policy) | Decision: CSS `white-space: pre-wrap; overflow-wrap: anywhere;` on `.record-description`. AC 14 added. |
| F8 (CSS layout non-atomic) | Spec now contains the full template diff in Task 3. AC 16 added. |
| F9 (footer drift) | Added test that pins static-page footer to `_footer.html` substrings (Task 4 case 13, AC 15). |
| F10 (no service-level test) | Added `tests/test_services/test_status_service.py` cases (Task 5, AC 17). |
| F11 (XSS escape not asserted) | Added `test_description_is_html_escaped` (Task 4 case 14, AC 13). |
| F12 (fixture kwargs doc) | Corrected: `make_repair_record(equipment, status, description, **kwargs)`; `area`/`name` not accepted. |
| F13 (sort policy) | Decision: severity priority then `created_at` ASC. (Task 1, AC 3.) |
| F14 (ordering test fragile) | Task 4 case 10 specifies explicit `datetime(…, tzinfo=UTC)` values. |
| F15 (CSP test weak) | Strengthened to assert verbatim directive contents (Task 4 case 15). |
| F16 (no seconds) | Decision: include seconds → `%Y-%m-%d %H:%M:%S`. |
| F17 ("self-contained" wording) | Clarified: "no external sub-resources" vs. anchor links to external sites permitted (AC 11). |
| F18 (year mismatch) | Decision: pass local-tz `generated_year` to template; footer uses it (Task 2/3, AC 10). |
| F19 (severity badge beyond ask) | Decision: keep badge for accessibility; called out as enhancement in Overview. |
| F20 (record cap) | Decision: no cap; documented in Notes/Explicit non-decisions. |
