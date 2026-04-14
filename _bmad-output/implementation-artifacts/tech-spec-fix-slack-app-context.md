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

Pass the Flask `app` instance into `register_handlers()` and wrap each handler's body in a conditional app context using a shared helper function. The helper uses `flask.has_app_context()` to skip pushing a new context when one already exists (e.g., during tests), avoiding nested-context issues with Flask-SQLAlchemy's scoped sessions.

### Scope

**In Scope:**
- Add `_ensure_app_context(app)` helper that returns `app.app_context()` or `nullcontext()`
- Wrap all 4 command handlers and 3 view submission handlers with the helper
- Pass Flask `app` from `init_slack()` to `register_handlers()`
- Update existing test helper to match new `register_handlers()` signature
- Add regression test verifying handlers work without pre-existing app context

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

Each handler wraps its own body in `with _ensure_app_context(app):`. This:
- Actually works — the context is active for the entire handler body
- Is explicit and auditable — each handler visibly declares its context needs
- Uses a shared helper to minimize boilerplate (one-line wrapper)

The trade-off is that future handlers must remember to include the wrapper. The regression test documents this requirement and would catch omissions.

### Nested Context Safety

`TestingConfig` uses `sqlite:///:memory:`. Modern SQLAlchemy automatically uses `StaticPool` for in-memory URIs, sharing a single connection across all sessions. This means:
- Nested `app.app_context()` creates a new scoped session but on the same connection
- Committed data from the outer session IS visible to the inner session
- Test assertions using fresh queries (e.g., `RepairRecord.query.all()`) work correctly

The `has_app_context()` guard in `_ensure_app_context()` avoids nesting entirely as defense-in-depth, but even without it, the tests would function correctly due to `StaticPool`.

### Codebase Patterns

- Service layer pattern: views/handlers delegate to `esb/services/` for business logic
- Deferred imports used throughout handlers to avoid circular imports
- `init_slack(app)` receives Flask app but currently doesn't pass it to handlers
- Existing tests (~840 lines in `test_handlers.py`, 9 test classes) pass because `conftest.py`'s `app` fixture wraps everything in `with app.app_context()`, masking the bug
- `_register_and_capture()` test helper captures Bolt handler registrations via mock decorators

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
| `esb/config.py` | `TestingConfig` uses `sqlite:///:memory:` |

## Implementation Plan

### Tasks

- [ ] Task 1: Add `_ensure_app_context()` helper and update `register_handlers()` signature
  - File: `esb/slack/handlers.py`
  - Action:
    1. Add a module-level helper function before `register_handlers()`:
       ```python
       def _ensure_app_context(app):
           """Return app context manager if not already in one, else a no-op context."""
           from contextlib import nullcontext
           from flask import has_app_context
           if has_app_context():
               return nullcontext()
           return app.app_context()
       ```
    2. Change `def register_handlers(bolt_app):` (line 38) to `def register_handlers(bolt_app, app):`
  - Notes: `_ensure_app_context` is a module-level function (not inside `register_handlers`) so it can also be tested independently.

- [ ] Task 2: Wrap all 4 command handlers with `_ensure_app_context(app)`
  - File: `esb/slack/handlers.py`
  - Action: In each command handler, wrap the entire body **after** `ack()` in `with _ensure_app_context(app):`. The `ack()` call stays outside — it doesn't access the DB and must respond immediately.
  - Specific locations:
    - `handle_esb_report` (line 42): wrap lines 44-58 (from `from esb.slack.forms import...` through `client.views_open(...)`)
    - `handle_esb_repair` (line 117): wrap lines 119-143 (from `esb_user = _resolve_esb_user(...)` through `client.views_open(...)`)
    - `handle_esb_status` (line 214): wrap lines 217-249 (from `search_term = ...` through `client.chat_postEphemeral(...)`)
    - `handle_esb_update` (line 251): wrap lines 253-311 (from `esb_user = _resolve_esb_user(...)` through `client.views_open(...)`)
  - Notes: Everything that touches DB, services, or forms must be inside the `with` block. This includes `_resolve_esb_user()`, `build_equipment_options()`, `build_user_options()`, and all service calls.

- [ ] Task 3: Wrap all 3 view submission handlers with `_ensure_app_context(app)`
  - File: `esb/slack/handlers.py`
  - Action: In each view handler, wrap the **entire body** in `with _ensure_app_context(app):`. Unlike command handlers, view handlers call `ack()` conditionally (at the end on success, or with `response_action='errors'` on failure), so `ack()` stays inside the `with` block.
  - Specific locations:
    - `handle_problem_report_submission` (line 61): wrap lines 62-114
    - `handle_repair_create_submission` (line 146): wrap lines 147-212
    - `handle_repair_update_submission` (line 314): wrap lines 315-381
  - Notes: `ack()` does not access the DB, but since it's called conditionally at different points in the handler, it's simpler and safer to keep it inside the `with` block. The overhead of `ack()` running inside an app context is negligible.

- [ ] Task 4: Pass Flask `app` from `init_slack()` to `register_handlers()`
  - File: `esb/slack/__init__.py`
  - Action: Change line 41 from `register_handlers(_bolt_app)` to `register_handlers(_bolt_app, app)`
  - Notes: `app` is already the parameter of `init_slack(app)`.

- [ ] Task 5: Update test helper to pass `app` to `register_handlers()`
  - File: `tests/test_slack/test_handlers.py`
  - Action: On line 31, change `register_handlers(bolt_app)` to `register_handlers(bolt_app, app)`. The `_register_and_capture(app)` function already receives `app` as a parameter.
  - Notes: All 9 existing test classes pass `self.app` to `_register_and_capture(app)` in their setup fixtures. The handler functions captured by the mock close over the test's `app` instance.

