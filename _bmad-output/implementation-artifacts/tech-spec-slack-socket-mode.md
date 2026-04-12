---
title: 'Switch Slack Integration from HTTP Mode to Socket Mode'
slug: 'slack-socket-mode'
created: '2026-04-12'
status: 'ready-for-dev'
stepsCompleted: [1, 2, 3, 4]
tech_stack: ['Python 3.14', 'Flask', 'slack-bolt>=1.27.0', 'slack_sdk>=3.39.0', 'websocket-client']
files_to_modify: ['esb/slack/__init__.py', 'esb/config.py', '.env.example', 'docs/administrators.md', 'tests/test_slack/test_init.py', 'requirements.txt', 'Dockerfile', 'docker-compose.yml', 'esb/__init__.py']
code_patterns: ['App factory init_slack(app) called from create_app()', 'Module-level _bolt_app/_handler globals', 'Conditional blueprint registration', 'register_handlers(bolt_app) decorator pattern']
test_patterns: ['Mock Bolt App and adapter in TestSlackEnabled', 'Transport-agnostic handler tests via _register_and_capture()', 'TestSlackDisabled verifies no routes when unconfigured']
---

# Tech-Spec: Switch Slack Integration from HTTP Mode to Socket Mode

**Created:** 2026-04-12

## Overview

### Problem Statement

The Slack integration uses HTTP mode (Slack Bolt with `SlackRequestHandler`), which requires Slack to POST to a publicly accessible `/slack/events` endpoint. However, the architecture explicitly mandates no public internet exposure for the application (NFR14). The admin guide currently works around this by suggesting ngrok or Cloudflare Tunnel, which contradicts the design intent and adds operational complexity for a volunteer-maintained makerspace tool.

### Solution

Switch from Slack Bolt HTTP mode to Socket Mode. Socket Mode uses an outbound WebSocket connection from the app to Slack, eliminating the need for any public URL. The socket connection will run in the main app process via a background thread. This aligns with the existing architectural constraint and simplifies deployment.

### Scope

**In Scope:**
- Modify `esb/slack/__init__.py` to use Socket Mode instead of HTTP mode
- Add `SLACK_APP_TOKEN` config variable (app-level token required for Socket Mode)
- Remove `SLACK_SIGNING_SECRET` config variable (HTTP signing no longer needed)
- Remove the `/slack/events` HTTP endpoint and Flask blueprint route
- Update `docs/administrators.md` with Socket Mode setup instructions
- Add `websocket-client` to `requirements.txt` for stable Socket Mode transport
- Reduce gunicorn workers to 1 in `Dockerfile` (prevent duplicate event processing)
- Add `SLACK_SOCKET_MODE_CONNECT=true` to app service in `docker-compose.yml` (opt-in design)
- Add graceful shutdown, connect error handling, and testing guards to `init_slack()`

**Out of Scope:**
- Slash command handler logic (unchanged)
- Modal/view submission handler logic (unchanged)
- Notification queue and background worker (unchanged)
- Any new Slack features

## Context for Development

### Codebase Patterns

- **App factory pattern:** `init_slack(app)` is called from `create_app()` in `esb/__init__.py:61`. It conditionally initializes Slack based on config vars.
- **Module-level globals:** `_bolt_app` and `_handler` are set during `init_slack()`. With Socket Mode, `_handler` becomes `_socket_handler` (a `SocketModeHandler`).
- **Conditional blueprint registration:** The Slack blueprint is only registered when tokens are configured. With Socket Mode, the blueprint and its HTTP route are removed entirely.
- **Handler registration:** `register_handlers(bolt_app)` in `handlers.py` uses `@bolt_app.command()` and `@bolt_app.view()` decorators. This pattern is transport-agnostic — identical for HTTP and Socket Mode.
- **CSRF exemption:** Currently applied to the Slack blueprint (line 54-55 of `__init__.py`). No longer needed since there's no HTTP endpoint.

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `esb/slack/__init__.py` | Slack init + HTTP endpoint (primary change target) |
| `esb/slack/handlers.py` | Command/view handlers (unchanged, reference only) |
| `esb/config.py` | Config vars: add `SLACK_APP_TOKEN`, remove `SLACK_SIGNING_SECRET` |
| `.env.example` | Env template: replace `SLACK_SIGNING_SECRET` with `SLACK_APP_TOKEN` |
| `docs/administrators.md` | Admin guide Slack section (rewrite for Socket Mode) |
| `tests/test_slack/test_init.py` | Init tests (update mocks and assertions) |
| `tests/test_slack/test_handlers.py` | Handler tests (unchanged, reference for patterns) |
| `docker-compose.yml` | App service: set `SLACK_SOCKET_MODE_CONNECT=true` (opt-in socket connection) |
| `requirements.txt` | Add `websocket-client` dependency for stable Socket Mode WebSocket |
| `Dockerfile` | Reduce gunicorn workers to 1 to prevent duplicate event processing |

