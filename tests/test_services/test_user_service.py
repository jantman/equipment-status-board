"""Tests for user service (account provisioning, role management)."""

import json
from unittest.mock import MagicMock, patch

import pytest

from esb.extensions import db as _db
from esb.models.user import User
from esb.utils.exceptions import ValidationError


class TestCreateUser:
    """Tests for user_service.create_user()."""

    def test_creates_user_with_valid_data(self, app):
        """create_user() creates a user and returns tuple."""
        from esb.services.user_service import create_user

        user, temp_password, slack_delivered = create_user(
            username='newuser',
            email='newuser@example.com',
            role='technician',
            created_by='staffuser',
        )
        assert user.username == 'newuser'
        assert user.email == 'newuser@example.com'
        assert user.role == 'technician'
        assert user.is_active is True
        assert isinstance(temp_password, str)
        assert len(temp_password) >= 12
        assert slack_delivered is False  # No Slack configured

    def test_creates_staff_user(self, app):
        """create_user() can create staff users."""
        from esb.services.user_service import create_user

        user, _, _ = create_user(
            username='newstaff',
            email='newstaff@example.com',
            role='staff',
            created_by='admin',
        )
        assert user.role == 'staff'

    def test_password_is_hashed_in_db(self, app):
        """Temp password is hashed, not stored as plaintext."""
        from esb.services.user_service import create_user

        user, temp_password, _ = create_user(
            username='hashtest',
            email='hashtest@example.com',
            role='technician',
            created_by='admin',
        )
        assert user.password_hash != temp_password
        assert user.check_password(temp_password)

    def test_user_persisted_to_db(self, app):
        """Created user is saved to the database."""
        from esb.services.user_service import create_user

        create_user(
            username='persisted',
            email='persisted@example.com',
            role='technician',
            created_by='admin',
        )
        found = _db.session.execute(
            _db.select(User).filter_by(username='persisted')
        ).scalar_one_or_none()
        assert found is not None
        assert found.email == 'persisted@example.com'

    def test_duplicate_username_raises(self, app):
        """create_user() raises ValidationError on duplicate username."""
        from esb.services.user_service import create_user

        create_user(
            username='dupeuser',
            email='first@example.com',
            role='technician',
            created_by='admin',
        )
        with pytest.raises(ValidationError, match='username'):
            create_user(
                username='dupeuser',
                email='second@example.com',
                role='technician',
                created_by='admin',
            )

    def test_duplicate_email_raises(self, app):
        """create_user() raises ValidationError on duplicate email."""
        from esb.services.user_service import create_user

        create_user(
            username='first',
            email='dupe@example.com',
            role='technician',
            created_by='admin',
        )
        with pytest.raises(ValidationError, match='email'):
            create_user(
                username='second',
                email='dupe@example.com',
                role='technician',
                created_by='admin',
            )

    def test_invalid_role_raises(self, app):
        """create_user() raises ValidationError on invalid role."""
        from esb.services.user_service import create_user

        with pytest.raises(ValidationError, match='role'):
            create_user(
                username='badrole',
                email='badrole@example.com',
                role='admin',
                created_by='admin',
            )

    def test_stores_slack_handle(self, app):
        """create_user() stores the slack_handle on the user."""
        from esb.services.user_service import create_user

        user, _, _ = create_user(
            username='slackuser',
            email='slackuser@example.com',
            role='technician',
            slack_handle='@slackuser',
            created_by='admin',
        )
        assert user.slack_handle == '@slackuser'

    def test_logs_user_created_mutation(self, app, capture):
        """create_user() logs a user.created mutation event."""
        from esb.services.user_service import create_user

        create_user(
            username='logtest',
            email='logtest@example.com',
            role='technician',
            created_by='staffuser',
        )
        created_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.created' in r.message
        ]
        assert len(created_entries) == 1
        entry = created_entries[0]
        assert entry['event'] == 'user.created'
        assert entry['user'] == 'staffuser'
        assert entry['data']['username'] == 'logtest'
        assert entry['data']['email'] == 'logtest@example.com'
        assert entry['data']['role'] == 'technician'
        assert 'password' not in json.dumps(entry)

    def test_logs_slack_delivered_status(self, app, capture):
        """Mutation log includes slack_delivered status."""
        from esb.services.user_service import create_user

        create_user(
            username='slacklog',
            email='slacklog@example.com',
            role='technician',
            created_by='admin',
        )
        created_entries = [
            json.loads(r.message) for r in capture.records
            if 'user.created' in r.message
        ]
        assert 'slack_delivered' in created_entries[0]['data']

    def test_default_created_by_is_system(self, app):
        """create_user() defaults created_by to 'system'."""
        from esb.services.user_service import create_user

        # created_by defaults to 'system' when not provided
        user, _, _ = create_user(
            username='sysuser',
            email='sysuser@example.com',
            role='technician',
        )
        assert user is not None


