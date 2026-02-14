"""Tests for auth views, RBAC integration, and mutation logging."""

import json

from esb.extensions import db as _db
from esb.models.user import User


class TestLoginPage:
    """Tests for the login page (GET /auth/login)."""

    def test_login_page_renders(self, client):
        """GET /auth/login returns 200 with a login form."""
        resp = client.get('/auth/login')
        assert resp.status_code == 200
        assert b'Log In' in resp.data
        assert b'Username' in resp.data
        assert b'Password' in resp.data

    def test_login_page_has_form(self, client):
        """Login page contains a POST form."""
        resp = client.get('/auth/login')
        assert b'method="POST"' in resp.data

    def test_login_page_has_forgot_password_text(self, client):
        """Login page shows forgot password message."""
        resp = client.get('/auth/login')
        assert b'Contact an administrator' in resp.data


class TestLoginPost:
    """Tests for login POST handler."""

    def test_successful_login_redirects(self, client, staff_user):
        """Successful login redirects to health page."""
        resp = client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302
        assert '/health' in resp.headers['Location']

    def test_successful_login_sets_session(self, client, staff_user):
        """After login, user can access authenticated routes."""
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        # Verify session is active by accessing health (no redirect to login)
        resp = client.get('/health')
        assert resp.status_code == 200

    def test_wrong_password_shows_error(self, client, staff_user):
        """Wrong password re-renders login with error flash."""
        resp = client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'wrongpass',
        })
        assert resp.status_code == 200
        assert b'Invalid username or password' in resp.data

    def test_unknown_user_shows_error(self, client, app):
        """Unknown username re-renders login with error flash."""
        resp = client.post('/auth/login', data={
            'username': 'nobody',
            'password': 'anypass',
        })
        assert resp.status_code == 200
        assert b'Invalid username or password' in resp.data

    def test_inactive_user_shows_error(self, client, app):
        """Inactive user cannot login."""
        user = User(username='inactive', email='inactive@example.com', is_active=False)
        user.set_password('pass123')
        _db.session.add(user)
        _db.session.commit()
        resp = client.post('/auth/login', data={
            'username': 'inactive',
            'password': 'pass123',
        })
        assert resp.status_code == 200
        assert b'Invalid username or password' in resp.data

    def test_empty_username_shows_validation(self, client, app):
        """Empty username fails form validation."""
        resp = client.post('/auth/login', data={
            'username': '',
            'password': 'pass',
        })
        assert resp.status_code == 200

    def test_already_authenticated_redirects(self, staff_client):
        """Already authenticated user visiting login redirects to health."""
        resp = staff_client.get('/auth/login')
        assert resp.status_code == 302
        assert '/health' in resp.headers['Location']