### Technical Decisions

- **Socket Mode in main process:** `SocketModeHandler(bolt_app).connect()` runs a daemon thread within the Flask app process. No separate container or service needed. Simpler operationally for a volunteer-maintained tool.
- **Single gunicorn worker with threads (F1):** Slack Socket Mode sends events to ALL active WebSocket connections from the same app, not load-balanced. Multiple workers = multiple processes = duplicate event processing (duplicate repair records, duplicate modals). Switch gunicorn to `--workers 1 --threads 2`. One process means one Socket Mode connection (no duplication), while threads provide concurrent web request handling so a slow request doesn't block others.
- **Opt-in socket connection (F2, R2-F11):** Socket Mode connection is opt-in: only connects when `app.config['SLACK_SOCKET_MODE_CONNECT']` is `'true'`. This prevents accidental duplicate connections from new services or containers. The app container sets `SLACK_SOCKET_MODE_CONNECT=true` in `docker-compose.yml`; the worker and any other services don't set it, so they safely skip connection. `SLACK_SOCKET_MODE_CONNECT` is defined in the `Config` class (R2-F2), consistent with all other config vars.
- **`websocket-client` dependency (F3):** Slack's own docs recommend the `websocket-client` package for stable Socket Mode connections. The built-in `slack_sdk` WebSocket client has known limitations. Add `websocket-client>=1.6.0` to `requirements.txt`.
- **Graceful shutdown (F4, R2-F1):** Register both an `atexit` handler and a `signal.signal(SIGTERM, ...)` handler that call `_socket_handler.close()`. `atexit` fires on normal interpreter exit; the SIGTERM signal handler ensures clean shutdown when the process is killed directly (e.g., outside gunicorn). Gunicorn catches SIGTERM and triggers a clean exit that fires `atexit`, but the explicit signal handler covers non-gunicorn environments (e.g., `make run` with Flask dev server).
- **Testing guard (F9):** Skip `SocketModeHandler` creation and `connect()` when `app.config['TESTING']` is `True`, preventing real WebSocket connections if a developer runs tests with tokens in their `.env`.
- **Error handling on connect (F12):** Wrap `_socket_handler.connect()` in a `try/except` block. On failure (invalid token, network down), log a warning and allow the app to start normally without Slack. This prevents a Slack outage from crashing the entire Flask app.
- **Remove `SLACK_SIGNING_SECRET`:** Clean removal rather than keeping as a no-op. Socket Mode doesn't use HTTP payload signing.
- **Remove Flask blueprint:** The `/slack/events` route and `slack_bp` blueprint are removed entirely. Socket Mode receives events via WebSocket, not HTTP. The CSRF exemption is also removed.
- **`SLACK_APP_TOKEN` required for Socket Mode:** This is an app-level token (starts with `xapp-`) generated in the Slack App settings under "Basic Information > App-Level Tokens" with the `connections:write` scope.
- **No changes to handlers:** `register_handlers()` works identically — Bolt dispatches events the same way regardless of transport.
- **Remove no-op message event handler and `message.channels` subscription (F14, R2-F6):** The current `@_bolt_app.event('message')` no-op handler was added to suppress a Bolt warning in HTTP mode. In Socket Mode with persistent connections, this handler would fire for every channel message. Remove the handler AND remove the `message.channels` bot event subscription from the Slack App setup instructions. Without the subscription, Slack won't send message events, so no handler or warning suppression is needed.

## Implementation Plan

### Tasks

- [ ] Task 1: Add `websocket-client` to requirements (F3)
  - File: `requirements.txt`
  - Action: Add `websocket-client>=1.6.0` after the `slack-bolt` line.
  - Notes: Slack docs recommend this for production Socket Mode stability over the built-in SDK WebSocket client.