class TestListUsers:
    """Tests for user_service.list_users()."""

    def test_returns_all_users_ordered(self, app, staff_user, tech_user):
        """list_users() returns all users ordered by username."""
        from esb.services.user_service import list_users

        users = list_users()
        assert len(users) == 2
        usernames = [u.username for u in users]
        assert usernames == sorted(usernames)

    def test_returns_empty_list_when_no_users(self, app):
        """list_users() returns empty list when no users exist."""
        from esb.services.user_service import list_users

        users = list_users()
        assert users == []


class TestGetUser:
    """Tests for user_service.get_user()."""

    def test_returns_user_by_id(self, app, staff_user):
        """get_user() returns user when found."""
        from esb.services.user_service import get_user

        user = get_user(staff_user.id)
        assert user.username == staff_user.username

    def test_raises_on_not_found(self, app):
        """get_user() raises ValidationError when user not found."""
        from esb.services.user_service import get_user

        with pytest.raises(ValidationError, match='not found'):
            get_user(99999)


class TestChangeRole:
    """Tests for user_service.change_role()."""

    def test_changes_role_successfully(self, app, tech_user):
        """change_role() updates user's role."""
        from esb.services.user_service import change_role

        user = change_role(tech_user.id, 'staff', 'admin')
        assert user.role == 'staff'

    def test_change_role_persists(self, app, tech_user):
        """Role change is persisted to database."""
        from esb.services.user_service import change_role

        change_role(tech_user.id, 'staff', 'admin')
        found = _db.session.get(User, tech_user.id)
        assert found.role == 'staff'

    def test_invalid_role_raises(self, app, tech_user):
        """change_role() raises ValidationError on invalid role."""
        from esb.services.user_service import change_role

        with pytest.raises(ValidationError, match='role'):
            change_role(tech_user.id, 'superadmin', 'admin')

    def test_user_not_found_raises(self, app):
        """change_role() raises ValidationError when user not found."""
        from esb.services.user_service import change_role

        with pytest.raises(ValidationError, match='not found'):
            change_role(99999, 'staff', 'admin')

    def test_logs_role_changed_mutation(self, app, tech_user, capture):
        """change_role() logs user.role_changed mutation event."""
        from esb.services.user_service import change_role

        change_role(tech_user.id, 'staff', 'staffuser')
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
        assert entry['data']['username'] == 'techuser'


