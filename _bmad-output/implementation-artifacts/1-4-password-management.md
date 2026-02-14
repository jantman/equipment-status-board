# Story 1.4: Password Management

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a user,
I want to change my own password and have Staff reset my password when needed,
So that I can maintain account security and recover access if my password is lost.

## Acceptance Criteria

1. **Given** I am logged in **When** I navigate to Change Password and provide my current password and a valid new password **Then** my password is updated and I see a success message

2. **Given** I am on the Change Password page **When** I submit an incorrect current password **Then** I see an error message and my password is not changed

3. **Given** I am on the Change Password page **When** I submit with the new password fields not matching **Then** I see a validation error and my password is not changed

4. **Given** I am logged in as Staff **When** I click "Reset Password" for a user on the User Management page **Then** a new temporary password is generated for that user

5. **Given** a password is reset by Staff **When** Slack credentials are configured and the user has a Slack handle **Then** the new temporary password is delivered via Slack direct message, with fallback to on-screen display

6. **Given** a password is changed or reset **When** the action completes **Then** a mutation log entry is written to STDOUT

## Tasks / Subtasks

- [x] Task 1: Add password management functions to user_service (AC: #1, #2, #4, #5, #6)
  - [x] 1.1: Add `change_password(user_id, current_password, new_password)` to `esb/services/user_service.py`
  - [x] 1.2: `change_password()` verifies current password via `user.check_password(current_password)` -- raises `ValidationError('Current password is incorrect')` on mismatch
  - [x] 1.3: `change_password()` calls `user.set_password(new_password)` and `db.session.commit()`
  - [x] 1.4: `change_password()` logs mutation event `user.password_changed` with `{"user_id": id, "username": "..."}` -- **NEVER log passwords**
  - [x] 1.5: Add `reset_password(user_id, reset_by)` to `esb/services/user_service.py`
  - [x] 1.6: `reset_password()` generates a new temp password via `secrets.token_urlsafe(12)`, calls `user.set_password(temp_password)`, commits
  - [x] 1.7: `reset_password()` attempts Slack delivery via existing `_deliver_temp_password_via_slack(user, temp_password)`
  - [x] 1.8: `reset_password()` returns `tuple[User, str, bool]` -- (user, temp_password, slack_delivered) -- same pattern as `create_user()`
  - [x] 1.9: `reset_password()` logs mutation event `user.password_reset` with `{"user_id": id, "username": "...", "reset_by": "...", "slack_delivered": true/false}` -- **NEVER log passwords**
  - [x] 1.10: Write service tests in `tests/test_services/test_user_service.py` for both functions

- [x] Task 2: Create ChangePasswordForm (AC: #1, #2, #3)
  - [x] 2.1: Add `ChangePasswordForm` to `esb/forms/auth_forms.py`
  - [x] 2.2: Fields: `current_password` (PasswordField, DataRequired), `new_password` (PasswordField, DataRequired), `confirm_password` (PasswordField, DataRequired, EqualTo('new_password'))
  - [x] 2.3: Submit button: "Change Password"

- [x] Task 3: Create ResetPasswordForm (AC: #4)
  - [x] 3.1: Add `ResetPasswordForm` to `esb/forms/admin_forms.py`
  - [x] 3.2: Minimal form -- only needs CSRF protection (no user-editable fields; user_id comes from URL)

- [x] Task 4: Implement change password view in auth blueprint (AC: #1, #2, #3, #6)
  - [x] 4.1: Add `GET/POST /auth/change-password` route to `esb/views/auth.py`
  - [x] 4.2: Route protected by `@login_required` (all authenticated users, not just Staff)
  - [x] 4.3: GET: render `auth/change_password.html` with the form
  - [x] 4.4: POST: validate form, call `user_service.change_password(current_user.id, form.current_password.data, form.new_password.data)`
  - [x] 4.5: On success: flash `'Your password has been changed.'` as `'success'`, redirect to the role-appropriate landing page (or back to change password page)
  - [x] 4.6: On ValidationError (wrong current password): flash error as `'danger'`, re-render form
  - [x] 4.7: On form validation failure (passwords don't match): re-render form with inline WTForms errors

- [x] Task 5: Add password reset route to admin blueprint (AC: #4, #5, #6)
  - [x] 5.1: Add `POST /admin/users/<int:id>/reset-password` route to `esb/views/admin.py`
  - [x] 5.2: Route protected by `@role_required('staff')`
  - [x] 5.3: Call `user_service.reset_password(user_id=id, reset_by=current_user.username)`
  - [x] 5.4: If `slack_delivered == True`: flash `'Password reset. New temporary password sent via Slack DM.'` as `'success'`, redirect to user list
  - [x] 5.5: If `slack_delivered == False`: store temp password in `session['_temp_password']`, redirect to existing `GET /admin/users/<int:id>/created` page (reuse the one-time password display from Story 1.3)
  - [x] 5.6: Prevent Staff from resetting their own password via this route (optional safeguard -- they should use Change Password instead)

- [x] Task 6: Create change_password template (AC: #1, #2, #3)
  - [x] 6.1: Create `esb/templates/auth/change_password.html` extending `base.html`
  - [x] 6.2: Single-column form following UX patterns: labels above fields, required fields marked with *, inline validation errors
  - [x] 6.3: Fields: Current Password, New Password, Confirm New Password
  - [x] 6.4: Primary button: "Change Password" (`btn-primary`), Cancel link: "Cancel" (`btn-outline-secondary`) linking back

- [x] Task 7: Update user management page with Reset Password button (AC: #4)
  - [x] 7.1: Add "Reset Password" button (or link) to each user row in `esb/templates/admin/users.html`
  - [x] 7.2: Button submits a POST form to `/admin/users/<id>/reset-password` (with CSRF token)
  - [x] 7.3: Use `btn-outline-secondary btn-sm` styling -- not danger, since this is reversible (user gets a new temp password)

- [x] Task 8: Add "Change Password" link to navbar (AC: #1)
  - [x] 8.1: Add "Change Password" link to the right side of the navbar in `esb/templates/base.html`, next to the username and Logout link
  - [x] 8.2: Link points to `/auth/change-password`

- [x] Task 9: Write view and integration tests (AC: all)
  - [x] 9.1: Add change password tests to `tests/test_views/test_auth_views.py`
  - [x] 9.2: Test GET /auth/change-password renders form for authenticated user
  - [x] 9.3: Test unauthenticated user redirected to login
  - [x] 9.4: Test POST with valid data (correct current password, matching new passwords) changes password
  - [x] 9.5: Test POST with incorrect current password shows error, password unchanged
  - [x] 9.6: Test POST with non-matching new passwords shows validation error
  - [x] 9.7: Test POST with missing required fields shows validation errors
  - [x] 9.8: Test mutation logging for user.password_changed event
  - [x] 9.9: Add reset password tests to `tests/test_views/test_admin_views.py`
  - [x] 9.10: Test POST /admin/users/<id>/reset-password as staff generates new temp password
  - [x] 9.11: Test technician gets 403 on POST /admin/users/<id>/reset-password
  - [x] 9.12: Test unauthenticated user redirected to login
  - [x] 9.13: Test mutation logging for user.password_reset event
  - [x] 9.14: Test Slack delivery mock (success path returns True, failure returns False)
  - [x] 9.15: Test one-time password display page reuse from Story 1.3 (session-based, cleared after display)

## Dev Notes

### Technical Stack -- Key Details

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Password hashing | Werkzeug | 3.1.x (built-in) | `user.set_password(password)` / `user.check_password(password)` -- scrypt default. Do NOT specify method. |
| Forms/CSRF | Flask-WTF | 1.2.2 | `FlaskForm`, `form.validate_on_submit()`. CSRF token auto-included. |
| Form validators | WTForms | via Flask-WTF | `DataRequired`, `EqualTo('new_password')` for confirm field. |
| Slack SDK | `slack_sdk` | >=3.39.0 | Already installed. Reuse `_deliver_temp_password_via_slack()` from user_service. |
| Database | SQLAlchemy | via Flask-SQLAlchemy 3.1.1 | `db.session.get(User, id)` for PK lookups, `db.session.commit()` in service. |
| Auth/Sessions | Flask-Login | 0.6.3 | `@login_required` for change password, `current_user` for user context. |
| Temp passwords | `secrets` (stdlib) | Built-in | `secrets.token_urlsafe(12)` produces 16-char URL-safe string. |

### Architecture Compliance

**CRITICAL -- Follow these patterns exactly:**

- **Service Layer Pattern:** All password logic lives in `esb/services/user_service.py`. Views are thin -- parse form input, call service, render response. **No business logic in views.**
- **Dependency Flow:** `views/auth.py` -> `services/user_service.py` -> `models/user.py`. `views/admin.py` -> `services/user_service.py` -> `models/user.py`. Never reverse.
- **Mutation Logging:** Log ALL password events via `log_mutation()` in `esb/utils/logging.py`. Events: `user.password_changed`, `user.password_reset`. **NEVER log passwords in mutation data -- only user_id and username.**
- **Error Handling:** Service raises `ValidationError` (from `esb/utils/exceptions.py`) for input problems (wrong current password, user not found). Views catch and flash as `'danger'`. Use existing exception hierarchy -- do NOT create new exception types.
- **RBAC:** Change password route uses `@login_required` (any authenticated user). Reset password route uses `@role_required('staff')`. These decorators are in `esb/utils/decorators.py`.
- **Flash categories:** `'success'` for successful operations, `'danger'` for errors -- maps to Bootstrap `alert-success` / `alert-danger`.
- **Session-based temp password display:** Reuse the exact same pattern from Story 1.3 -- `session['_temp_password']` set before redirect, `session.pop('_temp_password', None)` on the display page. The `user_created` view and template at `/admin/users/<id>/created` already handle this perfectly.

### Library & Framework Requirements

**No new dependencies.** Everything needed is already installed:
- `Flask-WTF` (forms with CSRF) -- already in requirements.txt
- `slack_sdk>=3.39.0` -- already in requirements.txt
- `email_validator>=2.0` -- already in requirements.txt
- `WTForms` EqualTo validator -- built into WTForms, already available

**WTForms EqualTo validator usage:**
```python
from wtforms.validators import DataRequired, EqualTo

confirm_password = PasswordField('Confirm New Password', validators=[
    DataRequired(),
    EqualTo('new_password', message='Passwords must match'),
])
```

### File Structure Requirements

**New files to create:**
```
esb/
  templates/
    auth/
      change_password.html      # Change password form page
```

**Files to modify:**
```
esb/services/user_service.py    # Add change_password() and reset_password()
esb/forms/auth_forms.py         # Add ChangePasswordForm
esb/forms/admin_forms.py        # Add ResetPasswordForm
esb/views/auth.py               # Add GET/POST /auth/change-password route
esb/views/admin.py              # Add POST /admin/users/<id>/reset-password route
esb/templates/base.html         # Add "Change Password" link to navbar
esb/templates/admin/users.html  # Add "Reset Password" button per user row
tests/test_services/test_user_service.py  # Add tests for change_password, reset_password
tests/test_views/test_auth_views.py       # Add change password view tests
tests/test_views/test_admin_views.py      # Add reset password view tests
```

**Files to reuse (no changes needed):**
```
esb/templates/admin/user_created.html    # One-time temp password display (reuse from Story 1.3)
esb/views/admin.py: user_created()       # Existing route handles the display (already exists)
```

### Testing Requirements

- **Test DB:** SQLite in-memory (`TestingConfig`) -- CSRF disabled in test config
- **Auth fixtures:** Use existing `staff_client`, `tech_client`, `staff_user`, `tech_user` from `tests/conftest.py`
- **Mutation logger tests:** Use custom `_CaptureHandler` pattern and `capture` fixture from `tests/conftest.py` (mutation logger has `propagate=False` so `caplog` does NOT work)
- **Slack tests:** Mock `slack_sdk.WebClient` using `unittest.mock.patch` -- never make real API calls
- **Password verification in tests:** After calling change_password, verify by calling `user.check_password(new_password)` returns `True` and `user.check_password(old_password)` returns `False`

**Test coverage targets:**

*Service tests (add to `test_user_service.py`):*
- `change_password`: valid (correct current, new set), wrong current password raises ValidationError, user not found raises ValidationError
- `reset_password`: generates new temp password, Slack delivery attempted (mock success), Slack not configured (returns False), user not found raises ValidationError
- Mutation logging: verify `user.password_changed` logged on change, verify `user.password_reset` logged on reset, verify NO passwords in log data

*Auth view tests (add to `test_auth_views.py`):*
- GET /auth/change-password: renders for authenticated user, redirects unauthenticated to login
- POST /auth/change-password: valid data changes password, wrong current password shows error, mismatched new passwords shows error, missing fields shows errors

*Admin view tests (add to `test_admin_views.py`):*
- POST /admin/users/<id>/reset-password: staff can reset, technician gets 403, unauthenticated redirected to login
- Reset with Slack not configured redirects to one-time display page
- One-time display page shows temp password (reuses existing template)

### Previous Story Intelligence (from Story 1.3)

**What was built in Stories 1.1-1.3:**
- Flask app factory in `esb/__init__.py` with `create_app(config_name)`
- User model in `esb/models/user.py`: `set_password()`, `check_password()`, role field, slack_handle
- Auth service in `esb/services/auth_service.py`: `authenticate()`, `load_user()`
- User service in `esb/services/user_service.py`: `create_user()`, `list_users()`, `get_user()`, `change_role()`, `_deliver_temp_password_via_slack()`
- Admin views in `esb/views/admin.py`: `/admin/users`, `/admin/users/new`, `/admin/users/<id>/created`, `/admin/users/<id>/role`
- Auth views in `esb/views/auth.py`: `/auth/login`, `/auth/logout`
- LoginForm in `esb/forms/auth_forms.py`
- UserCreateForm, RoleChangeForm in `esb/forms/admin_forms.py`
- Admin templates: `users.html`, `user_create.html`, `user_created.html`
- Auth templates: `login.html`
- RBAC decorator: `@role_required(role)` with Staff > Technician hierarchy
- Mutation logger: `log_mutation(event, user, data)` with `propagate=False`
- Domain exceptions: `ESBError`, `ValidationError`, etc.
- Test fixtures: `staff_user`, `tech_user`, `staff_client`, `tech_client`, `capture` handler
- 157 tests passing, ruff lint clean

**Key learnings from Stories 1.2-1.3 dev notes:**
- `ruff target-version = "py314"` is not supported -- use `"py313"` in ruff config
- Mutation logger `propagate = False` -- tests must use `capture` fixture with `_CaptureHandler`, NOT `caplog`
- Flash category is `'danger'` (not `'error'`) per Bootstrap alert classes
- `db.session.execute(db.select(User).filter_by(...)).scalar_one_or_none()` for queries
- `db.session.get(User, id)` for primary key lookups
- Session-based one-time password display: `session['_temp_password']` set before redirect, `session.pop()` on display page, redirect to user list if no password in session
- Slack DM delivery is best-effort -- failures are graceful, never blocking
- All `slack_sdk` imports guarded with `try/except`

### Git Intelligence

**Recent commits (newest first):**
1. `3cefae1` Fix code review issues for Story 1.3 user account provisioning
2. `8d6ab07` Implement Story 1.3: User account provisioning and role management
3. `1ce27c4` Create Story 1.3: User Account Provisioning & Role Management context for dev agent
4. `50b63f1` Fix code review issues for Story 1.2 authentication system
5. `75bfd4e` Implement Story 1.2: User authentication system with login/logout and RBAC

**Patterns established:**
- Views follow thin pattern: parse input -> call service -> flash message -> redirect/render
- Service functions accept primitive types, return model instances, raise domain exceptions
- All mutations logged via `log_mutation(event, user, data)` -- called from service layer
- Tests organized in `test_models/`, `test_services/`, `test_views/` mirroring `esb/` structure
- 157 existing tests -- run `make test` or `pytest tests/ -v` to verify no regressions

**Files changed in Story 1.3 (directly relevant to this story):**
- `esb/services/user_service.py` -- **we will ADD to this file** (change_password, reset_password)
- `esb/views/admin.py` -- **we will ADD a route** (reset-password)
- `esb/forms/admin_forms.py` -- **we will ADD a form** (ResetPasswordForm)
- `esb/templates/admin/users.html` -- **we will MODIFY** (add reset button)
- `esb/templates/admin/user_created.html` -- **reuse as-is** for temp password display

### Service Function Contracts

```python
# esb/services/user_service.py -- ADD these functions

def change_password(user_id: int, current_password: str, new_password: str) -> User:
    """Change a user's own password.

    Args:
        user_id: ID of the user changing their password.
        current_password: The user's current password (verified before changing).
        new_password: The new password to set.

    Returns:
        The updated User instance.

    Raises:
        ValidationError: if user not found or current password is incorrect.
    """

def reset_password(user_id: int, reset_by: str) -> tuple[User, str, bool]:
    """Reset a user's password (Staff action).

    Generates a new temporary password, attempts Slack delivery.

    Args:
        user_id: ID of the user whose password is being reset.
        reset_by: Username of the Staff member performing the reset.

    Returns:
        Tuple of (user, temp_password, slack_delivered).

    Raises:
        ValidationError: if user not found.
    """
```

### View Routes

| Method | Path | Function | Auth | Description |
|--------|------|----------|------|-------------|
| GET | `/auth/change-password` | `change_password()` | `@login_required` | Render change password form |
| POST | `/auth/change-password` | `change_password()` | `@login_required` | Process password change |
| POST | `/admin/users/<int:id>/reset-password` | `reset_password()` | `@role_required('staff')` | Reset user password |

### Mutation Logging Events

| Event | When | Data |
|-------|------|------|
| `user.password_changed` | User changes own password | `{"user_id": id, "username": "..."}` |
| `user.password_reset` | Staff resets user's password | `{"user_id": id, "username": "...", "reset_by": "...", "slack_delivered": true/false}` |

**NEVER log passwords in mutation data!**

### Security Considerations

- **Never log passwords** (new or old) in mutation logs, app logs, or any output
- **Verify current password** before allowing change -- prevents unauthorized changes if a session is hijacked
- **Temp passwords on reset** are cryptographically secure -- `secrets.token_urlsafe(12)`
- **One-time display** for temp passwords -- same session-based pattern as Story 1.3
- **CSRF protection** on all forms -- Flask-WTF handles this automatically
- **Slack DM delivery is best-effort** -- failures are graceful, fallback to on-screen display
- **No rate limiting in v1.0** -- per architecture doc

### UX Notes (from UX Design Specification)

Per the UX spec and Journey 4 (Staff Manages Equipment & Users):
- Change Password page: single-column form, labels above fields, required fields marked with asterisk (*)
- Form follows UX form patterns: validate on submit, inline errors below fields
- Button hierarchy: "Change Password" is `btn-primary`, "Cancel" is `btn-outline-secondary`
- Flash messages: `'success'` for successful operations, `'danger'` for errors
- Navbar right side: username + "Change Password" link + "Logout" link
- Per UX spec navigation table: Staff navbar includes link for Users admin; "Change Password" sits in the user section (right side of navbar), not in main nav

### Naming Conventions

**Python:**
- Service functions: `change_password()`, `reset_password()` (snake_case)
- Form classes: `ChangePasswordForm`, `ResetPasswordForm` (PascalCase)
- View functions: `change_password()`, `reset_password()` (snake_case)

**Routes:**
- `/auth/change-password` (GET+POST) -- change own password
- `/admin/users/<int:id>/reset-password` (POST) -- staff resets user password

**Templates:**
- `auth/change_password.html` (snake_case, per-blueprint directory)

### Project Structure Notes

- `esb/templates/auth/` directory EXISTS with `login.html` -- add `change_password.html` alongside it
- `esb/services/user_service.py` EXISTS with `create_user()`, `list_users()`, `get_user()`, `change_role()`, `_deliver_temp_password_via_slack()` -- ADD `change_password()` and `reset_password()` to this file
- `esb/forms/auth_forms.py` EXISTS with `LoginForm` -- ADD `ChangePasswordForm`
- `esb/forms/admin_forms.py` EXISTS with `UserCreateForm`, `RoleChangeForm` -- ADD `ResetPasswordForm`
- `esb/views/auth.py` EXISTS with `login()`, `logout()` -- ADD `change_password()` route
- `esb/views/admin.py` EXISTS with `list_users()`, `create_user()`, `user_created()`, `change_role()` -- ADD `reset_password()` route
- `esb/templates/admin/user_created.html` EXISTS -- REUSE for temp password display after reset (no changes needed)
- No database migration needed -- User model and users table already exist
- No new dependencies -- all packages already installed

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.4: Password Management]
- [Source: _bmad-output/planning-artifacts/architecture.md#Authentication & Security]
- [Source: _bmad-output/planning-artifacts/architecture.md#API & Communication Patterns - Service Layer Pattern]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns - Project Organization]
- [Source: _bmad-output/planning-artifacts/prd.md#User Management & Authentication (FR45-FR51)]
- [Source: _bmad-output/planning-artifacts/prd.md#Security (NFR5-NFR9)]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Navigation Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Form Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Feedback Patterns]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Journey 4: Staff Manages Equipment & Users]
- [Source: _bmad-output/implementation-artifacts/1-3-user-account-provisioning-role-management.md#Dev Notes]
- [Source: _bmad-output/implementation-artifacts/1-3-user-account-provisioning-role-management.md#Completion Notes List]

## Dev Agent Record

### Agent Model Used

Claude Opus 4.6 (claude-opus-4-6)

### Debug Log References

None

### Completion Notes List

- All 9 tasks and 42 subtasks completed
- 26 new tests added (183 total, all passing)
- Ruff lint clean
- No new dependencies required
- Reused existing `user_created` view/template for temp password display after reset
- Reused existing `_deliver_temp_password_via_slack()` for password reset Slack delivery
- Fixed mutation log test assertions to check `entry['data']` instead of full `entry` (event names contain "password")

### Change Log

- `esb/services/user_service.py` - Added `change_password()` and `reset_password()` functions
- `esb/forms/auth_forms.py` - Added `ChangePasswordForm` with EqualTo validator
- `esb/forms/admin_forms.py` - Added `ResetPasswordForm` (CSRF-only)
- `esb/views/auth.py` - Added `GET/POST /auth/change-password` route
- `esb/views/admin.py` - Added `POST /admin/users/<id>/reset-password` route, pass `reset_form` to template
- `esb/templates/auth/change_password.html` - New template for change password form
- `esb/templates/admin/users.html` - Added Reset Password button per user row
- `esb/templates/base.html` - Added Change Password link to navbar

### File List

- esb/services/user_service.py (modified)
- esb/forms/auth_forms.py (modified)
- esb/forms/admin_forms.py (modified)
- esb/views/auth.py (modified)
- esb/views/admin.py (modified)
- esb/templates/auth/change_password.html (new)
- esb/templates/admin/users.html (modified)
- esb/templates/base.html (modified)
- tests/test_services/test_user_service.py (modified)
- tests/test_views/test_auth_views.py (modified)
- tests/test_views/test_admin_views.py (modified)
- _bmad-output/implementation-artifacts/sprint-status.yaml (modified)
- _bmad-output/implementation-artifacts/1-4-password-management.md (modified)
