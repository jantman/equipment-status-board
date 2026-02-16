"""Tests for the notification service."""

import signal
from datetime import UTC, datetime, timedelta
from unittest.mock import patch

import pytest

from esb.extensions import db as _db
from esb.models.pending_notification import PendingNotification
from esb.services import notification_service
from esb.services.notification_service import (
    BACKOFF_SCHEDULE,
    DEFAULT_BATCH_SIZE,
    MAX_RETRIES,
    VALID_NOTIFICATION_TYPES,
    get_pending_notifications,
    mark_delivered,
    mark_failed,
    process_notification,
    queue_notification,
    run_worker_loop,
)
from esb.utils.exceptions import ValidationError


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

    def test_rejects_invalid_notification_type(self, app):
        """queue_notification raises ValidationError for invalid type."""
        with pytest.raises(ValidationError, match='Invalid notification_type'):
            queue_notification('email', '#test', {'msg': 'hello'})

    def test_rejects_empty_notification_type(self, app):
        """queue_notification raises ValidationError for empty string type."""
        with pytest.raises(ValidationError, match='Invalid notification_type'):
            queue_notification('', '#test')

    def test_accepts_all_valid_types(self, app):
        """queue_notification accepts all VALID_NOTIFICATION_TYPES."""
        for ntype in VALID_NOTIFICATION_TYPES:
            result = queue_notification(ntype, '#test')
            assert result.notification_type == ntype


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

    def test_excludes_failed_notifications(self, app):
        """Does not return permanently failed notifications."""
        _create_notification(status='failed')
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

    def test_respects_batch_size_limit(self, app):
        """Returns at most batch_size notifications."""
        for i in range(5):
            _create_notification(target=f'#channel-{i}')
        result = get_pending_notifications(batch_size=3)
        assert len(result) == 3

    def test_default_batch_size(self, app):
        """Default batch_size is DEFAULT_BATCH_SIZE."""
        assert DEFAULT_BATCH_SIZE == 100


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

    def test_raises_on_nonexistent_id(self, app):
        """mark_delivered raises ValidationError for nonexistent notification."""
        with pytest.raises(ValidationError, match='not found'):
            mark_delivered(99999)


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
        fixed_now = datetime(2026, 1, 15, 12, 0, 0)

        for i, expected_seconds in enumerate(BACKOFF_SCHEDULE):
            with patch('esb.services.notification_service.datetime') as mock_dt:
                mock_dt.now.return_value = fixed_now
                mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
                mark_failed(n.id, f'Error attempt {i + 1}')

            expected_retry = fixed_now + timedelta(seconds=expected_seconds)
            assert n.next_retry_at == expected_retry
            assert n.retry_count == i + 1

    def test_caps_backoff_at_one_hour(self, app):
        """mark_failed caps backoff at 1 hour for retries beyond schedule."""
        n = _create_notification(retry_count=8)
        fixed_now = datetime(2026, 1, 15, 12, 0, 0)

        with patch('esb.services.notification_service.datetime') as mock_dt:
            mock_dt.now.return_value = fixed_now
            mock_dt.side_effect = lambda *a, **kw: datetime(*a, **kw)
            mark_failed(n.id, 'Still failing')

        expected_retry = fixed_now + timedelta(seconds=3600)
        assert n.next_retry_at == expected_retry

    def test_logs_mutation(self, app, capture):
        """mark_failed logs a mutation event."""
        n = _create_notification()
        mark_failed(n.id, 'Error')

        messages = [r.getMessage() for r in capture.records]
        assert any('notification.failed' in m for m in messages)

    def test_raises_on_nonexistent_id(self, app):
        """mark_failed raises ValidationError for nonexistent notification."""
        with pytest.raises(ValidationError, match='not found'):
            mark_failed(99999, 'Error')

    def test_marks_permanently_failed_after_max_retries(self, app):
        """mark_failed sets status to 'failed' after MAX_RETRIES attempts."""
        n = _create_notification(retry_count=MAX_RETRIES - 1)
        result = mark_failed(n.id, 'Final failure')

        assert result.status == 'failed'
        assert result.retry_count == MAX_RETRIES
        assert result.next_retry_at is None
        assert result.error_message == 'Final failure'

    def test_permanently_failed_excluded_from_pending(self, app):
        """Permanently failed notifications are not returned by get_pending_notifications."""
        n = _create_notification(retry_count=MAX_RETRIES - 1)
        mark_failed(n.id, 'Final failure')

        result = get_pending_notifications()
        assert len(result) == 0

    def test_permanently_failed_logs_distinct_event(self, app, capture):
        """mark_failed logs 'notification.permanently_failed' after max retries."""
        n = _create_notification(retry_count=MAX_RETRIES - 1)
        mark_failed(n.id, 'Done')

        messages = [r.getMessage() for r in capture.records]
        assert any('notification.permanently_failed' in m for m in messages)


