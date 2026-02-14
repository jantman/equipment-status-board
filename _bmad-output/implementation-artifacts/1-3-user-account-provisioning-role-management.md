# Story 1.3: User Account Provisioning & Role Management

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member,
I want to create user accounts and assign roles,
So that Technicians and other Staff can access the system.

## Acceptance Criteria

1. **Given** I am logged in as Staff **When** I navigate to the User Management page (/admin/users) **Then** I see a table listing all users with columns for username, email, role, and status

2. **Given** I am on the User Management page **When** I click "Add User" and fill in username, email, Slack handle, select a role (Technician or Staff), and submit **Then** a new user account is created with a system-generated temporary password

3. **Given** a new user is created and Slack credentials are configured **When** the account is created **Then** the system attempts to deliver the temporary password via Slack direct message to the user's Slack handle

4. **Given** Slack delivery fails or Slack is not configured **When** the account is created **Then** the temporary password is displayed on-screen to the creating Staff member with a one-time visibility warning

5. **Given** I am logged in as Staff **When** I change a user's role from Technician to Staff (or vice versa) on the User Management page **Then** the role change is saved immediately and reflected in the user list

6. **Given** I am logged in as a Technician **When** I try to access /admin/users **Then** I receive a 403 Forbidden error

7. **Given** any user management action (create, role change) **When** the action is performed **Then** a mutation log entry is written to STDOUT with the action details

## Tasks / Subtasks

