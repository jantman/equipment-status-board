---
title: 'Fix Slack handlers missing Flask application context'
slug: 'fix-slack-app-context'
created: '2026-04-13'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'Flask-SQLAlchemy', 'Slack Bolt SDK', 'Socket Mode', 'pytest']
files_to_modify: ['esb/slack/__init__.py', 'esb/slack/handlers.py', 'tests/test_slack/test_handlers.py']
code_patterns: ['service-layer delegation', 'deferred imports in handlers', 'MagicMock Bolt app for test capture']
test_patterns: ['pytest fixtures with app context in conftest.py', 'MagicMock-based handler invocation', '_register_and_capture helper']
---

# Tech-Spec: Fix Slack handlers missing Flask application context

**Created:** 2026-04-13

## Overview

### Problem Statement

All Slack slash commands (`/esb-status`, `/esb-repair`, `/esb-report`, `/esb-update`) crash with `RuntimeError: Working outside of application context`. Slack Bolt dispatches command handlers in its own threads via Socket Mode, outside Flask's request lifecycle. Any call to `db.session` in those threads fails because no Flask app context exists.

GitHub Issue: https://github.com/jantman/equipment-status-board/issues/15

### Solution

Pass the Flask `app` instance into `register_handlers()` and wrap each handler's DB-accessing body in a conditional app context using a shared helper function. The helper uses `flask.has_app_context()` to skip pushing a new context when one already exists (e.g., during tests), avoiding nested-context issues with Flask-SQLAlchemy's scoped sessions.

### Scope

**In Scope:**
- Add `_ensure_app_context(app)` helper that returns `app.app_context()` or `nullcontext()`
- Wrap all 4 command handlers and 3 view submission handlers with the helper
- Pass Flask `app` from `init_slack()` to `register_handlers()`
- Update existing test helper to match new `register_handlers()` signature
- Add regression tests verifying handlers work without pre-existing app context

**Out of Scope:**
- Changing Slack Bolt or Socket Mode architecture
- Refactoring the service layer
- Modifying `esb/slack/forms.py` (DB functions inherit context from calling handlers)
- Modifying `_resolve_esb_user` (called from within already-wrapped handlers)

## Context for Development

### Why NOT Bolt Global Middleware

Bolt global middleware was considered but **does not work** for this use case. Bolt's `dispatch()` method (`slack_bolt/app/app.py` lines 540-646) uses a `for` loop over middleware. The `next()` function passed to middleware is a flag-setter (`middleware_state["next_called"] = True`), not a callback. When middleware calls `next()` inside a `with app.app_context():` block, the flag is set, the `with` block exits (popping the context), and only then does `dispatch()` continue to the listener. The handler executes after the context is already gone.

Additionally, Bolt's `ThreadListenerRunner` may run listeners in a separate thread from `dispatch()` when `process_before_response=False` (the Socket Mode default), further isolating the handler from any context pushed in the dispatch thread.

### Why Per-Handler Wrapping

Each handler wraps its DB-accessing body in `with _ensure_app_context(app):`. This:
- Actually works — the context is active for the entire handler body
- Is explicit and auditable — each handler visibly declares its context needs
- Uses a shared helper to minimize boilerplate (one-line wrapper)

The trade-off is that future handlers must remember to include the wrapper. To mitigate this:
- The `_ensure_app_context` function is discoverable via grep
- The regression tests exercise handlers outside app context
- A comment should be added above `register_handlers()` documenting the requirement:
  `# IMPORTANT: All handlers that access DB/services must wrap their body in`
  `# with _ensure_app_context(app): — see _ensure_app_context docstring.`

### Nested Context Safety

`TestingConfig` uses `sqlite:///:memory:`. Flask-SQLAlchemy (not raw SQLAlchemy) overrides the default pool to `StaticPool` for in-memory URIs, sharing a single connection across all sessions. This means:
- Nested `app.app_context()` would create a new scoped session but on the same connection
- Committed data from the outer session IS visible to the inner session
- Test assertions using fresh queries (e.g., `RepairRecord.query.all()`) work correctly

