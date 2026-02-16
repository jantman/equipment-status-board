# Story 5.3: Notification Trigger Configuration

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to configure which events trigger notifications,
So that the team gets notified about important changes without being overwhelmed by noise.

## Acceptance Criteria

1. **Given** I am logged in as Staff, **When** I navigate to App Configuration (`/admin/config`), **Then** I see a "Notification Triggers" section with toggles for each trigger event type. (AC: #1)

2. **Given** the notification trigger settings, **When** I view them, **Then** the available trigger types are: `new_report`, `resolved`, `severity_changed`, `eta_updated`, **And** all four are enabled by default. (AC: #2)

3. **Given** I toggle a notification trigger off (e.g., disable `eta_updated`), **When** I save the configuration, **Then** the setting is stored in the AppConfig table. (AC: #3)

4. **Given** a trigger event occurs (e.g., a new problem report is submitted), **When** the service layer processes the event, **Then** it checks the AppConfig trigger settings before queuing any notification, **And** if the trigger type is disabled, no notification is queued. (AC: #4)

5. **Given** a trigger event occurs and the trigger type is enabled, **When** the service layer processes the event, **Then** a notification is queued in PendingNotification for future delivery (Slack delivery implemented in Epic 6). (AC: #5)

6. **Given** the notification trigger configuration, **When** I change settings, **Then** the changes take effect immediately for subsequent events without requiring a restart. (AC: #6)

7. **Given** any configuration change, **When** the action is performed, **Then** a mutation log entry is written to STDOUT. (AC: #7)

## Tasks / Subtasks

- [ ] Task 1: Add notification trigger fields to `AppConfigForm` in `esb/forms/admin_forms.py` (AC: #1, #2)
  - [ ] 1.1: Add `BooleanField` for `notify_new_report` with label "New problem report submitted"
  - [ ] 1.2: Add `BooleanField` for `notify_resolved` with label "Repair record resolved"
  - [ ] 1.3: Add `BooleanField` for `notify_severity_changed` with label "Severity changed"
  - [ ] 1.4: Add `BooleanField` for `notify_eta_updated` with label "ETA set or updated"

- [ ] Task 2: Update admin config view in `esb/views/admin.py` (AC: #1, #3, #6, #7)
  - [ ] 2.1: On GET, populate the 4 trigger fields from AppConfig via `config_service.get_config()` (default 'true')
  - [ ] 2.2: On POST, save each trigger field via `config_service.set_config()` with `changed_by=current_user.username`
  - [ ] 2.3: Mutation logging already handled by `config_service.set_config()` -- no extra code needed

- [ ] Task 3: Update admin config template `esb/templates/admin/config.html` (AC: #1, #2)
  - [ ] 3.1: Add a "Notification Triggers" Bootstrap card section after the existing "Permissions" card
  - [ ] 3.2: Display each trigger as a `form-check form-switch` toggle with descriptive labels
  - [ ] 3.3: Add form-text explaining: "These control which events queue Slack notifications. Slack delivery requires Epic 6."

- [ ] Task 4: Add notification trigger checking and `slack_message` queuing in `esb/services/repair_service.py` (AC: #4, #5, #6)
  - [ ] 4.1: Create a helper function `_queue_slack_notification(equipment, event_type, extra_payload=None)` that builds and queues a `slack_message` notification with the standard payload structure
  - [ ] 4.2: In `create_repair_record()`, after commit: check `notify_new_report` config, if enabled queue `slack_message` with event_type='new_report'
  - [ ] 4.3: In `update_repair_record()`, after commit: check `notify_resolved` config when status changes to a resolved/closed status, if enabled queue `slack_message` with event_type='resolved'
  - [ ] 4.4: In `update_repair_record()`, after commit: check `notify_severity_changed` config when severity changes, if enabled queue `slack_message` with event_type='severity_changed'
  - [ ] 4.5: In `update_repair_record()`, after commit: check `notify_eta_updated` config when ETA changes, if enabled queue `slack_message` with event_type='eta_updated'

- [ ] Task 5: Write admin view tests in `tests/test_views/test_admin_views.py` (AC: #1, #2, #3, #6, #7)
  - [ ] 5.1: Test GET `/admin/config` shows notification trigger toggles
  - [ ] 5.2: Test GET shows triggers enabled by default (when no AppConfig entries exist)
  - [ ] 5.3: Test POST disabling a trigger stores 'false' in AppConfig
  - [ ] 5.4: Test POST enabling a trigger stores 'true' in AppConfig
  - [ ] 5.5: Test mutation logging on trigger config changes
  - [ ] 5.6: Test Technician cannot access config page (403)

- [ ] Task 6: Write repair service trigger tests in `tests/test_services/test_repair_service.py` (AC: #4, #5)
  - [ ] 6.1: Test `create_repair_record()` queues `slack_message` when `notify_new_report` is enabled (default)
  - [ ] 6.2: Test `create_repair_record()` does NOT queue `slack_message` when `notify_new_report` is disabled
  - [ ] 6.3: Test `update_repair_record()` with status→Resolved queues `slack_message` when `notify_resolved` is enabled
  - [ ] 6.4: Test `update_repair_record()` with status→Resolved does NOT queue `slack_message` when `notify_resolved` is disabled
  - [ ] 6.5: Test `update_repair_record()` with severity change queues `slack_message` when `notify_severity_changed` is enabled
  - [ ] 6.6: Test `update_repair_record()` with severity change does NOT queue `slack_message` when `notify_severity_changed` is disabled
  - [ ] 6.7: Test `update_repair_record()` with ETA change queues `slack_message` when `notify_eta_updated` is enabled
  - [ ] 6.8: Test `update_repair_record()` with ETA change does NOT queue `slack_message` when `notify_eta_updated` is disabled
  - [ ] 6.9: Test `slack_message` payload contains correct fields (equipment_name, area_name, severity, event_type, has_safety_risk)
  - [ ] 6.10: Test multiple triggers in one update (e.g., severity change + status→Resolved) queues multiple notifications

## Dev Notes

### Architecture Compliance (MANDATORY)

These rules are established across the codebase and MUST be followed:

1. **Service Layer Pattern:** ALL business logic in services. Views are thin controllers -- parse input, call service, render template.
2. **Dependency flow:** `views -> services -> models` (NEVER reversed).
3. **No raw SQL:** All queries via SQLAlchemy ORM in service functions.
4. **Function-based services:** All services use module-level functions, NOT classes. Follow the pattern in `esb/services/notification_service.py`.
5. **Mutation logging:** Use `log_mutation(event, user, data)` from `esb/utils/logging.py` for all data-changing operations. Config changes already logged by `config_service.set_config()`.
6. **Domain exceptions:** Use `ValidationError` from `esb/utils/exceptions.py`.
7. **UTC timestamps:** `default=lambda: datetime.now(UTC)` for all timestamp columns.
8. **Import pattern:** Import services locally inside view/CLI functions to avoid circular imports. This also applies to inter-service imports.
9. **Flash category:** Use `'danger'` NOT `'error'` for error flash messages.
10. **ruff target-version:** `"py313"` (NOT py314).
11. **Config storage pattern:** Boolean configs stored as `'true'`/`'false'` strings via `config_service.get_config(key, default)` and `config_service.set_config(key, value, changed_by)`.

### Critical Implementation Details

#### Notification Trigger Config Keys

Four AppConfig keys, all defaulting to `'true'` (enabled):

| Config Key | Trigger Event | Description |
|------------|--------------|-------------|
| `notify_new_report` | New repair record created | When a problem report is submitted or repair record created |
| `notify_resolved` | Repair resolved/closed | When status changes to Resolved, Closed - No Issue Found, or Closed - Duplicate |
| `notify_severity_changed` | Severity changed | When severity level is updated |
| `notify_eta_updated` | ETA set/changed | When ETA is set or modified |

**Default behavior:** All triggers enabled. When no AppConfig entry exists for a key, `config_service.get_config(key, 'true')` returns `'true'`, so all triggers fire by default until explicitly disabled.

#### AppConfigForm Update (`esb/forms/admin_forms.py`)

Add four new BooleanField entries to the existing `AppConfigForm`:

```python
class AppConfigForm(FlaskForm):
    """Form for application configuration settings."""

    tech_doc_edit_enabled = BooleanField('Allow Technicians to edit equipment documentation')
    notify_new_report = BooleanField('New problem report submitted')
    notify_resolved = BooleanField('Repair record resolved or closed')
    notify_severity_changed = BooleanField('Severity level changed')
    notify_eta_updated = BooleanField('ETA set or updated')
    submit = SubmitField('Save Configuration')
```

#### Admin Config View Update (`esb/views/admin.py`)

Extend the existing `app_config()` route to handle the 4 new fields on GET and POST:

```python
@admin_bp.route('/config', methods=['GET', 'POST'])
@role_required('staff')
def app_config():
    from esb.services import config_service

    form = AppConfigForm()

    if request.method == 'GET':
        # Existing field
        form.tech_doc_edit_enabled.data = (
            config_service.get_config('tech_doc_edit_enabled', 'false') == 'true'
        )
        # Notification trigger fields (default: enabled)
        form.notify_new_report.data = (
            config_service.get_config('notify_new_report', 'true') == 'true'
        )
        form.notify_resolved.data = (
            config_service.get_config('notify_resolved', 'true') == 'true'
        )
        form.notify_severity_changed.data = (
            config_service.get_config('notify_severity_changed', 'true') == 'true'
        )
        form.notify_eta_updated.data = (
            config_service.get_config('notify_eta_updated', 'true') == 'true'
        )

    if form.validate_on_submit():
        config_service.set_config(
            'tech_doc_edit_enabled',
            'true' if form.tech_doc_edit_enabled.data else 'false',
            changed_by=current_user.username,
        )
        config_service.set_config(
            'notify_new_report',
            'true' if form.notify_new_report.data else 'false',
            changed_by=current_user.username,
        )
        config_service.set_config(
            'notify_resolved',
            'true' if form.notify_resolved.data else 'false',
            changed_by=current_user.username,
        )
        config_service.set_config(
            'notify_severity_changed',
            'true' if form.notify_severity_changed.data else 'false',
            changed_by=current_user.username,
        )
        config_service.set_config(
            'notify_eta_updated',
            'true' if form.notify_eta_updated.data else 'false',
            changed_by=current_user.username,
        )
        flash('Configuration updated successfully.', 'success')
        return redirect(url_for('admin.app_config'))

    return render_template('admin/config.html', form=form)
```

**Key decisions:**
- All trigger fields default to `'true'` via `get_config(key, 'true')` -- this means triggers are enabled even before any Staff saves the config page
- Each field saved individually via `set_config()` which handles upsert and mutation logging
- `changed_by=current_user.username` for audit trail
- No new imports needed -- `config_service` already imported locally

#### Admin Config Template Update (`esb/templates/admin/config.html`)

Add a "Notification Triggers" card section after the existing "Permissions" card. Follow the exact same Bootstrap card + `form-check form-switch` pattern:

```html
<!-- Add this new card AFTER the existing Permissions card, BEFORE the submit button -->
<div class="card mb-4">
    <div class="card-header">
        <h5 class="card-title mb-0">Notification Triggers</h5>
    </div>
    <div class="card-body">
        <p class="text-muted mb-3">Control which events queue Slack notifications. All triggers are enabled by default.</p>

        <div class="mb-3">
            <div class="form-check form-switch">
                {{ form.notify_new_report(class="form-check-input", role="switch") }}
                {{ form.notify_new_report.label(class="form-check-label") }}
            </div>
            <div class="form-text">Notify when a new problem report is submitted or repair record created.</div>
        </div>

        <div class="mb-3">
            <div class="form-check form-switch">
                {{ form.notify_resolved(class="form-check-input", role="switch") }}
                {{ form.notify_resolved.label(class="form-check-label") }}
            </div>
            <div class="form-text">Notify when a repair record is resolved or closed.</div>
        </div>

        <div class="mb-3">
            <div class="form-check form-switch">
                {{ form.notify_severity_changed(class="form-check-input", role="switch") }}
                {{ form.notify_severity_changed.label(class="form-check-label") }}
            </div>
            <div class="form-text">Notify when a repair record's severity level changes.</div>
        </div>

        <div class="mb-3">
            <div class="form-check form-switch">
                {{ form.notify_eta_updated(class="form-check-input", role="switch") }}
                {{ form.notify_eta_updated.label(class="form-check-label") }}
            </div>
            <div class="form-text">Notify when an ETA is set or updated on a repair record.</div>
        </div>
    </div>
</div>
```

**Key decisions:**
- Uses `form-switch` variant for visual toggle UX (consistent with existing `tech_doc_edit_enabled` field if it uses switches; otherwise use `form-check`)
- Descriptive `form-text` under each toggle explains what triggers
- Card structure matches Bootstrap 5 patterns used elsewhere in the admin views

#### Repair Service Notification Hooks (`esb/services/repair_service.py`)

##### Helper function for building Slack notification payload:

```python
def _queue_slack_notification(equipment, event_type, extra_payload=None):
    """Queue a slack_message notification for a repair event.

    Args:
        equipment: Equipment model instance (must have area relationship loaded).
        event_type: One of 'new_report', 'resolved', 'severity_changed', 'eta_updated'.
        extra_payload: Additional payload fields to merge.
    """
    from esb.services import notification_service

    payload = {
        'event_type': event_type,
        'equipment_id': equipment.id,
        'equipment_name': equipment.name,
        'area_name': equipment.area.name if equipment.area else 'Unknown',
    }
    if extra_payload:
        payload.update(extra_payload)

    target = equipment.area.slack_channel if equipment.area and equipment.area.slack_channel else '#general'

    notification_service.queue_notification(
        notification_type='slack_message',
        target=target,
        payload=payload,
    )
```

**Key decisions:**
- Private helper function (underscore prefix) -- not part of the public API
- Builds a standard payload structure that Epic 6's Slack handler can consume
- `target` is the area's Slack channel (or `'#general'` fallback if not configured)
- `extra_payload` allows each trigger to add specific fields (old/new values, severity, reporter, etc.)
- Equipment area relationship must be loaded (it is, since repair_service already loads equipment via `db.session.get(Equipment, equipment_id)` and accesses `equipment.area`)

##### In `create_repair_record()` -- add AFTER the existing `static_page_push` hook:

```python
    # Queue Slack notification if new_report trigger is enabled
    from esb.services import config_service
    if config_service.get_config('notify_new_report', 'true') == 'true':
        _queue_slack_notification(equipment, 'new_report', {
            'severity': severity,
            'description': description,
            'reporter_name': reporter_name,
            'has_safety_risk': has_safety_risk,
        })
```

**Key decisions:**
- Checks config EVERY TIME (not cached) -- ensures immediate effect when config changes (AC: #6)
- `config_service.get_config('notify_new_report', 'true')` defaults to `'true'` -- trigger fires unless explicitly disabled
- Payload includes all fields Epic 6's Slack handler will need to compose the message
- Placed AFTER the `static_page_push` hook so both notifications are independent

##### In `update_repair_record()` -- add AFTER the existing `static_page_push` hook:

```python
    # Queue Slack notifications based on trigger configuration
    from esb.services import config_service

    # Resolved trigger: status changed to a resolved/closed status
    resolved_statuses = {'Resolved', 'Closed - No Issue Found', 'Closed - Duplicate'}
    if 'status' in audit_changes and audit_changes['status'][1] in resolved_statuses:
        if config_service.get_config('notify_resolved', 'true') == 'true':
            _queue_slack_notification(record.equipment, 'resolved', {
                'old_status': audit_changes['status'][0],
                'new_status': audit_changes['status'][1],
            })

    # Severity changed trigger
    if 'severity' in audit_changes:
        if config_service.get_config('notify_severity_changed', 'true') == 'true':
            _queue_slack_notification(record.equipment, 'severity_changed', {
                'old_severity': audit_changes['severity'][0],
                'new_severity': audit_changes['severity'][1],
            })

    # ETA updated trigger
    if 'eta' in audit_changes:
        if config_service.get_config('notify_eta_updated', 'true') == 'true':
            _queue_slack_notification(record.equipment, 'eta_updated', {
                'eta': str(audit_changes['eta'][1]) if audit_changes['eta'][1] else None,
                'old_eta': str(audit_changes['eta'][0]) if audit_changes['eta'][0] else None,
            })
```

**Key decisions:**
- Each trigger is checked independently -- if severity changes AND status→Resolved in one update, both notifications queue (if enabled)
- `resolved_statuses` includes all three closure statuses: Resolved, Closed - No Issue Found, Closed - Duplicate
- Config is read fresh each time (not cached) for immediate effect
- `audit_changes` dict already tracks old/new values (built earlier in `update_repair_record()`)
- ETA values converted to string for JSON serialization
- `record.equipment` relationship should be loaded -- verify in codebase that SQLAlchemy lazy loads it

##### How `audit_changes` works in `update_repair_record()`:

The existing code builds `audit_changes` as a dict mapping field names to `[old_value, new_value]` lists:
```python
audit_changes = {}
for field_name in _REPAIR_UPDATABLE_FIELDS:
    if field_name not in changes:
        continue
    new_value = changes[field_name]
    old_value = getattr(record, field_name)
    if old_value == new_value:
        continue
    audit_changes[field_name] = [_serialize(old_value), _serialize(new_value)]
    setattr(record, field_name, new_value)
```

**IMPORTANT:** `audit_changes['status']` is `[old_value, new_value]` -- index `[0]` is old, `[1]` is new. NOT a dict with 'old'/'new' keys.

The notification hooks run AFTER `db.session.commit()` so the changes are durable. The `audit_changes` dict tells us exactly what changed.

### What This Story Does NOT Include

1. **Slack message delivery** -- Epic 6 (Story 6.1) implements `_deliver_slack_message()` with actual Slack WebClient API calls. Story 5.3 only queues `slack_message` notifications; the worker will attempt delivery, hit `NotImplementedError`, and mark them as failed with retry backoff.
2. **Slack App setup** -- Epic 6 handles all Slack App initialization and event handlers.
3. **Notification preferences per user** -- This is a stretch goal (FR65-FR66), not in scope.
4. **Static page push triggers** -- Already implemented in Story 5.2. This story only adds `slack_message` triggers.
5. **Per-area notification configuration** -- FR38 specifies area-specific channels, but trigger configuration is global (all areas or none for a given event type).

### Reuse from Previous Stories (DO NOT recreate)

**From Story 1.1 (Project Scaffolding):**
- `esb/__init__.py` -- App factory
- `esb/extensions.py` -- `db`, `login_manager`, `migrate`, `csrf` instances
- `esb/config.py` -- Configuration classes
- `esb/utils/logging.py` -- `log_mutation(event, user, data)` function
- `esb/utils/exceptions.py` -- `ESBError`, `ValidationError` hierarchy

**From Story 2.4 (Equipment Archiving & Permissions):**
- `esb/models/app_config.py` -- AppConfig model (key-value store for runtime settings)
- `esb/services/config_service.py` -- `get_config(key, default)`, `set_config(key, value, changed_by)` functions
- `esb/views/admin.py` -- Existing `app_config()` route at `/admin/config`
- `esb/forms/admin_forms.py` -- Existing `AppConfigForm` with `tech_doc_edit_enabled` field
- `esb/templates/admin/config.html` -- Existing config page template

**From Story 5.1 (Notification Queue):**
- `esb/models/pending_notification.py` -- PendingNotification model
- `esb/services/notification_service.py` -- `queue_notification()`, worker loop, delivery handlers
- `VALID_NOTIFICATION_TYPES = {'slack_message', 'static_page_push'}` -- `'slack_message'` already valid

**From Story 5.2 (Static Page):**
- `static_page_push` hooks already in `repair_service.py` -- follow the same pattern for `slack_message`

**Existing test infrastructure:**
- `tests/conftest.py` -- `app`, `db`, `client`, `capture`, `staff_client`, `tech_client`, `staff_user`, `tech_user`, `make_area`, `make_equipment`, `make_repair_record` fixtures
- `tests/test_views/test_admin_views.py` -- `TestAppConfig` class with existing config tests
- `tests/test_services/test_repair_service.py` -- `TestCreateRepairRecordStaticPageHook`, `TestUpdateRepairRecordStaticPageHook` classes

### Project Structure Notes

**New files to create:**
- None -- all changes are to existing files

**Files to modify:**
- `esb/forms/admin_forms.py` -- Add 4 BooleanField entries to AppConfigForm
- `esb/views/admin.py` -- Extend app_config() route for trigger fields
- `esb/templates/admin/config.html` -- Add Notification Triggers card section
- `esb/services/repair_service.py` -- Add `_queue_slack_notification()` helper and trigger hooks in `create_repair_record()` and `update_repair_record()`
- `tests/test_views/test_admin_views.py` -- Add trigger config tests
- `tests/test_services/test_repair_service.py` -- Add trigger notification tests

**Files NOT to modify:**
- `esb/models/app_config.py` -- No schema changes needed, existing key-value store handles new keys
- `esb/services/config_service.py` -- Already has `get_config()` and `set_config()`, no changes needed
- `esb/services/notification_service.py` -- `'slack_message'` is already in `VALID_NOTIFICATION_TYPES`, handler is a stub (Epic 6)
- `esb/models/pending_notification.py` -- No changes needed
- `esb/config.py` -- No new environment variables needed (trigger config is in DB, not env vars)
- `docker-compose.yml` -- No changes needed
- No migration needed -- AppConfig table already exists and accepts arbitrary key-value pairs

### Previous Story Intelligence (from Story 5.2)

**Patterns to follow:**
- `ruff target-version = "py313"` (NOT py314)
- Import services locally inside functions to avoid circular imports
- `db.session.get(Model, id)` for PK lookups
- `db.select(Model).filter_by(...)` for queries
- `default=lambda: datetime.now(UTC)` for timestamps (import `UTC` from `datetime`)
- Test factories in `tests/conftest.py`: `make_area`, `make_equipment`, `make_repair_record`
- Boolean config values stored as `'true'`/`'false'` strings
- Config defaults: `config_service.get_config(key, 'true')` for triggers (enabled by default)
- 795 tests currently passing, 0 lint errors

**Code review lessons from previous stories:**
- Don't duplicate logic -- reuse existing service patterns
- Test all mutation log events using the `capture` fixture
- Include edge case tests (disabled triggers, multiple triggers, default behavior)
- Use `db.or_()` from SQLAlchemy for OR conditions
- Verify notification payloads contain all fields the Slack handler will need in Epic 6
- Import services locally in inter-service calls (`repair_service` importing `config_service` and `notification_service`)

### Git Commit Intelligence

Recent commit pattern (3-commit cadence per story):
1. Context creation: `Create Story X.Y: Title context for dev agent`
2. Implementation: `Implement Story X.Y: Title`
3. Code review fixes: `Fix code review issues for Story X.Y title`

### Testing Standards

**Admin view tests (add to `tests/test_views/test_admin_views.py` `TestAppConfig` class):**

```python
def test_config_shows_notification_triggers(self, staff_client, staff_user):
    """Config page shows notification trigger toggles."""
    resp = staff_client.get('/admin/config')
    assert resp.status_code == 200
    assert b'Notification Triggers' in resp.data
    assert b'notify_new_report' in resp.data
    assert b'notify_resolved' in resp.data
    assert b'notify_severity_changed' in resp.data
    assert b'notify_eta_updated' in resp.data

def test_triggers_enabled_by_default(self, staff_client, staff_user):
    """Triggers are checked (enabled) by default when no config exists."""
    resp = staff_client.get('/admin/config')
    assert resp.status_code == 200
    # All checkboxes should have 'checked' attribute
    assert b'checked' in resp.data  # At least one is checked

def test_disable_trigger(self, staff_client, staff_user):
    """Staff can disable a notification trigger."""
    resp = staff_client.post('/admin/config', data={
        'tech_doc_edit_enabled': 'y',
        'notify_new_report': 'y',
        'notify_resolved': 'y',
        'notify_severity_changed': 'y',
        # notify_eta_updated NOT included = disabled
    }, follow_redirects=True)
    assert resp.status_code == 200
    assert b'Configuration updated successfully' in resp.data

    from esb.services import config_service
    assert config_service.get_config('notify_eta_updated') == 'false'

def test_trigger_config_mutation_logging(self, staff_client, staff_user, capture):
    """Trigger config changes log mutations."""
    capture.records.clear()
    staff_client.post('/admin/config', data={
        'notify_new_report': 'y',
    })
    entries = [
        json.loads(r.message) for r in capture.records
        if 'app_config.updated' in r.message
    ]
    assert len(entries) >= 1  # At least one config change logged
```

**Repair service trigger tests (add to `tests/test_services/test_repair_service.py`):**

```python
class TestCreateRepairRecordSlackNotification:
    """Test slack_message notification queuing on repair record creation."""

    def test_slack_notification_queued_when_trigger_enabled(self, app, db, make_area, make_equipment):
        """create_repair_record() queues slack_message when notify_new_report is enabled (default)."""
        area = make_area(name='Woodshop', slack_channel='#woodshop')
        equip = make_equipment(name='SawStop', area=area)

        from esb.services import repair_service
        repair_service.create_repair_record(
            equipment_id=equip.id, description='Motor broken',
            reporter_name='Test User', severity='Down',
        )

        notifications = db.session.execute(
            db.select(PendingNotification).filter_by(notification_type='slack_message')
        ).scalars().all()
        assert len(notifications) == 1
        assert notifications[0].target == '#woodshop'
        assert notifications[0].payload['event_type'] == 'new_report'
        assert notifications[0].payload['equipment_name'] == 'SawStop'

    def test_no_slack_notification_when_trigger_disabled(self, app, db, make_area, make_equipment):
        """create_repair_record() does NOT queue slack_message when notify_new_report is disabled."""
        from esb.services import config_service
        config_service.set_config('notify_new_report', 'false', changed_by='test')

        area = make_area(name='Woodshop', slack_channel='#woodshop')
        equip = make_equipment(name='SawStop', area=area)

        from esb.services import repair_service
        repair_service.create_repair_record(
            equipment_id=equip.id, description='Motor broken',
            reporter_name='Test User', severity='Down',
        )

        notifications = db.session.execute(
            db.select(PendingNotification).filter_by(notification_type='slack_message')
        ).scalars().all()
        assert len(notifications) == 0
```

**Test data patterns:**
```python
# Create area with slack channel for notification target
area = make_area(name='Woodshop', slack_channel='#woodshop')
equip = make_equipment(name='SawStop', area=area)

# Query slack_message notifications specifically
notifications = db.session.execute(
    db.select(PendingNotification).filter_by(notification_type='slack_message')
).scalars().all()

# Disable a trigger before creating/updating repair record
from esb.services import config_service
config_service.set_config('notify_new_report', 'false', changed_by='test')

# For update tests, need to provide user (current_user param)
from esb.services import repair_service
repair_service.update_repair_record(
    record.id, status='Resolved', current_user=staff_user,
)
```

### Slack Message Payload Structure

The `slack_message` notifications queued by this story use this payload structure. Epic 6's `_deliver_slack_message()` handler will consume these payloads to compose formatted Slack messages:

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

### Technology Requirements

- **Python 3.14** (ruff target py313)
- **Flask 3.1.x** with Flask-WTF for forms
- **Flask-SQLAlchemy 3.1.x** for ORM
- **Flask-Login** for `current_user.username`
- **pytest** for tests
- **No new dependencies needed** -- all required packages already in requirements.txt

### Notification Behavior When Slack Is Not Yet Implemented

When this story is complete, `slack_message` notifications will be:
1. **Queued** in the `pending_notifications` table when trigger conditions are met
2. **Picked up** by the background worker during its 30-second polling cycle
3. **Attempted** for delivery via `_deliver_slack_message()` which raises `NotImplementedError`
4. **Marked as failed** by the worker with exponential backoff retry
5. **Retried** up to `MAX_RETRIES` (10) times, then permanently marked as `'failed'`

This is expected behavior. When Epic 6 implements `_deliver_slack_message()`, new notifications will be delivered. The old failed ones can be cleaned up or manually re-queued.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 5 Story 5.3]
- [Source: _bmad-output/planning-artifacts/prd.md#FR38 Notifications to Slack Channels]
- [Source: _bmad-output/planning-artifacts/prd.md#FR44 Staff Can Configure Notification Triggers]
- [Source: _bmad-output/planning-artifacts/architecture.md#Notification Event Types]
- [Source: _bmad-output/planning-artifacts/architecture.md#Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Environment Configuration]
- [Source: esb/models/app_config.py#AppConfig]
- [Source: esb/services/config_service.py#get_config]
- [Source: esb/services/config_service.py#set_config]
- [Source: esb/services/notification_service.py#queue_notification]
- [Source: esb/services/notification_service.py#VALID_NOTIFICATION_TYPES]
- [Source: esb/services/repair_service.py#create_repair_record]
- [Source: esb/services/repair_service.py#update_repair_record]
- [Source: esb/views/admin.py#app_config]
- [Source: esb/forms/admin_forms.py#AppConfigForm]
- [Source: esb/templates/admin/config.html]
- [Source: esb/utils/logging.py#log_mutation]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