class TestLoginNextRedirect:
    """Tests for login ?next= redirect (AC: safe redirect after login)."""

    def test_redirects_to_next_on_login(self, client, staff_user):
        """Successful login redirects to ?next= path."""
        resp = client.post('/auth/login?next=/health', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302
        assert resp.headers['Location'].endswith('/health')

    def test_ignores_absolute_url_next(self, client, staff_user):
        """Login ignores ?next= with absolute URL (open redirect prevention)."""
        resp = client.post('/auth/login?next=https://evil.com/steal', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302
        assert 'evil.com' not in resp.headers['Location']
        assert '/health' in resp.headers['Location']

    def test_ignores_protocol_relative_next(self, client, staff_user):
        """Login ignores ?next= with protocol-relative URL."""
        resp = client.post('/auth/login?next=//evil.com/steal', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302
        assert 'evil.com' not in resp.headers['Location']
        assert '/health' in resp.headers['Location']

    def test_no_next_redirects_to_health(self, client, staff_user):
        """Login without ?next= redirects to health."""
        resp = client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302
        assert '/health' in resp.headers['Location']


class TestLogout:
    """Tests for logout route."""

    def test_logout_redirects_to_login(self, staff_client):
        """Logout redirects to login page."""
        resp = staff_client.get('/auth/logout')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_logout_clears_session(self, staff_client):
        """After logout, accessing protected routes redirects to login."""
        staff_client.get('/auth/logout')
        resp = staff_client.get('/auth/logout')
        # Should redirect to login (not authenticated anymore)
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_logout_flashes_message(self, staff_client):
        """Logout flashes a logged out message."""
        resp = staff_client.get('/auth/logout', follow_redirects=True)
        assert b'You have been logged out.' in resp.data

    def test_unauthenticated_logout_redirects(self, client, app):
        """Unauthenticated user accessing logout redirects to login."""
        resp = client.get('/auth/logout')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']


class TestUnauthenticatedAccess:
    """Tests for unauthenticated access (AC: #5)."""

    def test_login_required_redirects_to_login(self, client, app):
        """@login_required routes redirect unauthenticated users to login."""
        resp = client.get('/auth/logout')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']


class TestRBACIntegration:
    """Tests for RBAC with real User model (AC: #5, #6, Task 8)."""

    def test_staff_accesses_staff_route(self, app, staff_user):
        """Staff user can access staff-only route."""
        from esb.utils.decorators import role_required

        @app.route('/test-staff-only')
        @role_required('staff')
        def test_staff_route():
            return 'staff ok'

        client = app.test_client()
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        resp = client.get('/test-staff-only')
        assert resp.status_code == 200
        assert resp.data == b'staff ok'

    def test_technician_gets_403_on_staff_route(self, app, tech_user):
        """Technician gets 403 on staff-only route."""
        from esb.utils.decorators import role_required

        @app.route('/test-staff-only2')
        @role_required('staff')
        def test_staff_route2():
            return 'staff ok'

        client = app.test_client()
        client.post('/auth/login', data={
            'username': 'techuser',
            'password': 'testpass',
        })
        resp = client.get('/test-staff-only2')
        assert resp.status_code == 403

    def test_technician_accesses_technician_route(self, app, tech_user):
        """Technician can access technician-only route."""
        from esb.utils.decorators import role_required

        @app.route('/test-tech-only')
        @role_required('technician')
        def test_tech_route():
            return 'tech ok'

        client = app.test_client()
        client.post('/auth/login', data={
            'username': 'techuser',
            'password': 'testpass',
        })
        resp = client.get('/test-tech-only')
        assert resp.status_code == 200

    def test_staff_accesses_technician_route(self, app, staff_user):
        """Staff can access technician-only route (hierarchy)."""
        from esb.utils.decorators import role_required

        @app.route('/test-tech-only2')
        @role_required('technician')
        def test_tech_route2():
            return 'tech ok'

        client = app.test_client()
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        resp = client.get('/test-tech-only2')
        assert resp.status_code == 200


class TestMutationLogging:
    """Tests for auth mutation logging (Task 10.3)."""

    def test_login_logs_mutation(self, client, staff_user, capture):
        """Successful login logs user.login event."""
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        login_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.login' in r.message and 'failed' not in r.message
        ]
        assert len(login_entries) == 1
        assert login_entries[0]['event'] == 'user.login'
        assert login_entries[0]['data']['username'] == 'staffuser'
        assert 'password' not in json.dumps(login_entries[0])

    def test_failed_login_logs_mutation(self, client, staff_user, capture):
        """Failed login logs user.login_failed event."""
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'wrongpass',
        })
        failed_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.login_failed' in r.message
        ]
        assert len(failed_entries) == 1
        assert failed_entries[0]['event'] == 'user.login_failed'
        assert failed_entries[0]['data']['username'] == 'staffuser'
        assert 'password' not in json.dumps(failed_entries[0])

    def test_logout_logs_mutation(self, client, staff_user, capture):
        """Logout logs user.logout event."""
        client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        # Clear login entries
        capture.records.clear()
        client.get('/auth/logout')
        logout_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.logout' in r.message
        ]
        assert len(logout_entries) == 1
        assert logout_entries[0]['event'] == 'user.logout'
        assert logout_entries[0]['data']['username'] == 'staffuser'


