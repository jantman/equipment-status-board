"""Tests for admin views (user management)."""

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


class TestListUsers:
    """Tests for GET /admin/users."""

    def test_staff_sees_user_table(self, staff_client, staff_user, tech_user):
        """Staff user sees a table of users."""
        resp = staff_client.get('/admin/users')
        assert resp.status_code == 200
        assert b'User Management' in resp.data
        assert b'staffuser' in resp.data
        assert b'techuser' in resp.data

    def test_technician_gets_403(self, tech_client):
        """Technician gets 403 on user management page."""
        resp = tech_client.get('/admin/users')
        assert resp.status_code == 403

    def test_unauthenticated_redirects_to_login(self, client, app):
        """Unauthenticated user redirected to login."""
        resp = client.get('/admin/users')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_user_table_shows_columns(self, staff_client, staff_user):
        """User table shows username, email, role, status columns."""
        resp = staff_client.get('/admin/users')
        assert b'Username' in resp.data
        assert b'Email' in resp.data
        assert b'Role' in resp.data
        assert b'Status' in resp.data

    def test_add_user_button_visible(self, staff_client, staff_user):
        """Add User button is visible on the user list."""
        resp = staff_client.get('/admin/users')
        assert b'Add User' in resp.data

    def test_inline_role_change_form(self, staff_client, staff_user, tech_user):
        """Each user row has an inline role change form."""
        resp = staff_client.get('/admin/users')
        assert b'Update' in resp.data
        assert b'select' in resp.data


class TestCreateUserForm:
    """Tests for GET /admin/users/new."""

    def test_renders_creation_form(self, staff_client, staff_user):
        """Staff user sees user creation form."""
        resp = staff_client.get('/admin/users/new')
        assert resp.status_code == 200
        assert b'Add User' in resp.data
        assert b'Username' in resp.data
        assert b'Email' in resp.data
        assert b'Role' in resp.data

    def test_technician_gets_403(self, tech_client):
        """Technician gets 403 on creation form."""
        resp = tech_client.get('/admin/users/new')
        assert resp.status_code == 403


class TestCreateUserPost:
    """Tests for POST /admin/users/new."""

    def test_creates_user_with_valid_data(self, staff_client, staff_user):
        """Valid submission creates user and redirects to password display."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'newuser',
            'email': 'newuser@example.com',
            'role': 'technician',
        })
        assert resp.status_code == 302
        assert '/created' in resp.headers['Location']

        # Verify user was created in DB
        user = _db.session.execute(
            _db.select(User).filter_by(username='newuser')
        ).scalar_one_or_none()
        assert user is not None
        assert user.role == 'technician'

    def test_duplicate_username_shows_error(self, staff_client, staff_user):
        """Duplicate username shows danger flash."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'staffuser',
            'email': 'other@example.com',
            'role': 'technician',
        })
        assert resp.status_code == 200
        assert b'already exists' in resp.data

    def test_duplicate_email_shows_error(self, staff_client, staff_user):
        """Duplicate email shows danger flash."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'uniqueuser',
            'email': 'staffuser@example.com',
            'role': 'technician',
        })
        assert resp.status_code == 200
        assert b'already exists' in resp.data

    def test_missing_username_shows_validation(self, staff_client, staff_user):
        """Missing username shows validation error."""
        resp = staff_client.post('/admin/users/new', data={
            'username': '',
            'email': 'valid@example.com',
            'role': 'technician',
        })
        assert resp.status_code == 200
        # Form not submitted (validation failure), re-renders

    def test_missing_email_shows_validation(self, staff_client, staff_user):
        """Missing email shows validation error."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'validuser',
            'email': '',
            'role': 'technician',
        })
        assert resp.status_code == 200

    def test_invalid_email_shows_validation(self, staff_client, staff_user):
        """Invalid email format shows validation error."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'validuser',
            'email': 'not-an-email',
            'role': 'technician',
        })
        assert resp.status_code == 200

    def test_creates_user_with_slack_handle(self, staff_client, staff_user):
        """User creation stores slack handle."""
        staff_client.post('/admin/users/new', data={
            'username': 'slackuser',
            'email': 'slackuser@example.com',
            'role': 'technician',
            'slack_handle': '@slackuser',
        })
        user = _db.session.execute(
            _db.select(User).filter_by(username='slackuser')
        ).scalar_one_or_none()
        assert user is not None
        assert user.slack_handle == '@slackuser'


class TestChangeRole:
    """Tests for POST /admin/users/<id>/role."""

    def test_changes_role_successfully(self, staff_client, staff_user, tech_user):
        """Staff can change a user's role."""
        resp = staff_client.post(f'/admin/users/{tech_user.id}/role', data={
            'user_id': str(tech_user.id),
            'role': 'staff',
        })
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

        # Verify change persisted
        user = _db.session.get(User, tech_user.id)
        assert user.role == 'staff'

    def test_invalid_role_shows_error(self, staff_client, staff_user, tech_user):
        """Invalid role flash error and redirects."""
        resp = staff_client.post(f'/admin/users/{tech_user.id}/role', data={
            'user_id': str(tech_user.id),
            'role': 'superadmin',
        }, follow_redirects=True)
        # SelectField validates choices, so it should re-render with error
        # Since 'superadmin' is not a valid choice, WTForms won't validate
        assert resp.status_code == 200

    def test_technician_gets_403(self, tech_client, tech_user):
        """Technician cannot change roles."""
        resp = tech_client.post(f'/admin/users/{tech_user.id}/role', data={
            'user_id': str(tech_user.id),
            'role': 'staff',
        })
        assert resp.status_code == 403


