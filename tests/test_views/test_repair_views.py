"""Tests for repair record views."""

from unittest.mock import patch

from esb.extensions import db as _db
from esb.models.repair_record import RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.utils.exceptions import ValidationError


class TestCreateRepairRecord:
    """Tests for GET/POST /repairs/new."""

    def test_staff_sees_form(self, staff_client, make_equipment):
        """Staff can access the create repair record form."""
        make_equipment('Laser Cutter')
        resp = staff_client.get('/repairs/new')
        assert resp.status_code == 200
        assert b'Create Repair Record' in resp.data

    def test_technician_sees_form(self, tech_client, make_equipment):
        """Technicians can access the create repair record form."""
        make_equipment('Laser Cutter')
        resp = tech_client.get('/repairs/new')
        assert resp.status_code == 200
        assert b'Create Repair Record' in resp.data

    def test_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated users are redirected to login."""
        resp = client.get('/repairs/new')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_staff_creates_record_successfully(self, staff_client, make_equipment):
        """Staff can create a repair record successfully."""
        eq = make_equipment('3D Printer')
        resp = staff_client.post('/repairs/new', data={
            'equipment_id': eq.id,
            'description': 'Nozzle clogged',
            'severity': 'Degraded',
            'assignee_id': 0,
            'has_safety_risk': False,
            'is_consumable': False,
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/repairs/' in resp.headers['Location']

        record = _db.session.execute(
            _db.select(RepairRecord)
        ).scalar_one()
        assert record.description == 'Nozzle clogged'
        assert record.status == 'New'

    def test_technician_creates_record_successfully(self, tech_client, make_equipment):
        """Technicians can create a repair record successfully."""
        eq = make_equipment('CNC Router')
        resp = tech_client.post('/repairs/new', data={
            'equipment_id': eq.id,
            'description': 'Bit broke',
            'severity': '',
            'assignee_id': 0,
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_missing_required_field_shows_error(self, staff_client, make_equipment):
        """Missing description shows validation error."""
        eq = make_equipment('Laser')
        resp = staff_client.post('/repairs/new', data={
            'equipment_id': eq.id,
            'description': '',
            'severity': '',
            'assignee_id': 0,
        })
        assert resp.status_code == 200
        assert b'This field is required' in resp.data

    def test_invalid_equipment_shows_flash(self, staff_client, make_equipment):
        """Selecting no equipment shows flash error."""
        make_equipment()
        resp = staff_client.post('/repairs/new', data={
            'equipment_id': 0,
            'description': 'Broken',
            'severity': '',
            'assignee_id': 0,
        })
        assert resp.status_code == 200
        assert b'Please select an equipment item' in resp.data

    def test_preselected_equipment_via_query_param(self, staff_client, make_equipment):
        """Equipment is pre-selected when equipment_id query param is provided."""
        eq = make_equipment('Table Saw')
        resp = staff_client.get(f'/repairs/new?equipment_id={eq.id}')
        assert resp.status_code == 200
        # WTForms renders: <option selected value="X">
        assert f'selected value="{eq.id}"'.encode() in resp.data


class TestRepairRecordDetail:
    """Tests for GET /repairs/<id>."""

    def test_staff_sees_detail(self, staff_client, make_repair_record):
        """Staff can view repair record detail page."""
        record = make_repair_record(description='Motor grinding')
        resp = staff_client.get(f'/repairs/{record.id}')
        assert resp.status_code == 200
        assert b'Motor grinding' in resp.data

    def test_technician_sees_detail(self, tech_client, make_repair_record):
        """Technicians can view repair record detail page."""
        record = make_repair_record(description='Belt slipping')
        resp = tech_client.get(f'/repairs/{record.id}')
        assert resp.status_code == 200
        assert b'Belt slipping' in resp.data

    def test_unauthenticated_redirects_to_login(self, client, make_repair_record):
        """Unauthenticated users are redirected to login."""
        record = make_repair_record()
        resp = client.get(f'/repairs/{record.id}')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_nonexistent_record_returns_404(self, staff_client):
        """Non-existent repair record returns 404."""
        resp = staff_client.get('/repairs/9999')
        assert resp.status_code == 404

    def test_shows_timeline_entries(self, staff_client, make_repair_record):
        """Detail page shows timeline entries."""
        record = make_repair_record(description='Broken belt')
        entry = RepairTimelineEntry(
            repair_record_id=record.id,
            entry_type='creation',
            content='Broken belt',
            author_name='staffuser',
        )
        _db.session.add(entry)
        _db.session.commit()

        resp = staff_client.get(f'/repairs/{record.id}')
        assert resp.status_code == 200
        assert b'Repair record created' in resp.data
        assert b'Broken belt' in resp.data

    def test_shows_equipment_name_and_link(self, staff_client, make_equipment, make_repair_record):
        """Detail page shows equipment name with link."""
        eq = make_equipment('Laser Cutter')
        record = make_repair_record(equipment=eq, description='Tube issue')
        resp = staff_client.get(f'/repairs/{record.id}')
        assert resp.status_code == 200
        assert b'Laser Cutter' in resp.data
        assert f'/equipment/{eq.id}'.encode() in resp.data


class TestEditRepairRecord:
    """Tests for GET/POST /repairs/<id>/edit."""

    def test_edit_page_staff_sees_form(self, staff_client, make_repair_record):
        """Staff can access the edit form pre-populated."""
        record = make_repair_record(status='New', description='Motor issue')
        resp = staff_client.get(f'/repairs/{record.id}/edit')
        assert resp.status_code == 200
        assert b'Edit Repair' in resp.data
        assert b'Save Changes' in resp.data

    def test_edit_page_technician_sees_form(self, tech_client, make_repair_record):
        """Technicians can access the edit form."""
        record = make_repair_record()
        resp = tech_client.get(f'/repairs/{record.id}/edit')
        assert resp.status_code == 200
        assert b'Edit Repair' in resp.data

    def test_edit_page_unauthenticated_redirects(self, client, make_repair_record):
        """Unauthenticated users are redirected to login."""
        record = make_repair_record()
        resp = client.get(f'/repairs/{record.id}/edit')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_edit_page_not_found(self, staff_client):
        """Non-existent record returns 404."""
        resp = staff_client.get('/repairs/9999/edit')
        assert resp.status_code == 404

    def test_edit_post_staff_updates_successfully(self, staff_client, make_repair_record):
        """Staff POST updates record and redirects to detail."""
        record = make_repair_record(status='New')
        resp = staff_client.post(f'/repairs/{record.id}/edit', data={
            'status': 'Assigned',
            'severity': '',
            'assignee_id': '0',
            'specialist_description': '',
            'note': '',
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert f'/repairs/{record.id}' in resp.headers['Location']

    def test_edit_post_technician_updates_successfully(self, tech_client, make_repair_record):
        """Technician POST updates record and redirects."""
        record = make_repair_record(status='New')
        resp = tech_client.post(f'/repairs/{record.id}/edit', data={
            'status': 'In Progress',
            'severity': '',
            'assignee_id': '0',
            'specialist_description': '',
            'note': '',
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_edit_post_status_change_saved(self, staff_client, make_repair_record):
        """Status change is saved to the record after POST."""
        record = make_repair_record(status='New')
        staff_client.post(f'/repairs/{record.id}/edit', data={
            'status': 'In Progress',
            'severity': '',
            'assignee_id': '0',
            'specialist_description': '',
            'note': '',
        })
        updated = _db.session.get(RepairRecord, record.id)
        assert updated.status == 'In Progress'

    def test_edit_post_multiple_changes(self, staff_client, make_repair_record, tech_user):
        """POST with multiple changes (status + assignee + note) all saved."""
        record = make_repair_record(status='New')
        staff_client.post(f'/repairs/{record.id}/edit', data={
            'status': 'Assigned',
            'severity': 'Degraded',
            'assignee_id': str(tech_user.id),
            'specialist_description': '',
            'note': 'Assigning to tech',
        })
        updated = _db.session.get(RepairRecord, record.id)
        assert updated.status == 'Assigned'
        assert updated.assignee_id == tech_user.id
        entries = _db.session.execute(
            _db.select(RepairTimelineEntry).filter_by(repair_record_id=record.id)
        ).scalars().all()
        entry_types = {e.entry_type for e in entries}
        assert 'status_change' in entry_types
        assert 'assignee_change' in entry_types
        assert 'note' in entry_types

    def test_edit_post_specialist_description(self, staff_client, make_repair_record):
        """POST with Needs Specialist status saves specialist description."""
        record = make_repair_record(status='New')
        staff_client.post(f'/repairs/{record.id}/edit', data={
            'status': 'Needs Specialist',
            'severity': '',
            'assignee_id': '0',
            'specialist_description': 'Need licensed electrician',
            'note': '',
        })
        updated = _db.session.get(RepairRecord, record.id)
        assert updated.status == 'Needs Specialist'
        assert updated.specialist_description == 'Need licensed electrician'

    def test_edit_post_validation_error_shows_flash(self, staff_client, make_repair_record):
        """Service ValidationError is caught and displayed as flash message."""
        record = make_repair_record(status='New')
        with patch('esb.services.repair_service.update_repair_record') as mock_update:
            mock_update.side_effect = ValidationError('Test validation error')
            resp = staff_client.post(f'/repairs/{record.id}/edit', data={
                'status': 'New',
                'severity': '',
                'assignee_id': '0',
                'specialist_description': '',
                'note': '',
            })
        assert resp.status_code == 200
        assert b'Test validation error' in resp.data

    def test_edit_post_unauthenticated_redirects(self, client, make_repair_record):
        """Unauthenticated POST redirects to login."""
        record = make_repair_record()
        resp = client.post(f'/repairs/{record.id}/edit', data={
            'status': 'Assigned',
            'severity': '',
            'assignee_id': '0',
            'specialist_description': '',
            'note': '',
        })
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']
