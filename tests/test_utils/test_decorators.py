"""Tests for RBAC decorator with real User model."""

from esb.extensions import db as _db
from esb.models.user import User
from esb.utils.decorators import ROLE_HIERARCHY, role_required


def _create_user_and_login(app, client, username, role):
    """Create a user in the DB and log them in via the auth view."""
    user = User(username=username, email=f'{username}@example.com', role=role)
    user.set_password('testpass')
    _db.session.add(user)
    _db.session.commit()
    client.post('/auth/login', data={
        'username': username,
        'password': 'testpass',
    })
    return user


class TestRoleHierarchy:
    """Tests for role hierarchy constants."""

    def test_staff_outranks_technician(self):
        assert ROLE_HIERARCHY['staff'] > ROLE_HIERARCHY['technician']

    def test_technician_has_level(self):
        assert ROLE_HIERARCHY['technician'] >= 1


class TestRoleRequired:
    """Tests for @role_required decorator with real User model instances."""

    def test_unauthenticated_redirects(self, app):
        """Unauthenticated users are redirected to login."""
        @app.route('/test-dec-staff')
        @role_required('staff')
        def dec_staff_route():
            return 'ok'

        with app.test_client() as client:
            resp = client.get('/test-dec-staff')
            assert resp.status_code == 302
            assert '/auth/login' in resp.headers['Location']

    def test_staff_gets_200_on_staff_route(self, app):
        """Staff user can access staff-only route."""
        @app.route('/test-dec-staff2')
        @role_required('staff')
        def dec_staff_route2():
            return 'ok'

        client = app.test_client()
        _create_user_and_login(app, client, 'dec_staff', 'staff')
        resp = client.get('/test-dec-staff2')
        assert resp.status_code == 200

    def test_staff_gets_200_on_technician_route(self, app):
        """Staff user can access technician-only route (hierarchy)."""
        @app.route('/test-dec-tech')
        @role_required('technician')
        def dec_tech_route():
            return 'ok'

        client = app.test_client()
        _create_user_and_login(app, client, 'dec_staff2', 'staff')
        resp = client.get('/test-dec-tech')
        assert resp.status_code == 200

    def test_technician_gets_403_on_staff_route(self, app):
        """Technician user gets 403 on staff-only route."""
        @app.route('/test-dec-staff3')
        @role_required('staff')
        def dec_staff_route3():
            return 'ok'

        client = app.test_client()
        _create_user_and_login(app, client, 'dec_tech', 'technician')
        resp = client.get('/test-dec-staff3')
        assert resp.status_code == 403

    def test_technician_gets_200_on_technician_route(self, app):
        """Technician user can access technician-only route."""
        @app.route('/test-dec-tech2')
        @role_required('technician')
        def dec_tech_route2():
            return 'ok'

        client = app.test_client()
        _create_user_and_login(app, client, 'dec_tech2', 'technician')
        resp = client.get('/test-dec-tech2')
        assert resp.status_code == 200

    def test_decorator_preserves_function_name(self, app):
        """Decorated function preserves original name via @wraps."""
        @role_required('staff')
        def my_view():
            return 'ok'
        assert my_view.__name__ == 'my_view'
