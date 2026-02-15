"""Tests for repair service layer."""

import json
from datetime import date

import pytest

from esb.extensions import db as _db
from esb.models.audit_log import AuditLog
from esb.models.repair_record import RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.services import repair_service
from esb.utils.exceptions import ValidationError


class TestCreateRepairRecord:
    """Tests for create_repair_record()."""

    def test_create_with_minimal_fields(self, app, make_equipment, staff_user, capture):
        """Creates record with minimal required fields."""
        eq = make_equipment()
        record = repair_service.create_repair_record(
            equipment_id=eq.id,
            description='Motor grinding noise',
            created_by='staffuser',
            author_id=staff_user.id,
        )
        assert record.id is not None
        assert record.equipment_id == eq.id
        assert record.description == 'Motor grinding noise'
        assert record.status == 'New'
        assert record.severity is None
        assert record.assignee_id is None

    def test_create_with_all_optional_fields(self, app, make_equipment, staff_user, tech_user, capture):
        """Creates record with all optional fields populated."""
        eq = make_equipment()
        record = repair_service.create_repair_record(
            equipment_id=eq.id,
            description='Laser tube needs replacement',
            created_by='staffuser',
            severity='Down',
            reporter_name='John Doe',
            reporter_email='john@example.com',
            assignee_id=tech_user.id,
            has_safety_risk=True,
            is_consumable=True,
            author_id=staff_user.id,
        )
        assert record.severity == 'Down'
        assert record.reporter_name == 'John Doe'
        assert record.reporter_email == 'john@example.com'
        assert record.assignee_id == tech_user.id
        assert record.has_safety_risk is True
        assert record.is_consumable is True

    def test_creates_timeline_creation_entry(self, app, make_equipment, staff_user, capture):
        """Creates a timeline entry with type 'creation'."""
        eq = make_equipment()
        record = repair_service.create_repair_record(
            equipment_id=eq.id,
            description='Broken belt',
            created_by='staffuser',
            author_id=staff_user.id,
        )
        entries = record.timeline_entries.all()
        assert len(entries) == 1
        assert entries[0].entry_type == 'creation'
        assert entries[0].content == 'Broken belt'
        assert entries[0].author_id == staff_user.id

    def test_creates_audit_log_entry(self, app, make_equipment, staff_user, capture):
        """Creates an audit log entry on creation."""
        eq = make_equipment()
        record = repair_service.create_repair_record(
            equipment_id=eq.id,
            description='Broken belt',
            created_by='staffuser',
            author_id=staff_user.id,
        )
        audit = _db.session.execute(
            _db.select(AuditLog).filter_by(
                entity_type='repair_record', entity_id=record.id,
            )
        ).scalar_one()
        assert audit.action == 'created'
        assert audit.user_id == staff_user.id
        assert audit.changes['status'] == 'New'

    def test_mutation_log_emitted(self, app, make_equipment, staff_user, capture):
        """Mutation log is emitted on creation."""
        eq = make_equipment()
        record = repair_service.create_repair_record(
            equipment_id=eq.id,
            description='Motor issue',
            created_by='staffuser',
            author_id=staff_user.id,
        )
        assert len(capture.records) == 1
        log_data = json.loads(capture.records[0].message)
        assert log_data['event'] == 'repair_record.created'
        assert log_data['user'] == 'staffuser'
        assert log_data['data']['id'] == record.id

    def test_raises_for_missing_description(self, app, make_equipment):
        """Raises ValidationError when description is empty."""
        eq = make_equipment()
        with pytest.raises(ValidationError, match='Description is required'):
            repair_service.create_repair_record(
                equipment_id=eq.id,
                description='   ',
                created_by='staffuser',
            )

    def test_raises_for_nonexistent_equipment(self, app):
        """Raises ValidationError when equipment doesn't exist."""
        with pytest.raises(ValidationError, match='Equipment with id 9999 not found'):
            repair_service.create_repair_record(
                equipment_id=9999,
                description='Broken',
                created_by='staffuser',
            )

    def test_raises_for_archived_equipment(self, app, make_equipment):
        """Raises ValidationError when equipment is archived."""
        eq = make_equipment(is_archived=True)
        with pytest.raises(ValidationError, match='archived'):
            repair_service.create_repair_record(
                equipment_id=eq.id,
                description='Broken',
                created_by='staffuser',
            )

    def test_raises_for_invalid_severity(self, app, make_equipment):
        """Raises ValidationError for invalid severity value."""
        eq = make_equipment()
        with pytest.raises(ValidationError, match='Invalid severity'):
            repair_service.create_repair_record(
                equipment_id=eq.id,
                description='Broken',
                created_by='staffuser',
                severity='Critical',
            )

    def test_raises_for_nonexistent_assignee(self, app, make_equipment):
        """Raises ValidationError when assignee user doesn't exist."""
        eq = make_equipment()
        with pytest.raises(ValidationError, match='User with id 9999 not found'):
            repair_service.create_repair_record(
                equipment_id=eq.id,
                description='Broken',
                created_by='staffuser',
                assignee_id=9999,
            )