class TestProcessNotification:
    """Tests for process_notification()."""

    def test_unknown_type_raises_value_error(self, app):
        """process_notification raises ValueError for unknown type."""
        n = _create_notification(notification_type='email')
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
        with pytest.raises(NotImplementedError):
            notification_service._deliver_slack_message(n)

    def test_static_page_push_no_longer_raises_not_implemented(self, app):
        """_deliver_static_page_push no longer raises NotImplementedError."""
        from esb.services import static_page_service
        n = _create_notification(notification_type='static_page_push')
        with patch.object(static_page_service, 'generate_and_push'):
            # Should not raise NotImplementedError
            notification_service._deliver_static_page_push(n)

    def test_static_page_push_delegates_to_service(self, app):
        """_deliver_static_page_push delegates to static_page_service.generate_and_push()."""
        from esb.services import static_page_service
        n = _create_notification(notification_type='static_page_push')
        with patch.object(static_page_service, 'generate_and_push') as mock_gap:
            notification_service._deliver_static_page_push(n)
            mock_gap.assert_called_once()

    def test_static_page_push_exceptions_propagate(self, app):
        """Exceptions from static_page_service propagate to the worker loop."""
        from esb.services import static_page_service
        n = _create_notification(notification_type='static_page_push')
        with patch.object(static_page_service, 'generate_and_push',
                          side_effect=RuntimeError('Push failed')):
            with pytest.raises(RuntimeError, match='Push failed'):
                notification_service._deliver_static_page_push(n)


