"""Tests for RBAC decorator."""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from esb.utils.decorators import ROLE_HIERARCHY, role_required


@pytest.fixture
def app():
    """Create a minimal Flask app for testing."""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'test-secret'
    app.config['TESTING'] = True

    from flask_login import LoginManager
    login_manager = LoginManager()
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return None

    @app.route('/technician-only')
    @role_required('technician')
    def technician_route():
        return 'ok'

    @app.route('/staff-only')
    @role_required('staff')
    def staff_route():
        return 'ok'

    return app


def _make_user(role):
    """Create a mock user with the given role."""
    user = MagicMock()
    user.is_authenticated = True
    user.is_active = True
    user.is_anonymous = False
    user.role = role
    user.get_id = MagicMock(return_value='1')
    return user


class TestRoleHierarchy:
    """Tests for role hierarchy constants."""

    def test_staff_outranks_technician(self):
        assert ROLE_HIERARCHY['staff'] > ROLE_HIERARCHY['technician']

    def test_technician_has_level(self):
        assert ROLE_HIERARCHY['technician'] >= 1


class TestRoleRequired:
    """Tests for @role_required decorator."""

    def test_unauthenticated_redirects(self, app):
        """Unauthenticated users are redirected (handled by Flask-Login)."""
        with app.test_client() as client:
            resp = client.get('/staff-only')
            assert resp.status_code in (302, 401)

    def test_staff_gets_200_on_staff_route(self, app):
        """Staff user can access staff-only route."""
        user = _make_user('staff')
        with app.test_client() as client:
            with patch('flask_login.utils._get_user', return_value=user):
                resp = client.get('/staff-only')
                assert resp.status_code == 200

    def test_staff_gets_200_on_technician_route(self, app):
        """Staff user can access technician-only route (hierarchy)."""
        user = _make_user('staff')
        with app.test_client() as client:
            with patch('flask_login.utils._get_user', return_value=user):
                resp = client.get('/technician-only')
                assert resp.status_code == 200

    def test_technician_gets_403_on_staff_route(self, app):
        """Technician user gets 403 on staff-only route."""
        user = _make_user('technician')
        with app.test_client() as client:
            with patch('flask_login.utils._get_user', return_value=user):
                resp = client.get('/staff-only')
                assert resp.status_code == 403

    def test_technician_gets_200_on_technician_route(self, app):
        """Technician user can access technician-only route."""
        user = _make_user('technician')
        with app.test_client() as client:
            with patch('flask_login.utils._get_user', return_value=user):
                resp = client.get('/technician-only')
                assert resp.status_code == 200

    def test_unknown_role_gets_403(self, app):
        """Unknown role gets 403 on any protected route."""
        user = _make_user('viewer')
        with app.test_client() as client:
            with patch('flask_login.utils._get_user', return_value=user):
                resp = client.get('/technician-only')
                assert resp.status_code == 403

    def test_decorator_preserves_function_name(self, app):
        """Decorated function preserves original name via @wraps."""
        @role_required('staff')
        def my_view():
            return 'ok'
        assert my_view.__name__ == 'my_view'