- [ ] Task 2: Update config to replace `SLACK_SIGNING_SECRET` with `SLACK_APP_TOKEN` and add `SLACK_SOCKET_MODE_CONNECT` (R2-F2)
  - File: `esb/config.py`
  - Action: Remove line 20 (`SLACK_SIGNING_SECRET`). Add two new config vars:
    ```python
    SLACK_APP_TOKEN = os.environ.get('SLACK_APP_TOKEN', '')
    SLACK_SOCKET_MODE_CONNECT = os.environ.get('SLACK_SOCKET_MODE_CONNECT', '')
    ```

    Also add a `SlackTestConfig` class and register it in the `config` dict (R3-F1):
    ```python
    class SlackTestConfig(TestingConfig):
        """Config for testing Socket Mode init path (TESTING=False so connect() runs)."""
        TESTING = False
    ```
    And in the `config` dict at the bottom of the file:
    ```python
    config = {
        ...
        'slack_test': SlackTestConfig,
        ...
    }
    ```
  - Notes: Keep `SLACK_BOT_TOKEN` and `SLACK_OOPS_CHANNEL` unchanged. `SLACK_SOCKET_MODE_CONNECT` follows the same `os.environ.get` pattern as all other config vars and is accessed via `app.config` in `init_slack()`. `SlackTestConfig` extends `TestingConfig` (SQLite in-memory, CSRF disabled) but overrides `TESTING=False` so the socket init path executes.

- [ ] Task 3: Update `.env.example` to replace `SLACK_SIGNING_SECRET` with `SLACK_APP_TOKEN` and add `SLACK_SOCKET_MODE_CONNECT` (R2-F8)
  - File: `.env.example`
  - Action: Replace the `SLACK_SIGNING_SECRET=` line with:
    ```
    SLACK_APP_TOKEN=
    # Slack channel for cross-area equipment notifications (R3-F9 — was missing from .env.example)
    # SLACK_OOPS_CHANNEL=#oops
    # Set to 'true' to enable Socket Mode connection (set in docker-compose for app service)
    # SLACK_SOCKET_MODE_CONNECT=true
    ```
  - Notes: Keep `SLACK_BOT_TOKEN=` unchanged. `SLACK_OOPS_CHANNEL` already exists in the `Config` class but was missing from `.env.example` (R3-F9) — add it here as a commented example. `SLACK_SOCKET_MODE_CONNECT` is also commented out because it's typically set in `docker-compose.yml` per-service, not in `.env`. Including both here documents their existence for developers running locally.

