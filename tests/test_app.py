"""Smoke tests for ESB application."""

import os

from esb import create_app


class TestAppFactory:
    """Tests for the app factory."""

    def test_app_creates(self):
        """App factory creates a Flask app."""
        app = create_app('testing')
        assert app is not None

    def test_testing_config(self):
        """App uses testing configuration."""
        app = create_app('testing')
        assert app.config['TESTING'] is True

    def test_health_endpoint(self, client):
        """Health endpoint responds with 200."""
        resp = client.get('/health')
        assert resp.status_code == 200
        assert resp.data == b'ok'

    def test_index_redirects_to_dashboard(self, client):
        """Index route redirects to public status dashboard."""
        resp = client.get('/')
        assert resp.status_code == 302
        assert '/public/' in resp.headers['Location']

    def test_blueprints_registered(self):
        """All expected blueprints are registered."""
        app = create_app('testing')
        expected = {'equipment', 'repairs', 'admin', 'public', 'auth'}
        assert expected.issubset(set(app.blueprints.keys()))

    def test_404_error(self, client):
        """Non-existent route returns 404."""
        resp = client.get('/nonexistent-route-that-does-not-exist')
        assert resp.status_code == 404

    def test_upload_path_is_absolute(self):
        """UPLOAD_PATH is normalized to an absolute path at startup.

        Ensures file serving works regardless of the process working directory,
        which differs between dev (project root) and Docker deployments (/app).
        """
        app = create_app('testing')
        with app.app_context():
            assert os.path.isabs(app.config['UPLOAD_PATH'])