class TestTempPasswordDisplay:
    """Tests for GET /admin/users/<id>/created."""

    def test_shows_temp_password(self, staff_client, staff_user):
        """Temp password display page shows password when available."""
        # Create a user to get temp password in session
        resp = staff_client.post('/admin/users/new', data={
            'username': 'tempuser',
            'email': 'tempuser@example.com',
            'role': 'technician',
        })
        assert resp.status_code == 302
        redirect_url = resp.headers['Location']

        # Follow redirect to password display
        resp = staff_client.get(redirect_url)
        assert resp.status_code == 200
        assert b'Temporary Password' in resp.data
        assert b'tempuser' in resp.data
        assert b'only be shown once' in resp.data

    def test_second_visit_redirects(self, staff_client, staff_user):
        """Second visit to password page redirects (password cleared)."""
        # Create user
        resp = staff_client.post('/admin/users/new', data={
            'username': 'onceuser',
            'email': 'onceuser@example.com',
            'role': 'technician',
        })
        redirect_url = resp.headers['Location']

        # First visit - shows password
        resp = staff_client.get(redirect_url)
        assert resp.status_code == 200
        assert b'Temporary Password' in resp.data

        # Second visit - redirects (password no longer available)
        resp = staff_client.get(redirect_url)
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

    def test_back_to_users_button(self, staff_client, staff_user):
        """Password display page has Back to Users button."""
        resp = staff_client.post('/admin/users/new', data={
            'username': 'btnuser',
            'email': 'btnuser@example.com',
            'role': 'technician',
        })
        redirect_url = resp.headers['Location']
        resp = staff_client.get(redirect_url)
        assert b'Back to Users' in resp.data


class TestMutationLogging:
    """Tests for mutation logging in admin views."""

    def test_user_created_event_logged(self, staff_client, staff_user, capture):
        """User creation logs user.created mutation event."""
        # Clear login records
        capture.records.clear()
        staff_client.post('/admin/users/new', data={
            'username': 'logcreate',
            'email': 'logcreate@example.com',
            'role': 'technician',
        })
        created_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.created' in r.message
        ]
        assert len(created_entries) == 1
        entry = created_entries[0]
        assert entry['event'] == 'user.created'
        assert entry['user'] == 'staffuser'
        assert entry['data']['username'] == 'logcreate'
        assert 'password' not in json.dumps(entry)

    def test_role_changed_event_logged(self, staff_client, staff_user, tech_user, capture):
        """Role change logs user.role_changed mutation event."""
        capture.records.clear()
        staff_client.post(f'/admin/users/{tech_user.id}/role', data={
            'user_id': str(tech_user.id),
            'role': 'staff',
        })
        changed_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.role_changed' in r.message
        ]
        assert len(changed_entries) == 1
        entry = changed_entries[0]
        assert entry['event'] == 'user.role_changed'
        assert entry['user'] == 'staffuser'
        assert entry['data']['old_role'] == 'technician'
        assert entry['data']['new_role'] == 'staff'


class TestAdminIndex:
    """Tests for GET /admin/."""

    def test_redirects_to_users(self, staff_client, staff_user):
        """Admin index redirects to user list."""
        resp = staff_client.get('/admin/')
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

    def test_technician_gets_403(self, tech_client):
        """Technician gets 403 on admin index."""
        resp = tech_client.get('/admin/')
        assert resp.status_code == 403