class TestChangePasswordPage:
    """Tests for GET /auth/change-password."""

    def test_renders_form_for_authenticated_user(self, staff_client):
        """Authenticated user sees change password form."""
        resp = staff_client.get('/auth/change-password')
        assert resp.status_code == 200
        assert b'Change Password' in resp.data
        assert b'Current Password' in resp.data
        assert b'New Password' in resp.data
        assert b'Confirm New Password' in resp.data

    def test_unauthenticated_redirects_to_login(self, client, app):
        """Unauthenticated user redirected to login."""
        resp = client.get('/auth/change-password')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_technician_can_access(self, tech_client):
        """Technician can access change password (not staff-only)."""
        resp = tech_client.get('/auth/change-password')
        assert resp.status_code == 200
        assert b'Change Password' in resp.data


class TestChangePasswordPost:
    """Tests for POST /auth/change-password."""

    def test_valid_change_succeeds(self, staff_client, staff_user):
        """Valid data changes password and shows success flash."""
        resp = staff_client.post('/auth/change-password', data={
            'current_password': 'testpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Your password has been changed.' in resp.data

        # Verify new password works
        from esb.models.user import User
        user = _db.session.get(User, staff_user.id)
        assert user.check_password('newpass123')
        assert not user.check_password('testpass')

    def test_wrong_current_password_shows_error(self, staff_client, staff_user):
        """Incorrect current password shows error."""
        resp = staff_client.post('/auth/change-password', data={
            'current_password': 'wrongpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        })
        assert resp.status_code == 200
        assert b'Current password is incorrect' in resp.data

        # Verify password unchanged
        from esb.models.user import User
        user = _db.session.get(User, staff_user.id)
        assert user.check_password('testpass')

    def test_mismatched_passwords_shows_error(self, staff_client, staff_user):
        """Non-matching new passwords shows validation error."""
        resp = staff_client.post('/auth/change-password', data={
            'current_password': 'testpass',
            'new_password': 'newpass123',
            'confirm_password': 'different456',
        })
        assert resp.status_code == 200
        assert b'Passwords must match' in resp.data

    def test_missing_fields_shows_errors(self, staff_client, staff_user):
        """Missing required fields re-renders form."""
        resp = staff_client.post('/auth/change-password', data={
            'current_password': '',
            'new_password': '',
            'confirm_password': '',
        })
        assert resp.status_code == 200
        # Form re-renders (validation failure)

    def test_logs_password_changed_mutation(self, staff_client, staff_user, capture):
        """Password change logs mutation event."""
        capture.records.clear()
        staff_client.post('/auth/change-password', data={
            'current_password': 'testpass',
            'new_password': 'newpass123',
            'confirm_password': 'newpass123',
        })
        entries = [
            json.loads(r.message) for r in capture.records
            if 'user.password_changed' in r.message
        ]
        assert len(entries) == 1
        assert entries[0]['event'] == 'user.password_changed'
        assert entries[0]['data']['username'] == 'staffuser'
        # Verify no password values leaked in data
        assert 'password' not in json.dumps(entries[0]['data'])


class TestFullFlow:
    """Integration tests for the full login->access->logout flow."""

    def test_login_access_logout_flow(self, app, staff_user):
        """Full flow: login -> access protected -> logout -> denied."""
        from esb.utils.decorators import role_required

        @app.route('/test-protected')
        @role_required('technician')
        def test_protected():
            return 'protected content'

        client = app.test_client()

        # Cannot access before login
        resp = client.get('/test-protected')
        assert resp.status_code == 302

        # Login
        resp = client.post('/auth/login', data={
            'username': 'staffuser',
            'password': 'testpass',
        })
        assert resp.status_code == 302

        # Access protected route
        resp = client.get('/test-protected')
        assert resp.status_code == 200
        assert resp.data == b'protected content'

        # Logout
        resp = client.get('/auth/logout')
        assert resp.status_code == 302

        # Cannot access after logout
        resp = client.get('/test-protected')
        assert resp.status_code == 302
