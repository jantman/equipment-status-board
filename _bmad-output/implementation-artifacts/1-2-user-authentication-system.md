# Story 1.2: User Authentication System

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a Staff member or Technician,
I want to log in with a username and password,
So that I can access role-appropriate functionality securely.

## Acceptance Criteria

1. **Given** the User model exists with username, email, password_hash, role, slack_handle, and is_active fields **When** Alembic migration is run **Then** the users table is created in MariaDB

2. **Given** I am on the login page **When** I submit valid credentials (username + password) **Then** I am authenticated via Flask-Login and redirected to a placeholder landing page

3. **Given** I am logged in **When** I click logout **Then** my session is terminated and I am redirected to the login page

4. **Given** my session is older than 12 hours **When** I make any request **Then** I am redirected to the login page with my session expired

5. **Given** I am not authenticated **When** I try to access any route decorated with @login_required or @role_required **Then** I am redirected to the login page

6. **Given** I am authenticated as a Technician **When** I try to access a route decorated with @role_required('staff') **Then** I receive a 403 Forbidden error page

7. **Given** the auth_service module **When** authentication is performed **Then** it goes through the auth_service interface (authenticate(username, password) -> User, load_user(user_id) -> User)

8. **Given** a user's password **When** it is stored in the database **Then** it is hashed using Werkzeug's generate_password_hash (never plaintext)

## Tasks / Subtasks