class TestChangePassword:
    """Tests for user_service.change_password()."""

    def test_changes_password_with_correct_current(self, app, staff_user):
        """change_password() updates password when current password is correct."""
        from esb.services.user_service import change_password

        user = change_password(staff_user.id, 'testpass', 'newpass123')
        assert user.check_password('newpass123')
        assert not user.check_password('testpass')

    def test_wrong_current_password_raises(self, app, staff_user):
        """change_password() raises ValidationError on wrong current password."""
        from esb.services.user_service import change_password

        with pytest.raises(ValidationError, match='Current password is incorrect'):
            change_password(staff_user.id, 'wrongpass', 'newpass123')

    def test_user_not_found_raises(self, app):
        """change_password() raises ValidationError when user not found."""
        from esb.services.user_service import change_password

        with pytest.raises(ValidationError, match='not found'):
            change_password(99999, 'anypass', 'newpass')

    def test_password_change_persists(self, app, staff_user):
        """Password change is persisted to database."""
        from esb.services.user_service import change_password

        change_password(staff_user.id, 'testpass', 'newpass123')
        found = _db.session.get(User, staff_user.id)
        assert found.check_password('newpass123')

    def test_logs_password_changed_mutation(self, app, staff_user, capture):
        """change_password() logs user.password_changed mutation event."""
        from esb.services.user_service import change_password

        change_password(staff_user.id, 'testpass', 'newpass123')
        entries = [
            json.loads(r.message) for r in capture.records
            if 'user.password_changed' in r.message
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry['event'] == 'user.password_changed'
        assert entry['user'] == 'staffuser'
        assert entry['data']['user_id'] == staff_user.id
        assert entry['data']['username'] == 'staffuser'
        # Verify no password values leaked in data
        assert 'password' not in json.dumps(entry['data'])


class TestResetPassword:
    """Tests for user_service.reset_password()."""

    def test_resets_password_successfully(self, app, tech_user):
        """reset_password() generates new temp password."""
        from esb.services.user_service import reset_password

        user, temp_password, slack_delivered = reset_password(tech_user.id, 'staffuser')
        assert user.id == tech_user.id
        assert isinstance(temp_password, str)
        assert len(temp_password) >= 12
        assert user.check_password(temp_password)
        assert not user.check_password('testpass')  # Old password no longer works
        assert slack_delivered is False  # No Slack configured

    def test_user_not_found_raises(self, app):
        """reset_password() raises ValidationError when user not found."""
        from esb.services.user_service import reset_password

        with pytest.raises(ValidationError, match='not found'):
            reset_password(99999, 'staffuser')

    def test_logs_password_reset_mutation(self, app, tech_user, capture):
        """reset_password() logs user.password_reset mutation event."""
        from esb.services.user_service import reset_password

        reset_password(tech_user.id, 'staffuser')
        entries = [
            json.loads(r.message) for r in capture.records
            if 'user.password_reset' in r.message
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry['event'] == 'user.password_reset'
        assert entry['user'] == 'staffuser'
        assert entry['data']['user_id'] == tech_user.id
        assert entry['data']['username'] == 'techuser'
        assert entry['data']['reset_by'] == 'staffuser'
        assert 'slack_delivered' in entry['data']
        # Verify no password values leaked in data
        assert 'password' not in json.dumps(entry['data'])

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_delivery_attempted(self, mock_client_cls, app, tech_user):
        """reset_password() attempts Slack delivery when configured."""
        from esb.services.user_service import reset_password

        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {'user': {'id': 'U12345'}}
        mock_client.conversations_open.return_value = {'channel': {'id': 'D12345'}}

        # Give the user a slack handle
        tech_user.slack_handle = '@techuser'
        _db.session.commit()

        user, temp_password, slack_delivered = reset_password(tech_user.id, 'staffuser')
        assert slack_delivered is True
        mock_client.chat_postMessage.assert_called_once()

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_failure_returns_false(self, mock_client_cls, app, tech_user):
        """reset_password() returns slack_delivered=False on Slack failure."""
        from esb.services.user_service import reset_password

        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = Exception('Slack error')

        tech_user.slack_handle = '@techuser'
        _db.session.commit()

        user, temp_password, slack_delivered = reset_password(tech_user.id, 'staffuser')
        assert slack_delivered is False
        assert user.check_password(temp_password)  # Password still changed


class TestSlackDelivery:
    """Tests for Slack temp password delivery."""

    def test_no_slack_token_returns_false(self, app):
        """When SLACK_BOT_TOKEN is empty, slack_delivered is False."""
        from esb.services.user_service import create_user

        app.config['SLACK_BOT_TOKEN'] = ''
        user, _, slack_delivered = create_user(
            username='noslack',
            email='noslack@example.com',
            role='technician',
            slack_handle='@noslack',
            created_by='admin',
        )
        assert slack_delivered is False

    def test_no_slack_handle_returns_false(self, app):
        """When user has no slack_handle, slack_delivered is False."""
        from esb.services.user_service import create_user

        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        user, _, slack_delivered = create_user(
            username='nohandle',
            email='nohandle@example.com',
            role='technician',
            slack_handle=None,
            created_by='admin',
        )
        assert slack_delivered is False

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_delivery_success(self, mock_client_cls, app):
        """When Slack is configured, delivery succeeds and returns True."""
        from esb.services.user_service import create_user

        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.return_value = {
            'user': {'id': 'U12345'}
        }
        mock_client.conversations_open.return_value = {
            'channel': {'id': 'D12345'}
        }

        user, temp_password, slack_delivered = create_user(
            username='slackok',
            email='slackok@example.com',
            role='technician',
            slack_handle='@slackok',
            created_by='admin',
        )
        assert slack_delivered is True
        mock_client.users_lookupByEmail.assert_called_once_with(
            email='slackok@example.com'
        )
        mock_client.conversations_open.assert_called_once_with(
            users=['U12345']
        )
        mock_client.chat_postMessage.assert_called_once()

    @patch('esb.services.user_service._slack_sdk_available', True)
    @patch('esb.services.user_service.WebClient')
    def test_slack_delivery_failure_returns_false(self, mock_client_cls, app):
        """When Slack API fails, slack_delivered is False and user is still created."""
        from esb.services.user_service import create_user

        app.config['SLACK_BOT_TOKEN'] = 'xoxb-fake-token'
        mock_client = MagicMock()
        mock_client_cls.return_value = mock_client
        mock_client.users_lookupByEmail.side_effect = Exception('Slack API error')

        user, temp_password, slack_delivered = create_user(
            username='slackfail',
            email='slackfail@example.com',
            role='technician',
            slack_handle='@slackfail',
            created_by='admin',
        )
        assert slack_delivered is False
        assert user is not None  # User still created