The `has_app_context()` guard in `_ensure_app_context()` avoids nesting entirely as defense-in-depth, but even without it, the tests would function correctly due to Flask-SQLAlchemy's `StaticPool` override.

### Context Exit and Test Data Survival

When a `with app.app_context():` block exits, Flask-SQLAlchemy's teardown handler calls `session.remove()`, which returns the connection to the pool. With `StaticPool`, this is a no-op on the connection itself — the single connection stays open and retains all committed data. A subsequent `app.app_context()` push gets the same connection back. This is why the regression test (Task 6, Test 1) works: data committed in the setup context survives the context exit and is visible when the handler pushes a fresh context.

### Codebase Patterns

- Service layer pattern: views/handlers delegate to `esb/services/` for business logic
- Deferred imports used throughout handlers to avoid circular imports
- `init_slack(app)` receives Flask app but currently doesn't pass it to handlers
- Existing tests (~840 lines in `test_handlers.py`, 9 test classes) pass because `conftest.py`'s `app` fixture wraps everything in `with app.app_context()`, masking the bug
- `_register_and_capture(app)` test helper captures Bolt handler registrations via mock decorators. Note: `app` parameter is already accepted but currently **silently discarded** — it is never passed through to `register_handlers()`. This is part of the bug: the plumbing was half-built.

### Handler Closure and `app` Lifetime

When `register_handlers(bolt_app, app)` is called, all handler functions defined inside close over the `app` parameter. In production, `create_app()` is called once and `app` lives for the process lifetime — safe. In tests, each test class's `setup` calls `_register_and_capture(app)` which calls `register_handlers(bolt_app, app)`, creating fresh handler closures that capture the current test's `app` fixture. This is safe because each test class re-registers handlers in its own setup. Do not cache or reuse handler functions across test classes with different `app` instances.

**Implicit constraint:** All handlers that need `app` must be defined as closures inside `register_handlers()`, since that is the only scope where `app` is available. If a handler is defined at module level (like `_resolve_esb_user`), it cannot access `app` and must rely on being called from within an already-wrapped handler.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/slack/__init__.py` | Slack Bolt init; calls `register_handlers(_bolt_app)` at line 41 |
| `esb/slack/handlers.py` | 4 command handlers + 3 view submission handlers + `_resolve_esb_user` helper |
| `esb/slack/forms.py` | Modal builders; `build_equipment_options()` and `build_user_options()` access DB |
| `tests/test_slack/test_handlers.py` | 9 existing test classes; `_register_and_capture()` helper at line 10 |
| `tests/test_slack/test_init.py` | Slack module init tests; `TestSlackEnabled` calls `init_slack(app)` — verify no regression |
| `tests/test_slack/test_forms.py` | Existing form builder tests (no changes needed) |
| `tests/conftest.py` | Shared fixtures; `app` fixture provides app context |
| `esb/config.py` | `TestingConfig` uses `sqlite:///:memory:`; `SlackTestConfig` inherits it with `TESTING=False` |

## Implementation Plan

### Wrapping Philosophy

**Command handlers:** `ack()` stays **outside** the `with` block — it doesn't access DB and keeping it separate makes the code structure clearer. The `with` block starts at the first line that accesses DB, services, or forms. Non-DB code like `search_term = body.get(...)` also stays outside when practical.

**View submission handlers:** The entire body goes inside the `with` block. View handlers call `ack()` conditionally at multiple points (success vs error), making it impractical to separate `ack()` from DB code. The overhead of `ack()` running inside an app context is negligible.

**Principle:** The `with` block must enclose ALL code that transitively touches `db.session` — including `_resolve_esb_user()`, `build_equipment_options()`, service calls, and any `db.session.get()` lookups. When in doubt, include the line inside the block. Non-DB early returns (e.g., input validation in `handle_esb_update`) may remain inside the `with` block when extracting them would complicate control flow.

### Task Dependencies

Tasks 1, 1b, 2, 3, and 4 are **atomically dependent** — the signature change in Task 1 requires the call-site update in Task 4, and vice versa. Apply all five together before running tests. Task 5 must also be applied before running `test_handlers.py`. Running tests between these tasks will produce `TypeError: register_handlers() missing 1 required positional argument: 'app'`.