class TestRunWorkerLoop:
    """Tests for run_worker_loop()."""

    def test_registers_signal_handlers(self, app):
        """run_worker_loop registers SIGTERM and SIGINT handlers."""
        with patch.object(notification_service, 'get_pending_notifications', return_value=[]), \
             patch('esb.services.notification_service.signal') as mock_signal, \
             patch('esb.services.notification_service.time') as mock_time:
            # Simulate shutdown after first iteration
            mock_time.sleep.side_effect = lambda _: setattr(
                mock_signal, '_shutdown_triggered', True
            )

            # Actually use a side_effect on get_pending_notifications to break the loop
            call_count = 0

            def stop_after_one():
                nonlocal call_count
                call_count += 1
                if call_count > 1:
                    # Trigger the signal handler that was registered
                    raise KeyboardInterrupt
                return []

            with patch.object(notification_service, 'get_pending_notifications',
                              side_effect=stop_after_one):
                # We need to trigger shutdown — simulate via signal handler
                original_handlers = {}

                def capture_signal(sig, handler):
                    original_handlers[sig] = handler

                mock_signal.signal.side_effect = capture_signal
                mock_signal.SIGTERM = signal.SIGTERM
                mock_signal.SIGINT = signal.SIGINT

                # Break the loop after first sleep
                def trigger_shutdown(_):
                    if signal.SIGTERM in original_handlers:
                        original_handlers[signal.SIGTERM](signal.SIGTERM, None)

                mock_time.sleep.side_effect = trigger_shutdown

                run_worker_loop(poll_interval=1)

            assert mock_signal.signal.call_count == 2
            signal_calls = [c[0][0] for c in mock_signal.signal.call_args_list]
            assert signal.SIGTERM in signal_calls
            assert signal.SIGINT in signal_calls

    def test_processes_pending_notifications(self, app):
        """run_worker_loop processes pending notifications and marks delivered."""
        n = _create_notification()

        with patch.object(notification_service, '_deliver_slack_message'):
            with patch('esb.services.notification_service.time') as mock_time, \
                 patch('esb.services.notification_service.signal'):
                # Stop after first iteration
                mock_time.sleep.side_effect = KeyboardInterrupt

                try:
                    run_worker_loop(poll_interval=1)
                except KeyboardInterrupt:
                    pass

        _db.session.expire(n)
        saved = _db.session.get(PendingNotification, n.id)
        assert saved.status == 'delivered'

    def test_marks_failed_on_not_implemented_error(self, app):
        """run_worker_loop marks notification failed on NotImplementedError."""
        n = _create_notification()

        with patch('esb.services.notification_service.time') as mock_time, \
             patch('esb.services.notification_service.signal'):
            mock_time.sleep.side_effect = KeyboardInterrupt

            try:
                run_worker_loop(poll_interval=1)
            except KeyboardInterrupt:
                pass

        _db.session.expire(n)
        saved = _db.session.get(PendingNotification, n.id)
        assert saved.retry_count == 1
        assert 'not yet implemented' in saved.error_message

    def test_marks_failed_on_general_exception(self, app):
        """run_worker_loop marks notification failed on general delivery error."""
        n = _create_notification()

        with patch.object(notification_service, 'process_notification',
                          side_effect=RuntimeError('Network down')), \
             patch('esb.services.notification_service.time') as mock_time, \
             patch('esb.services.notification_service.signal'):
            mock_time.sleep.side_effect = KeyboardInterrupt

            try:
                run_worker_loop(poll_interval=1)
            except KeyboardInterrupt:
                pass

        _db.session.expire(n)
        saved = _db.session.get(PendingNotification, n.id)
        assert saved.retry_count == 1
        assert saved.error_message == 'Network down'

    def test_graceful_shutdown_on_sigterm(self, app):
        """run_worker_loop exits cleanly when SIGTERM handler fires."""
        signal_handlers = {}

        def capture_signal(sig, handler):
            signal_handlers[sig] = handler

        with patch.object(notification_service, 'get_pending_notifications', return_value=[]), \
             patch('esb.services.notification_service.signal') as mock_signal, \
             patch('esb.services.notification_service.time') as mock_time:
            mock_signal.signal.side_effect = capture_signal
            mock_signal.SIGTERM = signal.SIGTERM
            mock_signal.SIGINT = signal.SIGINT

            # Trigger shutdown on first sleep
            def trigger_shutdown(_):
                signal_handlers[signal.SIGTERM](signal.SIGTERM, None)

            mock_time.sleep.side_effect = trigger_shutdown

            run_worker_loop(poll_interval=1)

        # Should exit cleanly without exception
        assert signal.SIGTERM in signal_handlers

    def test_polling_error_backoff(self, app):
        """run_worker_loop backs off on consecutive polling failures."""
        call_count = 0

        def failing_poll(batch_size=100):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise RuntimeError('DB connection lost')
            return []

        with patch.object(notification_service, 'get_pending_notifications',
                          side_effect=failing_poll), \
             patch('esb.services.notification_service.signal'), \
             patch('esb.services.notification_service.time') as mock_time:
            sleep_calls = []

            def record_sleep(seconds):
                sleep_calls.append(seconds)
                if len(sleep_calls) >= 3:
                    raise KeyboardInterrupt

            mock_time.sleep.side_effect = record_sleep

            try:
                run_worker_loop(poll_interval=5)
            except KeyboardInterrupt:
                pass

        # First failure: 5 * 2^1 = 10s, second failure: 5 * 2^2 = 20s
        assert sleep_calls[0] == 10
        assert sleep_calls[1] == 20
        # Third call is normal poll_interval (5) since poll succeeded
        assert sleep_calls[2] == 5

    def test_polling_backoff_caps_at_300s(self, app):
        """Polling backoff caps at 300 seconds."""
        call_count = 0

        def always_fail(batch_size=100):
            nonlocal call_count
            call_count += 1
            raise RuntimeError('DB down')

        with patch.object(notification_service, 'get_pending_notifications',
                          side_effect=always_fail), \
             patch('esb.services.notification_service.signal'), \
             patch('esb.services.notification_service.time') as mock_time:
            sleep_calls = []

            def record_sleep(seconds):
                sleep_calls.append(seconds)
                if len(sleep_calls) >= 8:
                    raise KeyboardInterrupt

            mock_time.sleep.side_effect = record_sleep

            try:
                run_worker_loop(poll_interval=10)
            except KeyboardInterrupt:
                pass

        # All backoffs should be <= 300
        assert all(s <= 300 for s in sleep_calls)

    def test_consecutive_failure_counter_resets(self, app):
        """Polling failure counter resets after a successful poll."""
        call_count = 0

        def fail_then_succeed(batch_size=100):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise RuntimeError('DB hiccup')
            return []

        with patch.object(notification_service, 'get_pending_notifications',
                          side_effect=fail_then_succeed), \
             patch('esb.services.notification_service.signal'), \
             patch('esb.services.notification_service.time') as mock_time:
            sleep_calls = []

            def record_sleep(seconds):
                sleep_calls.append(seconds)
                if len(sleep_calls) >= 2:
                    raise KeyboardInterrupt

            mock_time.sleep.side_effect = record_sleep

            try:
                run_worker_loop(poll_interval=5)
            except KeyboardInterrupt:
                pass

        # First call: failure backoff (5 * 2^1 = 10s)
        assert sleep_calls[0] == 10
        # Second call: success, normal poll_interval (5s)
        assert sleep_calls[1] == 5
