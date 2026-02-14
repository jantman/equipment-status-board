"""Shared test fixtures for ESB application."""

import pytest

from esb import create_app
from esb.extensions import db as _db
from esb.models.user import User


@pytest.fixture
def app():
    """Create a Flask application configured for testing."""
    app = create_app('testing')
    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture
def client(app):
    """Create a Flask test client."""
    return app.test_client()


@pytest.fixture
def db(app):
    """Provide the database session for tests."""
    return _db


def _create_user(role, username=None, password='testpass'):
    """Helper to create a user in the test database."""
    username = username or f'test_{role}'
    user = User(
        username=username,
        email=f'{username}@example.com',
        role=role,
    )
    user.set_password(password)
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture
def staff_user(app):
    """Create a staff user in the test database."""
    return _create_user('staff', 'staffuser')


@pytest.fixture
def tech_user(app):
    """Create a technician user in the test database."""
    return _create_user('technician', 'techuser')


@pytest.fixture
def staff_client(client, staff_user):
    """Return a test client logged in as a staff user."""
    client.post('/auth/login', data={
        'username': 'staffuser',
        'password': 'testpass',
    })
    return client


@pytest.fixture
def tech_client(client, tech_user):
    """Return a test client logged in as a technician user."""
    client.post('/auth/login', data={
        'username': 'techuser',
        'password': 'testpass',
    })
    return client