**Line number note:** All line numbers in Tasks 2 and 3 refer to the file **before** Task 1 edits. Task 1 inserts ~15 lines (imports, helper function, comment) before `register_handlers()`, so after applying Task 1, all handler line numbers shift down by ~15. Use function names (not line numbers) to locate handlers after Task 1.

### All 7 Handlers Requiring Wrapping (completeness checklist)

| # | Handler | Type | Task |
|---|---------|------|------|
| 1 | `handle_esb_report` | command | Task 2 |
| 2 | `handle_esb_repair` | command | Task 2 |
| 3 | `handle_esb_status` | command | Task 2 |
| 4 | `handle_esb_update` | command | Task 2 |
| 5 | `handle_problem_report_submission` | view | Task 3 |
| 6 | `handle_repair_create_submission` | view | Task 3 |
| 7 | `handle_repair_update_submission` | view | Task 3 |

### Tasks

- [ ] Task 1: Add `_ensure_app_context()` helper and update `register_handlers()` signature
  - File: `esb/slack/handlers.py`
  - Action:
    1. Add module-level imports and a helper function before `register_handlers()`:
       ```python
       from contextlib import nullcontext

       from flask import has_app_context


       def _ensure_app_context(app):
           """Return app context manager if not already in one, else a no-op context.

           Slack Bolt dispatches handlers in Socket Mode threads without Flask app
           context. This helper ensures DB operations work in both production (no
           existing context) and tests (context provided by fixture).

           IMPORTANT: All handlers registered in register_handlers() that access
           DB/services must wrap their body in: with _ensure_app_context(app):

           Note: _resolve_esb_user() and forms.py functions do NOT call this
           themselves — they rely on being called from within an already-wrapped
           handler. If you add a new caller of these functions, wrap it.
           """
           if has_app_context():
               return nullcontext()
           return app.app_context()
       ```
    2. Change `def register_handlers(bolt_app):` (line 38) to `def register_handlers(bolt_app, app):`
    3. Add a comment above `register_handlers`:
       ```python
       # IMPORTANT: All handlers that access DB/services must wrap their body in
       # with _ensure_app_context(app): — see _ensure_app_context docstring.
       ```
  - Notes: `_ensure_app_context` is a module-level function (not inside `register_handlers`) so it can be imported and tested independently via `from esb.slack.handlers import _ensure_app_context`. Import ordering for ruff/isort compliance: new imports must go between `import logging` (line 3) and `logger = logging.getLogger(__name__)` (line 5), pushing `logger` down. Order: `import logging`, `from contextlib import nullcontext` (both stdlib), blank line, `from flask import has_app_context` (third-party), blank line, `logger = ...`. Docstring lines may need wrapping to stay within the 120-char ruff limit.

- [ ] Task 1b: Update `_resolve_esb_user` docstring to note context dependency
  - File: `esb/slack/handlers.py`
  - Action: Append to the existing docstring of `_resolve_esb_user` (lines 9–21), before the closing `"""`: `"Note: Must be called from within a Flask app context (provided by the calling handler's _ensure_app_context wrapper)."`
  - Notes: This is documentation only — no functional change. Helps future developers understand why this function doesn't wrap itself.

