"""Tests for Slack module initialization (esb/slack/__init__.py)."""

from unittest.mock import MagicMock, patch

import pytest

from esb import create_app
from esb.config import Config


class TestSlackDisabled:
    """Tests for when Slack is NOT configured (default TestingConfig)."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Create app without Slack configured."""
        self.app = create_app('testing')
        with self.app.app_context():
            from esb.extensions import db
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()

    def test_app_starts_cleanly_without_slack(self):
        """App starts normally when SLACK_BOT_TOKEN is empty."""
        client = self.app.test_client()
        resp = client.get('/health')
        assert resp.status_code == 200

    def test_no_slack_routes_when_disabled(self):
        """No /slack/events route when Slack is not configured."""
        client = self.app.test_client()
        resp = client.post('/slack/events')
        assert resp.status_code == 404

    def test_no_slack_in_url_map_when_disabled(self):
        """No /slack/events in URL map when Slack is disabled."""
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]
        assert '/slack/events' not in rules


class TestSlackEnabled:
    """Tests for when Slack IS configured."""

    @pytest.fixture(autouse=True)
    def setup_app(self):
        """Create app with Slack configured (mocking Bolt App)."""
        import esb.slack as slack_mod
        slack_mod._bolt_app = None
        slack_mod._handler = None

        self.mock_bolt_app = MagicMock()
        self.mock_handler = MagicMock()

        with patch.object(Config, 'SLACK_BOT_TOKEN', 'xoxb-test-token'), \
             patch.object(Config, 'SLACK_SIGNING_SECRET', 'test-signing-secret'), \
             patch('slack_bolt.App', return_value=self.mock_bolt_app) as self.mock_app_cls, \
             patch('slack_bolt.adapter.flask.SlackRequestHandler',
                   return_value=self.mock_handler):
            self.app = create_app('testing')

            with self.app.app_context():
                from esb.extensions import db
                db.create_all()
                yield
                db.session.remove()
                db.drop_all()

        slack_mod._bolt_app = None
        slack_mod._handler = None

    def test_slack_module_loads_when_configured(self):
        """Slack module initializes when SLACK_BOT_TOKEN is configured."""
        import esb.slack as slack_mod
        assert slack_mod._bolt_app is not None
        assert slack_mod._handler is not None

    def test_slack_events_route_exists(self):
        """The /slack/events route is registered when Slack is configured."""
        rules = [rule.rule for rule in self.app.url_map.iter_rules()]
        assert '/slack/events' in rules

    def test_slack_events_route_is_post(self):
        """The /slack/events route only accepts POST."""
        client = self.app.test_client()
        resp = client.get('/slack/events')
        assert resp.status_code == 405

    def test_slack_events_delegates_to_handler(self):
        """POST /slack/events delegates to the Bolt SlackRequestHandler."""
        self.mock_handler.handle.return_value = ('ok', 200, {})
        client = self.app.test_client()
        client.post('/slack/events', data=b'{}',
                    content_type='application/json')
        self.mock_handler.handle.assert_called_once()

    def test_slack_blueprint_csrf_exempt(self):
        """The slack blueprint is CSRF exempt."""
        self.app.config['WTF_CSRF_ENABLED'] = True
        self.mock_handler.handle.return_value = ('ok', 200, {})
        client = self.app.test_client()
        client.post('/slack/events', data=b'{}',
                    content_type='application/json')
        self.mock_handler.handle.assert_called_once()

    def test_bolt_app_event_handler_registered(self):
        """A 'message' event handler is registered on the Bolt app."""
        self.mock_bolt_app.event.assert_called_with('message')

    def test_app_starts_cleanly_with_slack(self):
        """App starts and responds to health check with Slack configured."""
        client = self.app.test_client()
        resp = client.get('/health')
        assert resp.status_code == 200


class TestSlackMissingSigningSecret:
    """Tests for when only SLACK_BOT_TOKEN is set but signing secret is missing."""

    def test_slack_disabled_without_signing_secret(self):
        """Slack module is not loaded when SLACK_SIGNING_SECRET is missing."""
        with patch.object(Config, 'SLACK_BOT_TOKEN', 'xoxb-test-token'), \
             patch.object(Config, 'SLACK_SIGNING_SECRET', ''):
            app = create_app('testing')
            with app.app_context():
                from esb.extensions import db
                db.create_all()

                rules = [rule.rule for rule in app.url_map.iter_rules()]
                assert '/slack/events' not in rules

                db.session.remove()
                db.drop_all()
