"""Tests for AuditLog model."""

from esb.extensions import db as _db
from esb.models.audit_log import AuditLog


class TestAuditLogCreation:
    """Tests for AuditLog model creation and fields."""

    def test_create_with_required_fields(self, app):
        """AuditLog created with required fields has correct values."""
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=1,
            action='created',
        )
        _db.session.add(entry)
        _db.session.commit()
        assert entry.id is not None
        assert entry.entity_type == 'repair_record'
        assert entry.entity_id == 1
        assert entry.action == 'created'

    def test_json_changes_stored_and_retrieved(self, app):
        """JSON changes column stores and retrieves dict correctly."""
        changes = {'status': ['New', 'Assigned'], 'assignee': [None, 'techuser']}
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=1,
            action='updated',
            changes=changes,
        )
        _db.session.add(entry)
        _db.session.commit()

        fetched = _db.session.get(AuditLog, entry.id)
        assert fetched.changes == changes
        assert fetched.changes['status'] == ['New', 'Assigned']

    def test_user_relationship(self, app, staff_user):
        """User relationship returns associated User when user_id set."""
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=1,
            action='created',
            user_id=staff_user.id,
        )
        _db.session.add(entry)
        _db.session.commit()
        assert entry.user.username == 'staffuser'

    def test_user_id_nullable(self, app):
        """user_id can be None for system or anonymous actions."""
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=1,
            action='created',
        )
        _db.session.add(entry)
        _db.session.commit()
        assert entry.user_id is None
        assert entry.user is None

    def test_timestamp_auto_set(self, app):
        """created_at is set automatically."""
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=1,
            action='created',
        )
        _db.session.add(entry)
        _db.session.commit()
        assert entry.created_at is not None

    def test_repr(self, app):
        """__repr__ includes entity_type, entity_id, and action."""
        entry = AuditLog(
            entity_type='repair_record',
            entity_id=42,
            action='created',
        )
        _db.session.add(entry)
        _db.session.commit()
        assert repr(entry) == '<AuditLog repair_record:42 [created]>'
