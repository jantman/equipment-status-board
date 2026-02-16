"""Tests for the PendingNotification model."""

from esb.extensions import db as _db
from esb.models.pending_notification import PendingNotification


class TestPendingNotification:
    """Tests for PendingNotification model."""

    def test_create_with_all_fields(self, app):
        """Model can be created with all required fields."""
        notification = PendingNotification(
            notification_type='slack_message',
            target='#woodshop',
            payload={'equipment_name': 'SawStop', 'severity': 'Down'},
            status='pending',
        )
        _db.session.add(notification)
        _db.session.commit()

        saved = _db.session.get(PendingNotification, notification.id)
        assert saved.notification_type == 'slack_message'
        assert saved.target == '#woodshop'
        assert saved.payload == {'equipment_name': 'SawStop', 'severity': 'Down'}
        assert saved.status == 'pending'
        assert saved.created_at is not None
        assert saved.next_retry_at is None
        assert saved.delivered_at is None
        assert saved.error_message is None

    def test_default_status_pending(self, app):
        """Status defaults to 'pending'."""
        notification = PendingNotification(
            notification_type='slack_message',
            target='#test',
        )
        _db.session.add(notification)
        _db.session.commit()

        assert notification.status == 'pending'

    def test_default_retry_count_zero(self, app):
        """Retry count defaults to 0."""
        notification = PendingNotification(
            notification_type='slack_message',
            target='#test',
        )
        _db.session.add(notification)
        _db.session.commit()

        assert notification.retry_count == 0

    def test_payload_stored_as_json(self, app):
        """Payload is stored and retrieved as JSON."""
        payload = {
            'equipment_name': 'Drill Press',
            'area': 'Woodshop',
            'severity': 'Down',
            'description': 'Motor overheating',
            'nested': {'key': 'value'},
        }
        notification = PendingNotification(
            notification_type='static_page_push',
            target='/status',
            payload=payload,
        )
        _db.session.add(notification)
        _db.session.commit()

        _db.session.expire(notification)
        saved = _db.session.get(PendingNotification, notification.id)
        assert saved.payload == payload
        assert saved.payload['nested']['key'] == 'value'

    def test_notification_type_field(self, app):
        """Notification type stores expected values."""
        for ntype in ('slack_message', 'static_page_push'):
            notification = PendingNotification(
                notification_type=ntype,
                target='#test',
            )
            _db.session.add(notification)
            _db.session.commit()
            assert notification.notification_type == ntype

    def test_repr(self, app):
        """__repr__ includes id, type, and status."""
        notification = PendingNotification(
            notification_type='slack_message',
            target='#test',
        )
        _db.session.add(notification)
        _db.session.commit()

        result = repr(notification)
        assert 'PendingNotification' in result
        assert 'slack_message' in result
        assert 'pending' in result
