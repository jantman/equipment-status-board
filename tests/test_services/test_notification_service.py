"""Tests for the notification service."""

from datetime import UTC, datetime, timedelta
from unittest.mock import patch

from esb.extensions import db as _db
from esb.models.pending_notification import PendingNotification
from esb.services import notification_service
from esb.services.notification_service import (
    BACKOFF_SCHEDULE,
    get_pending_notifications,
    mark_delivered,
    mark_failed,
    process_notification,
    queue_notification,
)


def _create_notification(notification_type='slack_message', target='#test',
                         payload=None, status='pending', **kwargs):
    """Helper to create a notification directly in the database."""
    notification = PendingNotification(
        notification_type=notification_type,
        target=target,
        payload=payload,
        status=status,
        **kwargs,
    )
    _db.session.add(notification)
    _db.session.commit()
    return notification


class TestQueueNotification:
    """Tests for queue_notification()."""

    def test_creates_pending_row(self, app):
        """queue_notification creates a row with status 'pending'."""
        result = queue_notification('slack_message', '#woodshop', {'msg': 'test'})

        assert result.id is not None
        assert result.notification_type == 'slack_message'
        assert result.target == '#woodshop'
        assert result.status == 'pending'
        assert result.retry_count == 0
        assert result.created_at is not None

    def test_stores_payload_as_json(self, app):
        """queue_notification stores payload as JSON."""
        payload = {'equipment_name': 'SawStop', 'severity': 'Down'}
        result = queue_notification('slack_message', '#woodshop', payload)

        _db.session.expire(result)
        saved = _db.session.get(PendingNotification, result.id)
        assert saved.payload == payload

    def test_logs_mutation(self, app, capture):
        """queue_notification logs a mutation event."""
        queue_notification('slack_message', '#test', {'msg': 'hello'})

        assert len(capture.records) == 1
        assert 'notification.queued' in capture.records[0].getMessage()


class TestGetPendingNotifications:
    """Tests for get_pending_notifications()."""

    def test_returns_pending_with_no_retry_time(self, app):
        """Returns pending notifications with no next_retry_at."""
        n = _create_notification()
        result = get_pending_notifications()
        assert len(result) == 1
        assert result[0].id == n.id

    def test_returns_pending_with_past_retry_time(self, app):
        """Returns pending notifications with next_retry_at in the past."""
        n = _create_notification(
            next_retry_at=datetime.now(UTC) - timedelta(minutes=1),
        )
        result = get_pending_notifications()
        assert len(result) == 1
        assert result[0].id == n.id

    def test_excludes_delivered_notifications(self, app):
        """Does not return delivered notifications."""
        _create_notification(status='delivered')
        result = get_pending_notifications()
        assert len(result) == 0

    def test_excludes_future_retry_notifications(self, app):
        """Does not return notifications with future next_retry_at."""
        _create_notification(
            next_retry_at=datetime.now(UTC) + timedelta(hours=1),
        )
        result = get_pending_notifications()
        assert len(result) == 0

    def test_returns_empty_when_no_notifications(self, app):
        """Returns empty list when no pending notifications exist."""
        result = get_pending_notifications()
        assert result == []

    def test_orders_by_created_at(self, app):
        """Returns notifications ordered by created_at ascending."""
        n1 = _create_notification(target='#first')
        n2 = _create_notification(target='#second')
        result = get_pending_notifications()
        assert len(result) == 2
        assert result[0].id == n1.id
        assert result[1].id == n2.id


class TestMarkDelivered:
    """Tests for mark_delivered()."""

    def test_updates_status_and_delivered_at(self, app):
        """mark_delivered sets status to 'delivered' and sets delivered_at."""
        n = _create_notification()
        result = mark_delivered(n.id)

        assert result.status == 'delivered'
        assert result.delivered_at is not None

    def test_logs_mutation(self, app, capture):
        """mark_delivered logs a mutation event."""
        n = _create_notification()
        mark_delivered(n.id)

        messages = [r.getMessage() for r in capture.records]
        assert any('notification.delivered' in m for m in messages)


class TestMarkFailed:
    """Tests for mark_failed()."""

    def test_increments_retry_count_and_sets_error(self, app):
        """mark_failed increments retry_count and sets error_message."""
        n = _create_notification()
        result = mark_failed(n.id, 'Connection refused')

        assert result.retry_count == 1
        assert result.error_message == 'Connection refused'

    def test_computes_correct_backoff_intervals(self, app):
        """mark_failed uses correct exponential backoff schedule."""
        n = _create_notification()

        for i, expected_seconds in enumerate(BACKOFF_SCHEDULE):
            before = datetime.now(UTC).replace(tzinfo=None)
            mark_failed(n.id, f'Error attempt {i + 1}')
            after = datetime.now(UTC).replace(tzinfo=None)

            expected_min = before + timedelta(seconds=expected_seconds)
            expected_max = after + timedelta(seconds=expected_seconds)
            assert expected_min <= n.next_retry_at <= expected_max
            assert n.retry_count == i + 1

    def test_caps_backoff_at_one_hour(self, app):
        """mark_failed caps backoff at 1 hour for retries beyond schedule."""
        n = _create_notification(retry_count=10)

        before = datetime.now(UTC).replace(tzinfo=None)
        mark_failed(n.id, 'Still failing')
        after = datetime.now(UTC).replace(tzinfo=None)

        expected_min = before + timedelta(seconds=3600)
        expected_max = after + timedelta(seconds=3600)
        assert expected_min <= n.next_retry_at <= expected_max

    def test_logs_mutation(self, app, capture):
        """mark_failed logs a mutation event."""
        n = _create_notification()
        mark_failed(n.id, 'Error')

        messages = [r.getMessage() for r in capture.records]
        assert any('notification.failed' in m for m in messages)


class TestProcessNotification:
    """Tests for process_notification()."""

    def test_unknown_type_raises_value_error(self, app):
        """process_notification raises ValueError for unknown type."""
        n = _create_notification(notification_type='email')
        import pytest
        with pytest.raises(ValueError, match='Unknown notification type'):
            process_notification(n)

    def test_slack_message_calls_deliver_handler(self, app):
        """process_notification calls _deliver_slack_message for slack_message type."""
        n = _create_notification(notification_type='slack_message')
        with patch.object(notification_service, '_deliver_slack_message') as mock:
            process_notification(n)
            mock.assert_called_once_with(n)

    def test_static_page_push_calls_deliver_handler(self, app):
        """process_notification calls _deliver_static_page_push for static_page_push type."""
        n = _create_notification(notification_type='static_page_push')
        with patch.object(notification_service, '_deliver_static_page_push') as mock:
            process_notification(n)
            mock.assert_called_once_with(n)

    def test_slack_stub_raises_not_implemented(self, app):
        """_deliver_slack_message raises NotImplementedError."""
        n = _create_notification(notification_type='slack_message')
        import pytest
        with pytest.raises(NotImplementedError):
            notification_service._deliver_slack_message(n)

    def test_static_page_stub_raises_not_implemented(self, app):
        """_deliver_static_page_push raises NotImplementedError."""
        n = _create_notification(notification_type='static_page_push')
        import pytest
        with pytest.raises(NotImplementedError):
            notification_service._deliver_static_page_push(n)