- [x] Task 1: Create User model (AC: #1)
  - [x] 1.1: Create `esb/models/user.py` with User model implementing Flask-Login's UserMixin
  - [x] 1.2: Fields: id (PK), username (unique, not null), email (unique, not null), password_hash (not null), role (not null, default 'technician'), slack_handle (nullable), is_active (boolean, default True), created_at, updated_at
  - [x] 1.3: Add `set_password(password)` and `check_password(password)` methods using Werkzeug
  - [x] 1.4: Import User in `esb/models/__init__.py` for Alembic discovery
  - [x] 1.5: Generate Alembic migration for users table
  - [x] 1.6: Write model tests in `tests/test_models/test_user.py`

- [x] Task 2: Create auth_service module (AC: #7, #8)
  - [x] 2.1: Create `esb/services/auth_service.py` with `authenticate(username, password) -> User` and `load_user(user_id) -> User`
  - [x] 2.2: `authenticate()` queries User by username, checks password via `check_password()`, raises `ValidationError` on failure
  - [x] 2.3: `authenticate()` checks `is_active` flag before allowing login
  - [x] 2.4: `load_user()` queries User by ID, returns None if not found or inactive
  - [x] 2.5: Write service tests in `tests/test_services/test_auth_service.py`

- [x] Task 3: Create login form (AC: #2)
  - [x] 3.1: Create `esb/forms/auth_forms.py` with `LoginForm` (username, password, submit fields)
  - [x] 3.2: Add required validators on username and password fields

- [x] Task 4: Implement login view (AC: #2, #5)
  - [x] 4.1: Replace stub in `esb/views/auth.py` with full login route (GET: render form, POST: validate + authenticate)
  - [x] 4.2: On successful login, call `flask_login.login_user()` with `remember=False`
  - [x] 4.3: Set `session.permanent = True` to enable PERMANENT_SESSION_LIFETIME (12 hours)
  - [x] 4.4: Redirect to a placeholder landing page (e.g., `/health` or a simple authenticated home) after login
  - [x] 4.5: On failed login, flash error message and re-render login form
  - [x] 4.6: Create `esb/templates/auth/login.html` extending `base_public.html` -- centered card layout, no navbar

- [x] Task 5: Implement logout view (AC: #3)
  - [x] 5.1: Replace stub logout route with `flask_login.logout_user()` call
  - [x] 5.2: Flash "You have been logged out." message
  - [x] 5.3: Redirect to login page

- [x] Task 6: Update user_loader in app factory (AC: #5, #7)
  - [x] 6.1: Replace placeholder `user_loader` in `esb/__init__.py` with call to `auth_service.load_user()`
  - [x] 6.2: Ensure login_manager.login_view is 'auth.login' (already set in extensions.py)
  - [x] 6.3: Set login_manager.login_message_category to 'warning'

- [x] Task 7: Session timeout enforcement (AC: #4)
  - [x] 7.1: Implement `@app.before_request` handler that sets `session.permanent = True` on every request to ensure Flask uses PERMANENT_SESSION_LIFETIME
  - [x] 7.2: Verify PERMANENT_SESSION_LIFETIME = 43200 (12 hours) in config.py (already set)

- [x] Task 8: RBAC integration verification (AC: #5, #6)
  - [x] 8.1: Verify existing `@role_required` decorator works with the new User model (expects `current_user.role`)
  - [x] 8.2: Create a test-only protected route to verify @login_required redirects to login
  - [x] 8.3: Create a test-only staff-protected route to verify @role_required('staff') returns 403 for Technicians
  - [x] 8.4: Update existing RBAC decorator tests to use real User model instances

- [x] Task 9: Create seed data utility (supporting)
  - [x] 9.1: Create a Flask CLI command `flask seed-admin` that creates an initial Staff user if none exists
  - [x] 9.2: Command accepts username, email, and password as arguments
  - [x] 9.3: This supports development and initial deployment -- no user provisioning UI exists yet (that's Story 1.3)

- [x] Task 10: Write view and integration tests (AC: all)
  - [x] 10.1: Write tests in `tests/test_views/test_auth_views.py` covering:
    - Login page renders (GET)
    - Successful login redirects
    - Failed login shows error
    - Logout clears session
    - Unauthenticated access redirects to login
    - Technician accessing staff route gets 403
  - [x] 10.2: Add authenticated client fixtures to `tests/conftest.py` (staff_client, technician_client factory helpers)
  - [x] 10.3: Write mutation logging tests for auth events

## Dev Notes

### Architecture Compliance

**CRITICAL -- Follow these patterns exactly:**

- **Service Layer Pattern:** Auth logic lives in `esb/services/auth_service.py`. The view in `esb/views/auth.py` is thin -- parse form input, call `auth_service.authenticate()`, call `flask_login.login_user()`, render response. **No business logic in views.**
- **Dependency Flow:** `views/auth.py` -> `services/auth_service.py` -> `models/user.py`. Never reverse.
- **Mutation Logging:** Log all auth events via the mutation logger in `esb/utils/logging.py`. Events: `user.login`, `user.logout`, `user.login_failed`. Do NOT log passwords in mutation log data.
- **Error Handling:** `auth_service.authenticate()` raises `ValidationError` (from `esb/utils/exceptions.py`) on invalid credentials. The view catches this and flashes an error message. Do NOT expose whether the username or password was wrong (security best practice -- use generic "Invalid username or password" message).
- **Domain Exceptions:** Use existing `ValidationError` from `esb/utils/exceptions.py`. Do NOT create new exception types for auth failures.

### Technical Stack -- Key Details

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Auth/Sessions | Flask-Login | 0.6.3 | Installed in Story 1.1. 0.7.0 exists but was not available at install time. Use 0.6.3 APIs. |
| Password hashing | Werkzeug | 3.1.x (built-in) | **DEFAULT ALGORITHM IS NOW `scrypt` (not pbkdf2)**. Use default -- do NOT explicitly set method='pbkdf2'. |
| Forms/CSRF | Flask-WTF | 1.2.x | Use `FlaskForm`, `form.validate_on_submit()`. CSRF token auto-included. |
| Database | SQLAlchemy | via Flask-SQLAlchemy 3.1.x | `db.session.get(User, id)` for primary key lookups. |

**IMPORTANT -- Werkzeug Password Hashing Change:**
The architecture doc mentions `pbkdf2:sha256` but Werkzeug 3.x defaults to `scrypt`, which is a memory-hard algorithm providing better security. Use the default by calling `generate_password_hash(password)` without specifying method. `check_password_hash()` auto-detects the algorithm from the stored hash, so this is backward-compatible.

### Previous Story Intelligence (from Story 1.1)

**What was built:**
- Flask app factory in `esb/__init__.py` with `create_app(config_name)`
- Extension instances in `esb/extensions.py`: `db`, `login_manager`, `migrate`, `csrf`
- `login_manager.login_view = 'auth.login'` already configured
- RBAC decorators in `esb/utils/decorators.py` -- `@role_required(role)` with hierarchy Staff > Technician
- Mutation logger in `esb/utils/logging.py` -- `log_mutation(event, user, data)`
- Domain exceptions in `esb/utils/exceptions.py` -- `ESBError`, `ValidationError`, etc.
- Base templates: `base.html` (authenticated), `base_public.html` (public), `base_kiosk.html` (kiosk)
- Error templates in `esb/templates/errors/` extending `base_public.html`
- Auth blueprint stub in `esb/views/auth.py` with placeholder routes
- `esb/models/__init__.py` is EMPTY -- no models defined yet
- Alembic initialized but NO migration versions exist yet
- Tests use SQLite in-memory (`TestingConfig`)
- 55 tests passing, ruff lint clean
- Config: `PERMANENT_SESSION_LIFETIME = 43200` (12 hours) already set

**Key learnings from Story 1.1 dev notes:**
- `ruff target-version = "py314"` is not supported -- use `"py313"` in ruff config
- Mutation logger uses `propagate = False` -- tests need custom `_CaptureHandler` (not `caplog`) to capture mutation log output
- Error templates extend `base_public.html` to avoid `current_user` dependency during DB errors
- Placeholder `user_loader` returns `None` -- must be replaced with real implementation

**Files to modify (from Story 1.1):**
- `esb/__init__.py` -- replace placeholder user_loader
- `esb/views/auth.py` -- replace stub routes with real implementation
- `esb/models/__init__.py` -- import User model
- `tests/conftest.py` -- add authenticated client fixtures

### File Structure Requirements

**New files to create:**
```
esb/
  models/
    user.py                    # User model (UserMixin)
  services/
    auth_service.py            # Authentication service
  forms/
    auth_forms.py              # LoginForm
  templates/
    auth/
      login.html               # Login page template
tests/
  test_models/
    test_user.py               # User model tests
  test_services/
    test_auth_service.py       # Auth service tests
  test_views/
    test_auth_views.py         # Auth view tests
migrations/
  versions/
    xxxx_create_users_table.py # Auto-generated by flask db migrate
```

**Files to modify:**
```
esb/__init__.py                # Replace user_loader
esb/models/__init__.py         # Import User
esb/views/auth.py              # Replace stubs with real routes
tests/conftest.py              # Add auth test fixtures
```

### User Model Specification

```python
class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='technician')
    slack_handle = db.Column(db.String(80), nullable=True)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC))
    updated_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
                           onupdate=lambda: datetime.now(UTC))
```

**Key design decisions:**
- `password_hash` column is `String(256)` to accommodate scrypt hashes (which are longer than pbkdf2)
- `role` is a simple string column ('technician' or 'staff') -- not an enum, to keep flexibility for future role additions
- `is_active` enables soft-disable of accounts without deletion
- `UserMixin` provides `is_authenticated`, `is_active`, `is_anonymous`, `get_id()` for Flask-Login. **Note:** UserMixin's `is_active` property returns True by default; our column overrides this.
- Timestamps use `datetime.now(UTC)` (not `datetime.utcnow()` which is deprecated)

### Auth Service Contract

```python
# esb/services/auth_service.py

def authenticate(username: str, password: str) -> User:
    """
    Authenticate a user by username and password.

    Returns the User object on success.

    Raises:
        ValidationError: if credentials are invalid or account is inactive.
    """

def load_user(user_id: int) -> User | None:
    """
    Load a user by ID for Flask-Login's user_loader.

    Returns None if user not found or is inactive.
    """
```

### Login Page Design (from UX Spec)

Per the UX design specification:
- Standalone page with **no navbar** -- extends `base_public.html`
- Centered card with username + password fields + "Log In" button
- "Forgot your password? Contact an administrator." text below the form
- After login: redirect to role-appropriate default page (for now: placeholder landing page)
- Bootstrap `form-control` for inputs, `btn-primary` for submit
- Single-column layout, works at all viewport sizes
- Required fields marked with asterisk (*)
- Validation errors displayed inline below fields using Bootstrap `invalid-feedback`
- Flash messages for operation-level feedback (e.g., "Invalid username or password")

### Naming Conventions

**Database:**
- Table: `users` (plural, snake_case)
- Columns: `password_hash`, `slack_handle`, `is_active`, `created_at`, `updated_at`
- Booleans: `is_` prefix (`is_active`)
- Timestamps: UTC always, `DATETIME` type

**Python:**
- Model class: `User` (PascalCase)
- Service functions: `authenticate()`, `load_user()` (snake_case)
- Form class: `LoginForm` (PascalCase)

**Routes:**
- `/auth/login` (GET + POST)
- `/auth/logout` (GET or POST)

**Templates:**
- `auth/login.html` (snake_case, per-blueprint directory)

### Mutation Logging Events

| Event | When | Data |
|-------|------|------|
| `user.login` | Successful login | `{"user_id": id, "username": "..."}` |
| `user.logout` | User logs out | `{"user_id": id, "username": "..."}` |
| `user.login_failed` | Failed login attempt | `{"username": "..."}` (NO password!) |

### Testing Strategy

- **Test DB:** SQLite in-memory (`TestingConfig`) -- already configured
- **User creation in tests:** Create User instances directly in the test DB, set password via `set_password()` method
- **Authenticated client fixtures:** Create helper fixtures in `conftest.py` that log in a test user and return the client with an active session
- **CSRF in tests:** CSRF is disabled in TestingConfig (`WTF_CSRF_ENABLED = False`) -- already configured
- **Mutation logger tests:** Use custom `_CaptureHandler` pattern from Story 1.1 (not `caplog`)

**Test coverage targets:**
- User model: creation, password hashing/checking, is_active behavior, unique constraints
- Auth service: successful auth, wrong password, wrong username, inactive user
- Auth views: login page GET, successful POST, failed POST, logout, unauthenticated redirect, 403 for insufficient role
- Integration: full login->access protected route->logout flow

### Security Considerations

- **Never log passwords** in mutation logs or any output
- **Generic error messages** on login failure: "Invalid username or password" -- do not reveal whether the username exists
- **Session fixation prevention:** Flask-Login handles session ID regeneration on login by default
- **CSRF protection:** Flask-WTF CSRF is active for all form submissions (already configured in extensions.py)
- **Password storage:** Use Werkzeug defaults (scrypt) -- do NOT implement custom hashing
- **No rate limiting in v1.0:** Per architecture doc, no rate limiting is required. Can be added later if needed.

### Project Structure Notes

- This is the FIRST story that creates a database model. The initial Alembic migration will create the `users` table.
- After this story, the `models/__init__.py` file will no longer be empty.
- The `esb/templates/auth/` directory needs to be created (does not exist yet).
- The `esb/forms/auth_forms.py` file needs to be created (forms package exists but is empty except `__init__.py`).
- The `esb/services/auth_service.py` file needs to be created (services package exists but is empty except `__init__.py`).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.2: User Authentication System]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns - Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns - Project Organization]
- [Source: _bmad-output/planning-artifacts/prd.md#User Management & Authentication (FR45-FR51)]
- [Source: _bmad-output/planning-artifacts/prd.md#Security (NFR5-NFR9)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Navigation Patterns - Login Page]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- [Source: _bmad-output/implementation-artifacts/1-1-project-scaffolding-docker-deployment.md#Dev Notes]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6

### Debug Log References

- Flask-Login 0.6.3 `UserMixin.is_authenticated` delegates to `self.is_active`; SQLAlchemy column default not applied until flush, so tests must commit before checking `is_authenticated`
- Alembic autogenerate requires model imports in app factory; added `import esb.models` in `create_app()`
- Migration generated with SQLite (`DATABASE_URL=sqlite:///dev.db`) since MariaDB not available locally

### Completion Notes List

- All 10 tasks complete, all 8 acceptance criteria satisfied
- 108 tests passing (15 model + 9 service + 27 view/integration + 7 decorator + 3 CLI + 47 existing)
- ruff lint clean
- Werkzeug scrypt hashing used (default, not pbkdf2)
- `flask seed-admin` CLI command available for initial admin creation
- Task 8.4: RBAC decorator tests rewritten to use real User model instances (code review fix H1)

### Code Review Fixes Applied

- **H1:** Rewrote `test_decorators.py` to use real User model instances instead of MagicMock
- **H2:** Changed `scalar_one_or_none()` to `.scalars().first()` in seed-admin to handle multiple staff users
- **H3:** Created `tests/test_cli.py` with 3 tests for seed-admin CLI command
- **M1:** Changed seed-admin password from positional argument to `click.option(prompt=True, hide_input=True)`
- **M2:** Added constant-time dummy hash comparison in `auth_service.authenticate()` to prevent username enumeration
- **M3:** Added `next` parameter support to login view with open redirect prevention
- **L1:** Changed flash category from `'error'` to `'danger'` for consistency with architecture spec

### File List

**New files:**
- `esb/models/user.py` -- User model with UserMixin, password hashing
- `esb/services/auth_service.py` -- authenticate() and load_user() functions
- `esb/forms/auth_forms.py` -- LoginForm with WTForms validators
- `esb/templates/auth/login.html` -- Login page template (extends base_public.html)
- `migrations/versions/ff550b704fef_create_users_table.py` -- Alembic migration
- `tests/test_models/__init__.py`
- `tests/test_models/test_user.py` -- 15 tests for User model
- `tests/test_services/__init__.py`
- `tests/test_services/test_auth_service.py` -- 9 tests for auth service
- `tests/test_views/__init__.py`
- `tests/test_views/test_auth_views.py` -- 27 tests for auth views, RBAC, mutation logging
- `tests/test_cli.py` -- 3 tests for seed-admin CLI command

**Modified files:**
- `esb/__init__.py` -- Replaced placeholder user_loader, added before_request session handler, model import, seed-admin CLI command
- `esb/models/__init__.py` -- Added User import for Alembic discovery
- `esb/views/auth.py` -- Replaced stubs with full login/logout implementation
- `tests/conftest.py` -- Added staff_user, tech_user, staff_client, tech_client fixtures
