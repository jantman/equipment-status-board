"""Tests for admin views (user management)."""

import json
from unittest.mock import MagicMock, patch

from esb.extensions import db as _db
from esb.models.user import User


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

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_success_redirects_to_users(self, mock_client_cls, staff_client, staff_user, app):
        """When Slack delivery succeeds, redirects to user list with success flash."""
        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {'user': {'id': 'U12345'}}
        mock_client.conversations_open.return_value = {'channel': {'id': 'D12345'}}

        resp = staff_client.post('/admin/users/new', data={
            'username': 'slackdelivered',
            'email': 'slackdelivered@example.com',
            'role': 'technician',
            'slack_handle': '@slackdelivered',
        })
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

        resp = staff_client.get('/admin/users')
        assert b'sent via Slack' in resp.data


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
        """Invalid role flashes error and redirects."""
        resp = staff_client.post(f'/admin/users/{tech_user.id}/role', data={
            'user_id': str(tech_user.id),
            'role': 'superadmin',
        }, follow_redirects=True)
        assert resp.status_code == 200
        assert b'Invalid role change request' in resp.data

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


class TestResetPassword:
    """Tests for POST /admin/users/<id>/reset-password."""

    def test_staff_resets_password(self, staff_client, staff_user, tech_user):
        """Staff can reset a user's password."""
        resp = staff_client.post(f'/admin/users/{tech_user.id}/reset-password')
        assert resp.status_code == 302
        # Redirects to temp password display
        assert '/created' in resp.headers['Location']

    def test_technician_gets_403(self, tech_client, tech_user, staff_user):
        """Technician cannot reset passwords."""
        resp = tech_client.post(f'/admin/users/{staff_user.id}/reset-password')
        assert resp.status_code == 403

    def test_unauthenticated_redirects_to_login(self, client, app, tech_user):
        """Unauthenticated user redirected to login."""
        resp = client.post(f'/admin/users/{tech_user.id}/reset-password')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_temp_password_displayed_once(self, staff_client, staff_user, tech_user):
        """After reset, temp password page shows once then redirects."""
        resp = staff_client.post(f'/admin/users/{tech_user.id}/reset-password')
        redirect_url = resp.headers['Location']

        # First visit shows temp password
        resp = staff_client.get(redirect_url)
        assert resp.status_code == 200
        assert b'Temporary Password' in resp.data

        # Second visit redirects (password cleared from session)
        resp = staff_client.get(redirect_url)
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

    def test_nonexistent_user_shows_error(self, staff_client, staff_user):
        """Resetting nonexistent user flashes error and redirects."""
        resp = staff_client.post('/admin/users/99999/reset-password', follow_redirects=True)
        assert resp.status_code == 200
        assert b'not found' in resp.data

    def test_self_reset_blocked(self, staff_client, staff_user):
        """Staff cannot reset their own password via this route."""
        resp = staff_client.post(
            f'/admin/users/{staff_user.id}/reset-password', follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Use Change Password' in resp.data

    def test_old_password_no_longer_works(self, staff_client, staff_user, tech_user):
        """After reset, the old password no longer works."""
        staff_client.post(f'/admin/users/{tech_user.id}/reset-password')
        user = _db.session.get(User, tech_user.id)
        assert not user.check_password('testpass')

    def test_logs_password_reset_mutation(self, staff_client, staff_user, tech_user, capture):
        """Password reset logs mutation event."""
        capture.records.clear()
        staff_client.post(f'/admin/users/{tech_user.id}/reset-password')
        entries = [
            json.loads(r.message) for r in capture.records
            if 'user.password_reset' in r.message
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry['event'] == 'user.password_reset'
        assert entry['user'] == 'staffuser'
        assert entry['data']['username'] == 'techuser'
        assert entry['data']['reset_by'] == 'staffuser'
        # Verify no password values leaked in data
        assert 'password' not in json.dumps(entry['data'])

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_delivery_redirects_to_users(self, mock_client_cls, staff_client, staff_user, tech_user, app):
        """When Slack succeeds, redirects to user list with success flash."""
        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {'user': {'id': 'U12345'}}
        mock_client.conversations_open.return_value = {'channel': {'id': 'D12345'}}

        tech_user.slack_handle = '@techuser'
        _db.session.commit()

        resp = staff_client.post(f'/admin/users/{tech_user.id}/reset-password')
        assert resp.status_code == 302
        assert '/admin/users' in resp.headers['Location']

        resp = staff_client.get('/admin/users')
        assert b'sent via Slack' in resp.data


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