- [ ] Task 1: Create user_service module (AC: #2, #3, #4, #7)
  - [ ] 1.1: Create `esb/services/user_service.py` with `create_user()`, `list_users()`, `change_role()`, `get_user()`
  - [ ] 1.2: `create_user(username, email, role, slack_handle, created_by)` validates uniqueness of username and email, raises `ValidationError` on conflicts
  - [ ] 1.3: `create_user()` generates a cryptographically secure temporary password using `secrets.token_urlsafe(12)` (produces 16-char URL-safe string)
  - [ ] 1.4: `create_user()` returns a dict/tuple containing the User object, the plaintext temp password, and a `slack_delivered` boolean
  - [ ] 1.5: `create_user()` attempts Slack DM delivery if `SLACK_BOT_TOKEN` is configured and user has a `slack_handle` -- calls internal `_deliver_temp_password_via_slack()`
  - [ ] 1.6: `create_user()` logs mutation event `user.created` with user details (NEVER the password)
  - [ ] 1.7: `change_role(user_id, new_role, changed_by)` validates new role is 'technician' or 'staff', updates user, logs `user.role_changed`
  - [ ] 1.8: `list_users()` returns all users ordered by username
  - [ ] 1.9: `get_user(user_id)` returns a single User or raises `ValidationError` if not found
  - [ ] 1.10: Write service tests in `tests/test_services/test_user_service.py`

- [ ] Task 2: Implement Slack temp password delivery helper (AC: #3, #4)
  - [ ] 2.1: Create `_deliver_temp_password_via_slack(user, temp_password)` in user_service
  - [ ] 2.2: Guard import: `try: from slack_sdk import WebClient` with fallback if not installed
  - [ ] 2.3: If `SLACK_BOT_TOKEN` not configured or slack_sdk not installed, return `False` immediately
  - [ ] 2.4: Lookup Slack user: call `users_lookupByEmail(email=user.email)` to get Slack user ID
  - [ ] 2.5: Open DM: call `conversations_open(users=[slack_user_id])` to get DM channel
  - [ ] 2.6: Send message: call `chat_postMessage(channel=dm_channel_id, text=message)` with temp password
  - [ ] 2.7: Catch ALL Slack exceptions (SlackApiError, network errors) -- log warning, return `False`
  - [ ] 2.8: On success return `True`; NEVER block user creation on Slack failures

- [ ] Task 3: Create admin forms (AC: #2, #5)
  - [ ] 3.1: Create `esb/forms/admin_forms.py` with `UserCreateForm`
  - [ ] 3.2: `UserCreateForm` fields: username (StringField, required), email (StringField, required), slack_handle (StringField, optional), role (SelectField with choices [('technician', 'Technician'), ('staff', 'Staff')])
  - [ ] 3.3: Add validators: DataRequired on username and email, Email validator on email field
  - [ ] 3.4: Create `RoleChangeForm` with role SelectField and hidden user_id for inline role change on user list

- [ ] Task 4: Implement admin user management views (AC: #1, #2, #4, #5, #6)
  - [ ] 4.1: Replace stub in `esb/views/admin.py` with full user management implementation
  - [ ] 4.2: `GET /admin/users` -- list all users in a table, protected by `@role_required('staff')`
  - [ ] 4.3: `GET/POST /admin/users/new` -- render user creation form (GET), process submission (POST)
  - [ ] 4.4: On successful creation: call `user_service.create_user()` which returns user, temp_password, slack_delivered
  - [ ] 4.5: If `slack_delivered == True`: flash success "User created. Temporary password sent via Slack DM." and redirect to user list
  - [ ] 4.6: If `slack_delivered == False`: redirect to `GET /admin/users/<id>/created` -- one-time temp password display page
  - [ ] 4.7: `GET /admin/users/<int:id>/created` -- one-time password display page. Temp password passed via session flash or session variable (cleared after display)
  - [ ] 4.8: `POST /admin/users/<int:id>/role` -- change user role, flash success, redirect to user list
  - [ ] 4.9: All routes protected by `@role_required('staff')`
  - [ ] 4.10: On ValidationError from service: flash error as 'danger' and re-render form

- [ ] Task 5: Create admin templates (AC: #1, #2, #4)
  - [ ] 5.1: Create `esb/templates/admin/users.html` -- extends `base.html`, table of users with columns: username, email, role, status (Active/Inactive), actions
  - [ ] 5.2: Table includes inline role change form per row (dropdown + small submit button)
  - [ ] 5.3: "Add User" button (btn-primary) at top of user list
  - [ ] 5.4: Create `esb/templates/admin/user_create.html` -- extends `base.html`, user creation form following UX form patterns (single-column, labels above fields, required fields marked with *)
  - [ ] 5.5: Create `esb/templates/admin/user_created.html` -- extends `base.html`, one-time temp password display with prominent warning: "This password will only be shown once. Please ensure the user receives it."
  - [ ] 5.6: Password display uses a styled card/alert with the password in monospace font
  - [ ] 5.7: "Back to Users" button on the password display page

- [ ] Task 6: Write view and integration tests (AC: all)
  - [ ] 6.1: Create `tests/test_views/test_admin_views.py`
  - [ ] 6.2: Test GET /admin/users renders user table for staff
  - [ ] 6.3: Test technician gets 403 on GET /admin/users
  - [ ] 6.4: Test unauthenticated user redirected to login on GET /admin/users
  - [ ] 6.5: Test GET /admin/users/new renders creation form for staff
  - [ ] 6.6: Test POST /admin/users/new with valid data creates user
  - [ ] 6.7: Test POST /admin/users/new with duplicate username shows error
  - [ ] 6.8: Test POST /admin/users/new with duplicate email shows error
  - [ ] 6.9: Test POST /admin/users/new with missing required fields shows validation errors
  - [ ] 6.10: Test POST /admin/users/<id>/role changes role successfully
  - [ ] 6.11: Test POST /admin/users/<id>/role with invalid role shows error
  - [ ] 6.12: Test mutation logging for user.created event
  - [ ] 6.13: Test mutation logging for user.role_changed event
  - [ ] 6.14: Test temp password display page shows password when Slack not configured
  - [ ] 6.15: Add service tests in `tests/test_services/test_user_service.py` for all service functions

- [ ] Task 7: Add slack_sdk dependency (AC: #3)
  - [ ] 7.1: Add `slack_sdk>=3.39.0` to `requirements.txt`
  - [ ] 7.2: Add to `requirements-dev.txt` (inherits from requirements.txt)
  - [ ] 7.3: Guard all slack_sdk imports with try/except for environments without it installed

## Dev Notes

### Architecture Compliance

**CRITICAL -- Follow these patterns exactly:**

- **Service Layer Pattern:** All user management logic lives in `esb/services/user_service.py`. Views in `esb/views/admin.py` are thin -- parse form input, call service, render response. **No business logic in views.**
- **Dependency Flow:** `views/admin.py` -> `services/user_service.py` -> `models/user.py`. Never reverse.
- **Mutation Logging:** Log ALL user management events via `log_mutation()` in `esb/utils/logging.py`. Events: `user.created`, `user.role_changed`. **NEVER log passwords in mutation data.**
- **Error Handling:** Service raises `ValidationError` (from `esb/utils/exceptions.py`) for input problems. Views catch and flash as `'danger'`. Use existing exception hierarchy -- do NOT create new exception types.
- **RBAC:** All admin routes decorated with `@role_required('staff')` from `esb/utils/decorators.py`. This automatically includes `@login_required`.
- **Domain Exceptions:** Use existing `ValidationError` from `esb/utils/exceptions.py` for all validation failures (duplicate username, invalid role, etc.).

### Technical Stack -- Key Details

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Temp password generation | `secrets` (stdlib) | Built-in | `secrets.token_urlsafe(12)` produces 16-char URL-safe string |
| Password hashing | Werkzeug | 3.1.x (built-in) | `user.set_password(temp_password)` -- scrypt default. Do NOT specify method. |
| Forms/CSRF | Flask-WTF | 1.2.2 | `FlaskForm`, `form.validate_on_submit()`. CSRF token auto-included. |
| Slack SDK | `slack_sdk` | >=3.39.0 | Optional dependency -- guard all imports with try/except. |
| Database | SQLAlchemy | via Flask-SQLAlchemy 3.1.1 | `db.session.execute(db.select(User))` pattern. `db.session.get(User, id)` for PK lookups. |
| Auth/Sessions | Flask-Login | 0.6.3 | Use existing `current_user` in views for logging `changed_by`. |

### Slack DM Delivery Details

**Delivery Flow:**
1. Check if `slack_sdk` is importable (try/except at module level)
2. Check if `current_app.config['SLACK_BOT_TOKEN']` is configured (non-empty string)
3. If not configured or sdk not available: return `slack_delivered=False`
4. If configured and user has `slack_handle`:
   a. Initialize `WebClient(token=current_app.config['SLACK_BOT_TOKEN'])`
   b. Call `users_lookupByEmail(email=user.email)` to get Slack user ID
   c. Call `conversations_open(users=[slack_user_id])` to get DM channel ID
   d. Call `chat_postMessage(channel=dm_channel_id, text=message)` with temp password message
5. If ANY Slack API call fails: catch exception, log warning to app logger, return `slack_delivered=False`
6. On success: return `slack_delivered=True`

**IMPORTANT:** The Slack DM delivery is best-effort for this story. The primary delivery path is the on-screen fallback. Full Slack App integration comes in Epic 6. Do NOT add complexity around retry logic for Slack delivery -- that's the notification queue's job (Epic 5).

**Required Slack Bot Scopes (for reference -- not configured in this story):**
- `users:read.email` -- to lookup user by email
- `im:write` -- to open DM conversations
- `chat:write` -- to send messages

### Temporary Password Security

- Generate with `secrets.token_urlsafe(12)` -- produces a 16-character cryptographically secure URL-safe string
- Hash immediately using `user.set_password(temp_password)` before saving to DB
- The plaintext temp password exists only in memory during the create flow
- If delivered via Slack: plaintext is sent in the DM message, then discarded from server memory
- If displayed on-screen: passed to template via session variable, cleared after display
- **NEVER store the plaintext temp password** in the database, logs, or any persistent storage
- The one-time display page (`user_created.html`) should include a prominent warning that the password will not be shown again

### Previous Story Intelligence (from Story 1.2)

**What was built in Stories 1.1 and 1.2:**
- Flask app factory in `esb/__init__.py` with `create_app(config_name)`
- Extensions in `esb/extensions.py`: `db`, `login_manager`, `migrate`, `csrf`
- User model in `esb/models/user.py` with UserMixin, password hashing (scrypt), role field
- Auth service in `esb/services/auth_service.py`: `authenticate()`, `load_user()`
- LoginForm in `esb/forms/auth_forms.py`
- Auth views in `esb/views/auth.py`: login (with `next` parameter, open redirect prevention), logout
- RBAC decorator in `esb/utils/decorators.py`: `@role_required(role)` with Staff > Technician hierarchy
- Mutation logger in `esb/utils/logging.py`: `log_mutation(event, user, data)` -- **uses `propagate=False` so tests need custom `_CaptureHandler`, NOT `caplog`**
- Domain exceptions in `esb/utils/exceptions.py`: `ESBError`, `ValidationError`, etc.
- Base templates: `base.html` (authenticated with navbar), `base_public.html` (public, no nav)
- Error templates: `errors/403.html`, `errors/404.html`, `errors/500.html`
- Admin blueprint stub: `esb/views/admin.py` with placeholder `/admin/` route (text only, no template)
- Test fixtures: `staff_user`, `tech_user`, `staff_client`, `tech_client` in `tests/conftest.py`
- CLI: `flask seed-admin` for initial admin creation
- Config: `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` already in config.py (both default to empty string)
- 108 tests passing, ruff lint clean

**Key learnings from Story 1.2 dev notes:**
- `ruff target-version = "py314"` is not supported -- use `"py313"` in ruff config
- Mutation logger `propagate = False` -- tests must use custom `_CaptureHandler` pattern (see `tests/test_views/test_auth_views.py` for the exact implementation)
- Error templates extend `base_public.html` to avoid `current_user` dependency during DB errors
- Flash category is `'danger'` (not `'error'`) per Bootstrap alert classes
- `db.session.execute(db.select(User).filter_by(...)).scalar_one_or_none()` for queries
- `db.session.get(User, id)` for primary key lookups
- Constant-time dummy hash comparison in auth_service for username enumeration prevention
- Login view supports `next` parameter with open redirect prevention (check `urlparse(next_page).netloc == ''`)

### Git Intelligence

**Recent commits (newest first):**
1. `50b63f1` Fix code review issues for Story 1.2 authentication system
2. `75bfd4e` Implement Story 1.2: User authentication system with login/logout and RBAC
3. `11d37cb` Create Story 1.2: User Authentication System context for dev agent
4. `6ed1dc8` Implement Story 1.1: Project scaffolding & Docker deployment

**Patterns established:**
- Views follow thin pattern: parse input -> call service -> flash message -> redirect/render
- Service functions accept primitive types, return model instances, raise domain exceptions
- All mutations logged via `log_mutation(event, user, data)` -- never in views directly (call from service or view after service call)
- Tests organized in `test_models/`, `test_services/`, `test_views/` mirroring `esb/` structure
- 108 existing tests -- run `make test` or `pytest tests/ -v` to verify no regressions

### Latest Tech Information

**slack_sdk 3.39.0** (latest stable as of Feb 2026):
- `WebClient` for API calls: `chat_postMessage`, `users_lookupByEmail`, `conversations_open`
- All API methods return `SlackResponse` objects
- Errors raised as `slack_sdk.errors.SlackApiError`
- Thread-safe client -- can be initialized per-request or as a singleton
- For this story: initialize per-request inside `_deliver_temp_password_via_slack()` using `current_app.config['SLACK_BOT_TOKEN']`

**Python `secrets` module** (stdlib):
- `secrets.token_urlsafe(nbytes)` -- generates URL-safe Base64 string. `nbytes=12` produces 16 characters.
- Cryptographically secure -- uses OS-level randomness
- Do NOT use `random` module for password generation

### File Structure Requirements

**New files to create:**
```
esb/
  services/
    user_service.py             # User provisioning, role management, Slack DM delivery
  forms/
    admin_forms.py              # UserCreateForm, RoleChangeForm
  templates/
    admin/
      users.html                # User management table listing all users
      user_create.html          # User creation form
      user_created.html         # One-time temp password display page
tests/
  test_services/
    test_user_service.py        # User service tests
  test_views/
    test_admin_views.py         # Admin view tests
```

**Files to modify:**
```
esb/views/admin.py              # Replace stub with full user management routes
requirements.txt                # Add slack_sdk>=3.39.0
requirements-dev.txt            # Inherits from requirements.txt (no change needed if -r used)
```

### User Service Contract

```python
# esb/services/user_service.py

def create_user(username: str, email: str, role: str,
                slack_handle: str | None = None,
                created_by: str = 'system') -> tuple[User, str, bool]:
    """
    Create a new user with a system-generated temporary password.

    Returns:
        Tuple of (user, temp_password, slack_delivered).
        - user: the created User instance
        - temp_password: the plaintext temporary password (for one-time display if Slack fails)
        - slack_delivered: True if password was sent via Slack DM

    Raises:
        ValidationError: if username or email already exists, or role is invalid.
    """

def list_users() -> list[User]:
    """Return all users ordered by username."""

def get_user(user_id: int) -> User:
    """
    Get a single user by ID.

    Raises:
        ValidationError: if user not found.
    """

def change_role(user_id: int, new_role: str, changed_by: str) -> User:
    """
    Change a user's role.

    Raises:
        ValidationError: if user not found or role is invalid.
    """
```

### Admin View Routes

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET | `/admin/users` | `list_users()` | User management table |
| GET | `/admin/users/new` | `create_user()` | User creation form |
| POST | `/admin/users/new` | `create_user()` | Process user creation |
| GET | `/admin/users/<int:id>/created` | `user_created()` | One-time temp password display |
| POST | `/admin/users/<int:id>/role` | `change_role()` | Change user role |

### Naming Conventions

**Python:**
- Service functions: `create_user()`, `list_users()`, `change_role()`, `get_user()`, `_deliver_temp_password_via_slack()` (snake_case, private helper prefixed with `_`)
- Form classes: `UserCreateForm`, `RoleChangeForm` (PascalCase)
- View functions: `list_users()`, `create_user()`, `change_role()`, `user_created()` (snake_case)

**Routes:**
- `/admin/users` (GET) -- list users
- `/admin/users/new` (GET+POST) -- create user
- `/admin/users/<int:id>/created` (GET) -- temp password display
- `/admin/users/<int:id>/role` (POST) -- change role

**Templates:**
- `admin/users.html`, `admin/user_create.html`, `admin/user_created.html` (snake_case, per-blueprint directory)

### Mutation Logging Events

| Event | When | Data |
|-------|------|------|
| `user.created` | New user account provisioned | `{"user_id": id, "username": "...", "email": "...", "role": "...", "slack_handle": "...", "slack_delivered": true/false}` |
| `user.role_changed` | Role changed | `{"user_id": id, "username": "...", "old_role": "...", "new_role": "..."}` |

**NEVER log passwords in mutation data!**

### Testing Strategy

- **Test DB:** SQLite in-memory (`TestingConfig`) -- CSRF disabled in test config
- **Auth fixtures:** Use existing `staff_client` and `tech_client` from `tests/conftest.py`
- **Mutation logger tests:** Use custom `_CaptureHandler` pattern from `tests/test_views/test_auth_views.py` (mutation logger has `propagate=False` so `caplog` does NOT work)
- **Slack tests:** Mock `slack_sdk.WebClient` in tests using `unittest.mock.patch` -- never make real API calls
- **User creation in tests:** Use existing `_create_user()` helper from conftest for setup; test the service's `create_user()` for the actual feature

**Test coverage targets:**
- User service: create (valid, duplicate username, duplicate email, invalid role, missing fields), list, get (found, not found), change_role (valid, invalid role, user not found)
- Admin views: list users (staff OK, tech 403, unauth redirect), create user form renders (GET), create user with valid data (POST), create user with duplicate username, create user with duplicate email, role change success, role change invalid, temp password display page
- Mutation logging: verify `user.created` event logged on creation, verify `user.role_changed` event logged on role change
- Slack delivery: mock Slack SDK, test success path (returns True), test failure path (returns False), test not-configured path (returns False)

### Security Considerations

- **Never log temporary passwords** in mutation logs, app logs, or any output
- **Temp passwords are cryptographically secure** -- generated with `secrets.token_urlsafe(12)`
- **On-screen password display is one-time** -- passed via session, cleared after display. The user_created template should warn that the password will not be shown again.
- **User creation is Staff-only** -- enforced server-side via `@role_required('staff')`
- **Slack DM delivery is best-effort** -- failures are graceful, never blocking
- **No rate limiting in v1.0** -- per architecture doc. Can be added later if needed.
- **Input validation:** Username uniqueness and email uniqueness checked server-side before creation

### UX Notes (from UX Design Specification)

Per the UX spec and Journey 4 (Staff Manages Equipment & Users):
- User Management page at `/admin/users` -- table with columns: username, email, role, status
- "Add User" button (btn-primary) at top of user list
- User creation form: single-column, labels above fields, required fields marked with asterisk (*)
- Form follows UX form patterns: validate on submit, inline errors below fields, no auto-save
- On creation: temp password delivered via Slack DM (preferred) or shown on-screen to creator (fallback)
- Role change: inline dropdown on the user list table row, immediate save on submit
- Button hierarchy: "Create User" is `btn-primary`, "Cancel" is `btn-outline-secondary`
- Flash messages: `'success'` for successful operations, `'danger'` for errors (maps to Bootstrap `alert-success` / `alert-danger`)
- Staff navbar includes: Kanban, Repair Queue, Equipment, Users, Status Dashboard -- "Users" link should highlight as active on admin pages
- Empty state: show existing users table (at minimum, the current Staff user) with "Add User" always visible

### Project Structure Notes

- `esb/services/user_service.py` is a NEW file -- the `esb/services/` directory exists but only contains `__init__.py` (empty) and `auth_service.py`
- `esb/forms/admin_forms.py` is a NEW file -- the `esb/forms/` directory exists with `__init__.py` (empty) and `auth_forms.py`
- `esb/templates/admin/` directory EXISTS but is EMPTY -- all three templates are new
- `esb/views/admin.py` EXISTS with a minimal stub (single placeholder route returning text) -- must be REPLACED with full implementation
- No database migration needed -- the User model and `users` table already exist from Story 1.2
- `requirements.txt` needs `slack_sdk>=3.39.0` added

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.3: User Account Provisioning & Role Management]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns - Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns - Project Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#Project Structure & Boundaries]
- [Source: _bmad-output/planning-artifacts/prd.md#User Management & Authentication (FR45-FR51)]
- [Source: _bmad-output/planning-artifacts/prd.md#Security (NFR5-NFR9)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Navigation Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4: Staff Manages Equipment & Users]
- [Source: _bmad-output/implementation-artifacts/1-2-user-authentication-system.md#Dev Notes]
- [Source: _bmad-output/implementation-artifacts/1-2-user-authentication-system.md#Code Review Fixes Applied]

## Dev Agent Record

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List