- [ ] Task 4: Rewrite `esb/slack/__init__.py` for Socket Mode
  - File: `esb/slack/__init__.py`
  - Action: Complete rewrite of the module. Target structure:
    ```python
    """Slack App handlers package."""

    import atexit
    import logging
    import signal

    logger = logging.getLogger(__name__)

    # Module-level state (set during init_slack)
    _bolt_app = None
    _socket_handler = None


    def init_slack(app):
        """Initialize Slack Bolt app with Socket Mode.

        Skips initialization if SLACK_BOT_TOKEN or SLACK_APP_TOKEN is not configured.
        Skips Socket Mode connection if TESTING config is True or
        SLACK_SOCKET_MODE_CONNECT config is not 'true' (opt-in).
        Called from create_app() in esb/__init__.py.
        """
        global _bolt_app, _socket_handler

        token = app.config.get('SLACK_BOT_TOKEN', '')
        app_token = app.config.get('SLACK_APP_TOKEN', '')

        if not token:
            logger.info('SLACK_BOT_TOKEN not configured, Slack module disabled')
            return

        if not app_token:
            logger.warning('SLACK_APP_TOKEN not configured, Slack module disabled')
            return

        from slack_bolt import App

        _bolt_app = App(token=token)

        # Register command and view submission handlers
        from esb.slack.handlers import register_handlers
        register_handlers(_bolt_app)

        logger.info('Slack Bolt app initialized successfully')

        # Skip socket connection in tests
        if app.config.get('TESTING'):
            logger.info('Testing mode, skipping Socket Mode connection')
            return

        # Opt-in: only connect when SLACK_SOCKET_MODE_CONNECT is explicitly 'true'
        # No fallback needed — Config class defaults to '' (R3-F6)
        if app.config['SLACK_SOCKET_MODE_CONNECT'].lower() != 'true':
            logger.info('SLACK_SOCKET_MODE_CONNECT is not true, skipping Socket Mode connection')
            return

        from slack_bolt.adapter.socket_mode import SocketModeHandler

        _socket_handler = SocketModeHandler(app=_bolt_app, app_token=app_token)

        try:
            _socket_handler.connect()
            logger.info('Slack Socket Mode connected')
        except Exception:
            logger.warning('Failed to connect Slack Socket Mode — app will run without Slack', exc_info=True)
            _socket_handler = None
            return

        atexit.register(_shutdown_socket)

        # SIGTERM handler for environments that don't trigger atexit on SIGTERM
        # (e.g., Flask dev server). Gunicorn handles SIGTERM gracefully already,
        # but the explicit handler is harmless and covers other runtimes.
        # signal.signal() can only be called from the main thread (R3-F3).
        import threading
        if threading.current_thread() is threading.main_thread():
            prev_handler = signal.getsignal(signal.SIGTERM)

            def _sigterm_handler(signum, frame):
                _shutdown_socket()
                if callable(prev_handler) and prev_handler not in (signal.SIG_DFL, signal.SIG_IGN):
                    prev_handler(signum, frame)

            signal.signal(signal.SIGTERM, _sigterm_handler)
        else:
            logger.debug('Not main thread, skipping SIGTERM handler registration')


    def _shutdown_socket():
        """Cleanly close the Socket Mode WebSocket on shutdown.

        Intentionally idempotent — may be called from both the SIGTERM handler
        and atexit during the same shutdown sequence. The `is not None` guard
        ensures close() is only called once.
        """
        global _socket_handler
        if _socket_handler is not None:
            try:
                _socket_handler.close()
                logger.info('Slack Socket Mode disconnected')
            except Exception:
                logger.warning('Error closing Socket Mode connection', exc_info=True)
            _socket_handler = None
    ```
  - Key changes from current code:
    1. Removed all Flask imports (`Blueprint`, `request`), `slack_bp`, `_handler`, `SlackRequestHandler`, HTTP route, CSRF exemption
    2. Added `atexit` + `signal` imports and `_shutdown_socket()` for graceful shutdown (F4, R2-F1). Both `atexit.register` and `signal.signal(SIGTERM)` are set. The SIGTERM handler chains to any previous handler.
    3. `SLACK_APP_TOKEN` replaces `SLACK_SIGNING_SECRET` check — warning log level for missing app token, info level for missing bot token (F7)
    4. `Bolt App` created with `token=` only — no `signing_secret` param
    5. Testing guard: `app.config.get('TESTING')` skips `connect()` (F9)
    6. Socket connection is **opt-in** (R2-F11): only connects when `app.config['SLACK_SOCKET_MODE_CONNECT']` equals `'true'`. This is a safe default — new services or containers won't accidentally open duplicate connections.
    7. `SLACK_SOCKET_MODE_CONNECT` read from `app.config` (R2-F2), not `os.environ`, consistent with all other config vars.
    8. `connect()` wrapped in try/except — failure logs warning, app continues (F12)
    9. No-op `@_bolt_app.event('message')` handler removed (F14)
  - Notes: Deferred imports follow existing pattern. The Bolt app is still initialized in test/worker mode (handlers registered) — only the socket connection is skipped. This means tests can still capture and invoke handlers via the `_bolt_app` global.

- [ ] Task 5: Switch gunicorn to single worker with threads (F1)
  - File: `Dockerfile`
  - Action: Change line 25 from `"--workers", "2"` to `"--workers", "1", "--threads", "2"`.
  - Notes: Socket Mode sends events to ALL active WebSocket connections — multiple workers means duplicate processing. One worker with threads gives a single process (one socket connection, no duplication) while maintaining concurrent web request handling via threads.

