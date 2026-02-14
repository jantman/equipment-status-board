"""Shared test fixtures for ESB application."""

import pytest

from esb import create_app
from esb.extensions import db as _db


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
