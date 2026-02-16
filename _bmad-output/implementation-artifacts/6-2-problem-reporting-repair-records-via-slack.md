# Story 6.2: Problem Reporting & Repair Records via Slack

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a member,
I want to report equipment problems and manage repair records directly from Slack,
So that I can flag issues and track repairs without leaving the conversation I'm already in.

## Acceptance Criteria

1. **Given** the Slack App is installed in the workspace, **When** a member uses `/esb-report`, **Then** a Slack modal opens with fields: equipment selector, name, description (required), severity (defaults to "Not Sure"), safety risk flag, consumable checkbox. (AC: #1)

2. **Given** a member fills out the Slack problem report modal and submits, **When** the submission is processed, **Then** the Slack handler calls `repair_service.create_repair_record()` (same service function used by the web form), **And** a repair record is created with status "New", **And** a confirmation message is posted as an ephemeral message to the member. (AC: #2)

3. **Given** a Technician or Staff member uses `/esb-repair`, **When** the slash command is invoked, **Then** a Slack modal opens with rich form fields: equipment selector, description, severity, assignee, status. (AC: #3)

4. **Given** a Technician or Staff member submits a repair record creation modal, **When** the submission is processed, **Then** the Slack handler calls the same `repair_service` functions as the web UI, **And** the repair record is created with all provided details. (AC: #4)

5. **Given** a Technician or Staff member wants to update an existing repair record from Slack, **When** they use `/esb-update [repair-id]`, **Then** a Slack modal opens pre-populated with the current record data and editable fields: status, notes, severity, assignee, ETA. (AC: #5)

6. **Given** a repair record update is submitted via Slack, **When** the submission is processed, **Then** the Slack handler calls `repair_service.update_repair_record()` with the changes, **And** timeline entries are created for each change, with the Slack user identified as the author. (AC: #6)

7. **Given** a Slack handler encounters a service layer error (`EquipmentNotFound`, `ValidationError`, etc.), **When** the error is caught, **Then** a Slack-formatted error message is returned to the user (not a web HTML error page). (AC: #7)

## Tasks / Subtasks

- [ ] Task 1: Create `esb/slack/forms.py` with Block Kit modal builder functions (AC: #1, #3, #5)
  - [ ] 1.1: Create `build_problem_report_modal(equipment_options)` returning Block Kit modal view dict
  - [ ] 1.2: Create `build_repair_create_modal(equipment_options, user_options)` returning Block Kit modal view dict
  - [ ] 1.3: Create `build_repair_update_modal(repair_record, status_options, severity_options, user_options)` returning Block Kit modal view dict with pre-populated values and `private_metadata` containing repair record ID
  - [ ] 1.4: Create `build_equipment_options()` helper that queries non-archived equipment and returns Slack option dicts formatted as `"Equipment Name (Area)"`
  - [ ] 1.5: Create `build_user_options()` helper that queries active Technician/Staff users and returns Slack option dicts

- [ ] Task 2: Create `esb/slack/handlers.py` with command and view submission handlers (AC: #1-#7)
  - [ ] 2.1: Create `register_handlers(bolt_app)` function that registers all commands and views
  - [ ] 2.2: Implement `_resolve_esb_user(client, slack_user_id)` helper that maps Slack user ID to ESB User via email lookup
  - [ ] 2.3: Implement `/esb-report` command handler: `ack()`, build equipment options, open problem report modal
  - [ ] 2.4: Implement `problem_report_submission` view handler: extract form values, call `repair_service.create_repair_record()`, post ephemeral confirmation
  - [ ] 2.5: Implement `/esb-repair` command handler: `ack()`, resolve ESB user (must be tech/staff), build equipment + user options, open repair creation modal
  - [ ] 2.6: Implement `repair_create_submission` view handler: extract form values, call `repair_service.create_repair_record()` with author_id, post ephemeral confirmation
  - [ ] 2.7: Implement `/esb-update` command handler: `ack()`, resolve ESB user (must be tech/staff), parse repair ID from command text, load repair record, build pre-populated update modal
  - [ ] 2.8: Implement `repair_update_submission` view handler: extract form values from view state, get repair_record_id from `private_metadata`, call `repair_service.update_repair_record()` with author mapping, post ephemeral confirmation
  - [ ] 2.9: Implement error handling: catch `ValidationError` in all view handlers and return Slack-formatted error via `ack(response_action="errors")` or ephemeral message

- [ ] Task 3: Update `esb/slack/__init__.py` to register handlers (AC: #1-#6)
  - [ ] 3.1: Import and call `register_handlers(_bolt_app)` from `handlers.py` inside `init_slack()`
  - [ ] 3.2: Update the placeholder `handle_message_events` comment to reflect Story 6.2 is now implemented

- [ ] Task 4: Write tests for `esb/slack/forms.py` (`tests/test_slack/test_forms.py`) (AC: #1, #3, #5)
  - [ ] 4.1: Test `build_problem_report_modal()` returns valid Block Kit modal structure with correct blocks
  - [ ] 4.2: Test `build_repair_create_modal()` returns valid modal with equipment + user selectors
  - [ ] 4.3: Test `build_repair_update_modal()` returns modal with pre-populated values and correct `private_metadata`
  - [ ] 4.4: Test `build_equipment_options()` returns correct option format, excludes archived equipment
  - [ ] 4.5: Test `build_user_options()` returns only active tech/staff users

- [ ] Task 5: Write tests for `esb/slack/handlers.py` (`tests/test_slack/test_handlers.py`) (AC: #1-#7)
  - [ ] 5.1: Test `/esb-report` command calls `ack()` and opens modal via `client.views_open()`
  - [ ] 5.2: Test problem report submission creates repair record via `repair_service`
  - [ ] 5.3: Test problem report submission posts ephemeral confirmation
  - [ ] 5.4: Test `/esb-repair` command rejects non-tech/staff users with ephemeral error
  - [ ] 5.5: Test `/esb-repair` command opens modal for authorized users
  - [ ] 5.6: Test repair creation submission creates record with correct author_id
  - [ ] 5.7: Test `/esb-update 42` parses repair ID and opens pre-populated modal
  - [ ] 5.8: Test `/esb-update` without ID returns error message
  - [ ] 5.9: Test `/esb-update 999` with non-existent ID returns error
  - [ ] 5.10: Test repair update submission calls `update_repair_record()` with correct changes and author
  - [ ] 5.11: Test `_resolve_esb_user()` maps Slack user to ESB user via email
  - [ ] 5.12: Test `_resolve_esb_user()` returns None for unmapped user
  - [ ] 5.13: Test ValidationError in view handler returns Slack-formatted error
  - [ ] 5.14: Test all handlers work within Flask app context

- [ ] Task 6: Update `tests/test_slack/test_init.py` for new handler registration (AC: #1)
  - [ ] 6.1: Verify `register_handlers` is called during `init_slack()` when Slack is enabled
  - [ ] 6.2: Verify command handlers are registered on the Bolt app

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Slack handlers are thin -- parse input, call service, format response.
2. **Dependency flow:** `slack/handlers -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Function-based services:** All services use module-level functions, NOT classes.
5. **Mutation logging:** Use `log_mutation(event, user, data)` from `esb/utils/logging.py` for all data-changing operations. Repair service already does this -- do NOT duplicate in Slack handlers.
6. **Domain exceptions:** Use `ValidationError` from `esb/utils/exceptions.py`.
7. **UTC timestamps:** `default=lambda: datetime.now(UTC)` for all timestamp columns.
8. **Import pattern:** Import services locally inside handler functions to avoid circular imports.
9. **ruff target-version:** `"py313"` (NOT py314).
10. **Config storage pattern:** Boolean configs stored as `'true'`/`'false'` strings via `config_service.get_config(key, default)`.
11. **Slack isolation boundary:** `esb/slack/` is self-contained. It imports from `esb/services/` but nothing else imports from `esb/slack/`. If Slack is disabled, the module is not loaded.
12. **No duplicate notifications:** `repair_service` already queues all Slack notifications. Slack handlers MUST NOT queue additional notifications -- the service layer handles this.

### Critical Implementation Details

#### Module Architecture

```
esb/slack/
  __init__.py    # Bolt app setup, init_slack(), Blueprint (EXISTING -- modify)
  handlers.py    # Command + view submission handlers (NEW)
  forms.py       # Block Kit modal builder functions (NEW)
```

The architecture doc (`_bmad-output/planning-artifacts/architecture.md`) defines this structure. `handlers.py` contains command/view handlers. `forms.py` contains modal view definitions.

#### Flask App Context in Bolt Handlers

Bolt handlers are called via `SlackRequestHandler.handle()` from the Flask view `slack_events()`. Since this runs within Flask's request context, **`current_app`, `db`, and all services are available** inside Bolt handlers. Do NOT manually push app context.

```python
# CORRECT -- Flask context is already active
@bolt_app.command("/esb-report")
def handle_report(ack, body, client):
    ack()
    from esb.slack.forms import build_problem_report_modal, build_equipment_options
    options = build_equipment_options()  # DB access works here
    client.views_open(trigger_id=body["trigger_id"], view=build_problem_report_modal(options))

# WRONG -- do NOT push app context manually
# with flask_app.app_context():  # UNNECESSARY
```

#### Handler Registration Pattern

```python
# esb/slack/handlers.py
"""Slack command and view submission handlers."""

import logging

logger = logging.getLogger(__name__)


def register_handlers(bolt_app):
    """Register all Slack command and view submission handlers."""

    @bolt_app.command("/esb-report")
    def handle_esb_report(ack, body, client):
        ack()
        # ... handler logic ...

    @bolt_app.view("problem_report_submission")
    def handle_problem_report_submission(ack, body, client, view):
        # ... handler logic ...

    # ... more handlers ...
```

```python
# esb/slack/__init__.py -- ADD inside init_slack(), after _bolt_app creation:
    from esb.slack.handlers import register_handlers
    register_handlers(_bolt_app)
```

**Key: `register_handlers()` is called BEFORE registering the message event handler, so it runs after Bolt app is created but before the Flask blueprint is registered.**

#### User Mapping: Slack User ID -> ESB User

The `User` model has `slack_handle` (used for outbound DMs) and `email` fields. The existing `user_service._deliver_temp_password_via_slack()` uses email-based Slack user lookup (`users_lookupByEmail`) for outbound. For inbound (Slack -> ESB), reverse the mapping:

```python
def _resolve_esb_user(client, slack_user_id):
    """Map a Slack user ID to an ESB User account.

    Strategy:
    1. Call Slack API to get user's email from their profile
    2. Look up ESB User by matching email

    Args:
        client: Slack WebClient instance (provided by Bolt).
        slack_user_id: Slack user ID (e.g., 'U12345678').

    Returns:
        User instance or None if no matching ESB account.
    """
    from esb.extensions import db
    from esb.models.user import User

    try:
        result = client.users_info(user=slack_user_id)
        email = result['user']['profile'].get('email')
        if not email:
            return None
        return db.session.execute(
            db.select(User).filter_by(email=email, is_active=True)
        ).scalars().first()
    except Exception:
        logger.warning('Failed to resolve ESB user for Slack user %s', slack_user_id, exc_info=True)
        return None
```

**Critical:** This requires the Slack App to have `users:read` and `users:read.email` OAuth scopes. Note this in the Slack App configuration section.

**For `/esb-report` (member reports):** No user mapping needed. Use the Slack user's display name as `reporter_name` and `created_by`. Get it from `body["user_name"]` (Slack username) or `client.users_info()` for real name.

**For `/esb-repair` and `/esb-update` (tech/staff only):** User mapping IS required. If `_resolve_esb_user()` returns None or the user's role is not `technician`/`staff`, return an ephemeral error.

#### Equipment Selector (Block Kit static_select)

Query non-archived equipment and format as Slack options:

```python
def build_equipment_options():
    """Build Slack static_select options for non-archived equipment.

    Returns list of option dicts: [{"text": {"type": "plain_text", "text": "Name (Area)"}, "value": "id"}, ...]
    """
    from esb.extensions import db
    from esb.models.equipment import Equipment

    equipment_list = db.session.execute(
        db.select(Equipment)
        .filter(Equipment.is_archived.is_(False))
        .order_by(Equipment.name)
    ).scalars().all()

    options = []
    for e in equipment_list:
        area_name = e.area.name if e.area else 'No Area'
        options.append({
            'text': {'type': 'plain_text', 'text': f'{e.name} ({area_name})'[:75]},
            'value': str(e.id),
        })
    return options
```

**Note:** Slack `static_select` supports max 100 options. For this makerspace project, <100 equipment is expected. If the list is empty, the command handler should return an ephemeral error instead of opening an empty modal.

#### User Selector for Assignee

```python
def build_user_options():
    """Build Slack static_select options for active Technician/Staff users.

    Returns list of option dicts.
    """
    from esb.extensions import db
    from esb.models.user import User

    users = db.session.execute(
        db.select(User)
        .filter(User.is_active.is_(True), User.role.in_(['technician', 'staff']))
        .order_by(User.username)
    ).scalars().all()

    return [
        {
            'text': {'type': 'plain_text', 'text': f'{u.username} ({u.role})'[:75]},
            'value': str(u.id),
        }
        for u in users
    ]
```

#### Problem Report Modal (`/esb-report`)

```python
def build_problem_report_modal(equipment_options):
    """Build Block Kit modal for member problem reports.

    Args:
        equipment_options: List of equipment option dicts from build_equipment_options().

    Returns:
        Block Kit modal view dict.
    """
    return {
        'type': 'modal',
        'callback_id': 'problem_report_submission',
        'title': {'type': 'plain_text', 'text': 'Report a Problem'},
        'submit': {'type': 'plain_text', 'text': 'Submit Report'},
        'close': {'type': 'plain_text', 'text': 'Cancel'},
        'blocks': [
            {
                'type': 'input',
                'block_id': 'equipment_block',
                'element': {
                    'type': 'static_select',
                    'action_id': 'equipment_select',
                    'placeholder': {'type': 'plain_text', 'text': 'Select equipment'},
                    'options': equipment_options,
                },
                'label': {'type': 'plain_text', 'text': 'Equipment'},
            },
            {
                'type': 'input',
                'block_id': 'name_block',
                'element': {
                    'type': 'plain_text_input',
                    'action_id': 'reporter_name',
                    'placeholder': {'type': 'plain_text', 'text': 'Your name'},
                },
                'label': {'type': 'plain_text', 'text': 'Your Name'},
            },
            {
                'type': 'input',
                'block_id': 'description_block',
                'element': {
                    'type': 'plain_text_input',
                    'action_id': 'description',
                    'multiline': True,
                    'placeholder': {'type': 'plain_text', 'text': 'Describe the problem'},
                },
                'label': {'type': 'plain_text', 'text': 'Description'},
            },
            {
                'type': 'input',
                'block_id': 'severity_block',
                'optional': True,
                'element': {
                    'type': 'static_select',
                    'action_id': 'severity',
                    'initial_option': {
                        'text': {'type': 'plain_text', 'text': 'Not Sure'},
                        'value': 'Not Sure',
                    },
                    'options': [
                        {'text': {'type': 'plain_text', 'text': 'Not Sure'}, 'value': 'Not Sure'},
                        {'text': {'type': 'plain_text', 'text': 'Degraded'}, 'value': 'Degraded'},
                        {'text': {'type': 'plain_text', 'text': 'Down'}, 'value': 'Down'},
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Severity'},
            },
            {
                'type': 'input',
                'block_id': 'safety_risk_block',
                'optional': True,
                'element': {
                    'type': 'checkboxes',
                    'action_id': 'safety_risk',
                    'options': [
                        {
                            'text': {'type': 'plain_text', 'text': 'This is a safety risk'},
                            'value': 'safety_risk',
                        },
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Safety Risk'},
            },
            {
                'type': 'input',
                'block_id': 'consumable_block',
                'optional': True,
                'element': {
                    'type': 'checkboxes',
                    'action_id': 'consumable',
                    'options': [
                        {
                            'text': {'type': 'plain_text', 'text': 'This is a consumable item'},
                            'value': 'consumable',
                        },
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Consumable'},
            },
        ],
    }
```

#### Repair Creation Modal (`/esb-repair`)

Similar to problem report modal but includes: equipment selector, description (required), severity (optional), assignee (optional, static_select from user list), status (optional, defaults to "New"). All 10 statuses available.

The callback_id is `'repair_create_submission'`.

#### Repair Update Modal (`/esb-update [id]`)

Pre-populated with current values. Fields:
- **Status**: `static_select` with `initial_option` set to current status. All 10 REPAIR_STATUSES as options.
- **Severity**: `static_select` with `initial_option` set to current severity (optional -- can be cleared).
- **Assignee**: `static_select` with `initial_option` set to current assignee (optional -- can be unassigned).
- **ETA**: `datepicker` with `initial_date` set to current ETA if present (format: `"YYYY-MM-DD"`).
- **Specialist Description**: `plain_text_input` with `initial_value` set to current value (optional).
- **Note**: `plain_text_input`, multiline, empty (for adding a new note, optional).

The `private_metadata` field stores the repair record ID as a string. The callback_id is `'repair_update_submission'`.

```python
# In view submission handler:
repair_record_id = int(view['private_metadata'])
```

#### Extracting Values from View State

Slack view state values are nested: `view["state"]["values"][block_id][action_id]`

```python
# Text input
values = view['state']['values']
description = values['description_block']['description']['value']

# Static select
equipment_id = int(values['equipment_block']['equipment_select']['selected_option']['value'])

# Optional static select (may be None)
severity_data = values['severity_block']['severity'].get('selected_option')
severity = severity_data['value'] if severity_data else 'Not Sure'

# Checkboxes (returns list of selected options)
safety_options = values['safety_risk_block']['safety_risk'].get('selected_options', [])
has_safety_risk = any(o['value'] == 'safety_risk' for o in safety_options)

# Date picker (optional)
eta_str = values['eta_block']['eta'].get('selected_date')  # "YYYY-MM-DD" or None
eta = datetime.strptime(eta_str, '%Y-%m-%d').date() if eta_str else None
```

#### Error Handling Pattern

For **view submission errors** (validation failures), use `ack()` with `response_action="errors"`:

```python
@bolt_app.view("problem_report_submission")
def handle_submission(ack, body, client, view):
    values = view['state']['values']
    # ... extract values ...

    try:
        from esb.services import repair_service
        record = repair_service.create_repair_record(...)
    except ValidationError as e:
        # Return error displayed in the modal
        ack(response_action='errors', errors={
            'description_block': str(e),
        })
        return

    ack()
    # Post ephemeral confirmation
    client.chat_postEphemeral(
        channel=body['user']['id'],
        user=body['user']['id'],
        text=f':white_check_mark: Problem report submitted for *{equipment_name}* (Repair #{record.id})',
    )
```

For **command errors** (e.g., user not authorized), post ephemeral message:

```python
@bolt_app.command("/esb-repair")
def handle_repair(ack, body, client):
    ack()
    esb_user = _resolve_esb_user(client, body['user_id'])
    if esb_user is None or esb_user.role not in ('technician', 'staff'):
        client.chat_postEphemeral(
            channel=body['channel_id'],
            user=body['user_id'],
            text=':x: You must have a Technician or Staff account linked to use this command.',
        )
        return
    # ... proceed with modal ...
```

#### Ephemeral Confirmation Messages

After successful submission, post an ephemeral message (only visible to the submitter):

```python
# For problem reports:
client.chat_postEphemeral(
    channel=body['user']['id'],
    user=body['user']['id'],
    text=f':white_check_mark: Problem report submitted for *{equipment_name}* (Repair #{record.id})',
)

# For repair creation:
client.chat_postEphemeral(
    channel=body['user']['id'],
    user=body['user']['id'],
    text=f':white_check_mark: Repair record #{record.id} created for *{equipment_name}*',
)

# For repair updates:
client.chat_postEphemeral(
    channel=body['user']['id'],
    user=body['user']['id'],
    text=f':white_check_mark: Repair record #{repair_record_id} updated',
)
```

**Note:** `body['user']['id']` is used as both `channel` (to DM the user) and `user` (to make it ephemeral). In view submission bodies, the user ID is at `body['user']['id']`.

#### Slack App Configuration Requirements (Non-Code)

The Slack App (configured at api.slack.com) needs:

1. **Slash Commands** registered:
   - `/esb-report` -- Request URL: `https://<app-url>/slack/events`
   - `/esb-repair` -- Request URL: `https://<app-url>/slack/events`
   - `/esb-update` -- Request URL: `https://<app-url>/slack/events`

2. **Interactivity & Shortcuts** enabled:
   - Request URL: `https://<app-url>/slack/events` (for modal submissions)

3. **OAuth Scopes** (Bot Token Scopes):
   - `commands` -- for slash commands
   - `chat:write` -- for posting messages (already from Story 6.1)
   - `users:read` -- for looking up user profiles
   - `users:read.email` -- for getting user email from profile

These are admin tasks, NOT code changes. Document in the story completion notes.

### What This Story Does NOT Include

1. **Slack status bot** -- Story 6.3 implements `/esb-status` query
2. **Photo uploads via Slack** -- The web form supports photo upload; Slack modals don't support file upload natively. Photo upload via Slack is NOT in scope.
3. **Block Kit rich message formatting** -- v1 uses plain text for confirmations. Rich Block Kit cards can be added as enhancement.
4. **Notification changes** -- Outbound notifications already work from Story 6.1. This story is INBOUND only (commands/modals).
5. **Interactivity on outbound messages** -- Action buttons on notification messages are NOT in scope.
6. **Database migrations** -- No schema changes needed. All models exist.

### Reuse from Previous Stories (DO NOT recreate)

**From Story 6.1 (Slack App Setup):**
- `esb/slack/__init__.py` -- `init_slack(app)`, `_bolt_app`, `_handler`, `slack_bp`, CSRF exemption
- Slack module is already conditionally loaded in `create_app()`
- `/slack/events` endpoint already handles all Slack request types (events, commands, interactive components)
- `slack-bolt>=1.27.0` and `slack_sdk>=3.39.0` already in `requirements.txt`
- `tests/test_slack/__init__.py` and `tests/test_slack/test_init.py` already exist

**From Story 3.1-3.3 (Repair Records):**
- `repair_service.create_repair_record()` -- EXACT function signature at `esb/services/repair_service.py:58-175`
- `repair_service.update_repair_record()` -- EXACT function signature at `esb/services/repair_service.py:316-478`
- `repair_service.get_repair_record()` -- at `esb/services/repair_service.py:178-187`
- `REPAIR_STATUSES` list at `esb/models/repair_record.py:7-17`
- `REPAIR_SEVERITIES` list at `esb/models/repair_record.py:19`
- `CLOSED_STATUSES` at `esb/services/repair_service.py:211`

**From Story 5.3 (Notification Triggers):**
- `repair_service` already queues all Slack notifications (new_report, resolved, severity_changed, eta_updated) based on trigger config
- DO NOT queue additional notifications from Slack handlers

**Existing Slack WebClient pattern:**
- `esb/services/user_service.py` -- `_deliver_temp_password_via_slack()` uses `client.users_lookupByEmail(email=email)` for outbound user lookup. Story 6.2 uses the reverse: `client.users_info(user=slack_user_id)` for inbound user mapping.

**Existing test infrastructure:**
- `tests/conftest.py` -- `app`, `db`, `client`, `capture`, `staff_client`, `tech_client` fixtures
- `tests/conftest.py` -- `make_area()`, `make_equipment()`, `make_repair_record()` factory helpers
- `tests/test_slack/test_init.py` -- `TestSlackEnabled` fixture with mocked Bolt app

### Project Structure Notes

**New files to create:**
- `esb/slack/forms.py` -- Block Kit modal builder functions
- `esb/slack/handlers.py` -- Slack command and view submission handlers
- `tests/test_slack/test_handlers.py` -- Tests for command handlers and view submissions
- `tests/test_slack/test_forms.py` -- Tests for modal builder functions

**Files to modify:**
- `esb/slack/__init__.py` -- Add `register_handlers(_bolt_app)` call inside `init_slack()`
- `tests/test_slack/test_init.py` -- Add test verifying `register_handlers` is called

**Files NOT to modify:**
- `esb/services/repair_service.py` -- No changes needed, all functions already handle Slack use case
- `esb/services/notification_service.py` -- Delivery already works from Story 6.1
- `esb/models/` -- No schema changes, no migrations
- `esb/config.py` -- No new config values needed
- `requirements.txt` -- All dependencies already present
- `docker-compose.yml` -- No changes needed

### Previous Story Intelligence (from Story 6.1)

**Patterns established that MUST be followed:**

1. **Bolt App mocking in tests:** Use `patch.object(Config, 'SLACK_BOT_TOKEN', 'xoxb-test-token')` and `patch('slack_bolt.App', return_value=mock_bolt_app)` pattern from `tests/test_slack/test_init.py`

2. **Service import pattern in Slack context:** Import services locally inside handler functions:
   ```python
   def handle_submission(ack, body, client, view):
       ack()
       from esb.services import repair_service
       record = repair_service.create_repair_record(...)
   ```

3. **WebClient mocking pattern:** `patch('esb.services.notification_service.WebClient', return_value=mock_client)` -- patch at the import location, not the source module

4. **Code review lessons from Story 6.1:**
   - Use `except Exception` (broad) for non-critical secondary operations (like `#oops` posting), but `except ValidationError` (specific) for primary operations
   - Always include `exc_info=True` in warning logs
   - Shadowed parameter names in nested functions cause ruff warnings -- use unique names (e.g., `bolt_logger` not `logger`)

5. **Test count baseline:** 843 tests passing, 0 lint errors after Story 6.1

### Testing Patterns

**Mocking Bolt command handlers:**

Testing Bolt handlers requires simulating the Slack request flow. The pattern is to directly call the registered handler functions with mock objects:

```python
from unittest.mock import MagicMock, patch

class TestSlackHandlers:
    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        """Set up test fixtures with app context."""
        self.app = app
        # Create test data
        self.area = make_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = make_equipment(name='SawStop', area=self.area)
        self.staff_user = make_user(username='admin', email='admin@test.com', role='staff')
        db.session.commit()

    def test_esb_report_opens_modal(self, app):
        """The /esb-report command opens a problem report modal."""
        with app.app_context():
            from esb.slack.handlers import register_handlers

            bolt_app = MagicMock()
            register_handlers(bolt_app)

            # Get the registered command handler
            report_handler = bolt_app.command.call_args_list[0][0]  # First @bolt_app.command call
            # ... or capture the handler function directly

            ack = MagicMock()
            client = MagicMock()
            body = {
                'trigger_id': 'test-trigger',
                'user_id': 'U12345',
                'user_name': 'testuser',
                'channel_id': 'C12345',
                'text': '',
            }

            # Call the handler
            # ... verify ack() called, client.views_open() called with correct modal
```

**Alternative approach -- capture handlers via Bolt mock:**

```python
def test_report_command(self, app):
    """Test /esb-report command handler."""
    with app.app_context():
        from esb.slack.handlers import register_handlers

        handlers = {}
        bolt_app = MagicMock()

        # Capture handlers registered via decorators
        def capture_command(cmd):
            def decorator(fn):
                handlers[f'command:{cmd}'] = fn
                return fn
            return decorator

        def capture_view(callback_id):
            def decorator(fn):
                handlers[f'view:{callback_id}'] = fn
                return fn
            return decorator

        bolt_app.command = capture_command
        bolt_app.view = capture_view
        register_handlers(bolt_app)

        # Now call the handler directly
        ack = MagicMock()
        client = MagicMock()
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'user_name': 'test', 'channel_id': 'C123'}

        handlers['command:/esb-report'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.views_open.assert_called_once()
        modal = client.views_open.call_args.kwargs['view']
        assert modal['callback_id'] == 'problem_report_submission'
```

**Testing view submissions:**

```python
def test_problem_report_submission(self, app):
    """Problem report submission creates a repair record."""
    with app.app_context():
        # ... register handlers, capture view handler ...

        ack = MagicMock()
        client = MagicMock()
        view = {
            'state': {
                'values': {
                    'equipment_block': {'equipment_select': {'selected_option': {'value': str(self.equipment.id)}}},
                    'name_block': {'reporter_name': {'value': 'Test User'}},
                    'description_block': {'description': {'value': 'Machine is broken'}},
                    'severity_block': {'severity': {'selected_option': {'value': 'Down'}}},
                    'safety_risk_block': {'safety_risk': {'selected_options': []}},
                    'consumable_block': {'consumable': {'selected_options': []}},
                },
            },
        }
        body = {'user': {'id': 'U12345'}}

        handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()  # ack() with no args = success
        client.chat_postEphemeral.assert_called_once()

        # Verify repair record was created
        from esb.models.repair_record import RepairRecord
        records = RepairRecord.query.all()
        assert len(records) == 1
        assert records[0].description == 'Machine is broken'
        assert records[0].severity == 'Down'
        assert records[0].reporter_name == 'Test User'
```

**Mocking `_resolve_esb_user`:**

```python
def test_esb_repair_rejects_unauthorized(self, app):
    """The /esb-repair command rejects users without ESB accounts."""
    with app.app_context():
        # ... register handlers ...

        ack = MagicMock()
        client = MagicMock()
        # users_info returns a user whose email doesn't match any ESB user
        client.users_info.return_value = {
            'user': {'profile': {'email': 'nobody@test.com'}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U999', 'channel_id': 'C123'}

        handlers['command:/esb-repair'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_called_once()
        assert 'Technician or Staff' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()
```

### Service Function Signatures (Quick Reference)

```python
# esb/services/repair_service.py

def create_repair_record(
    equipment_id: int,
    description: str,
    created_by: str,
    severity: str | None = None,
    reporter_name: str | None = None,
    reporter_email: str | None = None,
    assignee_id: int | None = None,
    has_safety_risk: bool = False,
    is_consumable: bool = False,
    author_id: int | None = None,
) -> RepairRecord:
    # Raises ValidationError

def update_repair_record(
    repair_record_id: int,
    updated_by: str,
    author_id: int | None = None,
    **changes,  # status, severity, assignee_id, eta, specialist_description, note
) -> RepairRecord:
    # Raises ValidationError

def get_repair_record(repair_record_id: int) -> RepairRecord:
    # Raises ValidationError

# Constants
REPAIR_STATUSES = ['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered',
                   'Parts Received', 'Needs Specialist', 'Resolved',
                   'Closed - No Issue Found', 'Closed - Duplicate']
REPAIR_SEVERITIES = ['Down', 'Degraded', 'Not Sure']
CLOSED_STATUSES = ['Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']
```

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with CSRF via Flask-WTF
- **slack_sdk>=3.39.0** (already in requirements.txt)
- **slack-bolt>=1.27.0** (already in requirements.txt)
- **pytest** for tests with `unittest.mock` for Slack API mocking
- No new database migrations needed
- No new pip dependencies needed

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

Latest commits:
```
0d1f496 Fix code review issues for Story 6.1 Slack App outbound notifications
0d1c07f Implement Story 6.1: Slack App Setup & Outbound Notifications
4053047 Create Story 6.1: Slack App Setup & Outbound Notifications context for dev agent
c10b0ce Fix code review issues for Story 5.3 notification trigger configuration
49c9e1d Implement Story 5.3: Notification Trigger Configuration
```

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 6 Story 6.2]
- [Source: _bmad-output/planning-artifacts/prd.md#FR23 Problem Reporting via Slack]
- [Source: _bmad-output/planning-artifacts/prd.md#FR40 Problem Reporting via Slack App Forms]
- [Source: _bmad-output/planning-artifacts/prd.md#FR41 Create Repair Records via Slack App]
- [Source: _bmad-output/planning-artifacts/prd.md#FR42 Update Repair Records via Slack App]
- [Source: _bmad-output/planning-artifacts/architecture.md#Slack SDK]
- [Source: _bmad-output/planning-artifacts/architecture.md#Slack Integration Boundary]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure slack/handlers.py slack/forms.py]
- [Source: esb/services/repair_service.py#create_repair_record]
- [Source: esb/services/repair_service.py#update_repair_record]
- [Source: esb/services/repair_service.py#get_repair_record]
- [Source: esb/services/repair_service.py#_queue_slack_notification]
- [Source: esb/models/repair_record.py#REPAIR_STATUSES REPAIR_SEVERITIES]
- [Source: esb/models/equipment.py#Equipment]
- [Source: esb/models/user.py#User]
- [Source: esb/models/area.py#Area]
- [Source: esb/slack/__init__.py#init_slack _bolt_app _handler]
- [Source: esb/services/user_service.py#_deliver_temp_password_via_slack (reverse user mapping pattern)]
- [Source: esb/forms/repair_forms.py#ProblemReportForm (web form field reference)]
- [Source: esb/views/public.py#report_problem (web problem report flow reference)]
- [Source: tests/test_slack/test_init.py#TestSlackEnabled (Bolt mock patterns)]
- [Source: https://tools.slack.dev/bolt-python/concepts/commands/ (Bolt slash commands)]
- [Source: https://tools.slack.dev/bolt-python/concepts/creating-modals/ (Bolt modals)]
- [Source: https://api.slack.com/reference/block-kit/blocks (Block Kit reference)]
- [Source: https://api.slack.com/methods/users.info (users.info API)]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
