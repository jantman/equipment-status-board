---
title: 'Static status page export improvements'
slug: 'static-status-page-export-improvements'
created: '2026-05-11'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'Jinja2', 'pytest', 'Docker (python:3.14-slim)']
files_to_modify:
  - 'esb/services/static_page_service.py'
  - 'esb/services/status_service.py'
  - 'esb/templates/public/static_page.html'
  - 'tests/test_services/test_static_page_service.py'
  - 'tests/test_services/test_status_service.py'
  - 'docker-compose.yml'
  - 'Dockerfile'
  - 'docs/administrators.md'
code_patterns:
  - 'esb.services.status_service.get_area_status_dashboard() returns areas with computed status only — needs extension to expose ALL open repair records per equipment'
  - 'esb.templates.components._footer.html is the site copyright footer used on live pages; references current_year context var (injected in esb/__init__.py)'
  - 'esb.utils.filters.format_date is a registered Jinja filter'
  - 'esb.slack.forms.format_status_summary and format_area_status_detail consume the dashboard dict shape'
test_patterns:
  - 'tests/test_services/test_static_page_service.py uses make_area, make_equipment, make_repair_record fixtures; asserts on substrings in generated HTML'
  - 'fixtures: make_repair_record(equipment=None, status="New", description="Test issue", **kwargs) — kwargs become RepairRecord column values (severity, eta, created_at, etc.). NOTE: if equipment is omitted, the fixture auto-creates a fresh Area+Equipment.'
revision_history:
  - '2026-05-11 — initial spec'
  - '2026-05-11 — applied 20 adversarial-review findings (R1F1–R1F20)'
  - '2026-05-11 — applied real findings from round-2 adversarial review (R2F1–R2F19)'
---

# Tech-Spec: Static status page export improvements

**Created:** 2026-05-11
**Revised:** 2026-05-11 (post-R1 adversarial review, post-R2 adversarial review)

