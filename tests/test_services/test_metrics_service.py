"""Tests for the Prometheus metrics service."""

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
    before each test. _socket_mode_intended is included explicitly so that a
    Slack-init test running earlier in the session cannot leave it stale and
    bias an `is_socket_mode_enabled()` assertion in this file."""
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
    """Extract the value of an unlabelled metric from exposition text."""
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


class TestQueryPendingStats:
    def test_empty_table_returns_zero_and_none(self, app):
        count, oldest_ts = metrics_service._query_pending_stats()
        assert count == 0
        assert oldest_ts is None

    def test_only_delivered_rows_returns_zero_and_none(self, app):
        _make_pending(datetime.now(UTC) - timedelta(minutes=5), status='delivered')
        _make_pending(datetime.now(UTC) - timedelta(minutes=2), status='failed')
        count, oldest_ts = metrics_service._query_pending_stats()
        assert count == 0
        assert oldest_ts is None

    def test_counts_only_pending(self, app):
        _make_pending(datetime.now(UTC), status='pending')
        _make_pending(datetime.now(UTC), status='pending')
        _make_pending(datetime.now(UTC), status='delivered')
        count, _ = metrics_service._query_pending_stats()
        assert count == 2

    def test_oldest_timestamp_is_min_created_at(self, app):
        oldest = datetime.now(UTC) - timedelta(minutes=10)
        middle = datetime.now(UTC) - timedelta(minutes=5)
        newest = datetime.now(UTC)
        _make_pending(middle)
        _make_pending(oldest)
        _make_pending(newest)
        _, oldest_ts = metrics_service._query_pending_stats()
        # Allow a tiny float tolerance, but values come from datetime.timestamp()
        # so should match exactly.
        assert oldest_ts == oldest.timestamp()

    def test_oldest_timestamp_ignores_non_pending(self, app):
        # An older delivered row must not affect the oldest pending value.
        _make_pending(datetime.now(UTC) - timedelta(hours=1), status='delivered')
        pending_at = datetime.now(UTC) - timedelta(minutes=2)
        _make_pending(pending_at)
        _, oldest_ts = metrics_service._query_pending_stats()
        assert oldest_ts == pending_at.timestamp()


class TestRenderMetrics:
    def test_content_type_is_prometheus_exposition(self, app):
        _, content_type = metrics_service.render_metrics()
        assert 'text/plain' in content_type

    def test_empty_table_omits_oldest_metric(self, app):
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_pending_notifications_count 0.0' in text
        assert 'esb_oldest_pending_notification_timestamp_seconds' not in text

    def test_populated_table_includes_both_metrics(self, app):
        oldest = datetime.now(UTC) - timedelta(minutes=7)
        _make_pending(oldest)
        _make_pending(datetime.now(UTC))

        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert _extract_metric(text, 'esb_pending_notifications_count') == 2.0
        # prometheus_client formats large floats in scientific notation, so
        # parse the value rather than matching the literal.
        ts = _extract_metric(text, 'esb_oldest_pending_notification_timestamp_seconds')
        assert ts is not None
        assert abs(ts - oldest.timestamp()) < 0.001

    def test_help_and_type_lines_present(self, app):
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert '# HELP esb_pending_notifications_count' in text
        assert '# TYPE esb_pending_notifications_count gauge' in text


class TestWorkerStatusCollector:
    """Tests for the new system-health gauges from _WorkerStatusCollector."""

    def test_worker_last_iteration_timestamp_emitted_when_present(self, app):
        ts = datetime(2026, 5, 10, 12, 30, 0, tzinfo=UTC)
        _make_app_config('worker_last_iteration_at', ts.isoformat())

        body, _ = metrics_service.render_metrics()
        text = body.decode()
        value = _extract_metric(text, 'esb_worker_last_iteration_timestamp_seconds')
        assert value is not None
        assert abs(value - ts.timestamp()) < 1e-6

    def test_worker_last_iteration_timestamp_omitted_when_absent(self, app):
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_worker_last_iteration_timestamp_seconds' not in text

    def test_worker_last_iteration_timestamp_omitted_on_malformed_value(self, app, caplog):
        _make_app_config('worker_last_iteration_at', 'not a date')
        with caplog.at_level('WARNING', logger='esb.services.metrics_service'):
            body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_worker_last_iteration_timestamp_seconds' not in text
        assert any(
            'Failed to parse worker last-iteration timestamp' in r.getMessage()
            for r in caplog.records
        )
        # Other gauges still emit even though the timestamp parse failed.
        assert 'esb_socket_mode_enabled' in text
        assert 'esb_pending_notifications_count' in text

    def test_worker_last_iteration_timestamp_omitted_on_real_db_error(self, app, caplog):
        from sqlalchemy import select

        AppConfig.__table__.drop(_db.engine)
        try:
            with caplog.at_level('WARNING', logger='esb.services.metrics_service'):
                body, _ = metrics_service.render_metrics()
            text = body.decode()
            assert 'esb_worker_last_iteration_timestamp_seconds' not in text
            assert 'esb_socket_mode_enabled' in text
            assert 'esb_socket_mode_connected' in text
            assert any(
                'Failed to query worker_last_iteration_at from AppConfig' in r.getMessage()
                for r in caplog.records
            )
            # Genuinely verify the rollback inside _WorkerStatusCollector left
            # the session usable. Without rollback, this query would raise
            # PendingRollbackError. This is the crucial assertion: registration
            # order in render_metrics() puts _PendingNotificationsCollector
            # first, so without an explicit rollback inside the failing
            # collector, future requests reusing the session would break.
            result = _db.session.execute(select(PendingNotification)).all()
            assert result == []
        finally:
            AppConfig.__table__.create(_db.engine)

    def test_appconfig_query_error_logs_full_traceback_only_on_first_failure(
        self, app, caplog,
    ):
        AppConfig.__table__.drop(_db.engine)
        try:
            with caplog.at_level('WARNING', logger='esb.services.metrics_service'):
                metrics_service.render_metrics()
            first_records = [
                r for r in caplog.records
                if 'Failed to query worker_last_iteration_at' in r.getMessage()
            ]
            assert len(first_records) == 1
            assert first_records[0].exc_info is not None

            caplog.clear()
            with caplog.at_level('WARNING', logger='esb.services.metrics_service'):
                metrics_service.render_metrics()
            second_records = [
                r for r in caplog.records
                if 'Failed to query worker_last_iteration_at' in r.getMessage()
            ]
            assert len(second_records) == 1
            assert second_records[0].exc_info is None
            # Message must contain exception class+text but no traceback.
            assert 'OperationalError' in second_records[0].getMessage() or \
                   'ProgrammingError' in second_records[0].getMessage()
        finally:
            AppConfig.__table__.create(_db.engine)

    def test_socket_mode_enabled_emits_one_when_intent_true(self, app, monkeypatch):
        monkeypatch.setattr('esb.slack.is_socket_mode_enabled', lambda: True)
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_socket_mode_enabled 1.0' in text

    def test_socket_mode_enabled_emits_zero_when_intent_false(self, app, monkeypatch):
        monkeypatch.setattr('esb.slack.is_socket_mode_enabled', lambda: False)
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_socket_mode_enabled 0.0' in text

    def test_socket_mode_connected_emits_one_when_handler_bound(self, app, monkeypatch):
        monkeypatch.setattr('esb.slack.is_socket_mode_connected', lambda: True)
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_socket_mode_connected 1.0' in text

    def test_socket_mode_connected_emits_zero_when_handler_unbound(self, app, monkeypatch):
        monkeypatch.setattr('esb.slack.is_socket_mode_connected', lambda: False)
        body, _ = metrics_service.render_metrics()
        text = body.decode()
        assert 'esb_socket_mode_connected 0.0' in text
