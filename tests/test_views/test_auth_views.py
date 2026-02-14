"""Tests for auth views, RBAC integration, and mutation logging."""

import json
import logging

import pytest

from esb.extensions import db as _db
from esb.models.user import User
from esb.utils.logging import mutation_logger


class _CaptureHandler(logging.Handler):
    """Test handler that captures log records."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def capture():
    """Add a capture handler to the mutation logger for testing."""
    handler = _CaptureHandler()
    mutation_logger.addHandler(handler)
    yield handler
    mutation_logger.removeHandler(handler)


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