GitHub Issue: [#44](https://github.com/jantman/equipment-status-board/issues/44)

## Overview

### Problem Statement

The static status page (`esb/services/static_page_service.py` → `esb/templates/public/static_page.html`) — exported to local disk / S3 / GCS for public-facing display when the live Flask site is unavailable — has two presentation gaps:

1. **No repair detail for non-green equipment.** It lists each equipment item by area with a status dot (green/yellow/red), a label, and (for the highest-severity record only) an ETA. When equipment is Degraded or Down, the page does not enumerate the **open repair records** with their per-record status, ETA, and description, so a reader cannot see *why* equipment is impaired or *what is being done about it*.
2. **Generation metadata is inconsistent and visually weak.** A small "Generated: YYYY-MM-DD HH:MM UTC" line at the very bottom is the only branding/footer content. The live site uses a richer copyright/license footer (`esb/templates/components/_footer.html`). The static export should match the live look-and-feel (including its accessibility attributes), and the generation timestamp should be more prominent and in local/system timezone (not UTC).

### Solution

Update `static_page_service.generate()` to pass through (a) the open repair records per non-green equipment item (sorted by severity priority, then `created_at` ASC) and (b) a generation timestamp in the system's local timezone (with seconds). Update `esb/templates/public/static_page.html` to (i) render a list of open repair records — with each record's status, severity, ETA, and description — nested under each non-green equipment item; (ii) add a generation-time sub-heading immediately under the `<h1>Equipment Status</h1>` title, right-aligned, in local timezone; (iii) replace the bottom "Generated:" line with the site's copyright/license footer text (inlined verbatim including the `aria-label` attributes and `<small>` wrapper — the static page must remain CSP-locked and have no external **sub-resources**, though anchor links to external sites are permitted). Configure the `worker` container's `TZ` env via `docker-compose.yml` AND install the `tzdata` package in the `Dockerfile` so the configured zone actually resolves; document the env var in `docs/administrators.md`.

**Note on scope additions beyond issue #44's literal text:** The issue lists status, ETA, and description as required per-record fields. This spec additionally includes (a) a textual severity badge `[Down]` / `[Degraded]` / `[Not Sure]` per record — for accessibility, since color alone (the left-border indicator) is a WCAG concern; (b) sort-by-severity-priority — so the most urgent records bubble to the top at a glance, since this is the fallback view when the live site is down. These are explicitly called out as enhancements.

### Scope

**In Scope:**
- `esb/services/status_service.py` — extend `get_area_status_dashboard()` to include per-equipment `open_records` list, sorted by severity priority then `created_at` ASC. Unknown severities (and `None`) sort at "Not Sure" priority, matching the equipment-level fallback behavior.
- `esb/services/static_page_service.py` — compute local-tz generation timestamp (with seconds), pass local-tz year to the template.
- `esb/templates/public/static_page.html` — repair-record list under non-green items, top sub-heading with generated time, replace bottom footer with inlined copyright text + a11y attributes.
- Inline the copyright footer markup/text into the static template, including the live footer's `aria-label` attributes and `<small>` wrapper (the static page must have no external sub-resources — same self-contained / `default-src 'none'` CSP rule).
- `docker-compose.yml` — set `TZ=${TZ:-America/New_York}` as the default `worker`-service environment variable.
- `Dockerfile` — add `tzdata` to the `apt-get install` line so the configured `TZ` env var actually resolves against `/usr/share/zoneinfo/`.
- `docs/administrators.md` — document the `TZ` environment variable in the Environment Variable Reference table.
- `tests/test_services/test_static_page_service.py` — cover the new repair list, footer, generation-time placement, XSS escape, CSP directive integrity, pre-wrap CSS, footer a11y attributes.
- `tests/test_services/test_status_service.py` — regression test for the new `open_records` key in `get_area_status_dashboard()`.

**Out of Scope:**
- Live `public/status_dashboard.html`, kiosk views, or equipment-info pages.
- Database schema changes.
- Push delivery backends (`_push_local`, `_push_s3`, `_push_gcs`) — unchanged.
- Changes to `status_service` status derivation (color/label/severity logic stays as-is).
- Reuse of `_footer.html` via `{% include %}` — static export must remain self-contained.
- Pagination / cap on the number of open records displayed per equipment (explicit decision — see Notes).
- `get_single_area_status_dashboard()` extension (per-area kiosk static export).
- Empty-`tzname()` fallback in `_compute_generated_at()` — CPython 3.11+ always emits a non-empty tzname; the fallback branch added in v2 was unreachable in production and is dropped (see Decision #3).

## Context for Development

### Codebase Patterns

- **Self-contained static page.** `static_page.html` declares `Content-Security-Policy: default-src 'none'; style-src 'unsafe-inline'` and uses only inline `<style>`. The page must continue to render with no external **sub-resources** — no `<link>`, no `<script src=>`, no `<img src=…>` to external hosts. Anchor links (`<a href="…">`) to external sites are user-initiated navigation, not auto-fetched sub-resources, and are permitted under this CSP. Existing test `test_produces_self_contained_html` enforces no `<link>` / `<script src=>`.
- **Status derivation lives in `esb/services/status_service.py`.** `get_area_status_dashboard()` currently emits one `status` dict per equipment (computed from the highest-severity open record). The new requirement needs **all open repair records** per non-green equipment. Approach: extend `get_area_status_dashboard()` to additionally include the per-equipment list of `RepairRecord` instances in each entry (e.g., `open_records: list[RepairRecord]`). The records are already prefetched and grouped by `equipment_id` in the existing implementation (`records_by_equipment` dict). The new key is sorted by `(severity priority ASC, created_at ASC)` using `_SEVERITY_STATUS`; the prefetch query is already ordered by `(created_at ASC, id ASC)` and Python's `list.sort()` is stable, so the `id`-ASC tiebreak is preserved naturally without being in the sort key. Existing callers ignoring the new key continue to work.
- **Consumers of `get_area_status_dashboard()` return value** (audited 2026-05-11):
  - `esb/templates/public/status_dashboard.html` — iterates `area_data.equipment[*].equipment` and `.status` only.
  - `esb/templates/public/kiosk.html` — same.
  - `esb/views/public.py` `kiosk_area()` route — passes a single-area dict (from `get_single_area_status_dashboard()`, not changed here) into `public/kiosk.html`.
  - `esb/slack/forms.py` `format_status_summary(dashboard_data)` and `format_area_status_detail(area_data)` — iterate `equipment` and `status` only.
  - `esb/slack/handlers.py` `/esb-status` command path — calls `format_status_summary()`.
  - None of the above reference `open_records`, so the additive key change does not require any caller updates. The full test suite (Task 9) is the regression net.
- **`current_year` is injected via `app.context_processor` in `esb/__init__.py`** (`inject_current_year`); that processor works for `render_template()` calls so it is available to the static template without explicit kwargs. **However**, it is derived from `datetime.now(timezone.utc).year`, which can disagree with the static page's local-tz generation timestamp for a few hours either side of midnight Dec 31. Spec passes a local-tz year as a separate template var (`generated_year`) and the footer uses that, not `current_year`, to keep the two timestamps consistent (see Decision #7).
- **Jinja filter `format_date`** (in `esb/utils/filters.py`) is registered on the app's Jinja env and usable from any template, including the static one.
- **`RepairRecord` model fields** (confirmed in `esb/models/repair_record.py`):
  - `status: str` from `REPAIR_STATUSES = ['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered', 'Parts Received', 'Needs Specialist', 'Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']`. Non-closed = anything not in `CLOSED_STATUSES = ('Resolved', 'Closed - No Issue Found', 'Closed - Duplicate')`.
  - `severity: str | None` from `REPAIR_SEVERITIES = ['Down', 'Degraded', 'Not Sure']`. Column has **no DB-level CHECK constraint** — unknown strings are possible in legacy/future data.
  - `description: str` (Text, non-null). Can be multi-line and effectively unbounded.
  - `eta: date | None`.
  - `created_at: datetime` (UTC).
- **Severity → color map** (`status_service._SEVERITY_STATUS`): `Down`→red (priority 0), `Degraded`→yellow (priority 1), `Not Sure`→yellow (priority 2). For records whose severity is `None` or any *unknown* string, both the equipment-level status derivation (`status_service.py` `_derive_status_from_records`, "fall through to yellow/Degraded" branch) and the new sort key fall back to the **`Not Sure` priority (2)**. This keeps equipment-level rendering and record-list ordering consistent — a yellow-coded equipment cannot contain a record that sorts beneath a Not-Sure record (Round-2 finding R2F8). Per-record visual styling (`open-record-gray` left border) is independent of the sort priority.
- **Local-timezone formatting.** No existing helper. Place the implementation in a module-level helper `_compute_generated_at()` in `static_page_service.py` (NOT inline in `generate()`) so tests can monkey-patch it directly. Format: `'%Y-%m-%d %H:%M:%S %Z'` → `2026-05-11 14:32:15 EDT`. Build the string by concatenation of `dt.strftime('%Y-%m-%d %H:%M:%S ')` and `dt.tzname()` (rather than using `%Z`) so the trailing token is explicit and never an empty trailing space. No fallback branch — under CPython 3.11+ with `tzdata` available in the runtime, `datetime.now().astimezone()` always returns a `datetime` whose `tzinfo` produces a non-empty `tzname()`. The Dockerfile change (Task 8) ensures `tzdata` is present.
- **Reference data shape only** (not visual precedent): `esb/templates/public/equipment_page.html`'s `open_repairs` list shows the conceptual shape (one row per open record, severity-styled, description visible, ETA when set). The actual styling cannot be copied — `equipment_page.html` uses Bootstrap classes (`card`, `card-body`, `mb-2`, etc.) which are unavailable in the static export. The static page reimplements the layout in inline CSS.
- **Test fixtures** (`tests/conftest.py`):
  - `make_area(name='Test Area', slack_channel='#test-area')` → `Area`.
  - `make_equipment(name='Test Equipment', manufacturer='TestCo', model='Model X', area=None, **kwargs)` → `Equipment` (extra kwargs forwarded to model constructor). If `area=None`, the fixture auto-creates a fresh area.
  - `make_repair_record(equipment=None, status='New', description='Test issue', **kwargs)` → `RepairRecord`. Extra kwargs (`severity`, `eta`, `created_at`, `assignee_id`, `reporter_name`, etc.) are forwarded to the `RepairRecord` constructor. **The fixture does NOT accept `area` or `name` kwargs.** **If `equipment` is omitted, the fixture auto-creates a fresh Area + Equipment** — always pass `equipment=…` explicitly in the new tests to avoid surprise side-effects.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/services/static_page_service.py` | Modify `generate()`; add `_compute_generated_at()` module-level helper. |
| `esb/services/status_service.py` | Extend `get_area_status_dashboard()` with the new `open_records` key. |
| `esb/templates/public/static_page.html` | Render repair list, top-right generation timestamp, inline a11y-attributed copyright footer. |
| `esb/templates/components/_footer.html` | Source of truth for the copyright/license text, link targets, and a11y attributes (used as reference; not included via `{% include %}`). |
| `esb/__init__.py` | `inject_current_year` context processor (already wired; not modified — local-tz year is passed separately). |
| `esb/utils/filters.py` | `format_date` Jinja filter. |
| `esb/slack/forms.py`, `esb/slack/handlers.py` | Existing consumers of `get_area_status_dashboard()`; verified not affected by the additive `open_records` key. |
| `docker-compose.yml` | Add `TZ=${TZ:-America/New_York}` to the `worker` service. |
| `Dockerfile` | Add `tzdata` to the `apt-get install` line so the configured `TZ` resolves against `/usr/share/zoneinfo/`. **Without `tzdata`, `python:3.14-slim` falls back to UTC silently regardless of the `TZ` env var.** |
| `docs/administrators.md` | Document the `TZ` env var in the Environment Variable Reference section. |
| `tests/test_services/test_static_page_service.py` | Existing test class `TestGenerate`; add cases for repair list, top-right timestamp, inline footer, footer-text pin, XSS escape, CSP directive integrity, pre-wrap CSS, footer a11y attributes. |
| `tests/test_services/test_status_service.py` | Add regression test for `open_records` key. |
| `tests/conftest.py` | Fixture definitions (`make_area`, `make_equipment`, `make_repair_record`). |

### Technical Decisions

1. **Extend `get_area_status_dashboard()` to include an `open_records` list per equipment.** Records are already prefetched and grouped in `records_by_equipment`; threading the list through is a one-line change. Rejected the "new helper" option to avoid duplicating ~40 lines of prefetch code. Existing callers (live dashboard, kiosk, Slack formatters) ignore the new key.
2. **Sort open records by `(severity priority, created_at)` ASC.** Rationale: the static page is the fallback at-a-glance view. Sorting by severity ensures `Down` records bubble above `Degraded`/`Not Sure`/unknown within each equipment's record list. Sort key: `(priority, rec.created_at)` where `priority = _SEVERITY_STATUS.get(rec.severity, (..., ..., _SEVERITY_STATUS['Not Sure'][2]))[2]`. **No `id` in the sort key** — Python's `list.sort()` is stable and the prefetch query order (`created_at ASC, id ASC`) is preserved on ties. **Unknown severity strings and `None` both fall back to the `Not Sure` priority (2)** — same as the equipment-level status derivation — to avoid an inversion where the equipment dot says yellow but the unknown-severity record sorts beneath Not-Sure records (R2F8).
3. **Local-timezone generation timestamp.** Implemented in module-level helper `_compute_generated_at()` in `static_page_service.py` (so tests can patch it). Uses `datetime.now().astimezone()` (no `tzinfo` argument) — Python picks up the host system's TZ from `TZ` env / `/etc/localtime`. Format: `'%Y-%m-%d %H:%M:%S '` + `dt.tzname()` → `2026-05-11 14:32:15 EDT`. Seconds are included for debugging value when multiple pushes happen within a minute. **No empty-tzname fallback branch** — under CPython 3.11+ with `tzdata` present (Dockerfile Task 8), `astimezone()` always returns a tzinfo whose `tzname()` is non-empty. If a future runtime change ever produces `None`/empty, the code will fail loudly with a `TypeError` on string concatenation — which is the correct loud-failure mode for an invariant violation, vs. a silent fallback that masks a deployment problem.
4. **Footer text is inlined verbatim** from `_footer.html` (copyright line + GitHub link + MIT license link, INCLUDING `<small>` wrapper and all `aria-label` attributes) into `static_page.html`, NOT included via `{% include %}`. Reasons: (a) the static page must remain self-contained (no external sub-resources); (b) an include couples the export to a fragment used by the live site, which is brittle if that fragment later pulls in Bootstrap classes; (c) copyright text is short and stable. **Drift mitigation:** Task 4 case 13 adds a unit test that loads `_footer.html` through Flask's Jinja loader and asserts its **three load-bearing substrings** (`Jason Antman`, the GitHub URL, the MIT URL) appear in the rendered static page. The test is explicitly named `test_footer_text_pin` (not "drift detector") — it pins owner + URLs only, NOT year-token markup or `<small>`/aria attribute wrapping. Those are covered by their own ACs (AC 9 / AC 9a).
5. **Per-record styling**. Repair-record `<li>` items use a small inline left-border indicator color-coded by severity using the same mapping as the equipment-level dot (`Down`→red, `Degraded`/`Not Sure`→yellow, no severity → gray). Display order within the record: `[status badge] [severity badge if set] description …ETA: …`. Severity text badge is **retained** (e.g., `[Down]`) as an accessibility/redundancy feature — color alone is a WCAG concern, and the text badge gives the same information non-visually. This is called out as a spec-added enhancement beyond issue #44's literal ask.
6. **Description wrap, not truncate.** `RepairRecord.description` is unbounded Text. Apply inline CSS `white-space: pre-wrap; overflow-wrap: anywhere;` to `.record-description` so multi-line descriptions render correctly and long un-broken strings (URLs, etc.) wrap rather than overflow the page. **No truncation** — the static page is a fallback view and full text is more useful than an ellipsis.
7. **Local-tz year for the footer.** Compute the footer year from the same `datetime` used by `_compute_generated_at()` (Python's `datetime.astimezone()` returns a `datetime` whose `.year` is the converted local-tz year, not the source UTC year — verified empirically). Pass it to the template as a separate kwarg `generated_year`. The footer renders `&copy; {{ generated_year }} Jason Antman`. The `current_year` context processor (UTC) is left alone so the live site is unaffected. This avoids the ~5-hour disagreement window around midnight Dec 31.
8. **Generation sub-heading placement.** Below the `<h1>Equipment Status</h1>` block, right-aligned via `text-align: right` on a `.generated-at` div (new CSS rule).
9. **Equipment-row layout wrapper.** Existing `.equipment-item` uses `display: flex` to lay out dot/name/label/eta on one line. Adding a nested `<ul>` for open records inside the same `<li>` would make the `<ul>` a flex sibling. Spec wraps the existing four spans into a new `<div class="equipment-row">` (with `display: flex; flex-wrap: wrap; align-items: center; gap: 0.5rem;`) and changes `.equipment-item` to `display: block`. The new `<ul class="open-records-list">` lays out beneath the row with `margin-top: 0.4rem` for visual separation. The full template diff is spelled out in Task 3.
10. **TZ default in `docker-compose.yml` AND `tzdata` in Dockerfile.** Set `TZ=${TZ:-America/New_York}` in the `worker` service `environment:` block. Add `tzdata` to the `apt-get install` line in `Dockerfile` — this is the **load-bearing change** for the local-tz feature to work at all in production. Without `tzdata`, the `python:3.14-slim` base image has no `/usr/share/zoneinfo/America/New_York`, so glibc's `tzset()` falls back to UTC and the env var is effectively ignored. The `app` service does not need either change because it does not render the static page; the worker is the sole producer via `generate_and_push()`.
11. **Module-level datetime import in `static_page_service.py`.** Hoist `from datetime import datetime` to module top (it is currently function-scoped). This is required for the `_compute_generated_at()` helper to exist at module scope, and it lets tests patch `static_page_service._compute_generated_at` directly.

## Implementation Plan

### Tasks

- [ ] **Task 1: Extend `get_area_status_dashboard()` to include sorted per-equipment open repair records.**
  - File: `esb/services/status_service.py`
  - Action:
    1. Inside `get_area_status_dashboard()`, after the `records_by_equipment` grouping, add a sort: for each list in `records_by_equipment.values()`, sort in place by `(priority, created_at)`. Helper:
       ```python
       _NOT_SURE_PRIORITY = _SEVERITY_STATUS['Not Sure'][2]

       def _open_records_sort_key(rec):
           sev_entry = _SEVERITY_STATUS.get(rec.severity)
           priority = sev_entry[2] if sev_entry else _NOT_SURE_PRIORITY
           return (priority, rec.created_at)

       for records in records_by_equipment.values():
           records.sort(key=_open_records_sort_key)
       ```
       Define `_NOT_SURE_PRIORITY` and `_open_records_sort_key` at module level (right after the `_SEVERITY_STATUS` dict definition near line 17-21). Do **not** introduce a separate `999` sentinel — unknown severities and `None` both map to `Not Sure` priority for sort purposes, matching the equipment-level fallback (R2F7, R2F8).
    2. In the loop that builds `equip_statuses`, add `'open_records': equip_records` to the dict appended for each equipment.
    3. Update the function's docstring to document the new `open_records` key — list of `RepairRecord` instances, sorted by `(severity priority, created_at)` with unknown severities folded to `Not Sure` priority; ties on those fields preserve the prefetch query's `(created_at, id)` ASC order (stable sort).
  - Notes: Existing live-page templates (`public/status_dashboard.html`, `public/kiosk.html`) and Slack formatters (`esb/slack/forms.py`) iterate `area_data.equipment` but reference only `item.equipment` and `item.status`. The additive key is safe. `get_single_area_status_dashboard()` is **not** changed.

- [ ] **Task 2: Add `_compute_generated_at()` helper and hoist `datetime` import in `static_page_service.py`.**
  - File: `esb/services/static_page_service.py`
  - Action:
    1. Move `from datetime import UTC, datetime` from inside `generate()` to the module-level imports. Remove the unused `UTC` if not referenced elsewhere.
    2. Add a module-level helper:
       ```python
       def _compute_generated_at() -> tuple[str, int]:
           """Compute the generation timestamp string and year in the system's local timezone.

           Returns:
               (timestamp_str, year) where timestamp_str is formatted like
               '2026-05-11 14:32:15 EDT'. year is the local-tz year of the
               same instant (datetime.astimezone() returns a datetime whose
               .year reflects the converted zone, not the source UTC year).

           Requires the runtime to have a non-empty tzname for the local
           zone — production deployments must include the tzdata package
           in the base image (see Dockerfile).
           """
           dt = datetime.now().astimezone()
           return (dt.strftime('%Y-%m-%d %H:%M:%S ') + dt.tzname(), dt.year)
       ```
       Build the string by concatenation (not `%Z`) so the trailing token is explicit. **No fallback branch** — if `dt.tzname()` is `None`, this fails loudly with a `TypeError`, which is the correct response to a deployment that violates the tzdata invariant.
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
            .site-footer { text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #dee2e6; font-size: 0.8rem; color: #6c757d; word-break: break-word; }
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
        <footer class="site-footer" role="contentinfo" aria-label="Site copyright and license">
            <small>&copy; {{ generated_year }} Jason Antman. <a href="https://github.com/jantman/equipment-status-board" rel="noopener noreferrer" aria-label="Source code on GitHub">github.com/jantman/equipment-status-board</a> <a href="https://opensource.org/license/mit" rel="noopener noreferrer" aria-label="MIT License (opensource.org)">MIT licensed</a>.</small>
        </footer>
    </body>
    </html>
    ```

  - Key changes vs. previous template: `.equipment-item` becomes `display: block`; the existing dot/name/label/eta row is wrapped in `<div class="equipment-row">`; new `<ul class="open-records-list">` rendered only when equipment is non-green AND has open records; old `<div class="footer">Generated: …</div>` replaced by `<footer class="site-footer" role="contentinfo" aria-label="Site copyright and license">` with a `<small>` wrapper and `aria-label` on the GitHub and MIT anchors (mirrors `_footer.html`); new `.generated-at` sub-heading directly under the `<h1>`. The footer uses `generated_year` (local-tz, from `_compute_generated_at()`), NOT `current_year`. The CSP directive is unchanged.

- [ ] **Task 4: Add tests in `tests/test_services/test_static_page_service.py`.**
  - File: `tests/test_services/test_static_page_service.py`
  - Add the following tests (inside `class TestGenerate` unless noted). Always pass `equipment=…` explicitly to `make_repair_record` to avoid the fixture auto-creating its own area/equipment.

    1. `test_generated_at_subheading_renders_above_areas` — Given an area with one equipment item, when `generate()` runs, then the HTML contains `<div class="generated-at">` and its `find()` index is greater than the index of `</h1>` and less than the index of the first `<div class="area">`.

    2. `test_generated_at_uses_local_timezone_helper` (covers AC 7a) — Monkey-patch `esb.services.static_page_service._compute_generated_at` to return `('2026-05-11 14:32:15 EDT', 2026)`. Call `generate()`. Assert HTML contains `Generated: 2026-05-11 14:32:15 EDT` and footer contains `2026`.

    3. `test_compute_generated_at_formats_tzname` (covers AC 7b, helper-level) — Use `unittest.mock.patch.object(static_page_service, 'datetime')` to make `datetime.now().astimezone()` return a real `datetime` with `tzinfo=ZoneInfo('America/New_York')` set to `2026-07-15 14:32:15` US Eastern. Call `_compute_generated_at()` directly. Assert returned tuple is `('2026-07-15 14:32:15 EDT', 2026)`.

    4. `test_open_records_listed_for_non_green_equipment` (covers AC 1) — Create equipment with one record `make_repair_record(equipment=eq, status='In Progress', severity='Down', description='Belt slipping', eta=date(2026, 6, 1))`. Call `generate()`. Assert HTML contains `'In Progress'`, `'[Down]'`, `'Belt slipping'`, and `'ETA: ' + date(2026, 6, 1).strftime('%b %d, %Y')`, AND contains the substring `class="open-record open-record-red"`.

    5. `test_open_records_omitted_for_green_equipment` (covers AC 2) — Create equipment with no repair records. Assert HTML does NOT contain `'open-records-list'`.

    6. `test_open_records_uses_yellow_class_for_degraded_and_not_sure` (covers AC 4) — Create two equipment items in the same area, one with `severity='Degraded'`, one with `severity='Not Sure'`. Assert HTML contains at least two occurrences of `'open-record-yellow'`.

    7. `test_open_records_uses_gray_class_for_no_severity` (covers AC 4 None branch) — Create a repair record passing `severity=None`. Assert HTML contains `'open-record-gray'` AND does NOT contain `'<span class="record-severity">'` for that record.

    8. `test_open_records_omits_eta_when_unset` (covers AC 5) — In a fresh test fixture, create exactly one equipment with one record `make_repair_record(equipment=eq, severity='Down', eta=None)`. Assert HTML does NOT contain `'record-eta'`. (Scoped to a single equipment so the global assertion is safe — no substring splitting required.)

    9. `test_open_records_sorted_by_severity_priority_then_created_at` (covers AC 3) — Create one equipment with three records: `(severity='Down', created_at=datetime(2026, 5, 1, tzinfo=UTC), description='down-newer')`, `(severity='Not Sure', created_at=datetime(2026, 4, 1, tzinfo=UTC), description='notsure-older')`, `(severity='Degraded', created_at=datetime(2026, 4, 15, tzinfo=UTC), description='degraded-mid')`. Insert in mixed order. Call `generate()`. Assert `html.find('down-newer') < html.find('degraded-mid') < html.find('notsure-older')`.

    10. `test_site_footer_replaces_old_generated_line` (covers AC 9) — Call `generate()`. Assert HTML contains `'<footer class="site-footer"'`, `'role="contentinfo"'`, `'aria-label="Site copyright and license"'`, `'<small>'`, `'Jason Antman'`, `'aria-label="Source code on GitHub"'`, `'aria-label="MIT License (opensource.org)"'`, `'github.com/jantman/equipment-status-board'`, `'MIT licensed'`, AND does NOT contain `'<div class="footer">'` (the old class).

    11. `test_footer_renders_local_tz_year_as_entity` (covers AC 10) — Monkey-patch `_compute_generated_at` to return `(..., 2027)`. Assert HTML footer contains the literal substring `&copy; 2027 Jason Antman` (HTML-entity form — Jinja does NOT decode `&copy;`).

    12. `test_footer_text_pin` (covers AC 12 — footer-text pin against `_footer.html`) — Load `_footer.html` source via Flask's Jinja loader: `source = app.jinja_env.loader.get_source(app.jinja_env, 'components/_footer.html')[0]`. From that source, extract three load-bearing substrings: `'Jason Antman'`, `'https://github.com/jantman/equipment-status-board'`, and `'https://opensource.org/license/mit'`. Assert each appears in the rendered static page HTML. Scope: this test ONLY pins owner + URLs — it does NOT detect changes to year-token markup, `<small>` wrapping, or aria-label text (those have dedicated assertions in case 10). If a future edit to `_footer.html` changes the owner name or a link URL, this test fails loudly and the static page must be updated in lockstep.

    13. `test_description_is_html_escaped` (covers AC 11 / XSS defense) — Create a repair record with `description='<script>alert(1)</script><img src=x onerror=y>'`. Call `generate()`. Assert HTML contains `'&lt;script&gt;'` (escaped) AND does NOT contain the literal `'<script>alert(1)</script>'`.

    14. `test_csp_meta_tag_directive_unchanged` (strengthens existing `test_includes_csp_meta_tag`) — Replace the existing test (or add a sibling) that asserts only `'Content-Security-Policy' in html` with: `assert "default-src 'none'; style-src 'unsafe-inline'" in html` (verbatim directive contents).

    15. `test_equipment_row_keeps_dot_name_label_on_one_line` (covers AC 14 layout) — Assert HTML contains `<div class="equipment-row">` and within that wrapper (slice to its closing tag), the order of substrings is `status-dot`, `equipment-name`, `status-label`.

    16. `test_description_uses_prewrap_styles` (covers AC 13 wrap CSS) — Assert HTML contains the substring `.record-description { white-space: pre-wrap; overflow-wrap: anywhere; }` inside the `<style>` block.

    17. **Update existing `test_includes_generated_timestamp`** — Replace `assert 'UTC' in html` with `assert 'Generated:' in html`. The timezone token now depends on host TZ / patched helper.

  - Notes:
    - Use `from datetime import UTC, datetime` (Python 3.11+) for `created_at` kwarg values.
    - The fixture `make_repair_record(equipment=None, status='New', description='Test issue', **kwargs)` — pass `equipment=…` explicitly to avoid auto-create side effects; pass `severity`, `eta`, `created_at` via kwargs.

- [ ] **Task 5: Add a regression test for the new `open_records` key in `tests/test_services/test_status_service.py`.**
  - File: `tests/test_services/test_status_service.py`
  - Add (in an existing `TestGetAreaStatusDashboard` class, or create one):

    1. `test_includes_open_records_list_per_equipment` — Create one area with one equipment item and two non-closed repair records and one closed record (`status='Resolved'`). Call `get_area_status_dashboard()`. Assert `result[0]['equipment'][0]['open_records']` is a `list` of length 2; the closed record is excluded; each entry is a `RepairRecord` instance.

    2. `test_open_records_sorted_by_severity_then_created_at` — Create one equipment with `Down/2026-05-01`, `Not Sure/2026-04-01`, `Degraded/2026-04-15`, `None/2026-03-01`, `'Critical'` (unknown severity) `/2026-02-01`. Call the dashboard. Assert the `open_records` list order is: `Down`, `Degraded`, then within priority-2 (`Not Sure`/`None`/`'Critical'`) sorted by `created_at` ASC — so `'Critical'` (oldest), then `None`, then `Not Sure`.

    3. `test_empty_open_records_list_for_green_equipment` — Create equipment with zero non-closed records. Assert `equipment[0]['open_records'] == []`.

  - Notes: Verify existing tests still pass — the new key is additive.

- [ ] **Task 6: Configure default TZ in `docker-compose.yml` worker service.**
  - File: `docker-compose.yml`
  - Action: In the `worker:` service's `environment:` block, add a new line: `      - TZ=${TZ:-America/New_York}`. Place it adjacent to the existing `PYTHONUNBUFFERED=1` and `WORKER_HEARTBEAT_PATH=…` entries.
  - Notes: The `${TZ:-America/New_York}` syntax means "use the `TZ` env var if set in `.env` or shell, otherwise default to `America/New_York`." This matches the makerspace location (Decatur Makers) while letting other deployments override. The `app` service does **not** need TZ — only the worker calls `generate()`.

- [ ] **Task 7: Document the `TZ` environment variable in `docs/administrators.md`.**
  - File: `docs/administrators.md`
  - Action: In the Environment Variable Reference table, add a new row:
    ```markdown
    | `TZ` | IANA timezone name for the worker container. Controls the timezone displayed in the static status page's generation timestamp (sub-heading near top of page) and the year used in the footer. Set this to your local timezone for accurate display. The `app` service does not use this variable. Requires the `tzdata` package in the Docker image (included by default — see Dockerfile). | No | `America/New_York` | `America/Chicago` |
    ```
  - Also add a short paragraph in the "Static Status Page Setup" section noting that the static page's generation timestamp reflects the `worker` container's `TZ` and that operators should set `TZ` in `.env` to match their local timezone. Add a sentence: "Note: the Docker image installs the `tzdata` package; without it, the `TZ` env var has no effect and timestamps render in UTC."

- [ ] **Task 8: Add `tzdata` to the Dockerfile so `TZ` actually resolves.**
  - File: `Dockerfile`
  - Action: In the existing `apt-get install` line, add `tzdata` alongside `gcc` and `libzbar0`:
    ```dockerfile
    RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc \
        libzbar0 \
        tzdata \
        && rm -rf /var/lib/apt/lists/*
    ```
  - Notes: Without `tzdata`, the `python:3.14-slim` base image has no `/usr/share/zoneinfo/` database, so glibc's `tzset()` cannot resolve `TZ=America/New_York` and falls back to UTC. This task is the load-bearing change for the whole local-tz feature; setting the env var in compose without this Dockerfile change is a no-op (Round-2 finding R2F1). `apt-get` non-interactive install of `tzdata` does not require additional `DEBIAN_FRONTEND=noninteractive` because Debian's bookworm-based slim images configure non-interactive apt by default in `Dockerfile` contexts; if the build prompts for tz selection, prepend `ENV DEBIAN_FRONTEND=noninteractive` before the `RUN` line.

- [ ] **Task 9: Run lint and full test suite.**
  - Commands: `make lint` then `make test`.
  - Expected: All green. Existing test `test_includes_generated_timestamp` was updated in Task 4 case 17; `test_produces_self_contained_html` continues to pass; existing `test_includes_csp_meta_tag` is replaced/strengthened per Task 4 case 14. The full suite covers Slack formatter tests (`tests/test_slack/`) which exercise consumers of `get_area_status_dashboard()` — confirms no regression.

### Acceptance Criteria

- [ ] **AC 1 (happy path — repair list rendered):** Given a non-archived area with one equipment item whose only open repair record has `status='In Progress'`, `severity='Down'`, `description='Belt slipping'`, `eta=date(2026, 6, 1)`, when `static_page_service.generate()` is called, then the returned HTML contains a `<ul class="open-records-list">` nested under that equipment's `<li class="equipment-item">` whose single `<li>` includes the substrings `In Progress`, `[Down]`, `Belt slipping`, and `ETA: Jun 01, 2026`, and has the CSS class substring `open-record-red`.

- [ ] **AC 2 (green equipment — no list):** Given a non-archived equipment item with zero open repair records, when `generate()` is called, then the HTML for that equipment contains no `open-records-list` element.

- [ ] **AC 3 (severity-priority sort, unknown folds to Not Sure):** Given one equipment item with five open repair records — `(severity='Down', created_at=2026-05-01)`, `(severity='Degraded', created_at=2026-04-15)`, `(severity='Not Sure', created_at=2026-04-01)`, `(severity=None, created_at=2026-03-01)`, `(severity='Critical', created_at=2026-02-01)` — when `generate()` is called, then in the HTML the records appear in the order: Down, Degraded, `'Critical'` (priority-2 tie, oldest `created_at`), None (priority-2 tie), Not Sure (priority-2 tie). Unknown severities and `None` both sort at the `Not Sure` priority; ties are broken by `created_at` ASC.

- [ ] **AC 4 (severity color mapping):** Given open repair records with severities `'Down'`, `'Degraded'`, `'Not Sure'`, and `None`, when `generate()` is called, then their `<li class="open-record …">` elements receive classes `open-record-red`, `open-record-yellow`, `open-record-yellow`, and `open-record-gray` respectively, and the `None`-severity record does **not** render a `<span class="record-severity">[…]</span>` badge.

- [ ] **AC 5 (ETA optional):** Given an open repair record with `eta=None`, when `generate()` is called for an area containing only that record's equipment, then the rendered HTML contains no `record-eta` substring.

- [ ] **AC 6 (top sub-heading present and positioned):** Given any non-empty status dashboard, when `generate()` is called, then the HTML contains exactly one element matching `<div class="generated-at">` whose `find()` position is greater than the position of `</h1>` and less than the position of the first `<div class="area">`. Its inner text starts with `Generated: ` followed by a `YYYY-MM-DD HH:MM:SS ` (including seconds) and a non-empty timezone token.

- [ ] **AC 7a (helper-wiring):** Given `_compute_generated_at()` is patched to return `('2026-05-11 14:32:15 EDT', 2026)`, when `generate()` is called, then the rendered HTML contains the exact substring `Generated: 2026-05-11 14:32:15 EDT` inside the `<div class="generated-at">`, and the footer year is `2026`.

- [ ] **AC 7b (helper formats tzname correctly):** Given a `datetime` whose `tzinfo` is `ZoneInfo('America/New_York')` set to `2026-07-15 14:32:15` local time, when `_compute_generated_at()` is called (with `datetime.now().astimezone()` patched to return that instance), then the helper returns exactly `('2026-07-15 14:32:15 EDT', 2026)`.

- [ ] **AC 8 (site footer with a11y attributes):** Given any rendering, when `generate()` is called, then the HTML contains a `<footer class="site-footer" role="contentinfo" aria-label="Site copyright and license">` element wrapping a `<small>` that contains: the entity sequence `&copy; <YEAR> Jason Antman`, an anchor `<a href="https://github.com/jantman/equipment-status-board" …>` with `aria-label="Source code on GitHub"`, and an anchor `<a href="https://opensource.org/license/mit" …>` with `aria-label="MIT License (opensource.org)"` and link text `MIT licensed`. The HTML does NOT contain `<div class="footer">` (the old element).

- [ ] **AC 9 (footer year matches generation timestamp year):** Given `_compute_generated_at()` is patched to return year `2027`, when `generate()` is called, then the rendered footer contains the literal substring `&copy; 2027 Jason Antman` (HTML-entity form — Jinja does NOT decode `&copy;`).

- [ ] **AC 10 (still self-contained — no external sub-resources):** When `generate()` is called, then the HTML contains no `<link …>`, no `<script src="…">`, and no `<img src="http…">` or other external sub-resource references. Anchor (`<a href="…">`) links to external sites are permitted. The meta CSP tag's full directive `default-src 'none'; style-src 'unsafe-inline'` appears verbatim.

- [ ] **AC 11 (XSS defense — description is HTML-escaped):** Given a repair record with `description='<script>alert(1)</script><img src=x onerror=y>'`, when `generate()` is called, then the HTML contains `&lt;script&gt;` (escaped) and does NOT contain the literal `<script>alert(1)</script>` as a tag.

- [ ] **AC 12 (footer-text pin against `_footer.html`):** Given the source of `esb/templates/components/_footer.html` loaded via Flask's Jinja loader (`app.jinja_env.loader.get_source(app.jinja_env, 'components/_footer.html')[0]`), when `generate()` is called, then the three load-bearing substrings from `_footer.html` (`Jason Antman`, `https://github.com/jantman/equipment-status-board`, `https://opensource.org/license/mit`) all appear in the rendered static page HTML. Scope clarification: this AC pins owner + URLs only. Year-token markup, `<small>` wrapping, and aria-label texts are covered by AC 8 / AC 9 — not by this AC.

- [ ] **AC 13 (description preserves newlines and wraps long text):** Given any rendering, when `generate()` is called, then the rendered HTML's `<style>` block contains the verbatim substring `.record-description { white-space: pre-wrap; overflow-wrap: anywhere; }`.

- [ ] **AC 14 (single-line equipment row preserved):** When `generate()` is called for an area with at least one equipment item, then the HTML contains a `<div class="equipment-row">` wrapper, and within that wrapper the substrings `status-dot`, `equipment-name`, and `status-label` appear in that order. The new `<ul class="open-records-list">` (when rendered) is outside this wrapper but inside the parent `<li class="equipment-item">`.

- [ ] **AC 15 (`get_area_status_dashboard()` returns `open_records`):** Given an equipment item with two non-closed repair records and one record with `status='Resolved'`, when `get_area_status_dashboard()` is called, then `result[0]['equipment'][0]['open_records']` is a `list` of exactly 2 `RepairRecord` instances (the non-closed ones), in `(severity priority ASC, created_at ASC)` order, with unknown severities folded to the `Not Sure` priority.

- [ ] **AC 16 (existing tests preserved):** Existing tests in `tests/test_services/test_static_page_service.py` continue to pass after Task 4 case 17's adjustment (drop the `'UTC' in html` assertion in `test_includes_generated_timestamp`; replace with `'Generated:' in html`).

### Documentation Checklist

These items are verified by code review at PR time, not by automated tests:

- [ ] **DC 1 (`docker-compose.yml` worker has TZ default):** The `worker` service's `environment:` block contains a `TZ=${TZ:-America/New_York}` entry.
- [ ] **DC 2 (`Dockerfile` installs `tzdata`):** The `apt-get install` line includes `tzdata`.
- [ ] **DC 3 (admin docs document `TZ`):** `docs/administrators.md` Environment Variable Reference table contains a row for `TZ` with description, default, and example. The Static Status Page Setup section mentions that the `worker` container's `TZ` controls the generation-timestamp display and that the Dockerfile installs `tzdata` to make the env var effective.

## Additional Context

### Dependencies

No new Python packages. Adds the OS-level `tzdata` package to the Docker image. No DB migration.

### Testing Strategy

**Unit tests (pytest, SQLite in-memory per `TestingConfig`):**

All new tests live in `tests/test_services/test_static_page_service.py` (HTML-level) and `tests/test_services/test_status_service.py` (service-level). Use the existing fixtures: `app`, `make_area`, `make_equipment`, `make_repair_record`. The `make_repair_record(equipment=None, status='New', description='Test issue', **kwargs)` signature accepts `RepairRecord` column kwargs (`severity`, `eta`, `created_at`, etc.); it does NOT accept `area` or `name`. **Always pass `equipment=…` explicitly** to avoid the fixture's auto-create-area+equipment side effect.

Strategy for tz-sensitive tests: **never** assert on the unpatched host clock. Either patch `_compute_generated_at()` to return a known string, or patch `datetime` inside `static_page_service` so `datetime.now().astimezone()` returns a fixed `datetime` with a known `tzinfo` (`ZoneInfo('America/New_York')` for the helper-level test). This keeps tests deterministic on UTC CI runners.

| Test | Covers AC |
| ---- | --------- |
| `test_open_records_listed_for_non_green_equipment` | AC 1 |
| `test_open_records_omitted_for_green_equipment` | AC 2 |
| `test_open_records_sorted_by_severity_priority_then_created_at` | AC 3 |
| `test_open_records_uses_yellow_class_for_degraded_and_not_sure` | AC 4 |
| `test_open_records_uses_gray_class_for_no_severity` | AC 4 (None branch) |
| `test_open_records_omits_eta_when_unset` | AC 5 |
| `test_generated_at_subheading_renders_above_areas` | AC 6 |
| `test_generated_at_uses_local_timezone_helper` | AC 7a |
| `test_compute_generated_at_formats_tzname` | AC 7b |
| `test_site_footer_replaces_old_generated_line` | AC 8 |
| `test_footer_renders_local_tz_year_as_entity` | AC 9 |
| (existing, modified) `test_produces_self_contained_html` + `test_csp_meta_tag_directive_unchanged` | AC 10 |
| `test_description_is_html_escaped` | AC 11 |
| `test_footer_text_pin` | AC 12 |
| `test_description_uses_prewrap_styles` | AC 13 |
| `test_equipment_row_keeps_dot_name_label_on_one_line` | AC 14 |
| `test_status_service.test_includes_open_records_list_per_equipment` | AC 15 |
| `test_status_service.test_open_records_sorted_by_severity_then_created_at` | AC 15 (sort) |
| (existing, modified) `test_includes_generated_timestamp` | AC 16 |

DC 1, DC 2, DC 3 are verified by code review at PR time.

**Manual / smoke testing:**

1. Apply the changes locally.
2. `make db-up && make migrate && make run` and create at least one Area, two Equipment items, and one open `RepairRecord` per equipment (one `Down`, one `Degraded`, one `Not Sure` or `None`) via the staff UI. Include one long-text description (200+ chars) and one multi-line description (with embedded newlines) to verify wrap behavior. Add a fourth equipment with 5+ open records on a long-named equipment to verify visual spacing under the equipment row.
3. Set `TZ=America/New_York` in shell before running `flask shell`, then `from esb.services import static_page_service; print(static_page_service.generate())` (or hit the export path on disk via `STATIC_PAGE_PUSH_METHOD=local`).
4. Open the resulting `index.html` in a browser. Verify:
   - Top right under the title: `Generated: 2026-05-11 14:32:15 EDT` (or local zone).
   - Equipment header (dot + name + label + ETA) on a single line under each area.
   - Under each non-green equipment item: a list with one row per open record, colored by severity, showing status + `[severity]` badge + description (multi-line / long text wrapping correctly) + ETA (when set). Records sorted with `Down` records on top.
   - Bottom: centered copyright footer with `<small>` wrapper, GitHub and MIT license anchors, aria-labels present (verifiable in DevTools); year matches the generation sub-heading year.
   - View source: no `<link>`, no `<script src=...>`, no external `<img>`; CSP meta tag value is `default-src 'none'; style-src 'unsafe-inline'` verbatim; `<footer>` has `role="contentinfo"` and `aria-label="Site copyright and license"`.
5. **End-to-end Docker smoke (verifies R2F1 Dockerfile change):** Build the image with the Dockerfile change applied. Run `docker compose run --rm worker python -c "from datetime import datetime; print(datetime.now().astimezone().tzname())"`. Confirm output is `EDT`/`EST` (not `UTC`) when `TZ=America/New_York` is in `.env`. This catches the silent UTC fallback that occurs if `tzdata` is missing from the image.

### Notes

**Production timezone configuration.** The default `docker-compose.yml` sets `TZ=America/New_York` on the `worker` service AND the `Dockerfile` installs `tzdata`. Both changes are required — `TZ` without `tzdata` is a silent no-op. Operators in other zones override via the `TZ` env var in `.env`. Documented in `docs/administrators.md`. The `app` service does not need TZ.

**Risk: timezone test flakiness.** Mitigated. All tz-sensitive tests patch either `_compute_generated_at()` or `datetime.now().astimezone()`. No test depends on the runner's `TZ` env var.

**Risk: live dashboard / Slack regression.** Task 1 adds an `open_records` key to the dict returned by `get_area_status_dashboard()`. Audited consumers: `public/status_dashboard.html`, `public/kiosk.html`, `esb/slack/forms.py::format_status_summary`, `esb/slack/forms.py::format_area_status_detail`, `esb/slack/handlers.py` `/esb-status` path. None iterate or reference `open_records`. Task 9 runs the full suite to confirm.

**Risk: severity-priority sort change.** Spec changes the sort from "created_at ASC oldest-first" (round-1 default) to "severity priority then `created_at` ASC" with unknown severities folded to `Not Sure` priority. This is the right call for the static fallback view AND it matches the equipment-level status-fallback behavior, eliminating the inversion bug where a yellow-coded equipment could contain a record sorting below Not Sure (R2F8).

**Risk: footer-text pin is narrowly scoped.** AC 12 / Task 4 case 12 pins owner + URLs only — not year-token markup, `<small>`, or aria-labels. Those are covered by AC 8/9. If a future edit to `_footer.html` swaps `<small>` for `<span>`, AC 12 will NOT fire; the static page will visually diverge silently. Acceptable trade-off: the alternative (full markup pin) would require rendering `_footer.html` through Jinja with mocked context, which complicates the test and over-couples the static page to the live one. The aria-label / `<small>` invariants are pinned directly against the static page in AC 8 instead.

**Risk: `severity=None` and unknown severity strings.** Repair creation paths set severity by default, but the column is nullable AND unconstrained. Spec handles both cases identically in the sort (priority 2 = Not Sure), in the template class mapping (`open-record-gray` for None, would also be `gray` for any unknown string — see template `{% if rec.severity == 'Down' %}…{% elif rec.severity in ('Degraded', 'Not Sure') %}…{% else %}gray{% endif %}`), and in severity-badge rendering (the `{% if rec.severity %}` guard hides the `[…]` text for None but shows it for unknown strings). Tests cover the None branch in case 7 and the sort behavior in case 9 / Task 5 case 2.

**Explicit non-decisions:**
- **No cap on records displayed per equipment.** Static page is the fallback view; full information takes priority over visual tidiness in the rare worst case.
- **Severity text badge `[Down]` retained** as accessibility/redundancy for color-coding.
- **No empty-tzname fallback in `_compute_generated_at`.** CPython 3.11+ with `tzdata` installed always yields non-empty `tzname()`. If a future deployment violates that invariant, the helper fails loudly with `TypeError` (concatenating `str` and `None`) — preferable to a silent UTC-offset fallback that masks a Dockerfile regression.

**Future / out of scope (do not implement now):**
- Per-area kiosk static export (would require extending `get_single_area_status_dashboard()` similarly).
- Showing `specialist_description` or `assignee` on the static page (privacy / clutter concerns).
- Localizing the timestamp into a non-system timezone via an app-level config var (currently driven by OS `TZ`).

GitHub issue #44 text:
> 1. The static status page currently just shows a list of equipment by area and operational/degraded/down state. For degraded or down equipment this should also include a list of the open repair records, their status, ETA if set, and description.
> 2. There is currently a small unobtrusive "Generated:" line at the bottom of the static page. Let's replace that with the copyright footer used on the live site, and add a sub-heading near the top right under "Equipment Status" that gives the generated date and time in the local/system timezone.

### Adversarial Review Resolution

**Round 1 (2026-05-11):** 20 findings (R1F1–R1F20), all addressed in the second revision. Resolution table previously included; see commit history for full audit trail.

**Round 2 (2026-05-11):** 21 findings (R2F1–R2F21); fixed all real findings (15 of 21). The 6 "Noise" findings (R2F9 / test scoping nit, R2F16 / general line-number audit reminder, R2F18 / dt.year comment, R2F20 / broader XSS, R2F21 / fixture auto-create) deferred or rolled into adjacent fixes.

| ID | Severity | Resolution |
| --- | --- | --- |
| R2F1 | Critical | Added Task 8 (Dockerfile `tzdata`). Without this, the whole local-tz feature is a silent no-op. Added end-to-end Docker smoke step in manual testing. |
| R2F2 | High | Renamed Task 4 case 12 from "drift detector" to `test_footer_text_pin`. AC 12 explicitly scopes coverage to owner + URLs and documents what it does NOT detect; year/markup/aria covered by AC 8/9. |
| R2F3 | Med | Added `margin-top` ≥ 0.4rem on `.open-records-list` (already in spec — explicitly called out in Decision #9). Added long-name / many-records manual smoke step. |
| R2F4 | Med | Dropped the empty-tzname fallback entirely; helper now fails loudly via `TypeError` on `None`-tzname. Decision #3 and Task 2 updated. AC 8 fallback case removed. |
| R2F5 | Med | Split AC 7 into AC 7a (helper wiring via patched return) and AC 7b (helper formats tzname-present case via patched `datetime`). Dropped "via dt.tzname() not string inspection" — not externally testable. |
| R2F6 | Low | Dropped `id` from the sort key in Task 1; documented that Python's stable sort + prefetch `(created_at, id)` order provides the tiebreak. |
| R2F7 | Low | Eliminated the `_NO_SEVERITY_SORT_PRIORITY = 999` constant entirely. Unknown / None severities fold to `_NOT_SURE_PRIORITY` (= `_SEVERITY_STATUS['Not Sure'][2]`), avoiding both magic-number duplication AND the equipment-level inversion (R2F8). |
| R2F8 | Med | Unknown severities and `None` both sort at `Not Sure` priority (2), matching the equipment-level Degraded fallback. AC 3 expanded to cover the unknown-severity case explicitly. |
| R2F10 | Med | AC 9 (now AC 9) asserts `&copy; <YEAR> Jason Antman` literal entity. Test case renamed `test_footer_renders_local_tz_year_as_entity`. |
| R2F11 | Med | Inlined footer now includes `aria-label="Site copyright and license"` on `<footer>`, `<small>` wrapper, and `aria-label` on both anchors — mirrors `_footer.html`. AC 8 pins these. |
| R2F12 | Low | Task 4 case 12 specifies `app.jinja_env.loader.get_source(app.jinja_env, 'components/_footer.html')[0]` for path resolution. |
| R2F13 | Low | Moved AC 18/19 to a new **Documentation Checklist** section (DC 1, DC 2, DC 3). Hedge "in a test or" dropped. Explicit owner: PR reviewer. |
| R2F14 | Low | Corrected `description='X'` → `description='Test issue'` in code patterns, fixture description, and the test_patterns frontmatter. |
| R2F15 | Low | Removed inaccurate `tests/conftest.py:118-160` line range; cite by file + named fixture instead. Other line-number cites checked. |
| R2F17 | Med | Added Task 4 case 16 (`test_description_uses_prewrap_styles`) covering AC 13 (pre-wrap CSS). |
| R2F19 | Low | Tightened `equipment_page.html` precedent note: "shows conceptual data shape only; static page reimplements layout in inline CSS without Bootstrap." |
