"""Tests for the /metrics endpoint."""

import re
from datetime import UTC, datetime, timedelta

import pytest

from esb.extensions import db as _db
from esb.models.app_config import AppConfig
from esb.models.pending_notification import PendingNotification
from esb.services import metrics_service


@pytest.fixture(autouse=True)
def _reset_module_globals():
    """Reset Slack module-globals and the metrics-service first-failure latch
    before each test, mirroring the fixture in test_metrics_service.py.
    _socket_mode_intended is reset explicitly so a Slack-init test running
    earlier in the session can't leave it stale."""
    import esb.slack as slack_mod
    slack_mod._bolt_app = None
    slack_mod._socket_handler = None
    slack_mod._socket_mode_intended = False
    metrics_service._app_config_query_failed_once = False
    yield
    slack_mod._bolt_app = None
    slack_mod._socket_handler = None
    slack_mod._socket_mode_intended = False
    metrics_service._app_config_query_failed_once = False


def _make_app_config(key, value):
    row = AppConfig(key=key, value=value)
    _db.session.add(row)
    _db.session.commit()
    return row


def _extract_metric(text: str, name: str) -> float | None:
    match = re.search(rf'^{re.escape(name)} (\S+)$', text, re.MULTILINE)
    return float(match.group(1)) if match else None


def _make_pending(created_at, status='pending'):
    n = PendingNotification(
        notification_type='slack_message',
        target='#test',
        payload={'msg': 'x'},
        status=status,
        created_at=created_at,
    )
    _db.session.add(n)
    _db.session.commit()
    return n


class TestMetricsEndpoint:
    def test_unauthenticated_access_returns_200(self, client):
        response = client.get('/metrics')
        assert response.status_code == 200

    def test_returns_prometheus_content_type(self, client):
        response = client.get('/metrics')
        assert 'text/plain' in response.content_type

    def test_content_type_preserves_version_parameter(self, client):
        """The Content-Type header must carry Prometheus's version and charset
        parameters verbatim. Catches a regression to Response(..., mimetype=...)
        which strips parameters from the header."""
        response = client.get('/metrics')
        assert 'version=' in response.content_type
        assert 'charset=utf-8' in response.content_type

    def test_empty_table_emits_zero_count_and_omits_oldest(self, client):
        response = client.get('/metrics')
        text = response.data.decode()
        assert 'esb_pending_notifications_count 0.0' in text
        assert 'esb_oldest_pending_notification_timestamp_seconds' not in text

    def test_populated_table_emits_both_metrics(self, app, client):
        oldest = datetime.now(UTC) - timedelta(minutes=3)
        _make_pending(oldest)
        _make_pending(datetime.now(UTC))

        response = client.get('/metrics')
        text = response.data.decode()
        assert _extract_metric(text, 'esb_pending_notifications_count') == 2.0
        ts = _extract_metric(text, 'esb_oldest_pending_notification_timestamp_seconds')
        assert ts is not None
        assert abs(ts - oldest.timestamp()) < 0.001

    def test_only_pending_status_counted(self, app, client):
        _make_pending(datetime.now(UTC), status='delivered')
        _make_pending(datetime.now(UTC), status='failed')
        _make_pending(datetime.now(UTC), status='pending')

        response = client.get('/metrics')
        text = response.data.decode()
        assert 'esb_pending_notifications_count 1.0' in text


class TestMetricsEndpointSystemHealth:
    """Tests for the worker-timestamp and Socket Mode gauges added in this PR."""

    def test_metrics_endpoint_includes_worker_timestamp_when_present(self, app, client):
        ts = datetime(2026, 5, 10, 12, 0, 0, tzinfo=UTC)
        _make_app_config('worker_last_iteration_at', ts.isoformat())

        response = client.get('/metrics')
        assert response.status_code == 200
        text = response.data.decode()
        assert 'esb_worker_last_iteration_timestamp_seconds' in text

    def test_metrics_endpoint_omits_worker_timestamp_when_absent(self, app, client):
        response = client.get('/metrics')
        assert response.status_code == 200
        text = response.data.decode()
        assert 'esb_worker_last_iteration_timestamp_seconds' not in text

    def test_metrics_endpoint_returns_200_when_appconfig_table_missing(self, app, client):
        AppConfig.__table__.drop(_db.engine)
        try:
            response = client.get('/metrics')
            assert response.status_code == 200
            text = response.data.decode()
            assert 'esb_worker_last_iteration_timestamp_seconds' not in text
            assert 'esb_socket_mode_enabled' in text
            assert 'esb_socket_mode_connected' in text
            assert 'esb_pending_notifications_count' in text
        finally:
            AppConfig.__table__.create(_db.engine)

    def test_metrics_endpoint_socket_mode_state_enabled_connected(
        self, app, client, monkeypatch,
    ):
        monkeypatch.setattr('esb.slack.is_socket_mode_enabled', lambda: True)
        monkeypatch.setattr('esb.slack.is_socket_mode_connected', lambda: True)
        response = client.get('/metrics')
        text = response.data.decode()
        assert 'esb_socket_mode_enabled 1.0' in text
        assert 'esb_socket_mode_connected 1.0' in text

    def test_metrics_endpoint_socket_mode_state_enabled_not_connected(
        self, app, client, monkeypatch,
    ):
        monkeypatch.setattr('esb.slack.is_socket_mode_enabled', lambda: True)
        monkeypatch.setattr('esb.slack.is_socket_mode_connected', lambda: False)
        response = client.get('/metrics')
        text = response.data.decode()
        assert 'esb_socket_mode_enabled 1.0' in text
        assert 'esb_socket_mode_connected 0.0' in text

    def test_metrics_endpoint_socket_mode_state_neither(
        self, app, client, monkeypatch,
    ):
        monkeypatch.setattr('esb.slack.is_socket_mode_enabled', lambda: False)
        monkeypatch.setattr('esb.slack.is_socket_mode_connected', lambda: False)
        response = client.get('/metrics')
        text = response.data.decode()
        assert 'esb_socket_mode_enabled 0.0' in text
        assert 'esb_socket_mode_connected 0.0' in text