- [ ] Task 6: Add regression tests
  - File: `tests/test_slack/test_handlers.py`
  - Action: Add a new test class `TestHandlersOutsideAppContext` with tests that exercise handlers **without** a pre-existing app context:
    1. **Test: command handler works outside app context**
       - Create a Flask app via `create_app('testing')`
       - Inside a `with app.app_context():` block: create DB tables, create test area + equipment, commit
       - After the `with` block exits (no app context): register handlers, call `/esb-status` handler
       - Assert: no `RuntimeError`, `client.chat_postEphemeral` called with expected text containing 'Equipment Status Summary'
    2. **Test: `_ensure_app_context` pushes context when needed**
       - Create a Flask app, verify `has_app_context()` is `False`
       - Call `with _ensure_app_context(app):` and verify `has_app_context()` is `True` inside the block
    3. **Test: `_ensure_app_context` is a no-op when context exists**
       - Inside `with app.app_context():`, call `_ensure_app_context(app)`, verify it returns a `nullcontext` (i.e., doesn't push a second context)
  - Notes: Test 1 is the core regression test that reproduces issue #15. It works because `StaticPool` keeps the same SQLite connection across contexts, so test data created in one context is visible in the handler's context. Tests 2-3 validate the helper in isolation.

- [ ] Task 7: Verify `tests/test_slack/test_init.py` passes without changes
  - File: `tests/test_slack/test_init.py`
  - Action: Run `venv/bin/python -m pytest tests/test_slack/test_init.py -v` and confirm all tests pass. `TestSlackEnabled` calls `init_slack(app)` which calls `register_handlers(_bolt_app, app)` — the mock `_bolt_app` accepts any arguments, so the signature change is transparent.
  - Notes: No code changes expected. This is a verification step only. If any test imports and calls `register_handlers` directly with the old signature, it would need updating.

### Acceptance Criteria

- [ ] AC 1: Given a handler is called in a thread without Flask app context (production scenario), when `_ensure_app_context(app)` is used, then it pushes a Flask app context and the handler completes without `RuntimeError`.
- [ ] AC 2: Given a handler is called within an existing Flask app context (test scenario), when `_ensure_app_context(app)` is used, then it returns `nullcontext()` and no nested context is pushed.
- [ ] AC 3: Given the `/esb-status` command handler, when called outside any app context with equipment in the DB, then it returns the status summary text via `client.chat_postEphemeral`.
- [ ] AC 4: Given the `/esb-report` command handler, when called outside any app context with equipment in the DB, then it opens the problem report modal via `client.views_open`.
- [ ] AC 5: Given all 4 command handlers and 3 view submission handlers, when their source is inspected, then every handler body that accesses DB/services is wrapped in `with _ensure_app_context(app):`.
- [ ] AC 6: Given the existing test suite (`make test`), when all tests run, then they pass with no regressions — including all 9 existing test classes in `test_handlers.py`, all classes in `test_forms.py`, and all classes in `test_init.py`.
- [ ] AC 7: Given the new `TestHandlersOutsideAppContext` class, when its tests run, then they all pass — confirming handlers work without pre-existing app context and that the helper pushes/skips context correctly.

## Additional Context

### Dependencies

No new dependencies required. Uses existing Flask `app.app_context()`, `flask.has_app_context()`, and `contextlib.nullcontext` (stdlib).

### Testing Strategy

- **Existing unit tests (9 classes):** Update `_register_and_capture()` signature only. All existing tests continue to run within the `app` fixture's context. The `has_app_context()` guard in `_ensure_app_context` means handlers detect the existing context and skip pushing — same session, same behavior as before.
- **New regression tests:** `TestHandlersOutsideAppContext` class with 3 tests:
  1. Full handler execution outside app context (reproduces issue #15)
  2. `_ensure_app_context` pushes context when none exists
  3. `_ensure_app_context` is a no-op when context already exists
- **Verification:** Run `tests/test_slack/test_init.py` to confirm no regressions from the `register_handlers` signature change.
- **Manual testing:** Deploy and verify each Slack command end-to-end:
  - `/esb-status` — verify status summary appears (not an error message)
  - `/esb-status SawStop` — verify equipment detail appears
  - `/esb-report` — verify modal opens, submit a report, verify repair record appears in DB
  - `/esb-repair` — verify modal opens for authorized user
  - `/esb-update [id]` — verify modal opens with pre-populated values

### Notes

- The `forms.py` functions (`build_equipment_options`, `build_user_options`) access `db.session` but are always called from within handlers wrapped by `_ensure_app_context`, so they inherit context.
- All 4 command handlers and 3 view submission handlers are affected.
- `_resolve_esb_user` is always called from within already-wrapped handlers — it inherits context.
- `ack()` in command handlers does not access the DB. It stays outside the `with` block to respond to Slack immediately. In view handlers, `ack()` is called conditionally at various points, so it stays inside the `with` block for simplicity (negligible overhead).
- Pre-existing design note: view submission handlers call `ack()` at the END (after DB operations). If DB/service calls are slow, Slack may time out waiting for acknowledgment. This is not introduced by this fix and is out of scope.
- Risk: future handlers added without `_ensure_app_context(app)` wrapping will fail in production but pass in tests. The regression test and the `_ensure_app_context` helper (discoverable via grep) document this requirement.