class TestGetRepairRecord:
    """Tests for get_repair_record()."""

    def test_returns_record_by_id(self, app, make_equipment):
        """Returns the repair record for a valid ID."""
        eq = make_equipment()
        record = RepairRecord(equipment_id=eq.id, description='Test')
        _db.session.add(record)
        _db.session.commit()

        fetched = repair_service.get_repair_record(record.id)
        assert fetched.id == record.id

    def test_raises_when_not_found(self, app):
        """Raises ValidationError when record doesn't exist."""
        with pytest.raises(ValidationError, match='Repair record with id 9999 not found'):
            repair_service.get_repair_record(9999)


class TestListRepairRecords:
    """Tests for list_repair_records()."""

    def test_returns_all_ordered_by_created_at_desc(self, app, make_equipment):
        """Returns all records ordered by created_at desc."""
        eq = make_equipment()
        r1 = RepairRecord(equipment_id=eq.id, description='First')
        r2 = RepairRecord(equipment_id=eq.id, description='Second')
        _db.session.add_all([r1, r2])
        _db.session.commit()

        records = repair_service.list_repair_records()
        assert len(records) == 2
        # Most recent first
        assert records[0].created_at >= records[1].created_at

    def test_filters_by_equipment_id(self, app, make_area, make_equipment):
        """Filters records by equipment_id."""
        area = make_area()
        eq1 = make_equipment('Printer', area=area)
        eq2 = make_equipment('Laser', area=area)
        _db.session.add_all([
            RepairRecord(equipment_id=eq1.id, description='Printer issue'),
            RepairRecord(equipment_id=eq2.id, description='Laser issue'),
        ])
        _db.session.commit()

        records = repair_service.list_repair_records(equipment_id=eq1.id)
        assert len(records) == 1
        assert records[0].equipment_id == eq1.id

    def test_filters_by_status(self, app, make_equipment):
        """Filters records by status."""
        eq = make_equipment()
        r1 = RepairRecord(equipment_id=eq.id, description='First', status='New')
        r2 = RepairRecord(equipment_id=eq.id, description='Second', status='Assigned')
        _db.session.add_all([r1, r2])
        _db.session.commit()

        records = repair_service.list_repair_records(status='New')
        assert len(records) == 1
        assert records[0].status == 'New'

    def test_returns_empty_list_when_none_exist(self, app):
        """Returns empty list when no records exist."""
        records = repair_service.list_repair_records()
        assert records == []