- [ ] Task 6: Enable Socket Mode connection only in app container (F2, R2-F11)
  - File: `docker-compose.yml`
  - Action: Add `environment` section to the `app` service with `SLACK_SOCKET_MODE_CONNECT=true`. The worker service does NOT get this variable (opt-in means it won't connect by default).
    ```yaml
    app:
      build: .
      ports:
        - "5000:5000"
      depends_on:
        db:
          condition: service_healthy
      env_file: .env
      environment:
        - SLACK_SOCKET_MODE_CONNECT=true
      volumes:
        - ./uploads:/app/uploads
      restart: unless-stopped
    ```
    Worker service remains unchanged (no `SLACK_SOCKET_MODE_CONNECT` needed — default is to not connect).
  - Notes: Opt-in design (R2-F11). Only the app container explicitly enables the socket connection. Any new service that calls `create_app()` will safely skip socket connection unless it also sets `SLACK_SOCKET_MODE_CONNECT=true`. The worker still initializes the Bolt app (handlers registered) for database/service layer access, but never opens a WebSocket.

- [ ] Task 7: Update init tests for Socket Mode
  - File: `tests/test_slack/test_init.py`
  - Action:
    **IMPORTANT (R2-F4):** The `TESTING` config guard in `init_slack()` skips `SocketModeHandler` construction when `app.config['TESTING']` is `True`. Tests that need to verify socket connection behavior (connect called, atexit registered, etc.) MUST use `create_app('slack_test')`, which uses the `SlackTestConfig` registered in `esb/config.py` (Task 2). This config extends `TestingConfig` (SQLite in-memory, CSRF disabled) but sets `TESTING=False` so the socket init path executes.

    1. **`TestSlackDisabled`** (uses `create_app('testing')` — unchanged):
       - Keep `test_app_starts_cleanly_without_slack` as-is
       - Simplify `test_no_slack_routes_when_disabled` and `test_no_slack_in_url_map_when_disabled` to verify `slack_mod._bolt_app is None` (since `/slack/events` never exists now)
    2. **`TestSlackEnabled`** (R2-F4: use `create_app('slack_test')`):
       - Update `setup_app` fixture:
         - Change `create_app('testing')` to `create_app('slack_test')`
         - Import `SlackTestConfig` from `esb.config`
         - Replace `patch.object(Config, 'SLACK_SIGNING_SECRET', 'test-signing-secret')` with `patch.object(SlackTestConfig, 'SLACK_APP_TOKEN', 'xapp-test-token')`
         - Add `patch.object(SlackTestConfig, 'SLACK_SOCKET_MODE_CONNECT', 'true')` (opt-in)
         - Replace `patch('slack_bolt.adapter.flask.SlackRequestHandler', return_value=self.mock_handler)` with `patch('slack_bolt.adapter.socket_mode.SocketModeHandler', return_value=self.mock_socket_handler)` where `self.mock_socket_handler = MagicMock()`
         - Patch `atexit.register` and `signal.signal` to prevent real side effects (use context managers so they auto-restore in teardown — R3-F10)
       - Remove these tests (no HTTP endpoint):
         - `test_slack_events_route_exists`
         - `test_slack_events_route_is_post`
         - `test_slack_events_delegates_to_handler`
         - `test_slack_blueprint_csrf_exempt`
       - Update `test_slack_module_loads_when_configured`:
         - Assert `slack_mod._bolt_app is not None`
         - Assert `slack_mod._socket_handler is not None`
       - Add `test_socket_mode_connect_called`:
         - Assert `self.mock_socket_handler.connect.assert_called_once()`
       - Add `test_atexit_registered`:
         - Assert `atexit.register` was called with `esb.slack._shutdown_socket`
       - Add `test_sigterm_handler_registered` (R2-F1):
         - Assert `signal.signal` was called with `signal.SIGTERM`
       - Keep transport-agnostic tests unchanged:
         - `test_register_handlers_called`
         - `test_command_handlers_registered`
         - `test_view_handlers_registered`
         - `test_app_starts_cleanly_with_slack`
       - Remove `test_bolt_app_event_handler_registered` — no-op message handler removed (F14)
       - **Teardown (R2-F10):** Reset BOTH globals: `slack_mod._bolt_app = None` AND `slack_mod._socket_handler = None`. (The current code resets both `_bolt_app` and `_handler`; the new code must reset both `_bolt_app` and `_socket_handler`.)
    3. **`TestSlackMissingSigningSecret`** → rename to **`TestSlackMissingAppToken`**:
       - Use `create_app('testing')` with `patch.object(Config, 'SLACK_BOT_TOKEN', 'xoxb-test-token')` and `patch.object(Config, 'SLACK_APP_TOKEN', '')` (empty — the condition under test)
       - Assert `slack_mod._bolt_app is None` and `slack_mod._socket_handler is None`
       - Assert `SocketModeHandler` was never constructed
    4. **Add `TestSlackTestingModeSkipsConnect`** (new test class — verifies AC13):
       - Use `create_app('testing')` with valid tokens patched
       - Assert `_bolt_app is not None` (Bolt app initialized)
       - Assert `_socket_handler is None` (connect skipped due to TESTING=True)
       - Assert `SocketModeHandler` was never constructed
    5. **Add `TestSlackConnectSkippedWhenNotOptedIn`** (new test class — replaces old worker test):
       - Use `create_app('slack_test')` with both tokens valid but `SLACK_SOCKET_MODE_CONNECT` left as empty string (default — not opted in)
       - Assert `_bolt_app is not None` (Bolt app still initialized)
       - Assert `_socket_handler is None` (connect was skipped)
       - Assert `SocketModeHandler` was never constructed
    6. **Add `TestSlackConnectFailure`** (new test class) (F12):
       - Use `create_app('slack_test')` with both tokens valid and `SLACK_SOCKET_MODE_CONNECT='true'`
       - Make `mock_socket_handler.connect.side_effect = Exception('Network error')`
       - Assert app starts cleanly (no crash)
       - Assert `_socket_handler is None` (cleared after failure)
       - Assert `_bolt_app is not None` (Bolt app still initialized)
  - Notes: Handler tests in `test_handlers.py` are transport-agnostic and require no changes. The `SlackTestConfig` / `create_app('slack_test')` approach cleanly separates "test the socket connection init path" (needs `TESTING=False`) from "test with Slack disabled" (uses standard `TestingConfig`). Removal of message event handler test (F14) is covered in point 2 above.

- [ ] Task 8: Update administrators guide for Socket Mode
  - File: `docs/administrators.md`
  - Action: Rewrite the "Slack App Configuration" section. Find each section by its heading text (not by line number — line numbers may shift if earlier edits change content):
    1. **"1. Create a Slack App"**: unchanged
    2. **"2. Configure Bot Token Scopes"**: unchanged
    3. **Add new "3. Enable Socket Mode"**:
       - Go to **Settings > Socket Mode** in the Slack App settings
       - Turn on **Enable Socket Mode**
       - Create an App-Level Token with the `connections:write` scope
       - Name it (e.g., "esb-socket") and copy the token (starts with `xapp-`)
    4. **"Set Up Slash Commands"** becomes **"4. Set Up Slash Commands"**:
       - Remove the "Request URL" paragraph and code block (`https://<your-domain>/slack/events`)
       - Keep the command table (commands and descriptions unchanged)
       - Add note: "With Socket Mode enabled, slash commands are automatically routed to your app via WebSocket. No Request URL is needed."
    5. **"Enable Event Subscriptions"** becomes **"5. Enable Event Subscriptions"**:
       - Remove the "Set the Request URL" instruction
       - Keep "Enable Events: ON"
       - **Remove `message.channels`** from "Subscribe to bot events" (R2-F6). The no-op message handler has been removed, and without it Bolt would log warnings for every unhandled message event. The app does not use channel message events for any functionality.
       - If no bot events are needed after removing `message.channels`, this section can state: "Event subscriptions are not currently required but may be used for future features."
    6. **"Install the App"** becomes **"6. Install the App"**: unchanged
    7. **"Copy Credentials"** becomes **"7. Copy Credentials"**:
       - Replace step 2 (Signing Secret) with: "Copy the **App-Level Token** (starts with `xapp-`, created in step 3) and set it as `SLACK_APP_TOKEN` in your `.env`"
       - Keep step 1 (Bot Token) and step 3 (restart) unchanged
    8. **Remove the warning admonition** about publicly accessible URL. Replace with a note: "Socket Mode uses an outbound WebSocket connection — no public URL or reverse proxy is needed. Your ESB server can remain on a private network."
  - Also update the **Prerequisites** section (R2-F5):
    - Change "A **Slack workspace** with a paid plan (Pro or higher) if you want to use Slack integration" to "A **Slack workspace** for Slack integration (check current Slack plan requirements for Socket Mode at api.slack.com)"
  - Also update the **Environment Variable Reference** table:
    - Remove the `SLACK_SIGNING_SECRET` row
    - Add `SLACK_APP_TOKEN` row: "Slack App-Level Token for Socket Mode. Required for Slack integration. Leave empty to disable." with example `xapp-1-...`
    - Add `SLACK_SOCKET_MODE_CONNECT` row (R2-F8): "Set to `true` to enable the Socket Mode WebSocket connection. Only the app container should set this; worker and other services should leave it unset." with example `true`
  - Also update the **App Service** description in "Docker Services" section (R2-F7):
    - Change "Runs Flask via Gunicorn with 2 worker processes on port 5000" to "Runs Flask via Gunicorn with 1 worker process and 2 threads on port 5000"
  - Also update **Runtime Dependencies**:
    - Change "slash commands, modals, events" to "slash commands, modals, events via Socket Mode"
    - Add **websocket-client** to the list: "WebSocket transport for Slack Socket Mode"
  - Also update the **Troubleshooting > Slack commands not working** section:
    - Replace "Verify `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set correctly" with "Verify `SLACK_BOT_TOKEN` and `SLACK_APP_TOKEN` are set correctly"
    - Replace "Confirm the Request URL ... is reachable from the internet" with "Verify Socket Mode is enabled in the Slack App settings and the app-level token has the `connections:write` scope"
    - Add: "Verify `SLACK_SOCKET_MODE_CONNECT=true` is set in the app service environment"

- [ ] Task 9: Update stale comment in app factory (R2-F9)
  - File: `esb/__init__.py`
  - Action: Update comment on line 59 from `# Initialize Slack integration (conditional on SLACK_BOT_TOKEN)` to `# Initialize Slack integration (conditional on SLACK_BOT_TOKEN and SLACK_APP_TOKEN)`.

### Acceptance Criteria

- [ ] AC 1: Given `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN`, and `SLACK_SOCKET_MODE_CONNECT=true` are all set, when the app starts, then `SocketModeHandler.connect()` is called and the Slack Bolt app is initialized with all command and view handlers registered.
- [ ] AC 2: Given `SLACK_BOT_TOKEN` is empty, when the app starts, then Slack initialization is skipped entirely (info log) and the app starts normally without errors.
- [ ] AC 3: Given `SLACK_BOT_TOKEN` is set but `SLACK_APP_TOKEN` is empty, when the app starts, then Slack initialization is skipped with a warning-level log message "SLACK_APP_TOKEN not configured, Slack module disabled" and the app starts normally. Neither `_bolt_app` nor `_socket_handler` are set.
- [ ] AC 4: Given the app is running with Socket Mode enabled, when any URL is requested at `/slack/events`, then a 404 is returned (the HTTP endpoint no longer exists).
- [ ] AC 5: Given the app is running with Socket Mode enabled, when a user sends `/esb-report` in Slack, then the problem report modal opens (verifies end-to-end Socket Mode transport — manual test only).
- [ ] AC 6: Given the `.env.example` file, when a new administrator reads it, then `SLACK_APP_TOKEN` is listed and `SLACK_SIGNING_SECRET` is not present.
- [ ] AC 7: Given the administrators guide, when a new administrator follows the Slack setup steps, then no step references a public URL, Request URL, or Signing Secret — all instructions reference Socket Mode and App-Level Token.
- [ ] AC 8: Given the existing test suite, when `make test` is run, then all tests pass including updated Slack init tests.
- [ ] AC 9: Given a container does NOT set `SLACK_SOCKET_MODE_CONNECT=true` (e.g., the worker), when `create_app()` runs, then the Bolt app is initialized (handlers registered) but `SocketModeHandler` is never constructed and no WebSocket connection is opened.
- [ ] AC 10: Given gunicorn runs with `--workers 1 --threads 2` in the Dockerfile, when the app container starts, then exactly one Socket Mode WebSocket connection is established (no duplicate event processing) and the web UI handles concurrent requests via threads.
- [ ] AC 11: Given `SocketModeHandler.connect()` raises an exception (e.g., invalid token, network failure), when the app starts, then a warning is logged, `_socket_handler` is set to `None`, and the Flask app continues running normally without Slack integration.
- [ ] AC 12: Given the app is running with Socket Mode connected, when the app receives SIGTERM (e.g., `docker compose stop`), then `_socket_handler.close()` is called via the SIGTERM signal handler (and/or `atexit` handler) to cleanly disconnect the WebSocket.
- [ ] AC 13: Given `app.config['TESTING']` is `True`, when `init_slack()` runs with valid tokens, then the Bolt app is initialized but `SocketModeHandler` is never constructed (no real WebSocket in tests).
- [ ] AC 14: Given `requirements.txt`, when dependencies are installed, then `websocket-client>=1.6.0` is present and used by `slack_sdk.socket_mode` as the WebSocket transport.

## Additional Context

### Dependencies

- **New package: `websocket-client>=1.6.0`** (F3). Slack's documentation recommends this for production Socket Mode. The built-in `slack_sdk` WebSocket client has known stability limitations. When `websocket-client` is installed, `slack_sdk.socket_mode` automatically uses it as the transport.
- **Existing packages sufficient:** `slack-bolt>=1.27.0` includes `slack_bolt.adapter.socket_mode.SocketModeHandler`. `slack_sdk>=3.39.0` includes `slack_sdk.socket_mode`.
- **Slack App must be reconfigured:** Socket Mode must be enabled in the Slack App settings at api.slack.com, and an App-Level Token with `connections:write` scope must be generated. This is a one-time admin action documented in the updated admin guide.
- **Slack plan requirements:** Verify current Slack plan requirements for Socket Mode at setup time. Slack has historically required a paid plan (Pro or higher) for Socket Mode, but requirements may have changed. The admin guide should not make blanket assertions about plan requirements (F10).

### Testing Strategy

**Unit Tests (automated):**
- Update `tests/test_slack/test_init.py` to verify Socket Mode initialization:
  - `SocketModeHandler` constructed with correct `app_token`
  - `.connect()` called on the handler
  - `atexit.register` called with `_shutdown_socket`
  - No HTTP routes registered
  - Graceful skip when tokens missing
  - Graceful skip when `SLACK_SOCKET_MODE_CONNECT` is not `'true'` (Bolt app still initialized, no socket)
  - Graceful degradation when `connect()` raises an exception
  - Testing mode skips `connect()`
  - Teardown resets `_socket_handler = None` (F8)
- All handler tests in `tests/test_slack/test_handlers.py` remain unchanged — they test business logic, not transport.

**Manual Testing:**
- Deploy with Socket Mode enabled and verify all four slash commands work: `/esb-report`, `/esb-repair`, `/esb-update`, `/esb-status`
- Verify modal submissions complete successfully
- Verify notification delivery still works (background worker is unchanged)
- Verify the app starts cleanly with Slack disabled (no tokens set)
- Verify worker container logs show "SLACK_SOCKET_MODE_CONNECT is not true, skipping Socket Mode connection"
- Verify only one WebSocket connection in app container (single gunicorn worker)

**Regression:**
- Run `make test` — all existing tests must pass
- Run `make lint` — no ruff violations

### Notes

- **Gunicorn single worker with threads:** Changed from `--workers 2` to `--workers 1 --threads 2` to prevent duplicate Socket Mode event processing (F1). Slack sends events to ALL active WebSocket connections, not load-balanced. One process with threads gives concurrent web handling without multiple socket connections. If higher concurrency is ever needed, increase `--threads` (not `--workers`), or run Socket Mode in a dedicated container.
- **Connection resilience:** `SocketModeHandler` includes built-in reconnection logic. If the WebSocket drops, it automatically reconnects. No additional retry logic needed.
- **Opt-in socket connection:** Socket connection is opt-in — only the app container sets `SLACK_SOCKET_MODE_CONNECT=true` (R2-F11). The worker and any future services safely skip connection by default. The Bolt app is still initialized (handlers registered) but unused — this is harmless and avoids conditional import complexity.
- **Graceful shutdown:** Both `atexit` and explicit `SIGTERM` signal handler call `_shutdown_socket()` (F4, R2-F1). The SIGTERM handler chains to any previous handler. Docker sends SIGTERM on `docker compose stop/restart`, giving gunicorn time to shut down cleanly before SIGKILL. The explicit signal handler also covers non-gunicorn environments (Flask dev server via `make run`).
- **Connect failure resilience:** If `connect()` fails (bad token, network), the app logs a warning and starts without Slack (F12). This prevents a Slack outage from taking down the entire web application.
- **SIGTERM handler ordering (R3-F7):** `init_slack()` registers a SIGTERM handler during `create_app()`. The notification worker's `run_worker_loop()` registers its own SIGTERM handler AFTER `create_app()` returns. If the worker ever enables socket mode (by setting `SLACK_SOCKET_MODE_CONNECT=true`), the worker's SIGTERM handler would replace the socket handler without chaining. The opt-in design prevents this today, but do NOT enable socket mode in the worker without addressing this ordering constraint.
- **Notification service unaffected (R3-F8):** The notification service (`esb/services/notification_service.py`) creates `slack_sdk.WebClient` instances directly with `SLACK_BOT_TOKEN` for sending messages. This is independent of the Bolt app and Socket Mode transport. No changes needed to notification delivery.