- [ ] Task 2: Wrap all 4 command handlers with `_ensure_app_context(app)`
  - File: `esb/slack/handlers.py`
  - Action: In each command handler, `ack()` stays on its own line. The `with _ensure_app_context(app):` block starts at the **first line that accesses DB/services/forms**.
  - Specific locations (references use `def` line, not decorator line):
    - `handle_esb_report` (`def` at line 42): `ack()` on line 43 stays outside. `with` block wraps lines 44–58: starts at `from esb.slack.forms import build_equipment_options...`, ends at the `client.views_open(...)` call.
    - `handle_esb_repair` (`def` at line 117): `ack()` on line 118 stays outside. `with` block wraps lines 119–143: starts at `esb_user = _resolve_esb_user(...)` (first DB access via `db.session.execute()`), ends at `client.views_open(...)`.
    - `handle_esb_status` (`def` at line 215, decorator at 214): `ack()` on line 216 stays outside. `search_term = body.get('text', '').strip()` (line 217) stays outside (no DB access). `with` block wraps lines 219–249: the `with` line must appear BEFORE `try:` (line 219), not inside it at `if not search_term:` (line 220) — the entire `try/except` must be wholly inside the `with` block, ends at `client.chat_postEphemeral(...)`. Note: `client.chat_postEphemeral` doesn't need DB, but the `text` variable is computed inside the `with` block's try/except, so it's simplest to keep the final Slack API call inside.
    - `handle_esb_update` (`def` at line 252, decorator at 251): `ack()` on line 253 stays outside. `with` block wraps lines 254–311: starts at `esb_user = _resolve_esb_user(...)` (first DB access via `db.session.execute()`), ends at `client.views_open(...)`. Note: `command_text` parsing and early-return branches (empty text at lines 264–270, non-numeric ID at lines 272–280) don't access DB but are inside the `with` block for simplicity — they return early, so the overhead is negligible.
  - Notes: `_resolve_esb_user()` is the critical first-line-after-`ack()` in `handle_esb_repair` and `handle_esb_update` — it MUST be inside the `with` block since it calls `db.session.execute()`.

- [ ] Task 3: Wrap all 3 view submission handlers with `_ensure_app_context(app)`
  - File: `esb/slack/handlers.py`
  - Action: Wrap the **entire body** in `with _ensure_app_context(app):`.
  - Specific locations:
    - `handle_problem_report_submission` (line 61): wrap lines 62–114 (entire body)
    - `handle_repair_create_submission` (line 146): wrap lines 147–212 (entire body)
    - `handle_repair_update_submission` (line 314): wrap lines 315–381 (entire body)
  - Notes: All `ack()` calls (both success and error paths) remain inside the `with` block. They don't access DB, but separating them is impractical given their conditional placement throughout the handler.

- [ ] Task 4: Pass Flask `app` from `init_slack()` to `register_handlers()`
  - File: `esb/slack/__init__.py`
  - Action: Change line 41 from `register_handlers(_bolt_app)` to `register_handlers(_bolt_app, app)`
  - Notes: `app` is already the parameter of `init_slack(app)`.

- [ ] Task 5: Update test helper to pass `app` to `register_handlers()`
  - File: `tests/test_slack/test_handlers.py`
  - Action: On line 31, change `register_handlers(bolt_app)` to `register_handlers(bolt_app, app)`.
  - Notes: The `_register_and_capture(app)` function already receives `app` as its parameter. All 9 existing test classes pass the pytest `app` fixture (which is the Flask test app) to `_register_and_capture(app)` in their setup fixtures. The handler closures capture this `app` instance, so when a handler calls `_ensure_app_context(app)`, it checks `has_app_context()` — which returns `True` because the test runs inside the `app` fixture's context — and returns `nullcontext()`. Same session, same behavior as before.