class TestUpdateRepairRecord:
    """Tests for update_repair_record()."""

    def test_status_change_creates_timeline_entry(self, app, make_repair_record, staff_user, capture):
        """Status change creates a status_change timeline entry with old/new values."""
        record = make_repair_record(status='New')
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, status='In Progress',
        )
        assert updated.status == 'In Progress'
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='status_change',
            )
        ).scalar_one()
        assert timeline.old_value == 'New'
        assert timeline.new_value == 'In Progress'

    def test_assignee_change_creates_timeline_entry(self, app, make_repair_record, staff_user, tech_user, capture):
        """Assignee change creates an assignee_change timeline entry with usernames."""
        record = make_repair_record()
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, assignee_id=tech_user.id,
        )
        assert updated.assignee_id == tech_user.id
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='assignee_change',
            )
        ).scalar_one()
        assert timeline.old_value is None
        assert timeline.new_value == 'techuser'

    def test_assignee_clear_creates_timeline_entry(self, app, make_repair_record, staff_user, tech_user, capture):
        """Clearing assignee (set to None) creates a timeline entry."""
        record = make_repair_record(assignee_id=tech_user.id)
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, assignee_id=None,
        )
        assert updated.assignee_id is None
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='assignee_change',
            )
        ).scalar_one()
        assert timeline.old_value == 'techuser'
        assert timeline.new_value is None

    def test_eta_change_creates_timeline_entry(self, app, make_repair_record, staff_user, capture):
        """ETA change creates an eta_update timeline entry with date strings."""
        record = make_repair_record()
        eta_date = date(2026, 3, 15)
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, eta=eta_date,
        )
        assert updated.eta == eta_date
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='eta_update',
            )
        ).scalar_one()
        assert timeline.old_value is None
        assert timeline.new_value == '2026-03-15'

    def test_eta_clear_creates_timeline_entry(self, app, make_repair_record, staff_user, capture):
        """Clearing ETA creates a timeline entry."""
        record = make_repair_record(eta=date(2026, 3, 15))
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, eta=None,
        )
        assert updated.eta is None
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='eta_update',
            )
        ).scalar_one()
        assert timeline.old_value == '2026-03-15'
        assert timeline.new_value is None

    def test_note_creates_timeline_entry(self, app, make_repair_record, staff_user, capture):
        """Note creates a note timeline entry with content."""
        record = make_repair_record()
        repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, note='Checked wiring',
        )
        timeline = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(
                repair_record_id=record.id, entry_type='note',
            )
        ).scalar_one()
        assert timeline.content == 'Checked wiring'

    def test_batch_changes_create_individual_entries(self, app, make_repair_record, staff_user, tech_user, capture):
        """Multiple changes create individual timeline entries for each change type."""
        record = make_repair_record(status='New')
        repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id,
            status='In Progress', assignee_id=tech_user.id, note='Starting work',
        )
        entries = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(repair_record_id=record.id)
        ).scalars().all()
        entry_types = {e.entry_type for e in entries}
        assert 'status_change' in entry_types
        assert 'assignee_change' in entry_types
        assert 'note' in entry_types
        assert len(entries) == 3

    def test_severity_change_updates_record(self, app, make_repair_record, staff_user, capture):
        """Severity change updates record but does not create a specific timeline entry."""
        record = make_repair_record()
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, severity='Down',
        )
        assert updated.severity == 'Down'
        # No specific timeline entry type for severity
        entries = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(repair_record_id=record.id)
        ).scalars().all()
        assert len(entries) == 0

    def test_specialist_description_saved(self, app, make_repair_record, staff_user, capture):
        """Specialist description is persisted with audit log and mutation log."""
        record = make_repair_record()
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id,
            specialist_description='Needs electrician for high-voltage panel',
        )
        assert updated.specialist_description == 'Needs electrician for high-voltage panel'
        audit = _db.session.execute(
            _db.select(AuditLog).filter_by(
                entity_type='repair_record', entity_id=record.id, action='updated',
            )
        ).scalar_one()
        assert 'specialist_description' in audit.changes
        assert len(capture.records) == 1
        log_data = json.loads(capture.records[0].message)
        assert 'specialist_description' in log_data['data']['changes']

    def test_audit_log_created_with_changes(self, app, make_repair_record, staff_user, capture):
        """Audit log entry created with all changes as JSON."""
        record = make_repair_record(status='New')
        repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id,
            status='Assigned', severity='Degraded',
        )
        audit = _db.session.execute(
            _db.select(AuditLog).filter_by(
                entity_type='repair_record', entity_id=record.id, action='updated',
            )
        ).scalar_one()
        assert audit.user_id == staff_user.id
        assert 'status' in audit.changes
        assert audit.changes['status'] == ['New', 'Assigned']
        assert 'severity' in audit.changes

    def test_mutation_log_emitted(self, app, make_repair_record, staff_user, capture):
        """Mutation log is emitted on update."""
        record = make_repair_record(status='New')
        repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, status='Assigned',
        )
        assert len(capture.records) == 1
        log_data = json.loads(capture.records[0].message)
        assert log_data['event'] == 'repair_record.updated'
        assert log_data['user'] == 'staffuser'
        assert log_data['data']['id'] == record.id
        assert 'status' in log_data['data']['changes']

    def test_invalid_status_raises(self, app, make_repair_record, staff_user):
        """Raises ValidationError for invalid status value."""
        record = make_repair_record()
        with pytest.raises(ValidationError, match='Invalid status'):
            repair_service.update_repair_record(
                record.id, 'staffuser', author_id=staff_user.id, status='Bogus',
            )

    def test_invalid_severity_raises(self, app, make_repair_record, staff_user):
        """Raises ValidationError for invalid severity value."""
        record = make_repair_record()
        with pytest.raises(ValidationError, match='Invalid severity'):
            repair_service.update_repair_record(
                record.id, 'staffuser', author_id=staff_user.id, severity='Critical',
            )

    def test_invalid_assignee_raises(self, app, make_repair_record, staff_user):
        """Raises ValidationError for non-existent assignee user."""
        record = make_repair_record()
        with pytest.raises(ValidationError, match='User with id 9999 not found'):
            repair_service.update_repair_record(
                record.id, 'staffuser', author_id=staff_user.id, assignee_id=9999,
            )

    def test_not_found_raises(self, app, staff_user):
        """Raises ValidationError for non-existent repair record."""
        with pytest.raises(ValidationError, match='Repair record with id 9999 not found'):
            repair_service.update_repair_record(
                9999, 'staffuser', author_id=staff_user.id, status='New',
            )

    def test_no_changes_no_entries(self, app, make_repair_record, staff_user, capture):
        """No actual changes results in no timeline entries and no audit log."""
        record = make_repair_record(status='New')
        repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, status='New',
        )
        entries = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(repair_record_id=record.id)
        ).scalars().all()
        assert len(entries) == 0
        audits = _db.session.execute(
            _db.select(AuditLog).filter_by(
                entity_type='repair_record', entity_id=record.id, action='updated',
            )
        ).scalars().all()
        assert len(audits) == 0
        assert len(capture.records) == 0

    def test_unknown_field_raises(self, app, make_repair_record, staff_user):
        """Raises ValidationError for unknown field names."""
        record = make_repair_record()
        with pytest.raises(ValidationError, match='Unknown fields'):
            repair_service.update_repair_record(
                record.id, 'staffuser', author_id=staff_user.id, bogus_field='value',
            )

    def test_any_to_any_status_transition(self, app, make_repair_record, staff_user, capture):
        """Can transition from any status to any other status."""
        record = make_repair_record(status='Resolved')
        updated = repair_service.update_repair_record(
            record.id, 'staffuser', author_id=staff_user.id, status='New',
        )
        assert updated.status == 'New'
