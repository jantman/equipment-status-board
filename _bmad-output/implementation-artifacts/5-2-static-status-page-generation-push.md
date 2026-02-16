# Story 5.2: Static Status Page Generation & Push

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a remote member,
I want to view an up-to-date static status page online,
So that I can check equipment status without being on the makerspace local network.

## Acceptance Criteria

1. **Given** the `static_page_service` module, **When** it is called to generate the static page, **Then** it renders the `static_page.html` Jinja2 template with current status data for all areas and equipment into a standalone HTML file. (AC: #1)

2. **Given** the static status page, **When** it is rendered, **Then** it shows a summary of all areas with equipment names and status indicators (Minimal variant: color dot + equipment name), **And** it is a self-contained HTML file with no external dependencies (CSS inlined). (AC: #2)

3. **Given** an equipment status changes (repair record created, status updated, severity changed, repair resolved), **When** the service layer processes the change, **Then** a `static_page_push` job is inserted into the `PendingNotification` table. (AC: #3)

4. **Given** the background worker picks up a `static_page_push` job, **When** it processes the job, **Then** it calls `static_page_service` to render the template and push the file via the configured method. (AC: #4)

5. **Given** `STATIC_PAGE_PUSH_METHOD` is set to `"local"`, **When** the static page is pushed, **Then** the rendered HTML file is written to the directory specified by `STATIC_PAGE_PUSH_TARGET`. (AC: #5)

6. **Given** `STATIC_PAGE_PUSH_METHOD` is set to `"s3"`, **When** the static page is pushed, **Then** the rendered HTML file is uploaded to the S3 bucket/path specified by `STATIC_PAGE_PUSH_TARGET`. (AC: #6)

7. **Given** the static page push fails (network error, permission denied, service unavailable), **When** the delivery attempt errors, **Then** the notification queue retries with exponential backoff per Story 5.1's retry logic. (AC: #7)

8. **Given** the static page generation and push, **When** triggered by a status change, **Then** the entire process completes within 30 seconds under normal conditions. (AC: #8)

## Tasks / Subtasks

- [ ] Task 1: Create `esb/services/static_page_service.py` (AC: #1, #4, #5, #6)
  - [ ] 1.1: Implement `generate()` -- renders `public/static_page.html` template using `render_template()` with status data from `status_service.get_area_status_dashboard()`, returns HTML string
  - [ ] 1.2: Implement `push(html_content)` -- dispatcher that routes to `_push_local()` or `_push_s3()` based on `current_app.config['STATIC_PAGE_PUSH_METHOD']`
  - [ ] 1.3: Implement `_push_local(html_content, target_path)` -- writes HTML string to `{target_path}/index.html`, creates directory if needed
  - [ ] 1.4: Implement `_push_s3(html_content, target)` -- parses target as `bucket/key`, uploads via boto3 `put_object` with `ContentType='text/html; charset=utf-8'`
  - [ ] 1.5: Implement `generate_and_push()` -- convenience function calling generate() then push(), used by the notification handler
  - [ ] 1.6: Add mutation logging for push events
  - [ ] 1.7: Raise `RuntimeError` on push failures (caught by worker for retry)

- [ ] Task 2: Create `esb/templates/public/static_page.html` (AC: #2)
  - [ ] 2.1: Self-contained HTML document (own `<!DOCTYPE html>`, `<head>`, `<body>`) -- does NOT extend any base template
  - [ ] 2.2: Inline all CSS in a `<style>` block -- minimal styles for layout, status dot colors (green/yellow/red), typography
  - [ ] 2.3: Display areas with headings, equipment names with Minimal status indicators (color dot + equipment name + text label)
  - [ ] 2.4: Include generation timestamp in footer
  - [ ] 2.5: Include meta charset, viewport, and CSP meta tag

- [ ] Task 3: Wire `_deliver_static_page_push` in `notification_service.py` (AC: #4)
  - [ ] 3.1: Replace the `NotImplementedError` stub with a call to `static_page_service.generate_and_push()`
  - [ ] 3.2: Let any exceptions propagate to the worker loop (which handles retry via `mark_failed()`)

- [ ] Task 4: Add static page push hooks in `repair_service.py` (AC: #3)
  - [ ] 4.1: After `create_repair_record()` commits, queue a `static_page_push` notification
  - [ ] 4.2: After `update_repair_record()` commits, queue a `static_page_push` notification ONLY when `status` or `severity` changed (these are the fields that affect equipment status)
  - [ ] 4.3: Import `notification_service` locally inside each function to avoid circular imports

- [ ] Task 5: Write service tests in `tests/test_services/test_static_page_service.py` (AC: #1, #2, #4, #5, #6, #7)
  - [ ] 5.1: Test `generate()` renders HTML with area and equipment data
  - [ ] 5.2: Test `generate()` produces self-contained HTML (no external CSS/JS links)
  - [ ] 5.3: Test `push()` with method='local' writes file to target directory
  - [ ] 5.4: Test `push()` with method='local' creates directory if needed
  - [ ] 5.5: Test `push()` with method='s3' calls boto3 put_object with correct params
  - [ ] 5.6: Test `push()` with method='s3' handles ClientError (raises RuntimeError)
  - [ ] 5.7: Test `push()` with empty target raises RuntimeError
  - [ ] 5.8: Test `push()` with unknown method raises RuntimeError
  - [ ] 5.9: Test `generate_and_push()` calls generate then push
  - [ ] 5.10: Test mutation logging on successful push

- [ ] Task 6: Write notification handler tests in `tests/test_services/test_notification_service.py` (AC: #4)
  - [ ] 6.1: Update existing test for `_deliver_static_page_push` -- verify it no longer raises NotImplementedError
  - [ ] 6.2: Test that processing a `static_page_push` notification calls `static_page_service.generate_and_push()`
  - [ ] 6.3: Test that exceptions from static_page_service propagate to the worker loop

- [ ] Task 7: Write repair service hook tests (AC: #3)
  - [ ] 7.1: Test `create_repair_record()` queues a `static_page_push` notification
  - [ ] 7.2: Test `update_repair_record()` with status change queues a `static_page_push` notification
  - [ ] 7.3: Test `update_repair_record()` with severity change queues a `static_page_push` notification
  - [ ] 7.4: Test `update_repair_record()` with only assignee/eta/note changes does NOT queue a `static_page_push` notification

- [ ] Task 8: Add `boto3` to `requirements.txt` (AC: #6)
  - [ ] 8.1: Add `boto3` to requirements.txt
  - [ ] 8.2: Verify it installs cleanly in the venv

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Function-based services:** All services use module-level functions, NOT classes. Follow the pattern in `esb/services/notification_service.py`.
5. **Mutation logging:** Use `log_mutation(event, user, data)` from `esb/utils/logging.py` for all data-changing operations.
6. **Domain exceptions:** Use `ValidationError` from `esb/utils/exceptions.py`.
7. **UTC timestamps:** `default=lambda: datetime.now(UTC)` for all timestamp columns.
8. **Import pattern:** Import services locally inside view/CLI functions to avoid circular imports. This also applies to inter-service imports (e.g., `repair_service` importing `notification_service`).
9. **Flash category:** Use `'danger'` NOT `'error'` for error flash messages.
10. **ruff target-version:** `"py313"` (NOT py314).

### Critical Implementation Details

#### Static Page Service (`esb/services/static_page_service.py`)

```python
"""Static status page generation and push service."""

import logging
import os

from flask import current_app, render_template

from esb.utils.logging import log_mutation

logger = logging.getLogger(__name__)


def generate() -> str:
    """Render the static status page with current equipment status data.

    Uses status_service.get_area_status_dashboard() for data and renders
    the public/static_page.html Jinja2 template within the Flask app context.

    Returns:
        Rendered HTML string (self-contained, no external dependencies).
    """
    from esb.services import status_service

    areas = status_service.get_area_status_dashboard()
    return render_template('public/static_page.html', areas=areas)


def push(html_content: str) -> None:
    """Push the rendered static page to the configured destination.

    Dispatches to _push_local() or _push_s3() based on
    STATIC_PAGE_PUSH_METHOD config value.

    Args:
        html_content: The rendered HTML string to push.

    Raises:
        RuntimeError: if push method is unknown, target is empty, or push fails.
    """
    method = current_app.config.get('STATIC_PAGE_PUSH_METHOD', 'local')
    target = current_app.config.get('STATIC_PAGE_PUSH_TARGET', '')

    if not target:
        raise RuntimeError('STATIC_PAGE_PUSH_TARGET is not configured')

    if method == 'local':
        _push_local(html_content, target)
    elif method == 's3':
        _push_s3(html_content, target)
    else:
        raise RuntimeError(f'Unknown STATIC_PAGE_PUSH_METHOD: {method!r}')

    log_mutation('static_page.pushed', 'system', {
        'method': method,
        'target': target,
    })

    logger.info('Static page pushed via %s to %s', method, target)


def _push_local(html_content: str, target_path: str) -> None:
    """Write the static page HTML to a local directory.

    Writes to {target_path}/index.html, creating the directory if needed.

    Args:
        html_content: Rendered HTML string.
        target_path: Directory path to write to.

    Raises:
        RuntimeError: if file write fails.
    """
    try:
        os.makedirs(target_path, exist_ok=True)
        output_path = os.path.join(target_path, 'index.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logger.info('Static page written to %s', output_path)
    except OSError as e:
        raise RuntimeError(f'Failed to write static page to {target_path}: {e}') from e


def _push_s3(html_content: str, target: str) -> None:
    """Upload the static page HTML to an S3 bucket.

    Target format: "bucket-name/optional/key/path" (key defaults to index.html
    if target ends with / or has no key component).

    Args:
        html_content: Rendered HTML string.
        target: S3 target in format "bucket/key".

    Raises:
        RuntimeError: if S3 upload fails.
    """
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
    except ImportError as e:
        raise RuntimeError('boto3 is required for S3 push method. Install it with: pip install boto3') from e

    # Parse target: "bucket-name/optional/key/path"
    parts = target.split('/', 1)
    bucket = parts[0]
    key = parts[1] if len(parts) > 1 and parts[1] else 'index.html'

    try:
        s3 = boto3.client('s3')
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=html_content.encode('utf-8'),
            ContentType='text/html; charset=utf-8',
            CacheControl='no-cache, no-store, must-revalidate',
        )
        logger.info('Static page uploaded to s3://%s/%s', bucket, key)
    except NoCredentialsError as e:
        raise RuntimeError('AWS credentials not configured for S3 push') from e
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_msg = e.response['Error']['Message']
        raise RuntimeError(f'S3 upload failed ({error_code}): {error_msg}') from e


def generate_and_push() -> None:
    """Generate the static status page and push it to the configured destination.

    Convenience function used by the notification worker handler.
    """
    html = generate()
    push(html)
```

**Key decisions:**
- `generate()` uses `render_template()` which works because the worker runs in Flask app context
- `push()` dispatches based on `STATIC_PAGE_PUSH_METHOD` config -- "local" or "s3"
- `_push_local()` writes to `{target}/index.html` -- creates dir if needed
- `_push_s3()` imports `boto3` lazily -- fails gracefully if not installed (RuntimeError, not ImportError)
- S3 target format: `bucket-name/optional/key/path` -- simple split on first `/`
- All failures raise `RuntimeError` which the worker's `mark_failed()` catches for retry
- `boto3` is a soft dependency -- only needed when `STATIC_PAGE_PUSH_METHOD='s3'`

#### Static Page Template (`esb/templates/public/static_page.html`)

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
        h1 { font-size: 1.5rem; margin-bottom: 1rem; text-align: center; }
        .area { margin-bottom: 1.5rem; }
        .area h2 { font-size: 1.1rem; border-bottom: 2px solid #dee2e6; padding-bottom: 0.3rem; margin-bottom: 0.5rem; }
        .equipment-list { list-style: none; }
        .equipment-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.25rem 0; }
        .status-dot { width: 12px; height: 12px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
        .status-green { background-color: #198754; }
        .status-yellow { background-color: #ffc107; }
        .status-red { background-color: #dc3545; }
        .equipment-name { font-size: 0.95rem; }
        .status-label { font-size: 0.8rem; color: #6c757d; }
        .footer { text-align: center; margin-top: 2rem; font-size: 0.75rem; color: #6c757d; }
    </style>
</head>
<body>
    <h1>Equipment Status</h1>
    {% for area_data in areas %}
    <div class="area">
        <h2>{{ area_data.area.name }}</h2>
        {% if area_data.equipment %}
        <ul class="equipment-list">
            {% for item in area_data.equipment %}
            <li class="equipment-item">
                <span class="status-dot status-{{ item.status.color }}"></span>
                <span class="equipment-name">{{ item.equipment.name }}</span>
                <span class="status-label">{{ item.status.label }}</span>
            </li>
            {% endfor %}
        </ul>
        {% else %}
        <p style="color: #6c757d; font-size: 0.9rem;">No equipment in this area.</p>
        {% endif %}
    </div>
    {% endfor %}
    <div class="footer">
        Generated: {{ generated_at }}
    </div>
</body>
</html>
```

**Key decisions:**
- Completely self-contained -- no `{% extends %}`, no external CSS/JS links
- CSP meta tag restricts loading to only inline styles
- Minimal status indicator variant: color dot + equipment name + text label
- System font stack (no web fonts)
- Responsive via viewport meta tag -- minimal CSS works on mobile and desktop
- `generated_at` timestamp shows when page was last rendered
- Jinja2 autoescaping is on by default for `.html` templates -- all user data (area names, equipment names) is safely escaped
- Per NFR8: shows only area names, equipment names, and status -- no internal details, no user info, no URLs

#### Notification Service Update (`esb/services/notification_service.py`)

Replace the `_deliver_static_page_push` stub:

```python
def _deliver_static_page_push(notification: PendingNotification) -> None:
    """Generate and push the static status page.

    Called by the background worker when processing a static_page_push
    notification. Delegates to static_page_service for rendering and push.

    Raises:
        RuntimeError: if generation or push fails (worker will retry).
    """
    from esb.services import static_page_service

    static_page_service.generate_and_push()
```

**Key decisions:**
- Imports `static_page_service` locally to avoid circular imports
- Delegates entirely to `static_page_service.generate_and_push()`
- Exceptions propagate to the worker loop which calls `mark_failed()` for retry

#### Repair Service Hooks (`esb/services/repair_service.py`)

Add `static_page_push` notification queuing after status-affecting changes:

In `create_repair_record()`, after `db.session.commit()` and `log_mutation()`:

```python
    # Queue static page regeneration (new repair affects equipment status)
    from esb.services import notification_service
    notification_service.queue_notification(
        notification_type='static_page_push',
        target='status_change',
        payload={'trigger': 'repair_record_created', 'equipment_id': equipment_id},
    )
```

In `update_repair_record()`, after `db.session.commit()` and `log_mutation()`, check if status or severity changed:

```python
    # Queue static page regeneration if status-affecting fields changed
    if 'status' in audit_changes or 'severity' in audit_changes:
        from esb.services import notification_service
        notification_service.queue_notification(
            notification_type='static_page_push',
            target='status_change',
            payload={
                'trigger': 'repair_record_updated',
                'equipment_id': record.equipment_id,
                'changes': list(audit_changes.keys()),
            },
        )
```

**Key decisions:**
- Hook placement: AFTER `db.session.commit()` and `log_mutation()` -- the repair record change is already durable
- `create_repair_record()` always queues (creating a repair always changes equipment status)
- `update_repair_record()` only queues when `status` or `severity` changed (these are the only fields that affect equipment status derivation via `_derive_status_from_records`)
- Assignee changes, ETA changes, notes, and photos do NOT trigger static page push (they don't affect status)
- Import `notification_service` locally to avoid circular imports
- `target` is set to `'status_change'` -- a descriptive identifier (the actual push destination comes from config)
- `payload` includes trigger context for debugging/logging (what event caused the push)

### What This Story Does NOT Include

1. **Slack notification delivery** -- Story 6.1 implements `_deliver_slack_message()`
2. **Notification trigger configuration** -- Story 5.3 adds configurable Slack notification triggers and the AppConfig UI
3. **Slack notification hooks in repair_service** -- Story 5.3 adds `slack_message` queuing with configurable trigger checks
4. **SCP push method** -- Architecture mentions SCP as an option but `local` and `s3` are the specified methods in the ACs
5. **Deduplication of rapid static page pushes** -- Multiple rapid status changes will queue multiple pushes; each renders latest data, which is correct behavior

### Reuse from Previous Stories (DO NOT recreate)

**From Story 1.1 (Project Scaffolding):**
- `esb/__init__.py` -- App factory with `_register_cli()` function
- `esb/extensions.py` -- `db`, `login_manager`, `migrate`, `csrf` instances
- `esb/config.py` -- Configuration classes including `STATIC_PAGE_PUSH_METHOD` and `STATIC_PAGE_PUSH_TARGET`
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` function
- `esb/utils/exceptions.py` -- `ESBError`, `ValidationError` hierarchy
- `docker-compose.yml` -- Worker container already configured with `flask worker run`

**From Story 4.1 (Status Dashboard):**
- `esb/services/status_service.py` -- `get_area_status_dashboard()` provides exact data structure needed
- `esb/templates/components/_status_indicator.html` -- Has Minimal variant (though not used directly in static page since template is self-contained)

**From Story 5.1 (Notification Queue):**
- `esb/models/pending_notification.py` -- PendingNotification model
- `esb/services/notification_service.py` -- `queue_notification()`, worker loop, `mark_delivered()`, `mark_failed()`, exponential backoff
- `'static_page_push'` already in `VALID_NOTIFICATION_TYPES`
- Worker container and CLI command already operational

**Existing test infrastructure:**
- `tests/conftest.py` -- `app`, `db`, `client`, `capture`, `make_area`, `make_equipment`, `make_repair_record` fixtures
- `tests/test_services/test_notification_service.py` -- Existing tests (update, don't duplicate)
- `tests/test_services/test_status_service.py` -- Status computation tests

### Project Structure Notes

**New files to create:**
- `esb/services/static_page_service.py` -- Static page generation and push logic
- `esb/templates/public/static_page.html` -- Self-contained static page template
- `tests/test_services/test_static_page_service.py` -- Service tests

**Files to modify:**
- `esb/services/notification_service.py` -- Replace `_deliver_static_page_push` stub with real implementation
- `esb/services/repair_service.py` -- Add `static_page_push` notification hooks in `create_repair_record()` and `update_repair_record()`
- `requirements.txt` -- Add `boto3`
- `tests/test_services/test_notification_service.py` -- Update tests for the wired handler
- `tests/test_services/test_repair_service.py` -- Add tests for notification hooks

**Files NOT to modify:**
- `esb/config.py` -- `STATIC_PAGE_PUSH_METHOD` and `STATIC_PAGE_PUSH_TARGET` already defined
- `esb/services/status_service.py` -- No changes needed, already provides `get_area_status_dashboard()`
- `esb/models/pending_notification.py` -- No changes needed
- `esb/views/public.py` -- No changes needed (static page is generated by worker, not served by views)
- `docker-compose.yml` -- Worker container already configured
- `esb/__init__.py` -- No changes needed
- `esb/templates/base.html` or any other base templates -- Static page is self-contained

### Previous Story Intelligence (from Story 5.1)

**Patterns to follow:**
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside functions to avoid circular imports
- `db.session.get(Model, id)` for PK lookups
- `db.select(Model).filter_by(...)` for queries
- `default=lambda: datetime.now(UTC)` for timestamps (import `UTC` from `datetime`)
- Test factories in `tests/conftest.py`: `make_area`, `make_equipment`, `make_repair_record`
- 768 tests currently passing, 0 lint errors

**Code review lessons from previous stories:**
- Don't duplicate logic -- reuse existing service patterns
- Test all mutation log events using the `capture` fixture
- Include edge case tests (empty results, invalid inputs)
- Use `db.or_()` from SQLAlchemy for OR conditions
- Don't recreate what already exists -- the notification queue, worker, and status service are done

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

**Static page service tests (`tests/test_services/test_static_page_service.py`):**
- Test `generate()` returns HTML string containing area names and equipment names
- Test `generate()` output has no `<link>` or `<script src=` tags (self-contained)
- Test `generate()` includes status dot classes (status-green, status-yellow, status-red)
- Test `push()` with `method='local'` writes `index.html` to target directory
- Test `push()` with `method='local'` creates target directory if it doesn't exist
- Test `push()` with `method='s3'` calls `boto3.client('s3').put_object()` with correct bucket, key, content type
- Test `push()` with `method='s3'` handles `ClientError` by raising `RuntimeError`
- Test `push()` with empty target raises `RuntimeError`
- Test `push()` with unknown method raises `RuntimeError`
- Test `generate_and_push()` calls both `generate()` and `push()`
- Test mutation logging via `capture` fixture

**Notification handler tests (update existing):**
- Verify `_deliver_static_page_push` no longer raises `NotImplementedError`
- Verify it calls `static_page_service.generate_and_push()`

**Repair service hook tests (add to existing test file):**
- Test `create_repair_record()` creates a PendingNotification with type `static_page_push`
- Test `update_repair_record()` with status change creates a PendingNotification
- Test `update_repair_record()` with severity change creates a PendingNotification
- Test `update_repair_record()` with only assignee/eta/note does NOT create a PendingNotification

**Test data patterns:**
```python
# For static page generation tests, create areas with equipment
area = make_area(name='Woodshop')
equip = make_equipment(name='SawStop', area=area)

# For repair hooks, verify notification creation
from esb.models.pending_notification import PendingNotification
notifications = db.session.execute(
    db.select(PendingNotification).filter_by(notification_type='static_page_push')
).scalars().all()
assert len(notifications) == 1

# For S3 push tests, mock boto3
from unittest.mock import MagicMock, patch
with patch('esb.services.static_page_service.boto3') as mock_boto3:
    mock_s3 = MagicMock()
    mock_boto3.client.return_value = mock_s3
    push('<html>test</html>')
    mock_s3.put_object.assert_called_once()
```

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with `render_template()` (works in app context via worker)
- **Flask-SQLAlchemy 3.1.x** for ORM
- **Jinja2** (Flask built-in) for template rendering
- **boto3** (new dependency) for S3 push -- only imported when `STATIC_PAGE_PUSH_METHOD='s3'`
- **pytest** for tests
- `os` module from Python stdlib for local file operations
- `logging` module from Python stdlib

### Template Rendering Context

The `generate()` function calls `render_template('public/static_page.html', areas=areas)` where `areas` is the return value of `status_service.get_area_status_dashboard()`. The data structure is:

```python
[
    {
        'area': Area(name='Woodshop', ...),
        'equipment': [
            {
                'equipment': Equipment(name='SawStop', ...),
                'status': {
                    'color': 'green',        # 'green' | 'yellow' | 'red'
                    'label': 'Operational',   # 'Operational' | 'Degraded' | 'Down'
                    'issue_description': None, # str | None
                    'severity': None,          # str | None
                }
            },
            ...
        ]
    },
    ...
]
```

The template should also receive a `generated_at` variable with the current timestamp formatted for display. Add this in the `generate()` function:

```python
from datetime import UTC, datetime

generated_at = datetime.now(UTC).strftime('%Y-%m-%d %H:%M UTC')
return render_template('public/static_page.html', areas=areas, generated_at=generated_at)
```

### S3 Target Format

The `STATIC_PAGE_PUSH_TARGET` for S3 method is a string in format: `bucket-name/optional/key/path`

- `my-bucket/status/index.html` -> bucket=`my-bucket`, key=`status/index.html`
- `my-bucket/` -> bucket=`my-bucket`, key=`index.html` (default)
- `my-bucket` -> bucket=`my-bucket`, key=`index.html` (default)

Parsing: split on first `/`, first part is bucket, remainder is key (default `index.html`).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5 Story 5.2]
- [Source: _bmad-output/planning-artifacts/prd.md#FR29-FR30 Static Status Page]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR3 Static Page Performance]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR8 Public Page Security]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR12 Static Page Retry]
- [Source: _bmad-output/planning-artifacts/architecture.md#Static Page Generation]
- [Source: _bmad-output/planning-artifacts/architecture.md#Notification Queue]
- [Source: _bmad-output/planning-artifacts/architecture.md#Background Worker Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Environment Configuration]
- [Source: esb/services/status_service.py#get_area_status_dashboard]
- [Source: esb/services/notification_service.py#_deliver_static_page_push]
- [Source: esb/services/notification_service.py#queue_notification]
- [Source: esb/services/repair_service.py#create_repair_record]
- [Source: esb/services/repair_service.py#update_repair_record]
- [Source: esb/config.py#STATIC_PAGE_PUSH_METHOD]
- [Source: esb/config.py#STATIC_PAGE_PUSH_TARGET]
- [Source: esb/templates/components/_status_indicator.html#minimal]
- [Source: esb/utils/logging.py#log_mutation]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
