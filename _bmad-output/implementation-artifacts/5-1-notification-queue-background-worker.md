# Story 5.1: Notification Queue & Background Worker

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a system administrator,
I want a reliable notification queue with background processing,
So that outbound notifications and static page pushes are delivered even when external services are temporarily unavailable.

## Acceptance Criteria

1. **Given** the PendingNotification model exists with fields for `notification_type` (slack_message, static_page_push), `target` (channel or push destination), `payload` (JSON), `status` (pending, delivered, failed), `created_at`, `next_retry_at`, `retry_count`, `delivered_at`, `error_message`, **When** Alembic migration is run, **Then** the `pending_notifications` table is created in MariaDB. (AC: #1)

2. **Given** the `notification_service` module, **When** a service function calls `notification_service.queue_notification(type, target, payload)`, **Then** a new row is inserted into `pending_notifications` with status "pending". (AC: #2)

3. **Given** the background worker process, **When** it starts via `flask worker run` CLI command, **Then** it runs within the Flask app context with access to the database and all services. (AC: #3)

4. **Given** the background worker is running, **When** it polls the `pending_notifications` table every 30 seconds, **Then** it picks up all rows where status is "pending" and `next_retry_at` is null or in the past. (AC: #4)

5. **Given** a pending notification is processed successfully, **When** the delivery completes, **Then** the row is updated to status "delivered" with `delivered_at` timestamp. (AC: #5)

6. **Given** a pending notification fails to deliver, **When** the delivery attempt errors, **Then** the row's `retry_count` is incremented, `error_message` is recorded, and `next_retry_at` is set with exponential backoff (30s, 1m, 2m, 5m, 15m, max 1h). (AC: #6)

7. **Given** the background worker, **When** it processes jobs, **Then** all delivery attempts and failures are logged to STDOUT. (AC: #7)

8. **Given** the Docker Compose configuration, **When** `docker-compose up` is run, **Then** the worker runs as a separate container (same image, different entrypoint) alongside the app and db containers. (AC: #8 -- already configured in docker-compose.yml)

9. **Given** the system restarts (container restart, server reboot), **When** the worker starts up, **Then** it resumes processing any pending notifications that were not delivered before the restart. (AC: #9)

## Tasks / Subtasks

- [x] Task 1: Create `PendingNotification` model in `esb/models/pending_notification.py` (AC: #1)
  - [x] 1.1: Define `PendingNotification` class with all fields: `id`, `notification_type` (String(50), indexed), `target` (String(255)), `payload` (JSON), `status` (String(20), indexed, default 'pending'), `created_at`, `next_retry_at`, `retry_count` (Integer, default 0), `delivered_at`, `error_message` (Text)
  - [x] 1.2: Add `__repr__` method
  - [x] 1.3: Add import to `esb/models/__init__.py`

- [x] Task 2: Generate and verify Alembic migration (AC: #1)
  - [x] 2.1: Generate migration with `flask db migrate -m "Add pending_notifications table"`
  - [x] 2.2: Verify migration creates `pending_notifications` table with proper columns and indexes
  - [x] 2.3: Apply migration with `flask db upgrade`

- [x] Task 3: Create `notification_service.py` in `esb/services/` (AC: #2, #5, #6)
  - [x] 3.1: Implement `queue_notification(notification_type, target, payload)` -- inserts row with status 'pending'
  - [x] 3.2: Implement `get_pending_notifications()` -- queries rows where status='pending' AND (next_retry_at IS NULL OR next_retry_at <= now)
  - [x] 3.3: Implement `mark_delivered(notification_id)` -- updates status to 'delivered', sets delivered_at
  - [x] 3.4: Implement `mark_failed(notification_id, error_message)` -- increments retry_count, sets error_message, computes next_retry_at with exponential backoff
  - [x] 3.5: Implement `process_notification(notification)` -- dispatcher that routes to the correct delivery handler based on notification_type
  - [x] 3.6: Implement `_deliver_slack_message(notification)` -- stub that raises NotImplementedError (Slack delivery in Epic 6)
  - [x] 3.7: Implement `_deliver_static_page_push(notification)` -- stub that raises NotImplementedError (Static page push in Story 5.2)
  - [x] 3.8: Implement `run_worker_loop(app)` -- the main polling loop (poll every 30s, process all pending, handle errors)
  - [x] 3.9: Add mutation logging for queue and delivery events

- [x] Task 4: Register `flask worker run` CLI command in `esb/__init__.py` (AC: #3)
  - [x] 4.1: Add `worker` CLI group with `run` subcommand to `_register_cli()`
  - [x] 4.2: CLI command imports and calls `notification_service.run_worker_loop(app)`
  - [x] 4.3: Add `--poll-interval` option (default 30 seconds) for configurable polling
  - [x] 4.4: Add graceful shutdown handling (SIGTERM/SIGINT)

- [x] Task 5: Write model tests in `tests/test_models/test_pending_notification.py` (AC: #1)
  - [x] 5.1: Test model creation with all required fields
  - [x] 5.2: Test default values (status='pending', retry_count=0)
  - [x] 5.3: Test payload stored as JSON
  - [x] 5.4: Test notification_type field
  - [x] 5.5: Test repr output

- [x] Task 6: Write service tests in `tests/test_services/test_notification_service.py` (AC: #2, #4, #5, #6, #7)
  - [x] 6.1: Test `queue_notification()` creates pending row
  - [x] 6.2: Test `queue_notification()` stores payload as JSON
  - [x] 6.3: Test `queue_notification()` logs mutation
  - [x] 6.4: Test `get_pending_notifications()` returns only pending with eligible retry time
  - [x] 6.5: Test `get_pending_notifications()` excludes delivered notifications
  - [x] 6.6: Test `get_pending_notifications()` excludes notifications with future next_retry_at
  - [x] 6.7: Test `mark_delivered()` updates status and delivered_at
  - [x] 6.8: Test `mark_delivered()` logs mutation
  - [x] 6.9: Test `mark_failed()` increments retry_count and sets error_message
  - [x] 6.10: Test `mark_failed()` computes correct exponential backoff intervals
  - [x] 6.11: Test `mark_failed()` caps backoff at 1 hour maximum
  - [x] 6.12: Test `mark_failed()` logs mutation
  - [x] 6.13: Test `process_notification()` with unknown type raises/logs error
  - [x] 6.14: Test `process_notification()` with slack_message type calls _deliver_slack_message
  - [x] 6.15: Test `process_notification()` with static_page_push type calls _deliver_static_page_push

- [x] Task 7: Write CLI tests in `tests/test_cli.py` (AC: #3)
  - [x] 7.1: Test `flask worker run` command is registered
  - [x] 7.2: Test worker processes pending notifications (mock the worker loop for testability)

- [x] Task 8: Verify Docker Compose worker container config (AC: #8)
  - [x] 8.1: Verify `docker-compose.yml` worker service uses `flask worker run` command (already exists)
  - [x] 8.2: Ensure FLASK_APP env var is available to worker container (via .env file)

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Function-based services:** All services use module-level functions, NOT classes. Follow the pattern in `esb/services/repair_service.py`.
5. **Mutation logging:** Use `log_mutation(event, user, data)` from `esb/utils/logging.py` for all data-changing operations.
6. **Domain exceptions:** Use `ValidationError` from `esb/utils/exceptions.py`.
7. **CLI pattern:** Register commands via `_register_cli(app)` in `esb/__init__.py` using `@app.cli.command()` with click decorators.
8. **UTC timestamps:** `default=lambda: datetime.now(UTC)` for all timestamp columns.
9. **Import pattern:** Import services locally inside view/CLI functions to avoid circular imports.
10. **Flash category:** Use `'danger'` NOT `'error'` for error flash messages.

### Critical Implementation Details

#### PendingNotification Model (`esb/models/pending_notification.py`)

```python
"""PendingNotification model for the notification queue."""

from datetime import UTC, datetime

from esb.extensions import db


class PendingNotification(db.Model):
    """Queue table for outbound notifications and static page pushes."""

    __tablename__ = 'pending_notifications'

    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    target = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(UTC),
    )
    next_retry_at = db.Column(db.DateTime, nullable=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    delivered_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PendingNotification {self.id} type={self.notification_type!r} status={self.status!r}>'
```

**Key decisions:**
- `notification_type` uses String(50) -- values: `'slack_message'`, `'static_page_push'`
- `target` is String(255) -- stores Slack channel name or push destination path
- `payload` is JSON column -- stores notification-specific data (message content, equipment info, etc.)
- `status` values: `'pending'`, `'delivered'`, `'failed'` -- indexed for efficient polling queries
- `next_retry_at` is nullable DateTime -- NULL means "ready to process now"
- `retry_count` defaults to 0, incremented on each failure
- `error_message` is Text (nullable) -- stores the last error for debugging
- `delivered_at` is nullable -- set when status changes to 'delivered'
- No foreign keys to other tables -- notifications are self-contained messages

#### Notification Service (`esb/services/notification_service.py`)

```python
"""Notification queue management and background worker."""

import logging
import signal
import time
from datetime import UTC, datetime, timedelta

from esb.extensions import db
from esb.models.pending_notification import PendingNotification
from esb.utils.logging import log_mutation

logger = logging.getLogger(__name__)

# Exponential backoff schedule (in seconds): 30s, 1m, 2m, 5m, 15m, 1h max
BACKOFF_SCHEDULE = [30, 60, 120, 300, 900, 3600]


def queue_notification(
    notification_type: str,
    target: str,
    payload: dict | None = None,
) -> PendingNotification:
    """Insert a notification into the queue for background delivery.

    Args:
        notification_type: Type of notification ('slack_message', 'static_page_push').
        target: Delivery target (Slack channel name, push destination).
        payload: JSON-serializable data for the notification.

    Returns:
        The created PendingNotification.
    """
    notification = PendingNotification(
        notification_type=notification_type,
        target=target,
        payload=payload,
        status='pending',
    )
    db.session.add(notification)
    db.session.commit()

    log_mutation('notification.queued', 'system', {
        'id': notification.id,
        'type': notification_type,
        'target': target,
    })

    return notification


def get_pending_notifications() -> list[PendingNotification]:
    """Get all notifications ready for delivery.

    Returns notifications where status is 'pending' and either
    next_retry_at is NULL (first attempt) or next_retry_at <= now.
    """
    now = datetime.now(UTC)
    return list(
        db.session.execute(
            db.select(PendingNotification)
            .filter_by(status='pending')
            .filter(
                db.or_(
                    PendingNotification.next_retry_at.is_(None),
                    PendingNotification.next_retry_at <= now,
                )
            )
            .order_by(PendingNotification.created_at.asc())
        ).scalars().all()
    )


def mark_delivered(notification_id: int) -> PendingNotification:
    """Mark a notification as successfully delivered."""
    notification = db.session.get(PendingNotification, notification_id)
    notification.status = 'delivered'
    notification.delivered_at = datetime.now(UTC)
    db.session.commit()

    log_mutation('notification.delivered', 'system', {
        'id': notification.id,
        'type': notification.notification_type,
        'target': notification.target,
    })

    return notification


def mark_failed(notification_id: int, error_message: str) -> PendingNotification:
    """Mark a notification delivery as failed with exponential backoff.

    Backoff schedule: 30s, 1m, 2m, 5m, 15m, max 1h.
    """
    notification = db.session.get(PendingNotification, notification_id)
    notification.retry_count += 1
    notification.error_message = error_message

    # Compute backoff delay
    backoff_index = min(notification.retry_count - 1, len(BACKOFF_SCHEDULE) - 1)
    backoff_seconds = BACKOFF_SCHEDULE[backoff_index]
    notification.next_retry_at = datetime.now(UTC) + timedelta(seconds=backoff_seconds)

    db.session.commit()

    log_mutation('notification.failed', 'system', {
        'id': notification.id,
        'type': notification.notification_type,
        'target': notification.target,
        'retry_count': notification.retry_count,
        'error': error_message,
        'next_retry_at': notification.next_retry_at.isoformat(),
    })

    return notification


def process_notification(notification: PendingNotification) -> None:
    """Dispatch a notification to the appropriate delivery handler.

    Args:
        notification: The PendingNotification to process.

    Raises:
        NotImplementedError: For notification types not yet implemented.
        Exception: Any delivery error (caught by worker loop).
    """
    handlers = {
        'slack_message': _deliver_slack_message,
        'static_page_push': _deliver_static_page_push,
    }

    handler = handlers.get(notification.notification_type)
    if handler is None:
        raise ValueError(f'Unknown notification type: {notification.notification_type!r}')

    handler(notification)


def _deliver_slack_message(notification: PendingNotification) -> None:
    """Deliver a Slack message notification.

    Stub -- actual Slack API delivery will be implemented in Epic 6 (Story 6.1).
    For now, this raises NotImplementedError so the queue can properly
    retry or the notification can be left pending until Slack integration exists.
    """
    raise NotImplementedError('Slack message delivery not yet implemented (Epic 6)')


def _deliver_static_page_push(notification: PendingNotification) -> None:
    """Deliver a static page push notification.

    Stub -- actual static page generation and push will be implemented
    in Story 5.2.
    """
    raise NotImplementedError('Static page push not yet implemented (Story 5.2)')


def run_worker_loop(poll_interval: int = 30) -> None:
    """Main worker polling loop.

    Polls the pending_notifications table every `poll_interval` seconds
    and processes each ready notification. Handles errors gracefully by
    marking failed notifications for retry.

    Args:
        poll_interval: Seconds between polling cycles (default 30).
    """
    _shutdown = False

    def _handle_signal(signum, frame):
        nonlocal _shutdown
        logger.info('Received signal %s, shutting down gracefully...', signum)
        _shutdown = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info('Worker started, polling every %d seconds', poll_interval)

    while not _shutdown:
        try:
            notifications = get_pending_notifications()
            if notifications:
                logger.info('Processing %d pending notification(s)', len(notifications))

            for notification in notifications:
                if _shutdown:
                    break
                try:
                    logger.info(
                        'Processing notification %d (type=%s, target=%s)',
                        notification.id, notification.notification_type, notification.target,
                    )
                    process_notification(notification)
                    mark_delivered(notification.id)
                    logger.info('Notification %d delivered successfully', notification.id)
                except NotImplementedError as e:
                    # Delivery handler not yet implemented -- mark failed
                    mark_failed(notification.id, str(e))
                    logger.warning('Notification %d: %s', notification.id, e)
                except Exception as e:
                    mark_failed(notification.id, str(e))
                    logger.error(
                        'Notification %d delivery failed: %s', notification.id, e,
                        exc_info=True,
                    )

        except Exception:
            logger.error('Error in worker polling loop', exc_info=True)

        if not _shutdown:
            time.sleep(poll_interval)

    logger.info('Worker shut down cleanly')
```

**Key decisions:**
- `queue_notification()` commits immediately so the notification is durable
- `get_pending_notifications()` uses `db.or_()` for the retry-time check
- `mark_failed()` uses index-based lookup into `BACKOFF_SCHEDULE` (capped at the last entry for max 1h)
- `process_notification()` dispatches to type-specific handlers via a dict lookup
- `_deliver_slack_message()` and `_deliver_static_page_push()` are stubs raising `NotImplementedError` -- these will be implemented in Stories 5.2 and 6.1
- `run_worker_loop()` handles SIGTERM/SIGINT for graceful Docker container shutdown
- Worker catches `NotImplementedError` separately from general exceptions for cleaner logging
- All state changes logged via mutation logger

#### Flask CLI Command (`esb/__init__.py`)

Add to `_register_cli(app)`:

```python
@app.cli.group()
def worker():
    """Background worker commands."""
    pass

@worker.command('run')
@click.option('--poll-interval', default=30, type=int,
              help='Seconds between polling cycles (default: 30)')
def worker_run(poll_interval):
    """Run the background notification worker."""
    from esb.services import notification_service

    click.echo(f'Starting notification worker (poll interval: {poll_interval}s)')
    notification_service.run_worker_loop(poll_interval=poll_interval)
```

**Key decisions:**
- `worker` is a CLI group with `run` subcommand (matches `flask worker run` in docker-compose.yml and Makefile)
- `--poll-interval` option allows configuring the polling frequency
- Import `notification_service` inside the command function to avoid circular imports
- Uses `click.echo()` for initial startup message, then `logger.info()` inside the loop

#### Model Registration (`esb/models/__init__.py`)

Add import:
```python
from esb.models.pending_notification import PendingNotification
```

And add `'PendingNotification'` to the `__all__` list.

### Exponential Backoff Schedule

The backoff schedule for failed notification delivery:

| Retry # | Backoff Delay | Total Wait |
|---------|--------------|------------|
| 1       | 30 seconds   | 30s        |
| 2       | 1 minute     | 1m 30s     |
| 3       | 2 minutes    | 3m 30s     |
| 4       | 5 minutes    | 8m 30s     |
| 5       | 15 minutes   | 23m 30s    |
| 6+      | 1 hour (max) | 1h 23m 30s |

Formula: `BACKOFF_SCHEDULE[min(retry_count - 1, len(BACKOFF_SCHEDULE) - 1)]`

After retry 6, every subsequent retry waits 1 hour (the maximum).

### Notification Types

| Type | Target | Payload | Delivery |
|------|--------|---------|----------|
| `slack_message` | Slack channel (e.g., `#woodshop`) | `{equipment_name, area, severity, description, reporter_name, event_type, ...}` | Story 6.1 |
| `static_page_push` | Push destination (config-driven) | `{trigger_event, equipment_id, ...}` | Story 5.2 |

### What This Story Does NOT Include

1. **Slack API delivery** -- Story 6.1 will implement `_deliver_slack_message()` with the actual Slack WebClient call
2. **Static page generation/push** -- Story 5.2 will implement `_deliver_static_page_push()` with template rendering and file push
3. **Notification trigger configuration** -- Story 5.3 will add the AppConfig settings for which events trigger notifications
4. **Notification hooks in repair_service** -- Story 5.3 will add calls to `notification_service.queue_notification()` inside `create_repair_record()` and `update_repair_record()` after the trigger configuration is in place
5. **Slack App integration** -- Epic 6 handles all Slack App setup

### Reuse from Previous Stories (DO NOT recreate)

**From Story 1.1 (Project Scaffolding):**
- `esb/__init__.py` -- App factory with `_register_cli()` function
- `esb/extensions.py` -- `db`, `login_manager`, `migrate`, `csrf` instances
- `esb/config.py` -- Configuration classes (Config, TestingConfig, etc.)
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` function
- `esb/utils/exceptions.py` -- `ESBError`, `ValidationError` hierarchy
- `docker-compose.yml` -- Worker container already configured with `flask worker run`
- `Makefile` -- `worker:` target already defined

**From Story 2.4 (Equipment Archiving):**
- `esb/models/app_config.py` -- AppConfig model (key-value store for runtime settings)
- `esb/services/config_service.py` -- `get_config()`, `set_config()` functions

**Existing test infrastructure:**
- `tests/conftest.py` -- `app`, `db`, `client`, `capture` fixtures
- `tests/test_cli.py` -- CLI test patterns using `app.test_cli_runner()`

### Project Structure Notes

**New files to create:**
- `esb/models/pending_notification.py` -- PendingNotification model
- `esb/services/notification_service.py` -- Queue management, worker loop, delivery dispatching
- `tests/test_models/test_pending_notification.py` -- Model tests
- `tests/test_services/test_notification_service.py` -- Service tests
- `migrations/versions/XXXX_add_pending_notifications_table.py` -- Migration (auto-generated)

**Files to modify:**
- `esb/models/__init__.py` -- Add `PendingNotification` import
- `esb/__init__.py` -- Add `worker run` CLI command to `_register_cli()`
- `tests/test_cli.py` -- Add worker CLI tests

**Files NOT to modify:**
- `esb/services/repair_service.py` -- NO notification hooks yet (Story 5.3 adds these after trigger config)
- `esb/services/status_service.py` -- No changes needed
- `docker-compose.yml` -- Worker container already configured
- `Makefile` -- Worker target already defined
- `esb/config.py` -- No new config variables needed for the queue itself
- Any view files -- This story has no UI components

### Previous Story Intelligence (from Story 4.4)

**Patterns to follow:**
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside CLI/view functions to avoid circular imports
- `db.session.get(Model, id)` for PK lookups
- `db.select(Model).filter_by(...)` for queries
- `default=lambda: datetime.now(UTC)` for timestamps (import `UTC` from `datetime`)
- Test factories in `tests/conftest.py`: `make_area`, `make_equipment`, `make_repair_record`
- CLI tests use `app.test_cli_runner()` with `runner.invoke(args=[...])`
- 721 tests currently passing, 0 lint errors

**Code review lessons from previous stories:**
- Don't duplicate logic -- reuse existing service patterns
- Test all mutation log events using the `capture` fixture
- Include edge case tests (empty results, invalid inputs)
- Use `db.or_()` from SQLAlchemy for OR conditions (NOT Python `or`)

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

**Model tests (`tests/test_models/test_pending_notification.py`):**
- Test model creation with required fields
- Test default values (status='pending', retry_count=0)
- Test JSON payload storage and retrieval
- Test repr output
- Use `db` fixture from conftest

**Service tests (`tests/test_services/test_notification_service.py`):**
- Test `queue_notification()` creates row with correct fields
- Test `get_pending_notifications()` filtering logic (pending only, retry time eligible)
- Test `mark_delivered()` updates all relevant fields
- Test `mark_failed()` with exponential backoff calculations
- Test `process_notification()` dispatching
- Test mutation logging using `capture` fixture

**CLI tests (`tests/test_cli.py`):**
- Test `flask worker run` command registers without error
- Test worker processes a pending notification (use mocking to avoid actual polling loop)

**Test data patterns:**

```python
# Create a pending notification
from esb.models.pending_notification import PendingNotification
from esb.extensions import db as _db

notification = PendingNotification(
    notification_type='slack_message',
    target='#woodshop',
    payload={'equipment_name': 'SawStop', 'severity': 'Down', 'description': 'Motor broken'},
    status='pending',
)
_db.session.add(notification)
_db.session.commit()

# Test backoff calculation
from esb.services.notification_service import mark_failed, BACKOFF_SCHEDULE
mark_failed(notification.id, 'Connection refused')
assert notification.retry_count == 1
assert notification.error_message == 'Connection refused'
# next_retry_at should be ~30 seconds from now
```

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with Flask CLI (click-based)
- **Flask-SQLAlchemy 3.1.x** for ORM
- **Flask-Migrate** for Alembic migrations
- **MariaDB 12.2.2** (via Docker)
- **pytest** for tests
- **No new dependencies needed** -- all required packages already in requirements.txt
- `signal` module from Python stdlib for graceful shutdown
- `time` module from Python stdlib for sleep between polling cycles

### Docker Compose (Already Configured)

The `docker-compose.yml` already has a `worker` service:

```yaml
worker:
  build: .
  command: flask worker run
  depends_on:
    db:
      condition: service_healthy
  env_file: .env
  restart: unless-stopped
```

**IMPORTANT:** The `FLASK_APP` environment variable must be set in `.env` for the worker container to find the Flask app factory. The current `.env.example` should already include this. Verify that `FLASK_APP=esb:create_app` is present. If the `.env` file uses `FLASK_APP`, the worker will find the app factory and have full access to the database and services.

### Graceful Shutdown

The worker handles SIGTERM (Docker container stop) and SIGINT (Ctrl+C) to shut down gracefully:
- Sets a `_shutdown` flag when signal received
- Finishes processing the current notification (if any)
- Exits the polling loop cleanly
- Logs the shutdown event

This ensures notifications in-flight are completed before the worker stops, and pending notifications remain in the database for processing after restart (AC: #9).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5 Story 5.1]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR10-NFR12 Integration]
- [Source: _bmad-output/planning-artifacts/prd.md#NFR14-NFR17 Reliability]
- [Source: _bmad-output/planning-artifacts/architecture.md#Notification Queue]
- [Source: _bmad-output/planning-artifacts/architecture.md#Background Worker Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Docker Compose Topology]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment]
- [Source: esb/__init__.py#_register_cli]
- [Source: esb/models/app_config.py#AppConfig]
- [Source: esb/models/audit_log.py#AuditLog]
- [Source: esb/services/repair_service.py#create_repair_record]
- [Source: esb/services/repair_service.py#update_repair_record]
- [Source: esb/utils/logging.py#log_mutation]
- [Source: docker-compose.yml#worker]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Fixed timezone-aware vs naive datetime comparison in backoff test (SQLAlchemy DateTime returns naive datetimes from SQLite test DB)

### Completion Notes List

- Task 1: Created PendingNotification model with all specified fields, indexes on notification_type and status, UTC timestamps
- Task 2: Generated and applied Alembic migration `2d0213647834_add_pending_notifications_table.py` — creates pending_notifications table with proper columns and indexes
- Task 3: Created notification_service.py with queue_notification(), get_pending_notifications(), mark_delivered(), mark_failed() (exponential backoff), process_notification() dispatcher, stub handlers for slack_message and static_page_push, run_worker_loop() with SIGTERM/SIGINT graceful shutdown, mutation logging on all state changes
- Task 4: Registered `flask worker run` CLI command with `--poll-interval` option in _register_cli()
- Task 5: 6 model tests covering creation, defaults, JSON payload, notification_type values, repr
- Task 6: 39 service tests covering queue_notification (including input validation), get_pending_notifications filtering (including batch_size limit, failed status exclusion), mark_delivered (including not-found), mark_failed with backoff verification (including max retries/permanent failure, not-found), process_notification dispatching, stub NotImplementedError, mutation logging, and run_worker_loop (signal handling, delivery, error handling, graceful shutdown, polling backoff)
- Task 7: 2 CLI tests covering command registration and poll-interval option
- Task 8: Verified docker-compose.yml worker service and FLASK_APP env var in .env.example
- All 768 tests pass (721 existing + 47 new), 0 ruff lint errors

### Change Log

- 2026-02-16: Implemented Story 5.1 — Notification Queue & Background Worker
- 2026-02-16: Code review fixes — input validation, null checks, max retries, batch size limit, polling backoff, import ordering, worker loop tests

### File List

New files:
- esb/models/pending_notification.py
- esb/services/notification_service.py
- tests/test_models/test_pending_notification.py
- tests/test_services/test_notification_service.py
- migrations/versions/2d0213647834_add_pending_notifications_table.py

Modified files:
- esb/models/__init__.py
- esb/__init__.py
- tests/test_cli.py
