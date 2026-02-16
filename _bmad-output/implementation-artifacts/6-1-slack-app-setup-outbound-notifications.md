# Story 6.1: Slack App Setup & Outbound Notifications

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a makerspace community member,
I want equipment status changes and new problem reports posted to the relevant Slack channels,
So that the community stays informed without checking the web app.

## Acceptance Criteria

1. **Given** the `esb/slack/` module with `slack_bolt` and Flask adapter, **When** the app starts with `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` configured, **Then** the Slack App initializes and registers event handlers at the `/slack/events` endpoint. (AC: #1)

2. **Given** `SLACK_BOT_TOKEN` is not configured (empty or missing), **When** the app starts, **Then** the Slack module is not loaded and the core web application functions normally without any Slack-related errors. (AC: #2)

3. **Given** the Slack App is initialized, **When** incoming requests arrive at `/slack/events`, **Then** they are validated using the Slack signing secret before processing. (AC: #3)

4. **Given** a notification is queued with type `slack_message`, **When** the background worker processes it, **Then** it sends the message to the target Slack channel via the Slack WebClient API. (AC: #4)

5. **Given** a new problem report is created and the `new_report` trigger is enabled, **When** the notification is delivered to Slack, **Then** the message is posted to the equipment's area-specific Slack channel AND to `#oops`, **And** the message includes: equipment name, area, severity, description, and reporter name. (AC: #5)

6. **Given** a repair record is resolved and the `resolved` trigger is enabled, **When** the notification is delivered to Slack, **Then** the message is posted to the area channel and `#oops` indicating the equipment is back in service. (AC: #6)

7. **Given** a severity change occurs and the `severity_changed` trigger is enabled, **When** the notification is delivered to Slack, **Then** the message is posted with old and new severity levels. (AC: #7)

8. **Given** an ETA is set or updated and the `eta_updated` trigger is enabled, **When** the notification is delivered to Slack, **Then** the message includes the new ETA date. (AC: #8)

9. **Given** a problem report or notification has the safety risk flag set, **When** the Slack message is composed, **Then** the safety risk is prominently highlighted in the message (bold text, warning emoji, or distinct formatting). (AC: #9)

10. **Given** the Slack API is unreachable, **When** the background worker attempts delivery, **Then** the notification remains in the queue and retries with exponential backoff per the notification queue logic in Epic 5. (AC: #10)

## Tasks / Subtasks

- [ ] Task 1: Add `slack-bolt` dependency to `requirements.txt` (AC: #1)
  - [ ] 1.1: Add `slack-bolt>=1.27.0` to `requirements.txt`
  - [ ] 1.2: Install in venv and verify import works

- [ ] Task 2: Set up the Slack Bolt app in `esb/slack/__init__.py` (AC: #1, #2, #3)
  - [ ] 2.1: Create Bolt `App` instance with `token` and `signing_secret` from Flask config
  - [ ] 2.2: Create `SlackRequestHandler` for Flask integration
  - [ ] 2.3: Create `init_slack(app)` function that conditionally sets up Slack based on `SLACK_BOT_TOKEN` availability
  - [ ] 2.4: Register a Flask Blueprint `slack_bp` at `/slack` with a `/events` POST route
  - [ ] 2.5: Exempt `/slack/events` from CSRF protection (Slack uses signing secret validation)
  - [ ] 2.6: Register a minimal `@bolt_app.event("message")` handler (required by Bolt to avoid warnings)

- [ ] Task 3: Integrate Slack into the Flask app factory (`esb/__init__.py`) (AC: #1, #2)
  - [ ] 3.1: Call `init_slack(app)` in `create_app()` AFTER extension initialization
  - [ ] 3.2: Guard the call so it's skipped when `SLACK_BOT_TOKEN` is empty (AC: #2)

- [ ] Task 4: Implement `_deliver_slack_message()` in `esb/services/notification_service.py` (AC: #4, #5, #6, #7, #8, #9, #10)
  - [ ] 4.1: Replace the `NotImplementedError` stub with actual Slack WebClient delivery
  - [ ] 4.2: Use `current_app.config['SLACK_BOT_TOKEN']` to create WebClient instance
  - [ ] 4.3: Format messages based on `payload['event_type']` using `_format_slack_message()` helper
  - [ ] 4.4: Post to the notification's `target` channel
  - [ ] 4.5: If token is not configured, raise `RuntimeError` so the worker retries later
  - [ ] 4.6: Let Slack SDK exceptions propagate naturally (worker marks as failed + retries)

- [ ] Task 5: Implement dual-channel posting (area channel + `#oops`) (AC: #5, #6)
  - [ ] 5.1: After posting to the `target` channel, also post to `#oops`
  - [ ] 5.2: Use a configurable `SLACK_OOPS_CHANNEL` env var (default: `#oops`)
  - [ ] 5.3: Skip `#oops` post if target is already `#oops` or `#general`
  - [ ] 5.4: Failures to post to `#oops` should be logged but NOT prevent the primary notification from being marked as delivered

- [ ] Task 6: Implement message formatting for all 4 event types (AC: #5, #6, #7, #8, #9)
  - [ ] 6.1: Create `_format_slack_message(payload)` helper returning `(text, blocks)` tuple
  - [ ] 6.2: `new_report` format: equipment name, area, severity badge, description, reporter, safety risk highlight
  - [ ] 6.3: `resolved` format: equipment name, area, old/new status, "back in service" messaging
  - [ ] 6.4: `severity_changed` format: equipment name, area, old/new severity levels
  - [ ] 6.5: `eta_updated` format: equipment name, area, new ETA (and old ETA if available)
  - [ ] 6.6: Safety risk: prepend bold warning text when `has_safety_risk` is truthy in payload
  - [ ] 6.7: Fallback `text` parameter for all messages (Slack requires it for notifications/accessibility)

- [ ] Task 7: Add `SLACK_OOPS_CHANNEL` to configuration (AC: #5, #6)
  - [ ] 7.1: Add `SLACK_OOPS_CHANNEL` to `esb/config.py` (default: `#oops`)
  - [ ] 7.2: Add `SLACK_OOPS_CHANNEL=` to `.env` file

- [ ] Task 8: Write tests for Slack module setup (`tests/test_slack/`) (AC: #1, #2, #3)
  - [ ] 8.1: Create `tests/test_slack/__init__.py`
  - [ ] 8.2: Create `tests/test_slack/test_init.py` with tests for `init_slack()`
  - [ ] 8.3: Test Slack module loads when `SLACK_BOT_TOKEN` is configured
  - [ ] 8.4: Test Slack module is NOT loaded when `SLACK_BOT_TOKEN` is empty
  - [ ] 8.5: Test `/slack/events` route exists and is CSRF-exempt when Slack is configured
  - [ ] 8.6: Test app starts cleanly without slack-bolt import issues

- [ ] Task 9: Write tests for `_deliver_slack_message()` and `_format_slack_message()` (`tests/test_services/test_notification_service.py`) (AC: #4, #5, #6, #7, #8, #9, #10)
  - [ ] 9.1: Test `_deliver_slack_message()` calls WebClient `chat_postMessage` with correct channel and text
  - [ ] 9.2: Test `_deliver_slack_message()` posts to `#oops` as second channel
  - [ ] 9.3: Test `_deliver_slack_message()` raises RuntimeError when no SLACK_BOT_TOKEN configured
  - [ ] 9.4: Test Slack SDK errors propagate (worker will retry)
  - [ ] 9.5: Test `_format_slack_message()` for `new_report` event type
  - [ ] 9.6: Test `_format_slack_message()` for `resolved` event type
  - [ ] 9.7: Test `_format_slack_message()` for `severity_changed` event type
  - [ ] 9.8: Test `_format_slack_message()` for `eta_updated` event type
  - [ ] 9.9: Test safety risk highlighting is present when `has_safety_risk` is true
  - [ ] 9.10: Test `#oops` failure is logged but doesn't fail delivery
  - [ ] 9.11: Test skips `#oops` when target is already `#oops` or `#general`
  - [ ] 9.12: Update existing `test_slack_stub_raises_not_implemented` test to reflect new behavior (stub removed)

- [ ] Task 10: Update existing tests that mock `_deliver_slack_message` (AC: #4)
  - [ ] 10.1: Update `TestRunWorkerLoop` tests that expect `NotImplementedError` from `_deliver_slack_message`
  - [ ] 10.2: Ensure all worker loop tests properly mock the WebClient so no actual Slack calls are made

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
8. **Import pattern:** Import services locally inside view/CLI functions to avoid circular imports. This also applies to inter-service imports.
9. **Flash category:** Use `'danger'` NOT `'error'` for error flash messages.
10. **ruff target-version:** `"py313"` (NOT py314).
11. **Config storage pattern:** Boolean configs stored as `'true'`/`'false'` strings via `config_service.get_config(key, default)` and `config_service.set_config(key, value, changed_by)`.
12. **Slack isolation boundary:** `esb/slack/` is a self-contained module. It imports from `esb/services/` but nothing else imports from `esb/slack/`. If Slack is disabled (no token), the Slack module is not loaded and core app is unaffected.

### Critical Implementation Details

#### Slack Module Setup (`esb/slack/__init__.py`)

The Slack module uses `slack_bolt` with its Flask adapter. The key design is conditional initialization:

```python
"""Slack App handlers package."""

import logging

from flask import Blueprint, request

logger = logging.getLogger(__name__)

slack_bp = Blueprint('slack', __name__, url_prefix='/slack')

# Module-level state (set during init_slack)
_bolt_app = None
_handler = None


def init_slack(app):
    """Initialize Slack Bolt app and register the Blueprint.

    Skips initialization if SLACK_BOT_TOKEN is not configured.
    Called from create_app() in esb/__init__.py.
    """
    global _bolt_app, _handler

    token = app.config.get('SLACK_BOT_TOKEN', '')
    signing_secret = app.config.get('SLACK_SIGNING_SECRET', '')

    if not token:
        logger.info('SLACK_BOT_TOKEN not configured, Slack module disabled')
        return

    if not signing_secret:
        logger.warning('SLACK_SIGNING_SECRET not configured, Slack module disabled')
        return

    from slack_bolt import App
    from slack_bolt.adapter.flask import SlackRequestHandler

    _bolt_app = App(token=token, signing_secret=signing_secret)
    _handler = SlackRequestHandler(_bolt_app)

    # Register minimal event handler (Bolt requires at least one to avoid warnings)
    @_bolt_app.event('message')
    def handle_message_events(body, logger):
        pass  # Inbound message handling is Story 6.2

    # Register the blueprint with the Flask app
    app.register_blueprint(slack_bp)

    # Exempt from CSRF (Slack uses signing secret validation)
    from esb.extensions import csrf
    csrf.exempt(slack_bp)

    logger.info('Slack App initialized successfully')


@slack_bp.route('/events', methods=['POST'])
def slack_events():
    """Handle incoming Slack events via Bolt's Flask adapter."""
    return _handler.handle(request)
```

**Key decisions:**
- `init_slack(app)` is called from `create_app()`, NOT at module import time
- Blueprint is ONLY registered when Slack is configured -- no dead routes
- CSRF exemption applied to the entire blueprint (Slack verifies via signing secret)
- Module-level `_bolt_app` and `_handler` store the initialized instances
- Empty `handle_message_events` prevents Bolt warnings about unhandled events
- Stories 6.2 and 6.3 will add more event/command handlers to `_bolt_app`

#### App Factory Integration (`esb/__init__.py`)

Add after `register_blueprints(app)`:

```python
    # Initialize Slack integration (conditional on SLACK_BOT_TOKEN)
    from esb.slack import init_slack
    init_slack(app)
```

**Key decisions:**
- Called after blueprints are registered so the Slack blueprint can be added
- Called after CSRF is initialized so we can exempt the Slack blueprint
- The `init_slack` function handles the "not configured" case internally -- no conditional needed in create_app

#### `_deliver_slack_message()` Implementation (`esb/services/notification_service.py`)

Replace the stub with actual delivery:

```python
def _deliver_slack_message(notification: PendingNotification) -> None:
    """Deliver a Slack message notification via WebClient.

    Posts the message to the notification's target channel and also to
    the configured #oops channel (for visibility).

    Raises:
        RuntimeError: if SLACK_BOT_TOKEN is not configured.
        slack_sdk.errors.SlackApiError: on Slack API errors (worker will retry).
    """
    from flask import current_app

    token = current_app.config.get('SLACK_BOT_TOKEN', '')
    if not token:
        raise RuntimeError(
            'SLACK_BOT_TOKEN not configured -- cannot deliver Slack messages'
        )

    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError

    client = WebClient(token=token)
    payload = notification.payload or {}
    text, blocks = _format_slack_message(payload)

    # Post to primary target channel (area-specific or #general)
    client.chat_postMessage(
        channel=notification.target,
        text=text,
        blocks=blocks,
    )
    logger.info(
        'Slack message delivered to %s (notification=%d)',
        notification.target, notification.id,
    )

    # Post to #oops for cross-area visibility
    oops_channel = current_app.config.get('SLACK_OOPS_CHANNEL', '#oops')
    if notification.target not in (oops_channel, '#general'):
        try:
            client.chat_postMessage(
                channel=oops_channel,
                text=text,
                blocks=blocks,
            )
            logger.info(
                'Slack message also delivered to %s (notification=%d)',
                oops_channel, notification.id,
            )
        except SlackApiError:
            logger.warning(
                'Failed to post to %s (notification=%d), primary delivery succeeded',
                oops_channel, notification.id,
                exc_info=True,
            )
```

**Key decisions:**
- Uses `current_app.config` for token (Flask app context required -- worker runs within app context)
- Creates WebClient per call (not cached) -- simple, avoids stale token issues
- Primary channel failure raises (worker retries). `#oops` failure is logged but doesn't fail delivery.
- If target IS `#oops` or `#general`, skip the duplicate post
- `_format_slack_message()` returns `(text, blocks)` tuple -- `text` is the fallback, `blocks` are rich formatting

#### Message Formatting (`_format_slack_message()`)

```python
def _format_slack_message(payload: dict) -> tuple[str, list | None]:
    """Format a Slack notification message based on event type.

    Args:
        payload: Notification payload dict with 'event_type' and event-specific fields.

    Returns:
        Tuple of (text, blocks) where text is the fallback and blocks is the rich format.
        blocks may be None if simple text is sufficient.
    """
    event_type = payload.get('event_type', 'unknown')
    equipment_name = payload.get('equipment_name', 'Unknown Equipment')
    area_name = payload.get('area_name', 'Unknown Area')

    # Safety risk prefix
    safety_prefix = ''
    if payload.get('has_safety_risk'):
        safety_prefix = ':warning: *SAFETY RISK* :warning: '

    if event_type == 'new_report':
        severity = payload.get('severity', 'Unknown')
        description = payload.get('description', '')
        reporter = payload.get('reporter_name', 'Unknown')
        text = (
            f'{safety_prefix}New problem report: *{equipment_name}* ({area_name})\n'
            f'Severity: {severity} | Reported by: {reporter}\n'
            f'{description}'
        )

    elif event_type == 'resolved':
        new_status = payload.get('new_status', 'Resolved')
        text = (
            f':white_check_mark: *{equipment_name}* ({area_name}) is back in service\n'
            f'Status: {new_status}'
        )

    elif event_type == 'severity_changed':
        old_severity = payload.get('old_severity', 'Unknown')
        new_severity = payload.get('new_severity', 'Unknown')
        text = (
            f'{safety_prefix}Severity changed: *{equipment_name}* ({area_name})\n'
            f'{old_severity} -> {new_severity}'
        )

    elif event_type == 'eta_updated':
        eta = payload.get('eta', 'Unknown')
        old_eta = payload.get('old_eta')
        eta_text = f'ETA: {eta}'
        if old_eta:
            eta_text = f'ETA updated: {old_eta} -> {eta}'
        text = f'ETA update: *{equipment_name}* ({area_name})\n{eta_text}'

    else:
        text = f'Equipment notification: *{equipment_name}* ({area_name})'

    return text, None  # blocks=None for v1 -- plain text with mrkdwn formatting
```

**Key decisions:**
- Returns `(text, blocks)` tuple. For v1, `blocks=None` uses Slack's mrkdwn text formatting. Blocks can be added later for richer layout.
- Safety risk uses `:warning:` emoji + bold text prefix on relevant event types (new_report, severity_changed)
- Resolved uses `:white_check_mark:` emoji for positive visual signal
- Equipment name and area are always included for context
- Fallback `text` is always set (required by Slack API for accessibility and push notifications)

#### `SLACK_OOPS_CHANNEL` Configuration

Add to `esb/config.py` `Config` class:

```python
SLACK_OOPS_CHANNEL = os.environ.get('SLACK_OOPS_CHANNEL', '#oops')
```

Add to `.env`:

```bash
# Slack cross-posting channel for all notifications (default: #oops)
SLACK_OOPS_CHANNEL=#oops
```

### What This Story Does NOT Include

1. **Inbound Slack commands/forms** -- Story 6.2 implements slash commands (`/esb-report`, `/esb-repair`, `/esb-update`) and Slack modals for creating/updating repair records
2. **Slack status bot** -- Story 6.3 implements `/esb-status` bot query
3. **Block Kit rich messages** -- v1 uses mrkdwn text formatting. Block Kit can be added as enhancement
4. **Per-area notification preferences** -- Trigger config is global (Story 5.3). Per-area is not in scope.
5. **Notification trigger queuing** -- Already implemented in Story 5.3. This story only delivers the queued `slack_message` notifications.
6. **Static page push** -- Already implemented in Story 5.2.

### Reuse from Previous Stories (DO NOT recreate)

**From Story 1.1 (Project Scaffolding):**
- `esb/__init__.py` -- App factory (`create_app`)
- `esb/extensions.py` -- `db`, `login_manager`, `migrate`, `csrf` instances
- `esb/config.py` -- Configuration classes
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` function
- `esb/utils/exceptions.py` -- `ESBError`, `ValidationError` hierarchy

**From Story 5.1 (Notification Queue):**
- `esb/models/pending_notification.py` -- PendingNotification model
- `esb/services/notification_service.py` -- Queue management, worker loop, delivery dispatch
- `_deliver_slack_message()` stub at line 180 -- **THIS IS WHAT WE REPLACE**
- `VALID_NOTIFICATION_TYPES = {'slack_message', 'static_page_push'}` -- `slack_message` already valid
- Background worker: `flask worker run` CLI command
- Docker worker container already defined

**From Story 5.2 (Static Page):**
- `_deliver_static_page_push()` -- Reference implementation for how delivery handlers work
- Pattern: service function called from worker, uses `current_app.config`, raises on failure

**From Story 5.3 (Notification Triggers):**
- `repair_service.py` `_queue_slack_notification()` -- Already queues notifications with correct payload structure
- Trigger configuration via `config_service.get_config('notify_*', 'true')`
- All 4 event types already producing correct payloads: `new_report`, `resolved`, `severity_changed`, `eta_updated`

**Existing Slack pattern in codebase:**
- `esb/services/user_service.py` lines 19-26 and 204-249 -- Guard import pattern for `slack_sdk`, `WebClient` usage, `chat_postMessage` call pattern

**Existing test infrastructure:**
- `tests/conftest.py` -- `app`, `db`, `client`, `capture`, `staff_client`, `tech_client` fixtures
- `tests/test_services/test_notification_service.py` -- Existing tests for queue, delivery, worker loop
- `tests/test_slack/` -- Directory does NOT exist yet (needs to be created)

### Project Structure Notes

**New files to create:**
- `tests/test_slack/__init__.py` -- Test package init
- `tests/test_slack/test_init.py` -- Tests for Slack module initialization

**Files to modify:**
- `requirements.txt` -- Add `slack-bolt>=1.27.0`
- `esb/slack/__init__.py` -- Full Bolt app setup, `init_slack()`, Blueprint, events route
- `esb/__init__.py` -- Call `init_slack(app)` in `create_app()`
- `esb/config.py` -- Add `SLACK_OOPS_CHANNEL` config
- `.env` -- Add `SLACK_OOPS_CHANNEL`
- `esb/services/notification_service.py` -- Replace `_deliver_slack_message()` stub, add `_format_slack_message()`
- `tests/test_services/test_notification_service.py` -- Add delivery tests, update stub test
- `docker-compose.yml` -- No changes needed (worker already configured)

**Files NOT to modify:**
- `esb/models/pending_notification.py` -- No schema changes
- `esb/services/repair_service.py` -- Notification queuing already works from Story 5.3
- `esb/services/config_service.py` -- Trigger config already works
- `esb/forms/admin_forms.py` -- No form changes
- `esb/views/admin.py` -- No admin UI changes
- No migration needed -- all tables already exist

### Previous Story Intelligence (from Story 5.3)

**Patterns to follow:**
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside functions to avoid circular imports
- `db.session.get(Model, id)` for PK lookups
- `default=lambda: datetime.now(UTC)` for timestamps (import `UTC` from `datetime`)
- Test factories in `tests/conftest.py`: `make_area`, `make_equipment`, `make_repair_record`
- Boolean config values stored as `'true'`/`'false'` strings
- 815 tests currently passing, 0 lint errors

**Code review lessons from previous stories:**
- Don't duplicate logic -- reuse existing service patterns
- Test all mutation log events using the `capture` fixture
- Use `unittest.mock.patch` for external API calls (Slack WebClient)
- Import services locally in inter-service calls
- Guard optional imports (slack_sdk/slack_bolt) with try/except

### Slack Message Payload Structure

These are the payloads already being queued by `repair_service.py` (Story 5.3). Your `_format_slack_message()` must handle all of them:

```python
# new_report event
{
    'event_type': 'new_report',
    'equipment_id': 42,
    'equipment_name': 'SawStop',
    'area_name': 'Woodshop',
    'severity': 'Down',
    'description': 'Motor makes grinding noise',
    'reporter_name': 'John',
    'has_safety_risk': True,
}

# resolved event
{
    'event_type': 'resolved',
    'equipment_id': 42,
    'equipment_name': 'SawStop',
    'area_name': 'Woodshop',
    'old_status': 'In Progress',
    'new_status': 'Resolved',
}

# severity_changed event
{
    'event_type': 'severity_changed',
    'equipment_id': 42,
    'equipment_name': 'SawStop',
    'area_name': 'Woodshop',
    'old_severity': 'Degraded',
    'new_severity': 'Down',
}

# eta_updated event
{
    'event_type': 'eta_updated',
    'equipment_id': 42,
    'equipment_name': 'SawStop',
    'area_name': 'Woodshop',
    'eta': '2026-02-20',
    'old_eta': '2026-02-18',
}
```

### Dual-Channel Posting Logic

The notification target (set by `_queue_slack_notification()` in `repair_service.py`) is the area's `slack_channel` (e.g., `#woodshop`), or `#general` if no area channel is configured.

For Story 6.1, notifications must ALSO be posted to `#oops` for cross-area visibility. The logic:

1. Post to `notification.target` (primary channel) -- failure raises exception, worker retries
2. If `notification.target` is NOT `#oops` and NOT `#general`, also post to `SLACK_OOPS_CHANNEL` (default `#oops`)
3. If the `#oops` post fails, log a warning but DO NOT fail the notification -- the primary delivery succeeded
4. This means each queued notification results in 1-2 Slack API calls

### Testing Patterns

**Mocking WebClient for tests:**

```python
from unittest.mock import MagicMock, patch

def test_deliver_slack_message(self, app):
    """_deliver_slack_message sends to target channel via WebClient."""
    n = _create_notification(
        notification_type='slack_message',
        target='#woodshop',
        payload={'event_type': 'new_report', 'equipment_name': 'SawStop',
                 'area_name': 'Woodshop', 'severity': 'Down',
                 'description': 'Broken', 'reporter_name': 'Test',
                 'has_safety_risk': False},
    )

    mock_client = MagicMock()
    with patch('esb.services.notification_service.WebClient',
               return_value=mock_client):
        notification_service._deliver_slack_message(n)

    # Verify primary channel post
    calls = mock_client.chat_postMessage.call_args_list
    assert len(calls) == 2  # primary + #oops
    assert calls[0].kwargs['channel'] == '#woodshop'
    assert calls[1].kwargs['channel'] == '#oops'
```

**Testing init_slack conditional loading:**

```python
def test_slack_disabled_when_no_token(self, app):
    """App starts normally when SLACK_BOT_TOKEN is empty."""
    # TestingConfig has empty SLACK_BOT_TOKEN by default
    client = app.test_client()
    resp = client.get('/health')
    assert resp.status_code == 200

def test_no_slack_routes_when_disabled(self, app):
    """No /slack/events route when Slack is not configured."""
    client = app.test_client()
    resp = client.post('/slack/events')
    assert resp.status_code == 404
```

**Testing with Slack configured:**

```python
import os

@pytest.fixture
def slack_app():
    """Create app with Slack configured."""
    os.environ['SLACK_BOT_TOKEN'] = 'xoxb-test-token'
    os.environ['SLACK_SIGNING_SECRET'] = 'test-signing-secret'
    try:
        from esb import create_app
        app = create_app('testing')
        app.config['SLACK_BOT_TOKEN'] = 'xoxb-test-token'
        app.config['SLACK_SIGNING_SECRET'] = 'test-signing-secret'
        with app.app_context():
            yield app
    finally:
        os.environ.pop('SLACK_BOT_TOKEN', None)
        os.environ.pop('SLACK_SIGNING_SECRET', None)
```

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with CSRF via Flask-WTF
- **slack_sdk>=3.39.0** (already in requirements.txt)
- **slack-bolt>=1.27.0** (NEW -- add to requirements.txt)
- **pytest** for tests with `unittest.mock` for Slack API mocking
- No new database migrations needed

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 6 Story 6.1]
- [Source: _bmad-output/planning-artifacts/prd.md#FR38 Notifications to Slack Channels]
- [Source: _bmad-output/planning-artifacts/prd.md#FR39 Safety Risk Highlighting]
- [Source: _bmad-output/planning-artifacts/architecture.md#Slack SDK]
- [Source: _bmad-output/planning-artifacts/architecture.md#Notification Queue]
- [Source: _bmad-output/planning-artifacts/architecture.md#Slack Integration Boundary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Background Worker Pattern]
- [Source: esb/services/notification_service.py#_deliver_slack_message (stub)]
- [Source: esb/services/notification_service.py#_deliver_static_page_push (reference pattern)]
- [Source: esb/services/notification_service.py#process_notification]
- [Source: esb/services/notification_service.py#run_worker_loop]
- [Source: esb/services/repair_service.py#_queue_slack_notification]
- [Source: esb/services/user_service.py#_deliver_temp_password_via_slack (WebClient pattern)]
- [Source: esb/slack/__init__.py (currently empty)]
- [Source: esb/__init__.py#create_app]
- [Source: esb/config.py#Config]
- [Source: docker-compose.yml#worker]
- [Source: requirements.txt]
- [Source: tests/test_services/test_notification_service.py]
- [Source: https://tools.slack.dev/bolt-python/concepts/adapters/ (Bolt Flask adapter)]
- [Source: https://pypi.org/project/slack-bolt/ (slack-bolt 1.27.0)]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
