"""Tests for authentication service."""

import pytest

from esb.extensions import db as _db
from esb.models.user import User
from esb.services.auth_service import authenticate, load_user
from esb.utils.exceptions import ValidationError


@pytest.fixture
def staff_user(app):
    """Create and persist a staff user."""
    user = User(username='admin', email='admin@example.com', role='staff')
    user.set_password('staffpass')
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def tech_user(app):
    """Create and persist a technician user."""
    user = User(username='tech1', email='tech1@example.com', role='technician')
    user.set_password('techpass')
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def inactive_user(app):
    """Create and persist an inactive user."""
    user = User(
        username='disabled', email='disabled@example.com', is_active=False
    )
    user.set_password('disabledpass')
    _db.session.add(user)
    _db.session.commit()
    return user


class TestAuthenticate:
    """Tests for authenticate() function."""

    def test_valid_credentials_returns_user(self, staff_user):
        """Successful auth returns the User object."""
        result = authenticate('admin', 'staffpass')
        assert result.id == staff_user.id
        assert result.username == 'admin'

    def test_wrong_password_raises(self, staff_user):
        """Wrong password raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid username or password'):
            authenticate('admin', 'wrongpass')

    def test_unknown_username_raises(self, app):
        """Non-existent username raises ValidationError."""
        with pytest.raises(ValidationError, match='Invalid username or password'):
            authenticate('nonexistent', 'anypass')

    def test_inactive_user_raises(self, inactive_user):
        """Inactive user raises ValidationError even with correct password."""
        with pytest.raises(ValidationError, match='Invalid username or password'):
            authenticate('disabled', 'disabledpass')

    def test_technician_can_authenticate(self, tech_user):
        """Technician can authenticate successfully."""
        result = authenticate('tech1', 'techpass')
        assert result.role == 'technician'


class TestLoadUser:
    """Tests for load_user() function."""

    def test_returns_user_by_id(self, staff_user):
        """load_user returns user when found and active."""
        result = load_user(staff_user.id)
        assert result is not None
        assert result.id == staff_user.id

    def test_returns_none_for_missing_id(self, app):
        """load_user returns None for non-existent ID."""
        result = load_user(9999)
        assert result is None

    def test_returns_none_for_inactive_user(self, inactive_user):
        """load_user returns None when user is inactive."""
        result = load_user(inactive_user.id)
        assert result is None

    def test_accepts_string_id(self, staff_user):
        """load_user accepts string ID (Flask-Login passes string)."""
        result = load_user(str(staff_user.id))
        assert result is not None
        assert result.id == staff_user.id