- [ ] Task 6: Add regression tests
  - File: `tests/test_slack/test_handlers.py`
  - Action: Add a new test class `TestHandlersOutsideAppContext` with these tests:

    1. **`test_command_handler_works_outside_app_context`** (core regression test for issue #15):
       ```python
       def test_command_handler_works_outside_app_context(self):
           """Handler pushes its own app context when none exists (reproduces #15)."""
           from esb import create_app
           app = create_app('testing')
           # Setup: create test data inside a temporary context
           with app.app_context():
               from esb.extensions import db
               db.create_all()
               area = _create_area(name='Woodshop', slack_channel='#woodshop')
               _create_equipment(name='SawStop', area=area)
           # Now OUTSIDE any app context — simulates Socket Mode thread
           handlers = _register_and_capture(app)
           ack = MagicMock()
           client = MagicMock()
           body = {'trigger_id': 'T1', 'user_id': 'U1', 'channel_id': 'C1', 'text': ''}
           # This would raise RuntimeError before the fix
           handlers['command:/esb-status'](ack=ack, body=body, client=client)
           ack.assert_called_once()
           response_text = client.chat_postEphemeral.call_args.kwargs['text']
           # Check for specific data to make failures diagnostic
           assert 'Woodshop' in response_text
           # Teardown
           with app.app_context():
               db.drop_all()
       ```
       Note: `_create_area` and `_create_equipment` are already imported at the top of `test_handlers.py` (line 7). Use the `area` return value directly instead of `Area.query.first()` to avoid fragility. Always tear down with `db.drop_all()` in a fresh context to match `conftest.py`'s pattern.
       **Why data survives:** Flask-SQLAlchemy uses `StaticPool` for `sqlite:///:memory:`, so the single connection persists across context exits. `session.remove()` on teardown returns the connection to the pool but doesn't close it. The handler's fresh context gets the same connection with all committed data intact.

    2. **`test_view_handler_works_outside_app_context`**:
       ```python
       def test_view_handler_works_outside_app_context(self):
           """View submission handler pushes its own app context (reproduces #15)."""
           from esb import create_app
           app = create_app('testing')
           with app.app_context():
               from esb.extensions import db
               db.create_all()
               area = _create_area(name='Woodshop', slack_channel='#woodshop')
               equipment = _create_equipment(name='SawStop', area=area)
               equipment_id = equipment.id
           # Outside any app context
           handlers = _register_and_capture(app)
           ack = MagicMock()
           client = MagicMock()
           view = {
               'state': {
                   'values': {
                       'equipment_block': {'equipment_select': {'selected_option': {'value': str(equipment_id)}}},
                       'name_block': {'reporter_name': {'value': 'Test User'}},
                       'description_block': {'description': {'value': 'Machine is broken'}},
                       'severity_block': {'severity': {'selected_option': {'value': 'Down'}}},
                       'safety_risk_block': {'safety_risk': {'selected_options': []}},
                       'consumable_block': {'consumable': {'selected_options': []}},
                   },
               },
           }
           body = {'user': {'id': 'U123', 'username': 'testuser'}}
           handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)
           ack.assert_called_once_with()
           # Verify repair record created by querying inside a fresh context
           with app.app_context():
               from esb.models.repair_record import RepairRecord
               records = RepairRecord.query.all()
               assert len(records) == 1
               assert records[0].description == 'Machine is broken'
               assert records[0].created_by == 'testuser'
               # Teardown
               from esb.extensions import db
               db.drop_all()
       ```

    3. **`test_ensure_app_context_pushes_when_needed`**:
       ```python
       def test_ensure_app_context_pushes_when_needed(self):
           from esb import create_app
           from esb.slack.handlers import _ensure_app_context
           from flask import has_app_context
           app = create_app('testing')
           assert not has_app_context()
           with _ensure_app_context(app):
               assert has_app_context()
           assert not has_app_context()
       ```

    4. **`test_ensure_app_context_noop_when_context_exists`**:
       ```python
       def test_ensure_app_context_noop_when_context_exists(self):
           from contextlib import nullcontext
           from esb import create_app
           from esb.slack.handlers import _ensure_app_context
           app = create_app('testing')
           with app.app_context():
               ctx_mgr = _ensure_app_context(app)
               assert isinstance(ctx_mgr, nullcontext)
       ```

  - Notes: Tests import `_ensure_app_context` via `from esb.slack.handlers import _ensure_app_context`. The test class does NOT use the `app` fixture from `conftest.py` — it creates its own app to control context lifecycle precisely.

- [ ] Task 7: Verify `tests/test_slack/test_init.py` passes without changes
  - File: `tests/test_slack/test_init.py`
  - Action: Run `venv/bin/python -m pytest tests/test_slack/test_init.py -v` and confirm all tests pass. No test in `test_init.py` directly imports or calls `register_handlers` — they all go through `create_app()` → `init_slack(app)` → `register_handlers(_bolt_app, app)`. The mock `_bolt_app` (a `MagicMock`) accepts any arguments, so the signature change is transparent.
  - Notes: No code changes expected. This is a verification step only. Pre-existing gap: `test_command_handlers_registered` in `TestSlackEnabled` only checks `/esb-report`, `/esb-repair`, `/esb-update` — `/esb-status` is not verified. This is out of scope for this fix but worth noting.

### Acceptance Criteria

- [ ] AC 1: Given a handler is called in a thread without Flask app context (production scenario), when `_ensure_app_context(app)` is used, then it pushes a Flask app context and the handler completes without `RuntimeError`.
- [ ] AC 2: Given a handler is called within an existing Flask app context (test scenario), when `_ensure_app_context(app)` is used, then it returns `nullcontext()` and no nested context is pushed.
- [ ] AC 3: Given the `/esb-status` command handler, when called outside any app context with equipment in the DB, then it returns the status summary text via `client.chat_postEphemeral`. *(Verified by Task 6, Test 1)*
- [ ] AC 4: Given the `problem_report_submission` view handler, when called outside any app context with equipment in the DB, then it creates a repair record and calls `ack()`. *(Verified by Task 6, Test 2)*
- [ ] AC 5: Given all 4 command handlers and 3 view submission handlers, when their source is inspected, then every handler body that accesses DB/services is wrapped in `with _ensure_app_context(app):`. *(Verified by code review)*
- [ ] AC 6: Given the existing test suite (`make test`), when all tests run, then they pass with no regressions — including all 9 existing test classes in `test_handlers.py`, all classes in `test_forms.py`, and all classes in `test_init.py`.
- [ ] AC 7: Given the new `TestHandlersOutsideAppContext` class, when its tests run, then all 4 tests pass — confirming both a command handler and a view handler work outside app context, and that the helper pushes/skips context correctly.

## Additional Context

### Dependencies

No new dependencies required. Uses existing Flask `app.app_context()`, `flask.has_app_context()`, and `contextlib.nullcontext` (stdlib).

### Testing Strategy

- **Existing unit tests (9 classes):** Update `_register_and_capture()` signature only. All existing tests continue to run within the `app` fixture's context. The `has_app_context()` guard in `_ensure_app_context` means handlers detect the existing context and return `nullcontext()` — same session, same behavior as before.
- **New regression tests:** `TestHandlersOutsideAppContext` class with 4 tests:
  1. `/esb-status` command handler outside app context (reproduces issue #15)
  2. `problem_report_submission` view handler outside app context (heavier DB path)
  3. `_ensure_app_context` pushes context when none exists
  4. `_ensure_app_context` returns `nullcontext` when context already exists
- **Verification:** Run `tests/test_slack/test_init.py` to confirm no regressions from the `register_handlers` signature change.
- **Manual testing:** Deploy and verify each Slack command end-to-end:
  - `/esb-status` — verify status summary appears (not an error message)
  - `/esb-status SawStop` — verify equipment detail appears with name and status
  - `/esb-report` — verify modal opens, submit a report, verify repair record created in DB via admin UI
  - `/esb-repair` — verify modal opens for authorized user, submit, verify record created
  - `/esb-update [id]` — verify modal opens with pre-populated values, submit update, verify changes

### Notes

- The `forms.py` functions (`build_equipment_options`, `build_user_options`) access `db.session` but are always called from within handlers wrapped by `_ensure_app_context`, so they inherit context.
- All 4 command handlers and 3 view submission handlers are affected.
- `_resolve_esb_user` is always called from within already-wrapped handlers — it inherits context. Its docstring should note this dependency: "Must be called from within a Flask app context (provided by handler's `_ensure_app_context` wrapper)."
- `ack()` in command handlers does not access the DB. It stays outside the `with` block for code clarity. In view handlers, `ack()` is called conditionally at various points, so it stays inside the `with` block for simplicity (negligible overhead).
- Pre-existing design note: view submission handlers call `ack()` at the END (after DB operations). If DB/service calls are slow, Slack may time out waiting for acknowledgment. This is not introduced by this fix and is out of scope.
- Future handler guidance: all new handlers registered in `register_handlers()` must wrap their DB-accessing body in `with _ensure_app_context(app):`. The docstring on `_ensure_app_context` and the comment above `register_handlers` document this. The regression tests would catch missing wrappers if they exercise the new handler outside app context.
