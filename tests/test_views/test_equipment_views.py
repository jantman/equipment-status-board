"""Tests for equipment views."""

import json

from esb.extensions import db as _db
from esb.models.equipment import Equipment


class TestListEquipment:
    """Tests for GET /equipment/."""

    def test_staff_sees_equipment_list(self, staff_client, make_equipment):
        """Staff can access the equipment list page."""
        make_equipment('Table Saw', 'SawStop', 'PCS')
        resp = staff_client.get('/equipment/')
        assert resp.status_code == 200
        assert b'Table Saw' in resp.data
        assert b'Equipment Registry' in resp.data

    def test_technician_sees_equipment_list(self, tech_client, make_equipment):
        """Technicians can access the equipment list page."""
        make_equipment('Drill Press', 'JET', 'JDP-17')
        resp = tech_client.get('/equipment/')
        assert resp.status_code == 200
        assert b'Drill Press' in resp.data

    def test_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated users are redirected to login."""
        resp = client.get('/equipment/')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_area_filter(self, staff_client, make_area, make_equipment):
        """Equipment list can be filtered by area."""
        area1 = make_area('Woodshop', '#wood')
        area2 = make_area('Metal Shop', '#metal')
        make_equipment('Table Saw', 'SawStop', 'PCS', area=area1)
        make_equipment('Welder', 'Lincoln', '210MP', area=area2)

        resp = staff_client.get(f'/equipment/?area_id={area1.id}')
        assert resp.status_code == 200
        assert b'Table Saw' in resp.data
        assert b'Welder' not in resp.data

    def test_empty_state(self, staff_client):
        """Empty state is shown when no equipment exists."""
        resp = staff_client.get('/equipment/')
        assert resp.status_code == 200
        assert b'No equipment' in resp.data

    def test_archived_equipment_excluded(self, staff_client, make_equipment):
        """Archived equipment is not shown in listings."""
        eq = make_equipment('Old Laser', 'Epilog', 'Zing')
        eq.is_archived = True
        _db.session.commit()

        resp = staff_client.get('/equipment/')
        assert b'Old Laser' not in resp.data

    def test_add_equipment_button_staff_only(self, tech_client, make_equipment):
        """Technicians do not see the Add Equipment button."""
        make_equipment('Item', 'Co', 'M')
        resp = tech_client.get('/equipment/')
        assert b'Add Equipment' not in resp.data


class TestCreateEquipment:
    """Tests for GET/POST /equipment/new."""

    def test_staff_sees_create_form(self, staff_client, make_area):
        """Staff can access the create equipment form."""
        make_area('Woodshop', '#wood')
        resp = staff_client.get('/equipment/new')
        assert resp.status_code == 200
        assert b'Add Equipment' in resp.data

    def test_technician_gets_403(self, tech_client):
        """Technicians cannot access the create form."""
        resp = tech_client.get('/equipment/new')
        assert resp.status_code == 403

    def test_creates_equipment_with_valid_data(self, staff_client, make_area):
        """Staff can create equipment with valid data."""
        area = make_area('Woodshop', '#wood')
        resp = staff_client.post('/equipment/new', data={
            'name': 'Table Saw',
            'manufacturer': 'SawStop',
            'model': 'PCS',
            'area_id': area.id,
        }, follow_redirects=False)
        assert resp.status_code == 302

        eq = _db.session.execute(
            _db.select(Equipment).filter_by(name='Table Saw')
        ).scalar_one_or_none()
        assert eq is not None
        assert eq.manufacturer == 'SawStop'

    def test_redirects_to_detail_after_create(self, staff_client, make_area):
        """After creating equipment, redirects to detail page."""
        area = make_area('Woodshop', '#wood')
        resp = staff_client.post('/equipment/new', data={
            'name': 'Drill Press',
            'manufacturer': 'JET',
            'model': 'JDP-17',
            'area_id': area.id,
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/equipment/' in resp.headers['Location']

    def test_validation_error_missing_name(self, staff_client, make_area):
        """Missing name shows validation error."""
        area = make_area('Woodshop', '#wood')
        resp = staff_client.post('/equipment/new', data={
            'name': '',
            'manufacturer': 'SawStop',
            'model': 'PCS',
            'area_id': area.id,
        })
        assert resp.status_code == 200
        assert b'This field is required' in resp.data

    def test_validation_error_missing_area(self, staff_client, make_area):
        """Missing area shows validation error."""
        make_area('Woodshop', '#wood')
        resp = staff_client.post('/equipment/new', data={
            'name': 'Drill Press',
            'manufacturer': 'JET',
            'model': 'JDP-17',
            'area_id': 0,
        })
        assert resp.status_code == 200

    def test_creates_equipment_with_optional_fields(self, staff_client, make_area):
        """Staff can create equipment with optional fields populated."""
        area = make_area('Woodshop', '#wood')
        resp = staff_client.post('/equipment/new', data={
            'name': 'CNC Router',
            'manufacturer': 'ShopBot',
            'model': 'Desktop',
            'area_id': area.id,
            'serial_number': 'SN-99887',
            'acquisition_date': '2024-06-15',
            'acquisition_source': 'Direct purchase',
            'acquisition_cost': '4999.99',
            'warranty_expiration': '2026-06-15',
            'description': 'Desktop CNC for woodworking',
        }, follow_redirects=False)
        assert resp.status_code == 302

        eq = _db.session.execute(
            _db.select(Equipment).filter_by(name='CNC Router')
        ).scalar_one_or_none()
        assert eq is not None
        assert eq.serial_number == 'SN-99887'
        assert str(eq.acquisition_date) == '2024-06-15'
        assert eq.acquisition_source == 'Direct purchase'
        assert str(eq.acquisition_cost) == '4999.99'
        assert str(eq.warranty_expiration) == '2026-06-15'
        assert eq.description == 'Desktop CNC for woodworking'

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated users are redirected to login."""
        resp = client.get('/equipment/new')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']


class TestEquipmentDetail:
    """Tests for GET /equipment/<id>."""

    def test_staff_sees_detail(self, staff_client, make_equipment):
        """Staff can access equipment detail page."""
        eq = make_equipment('Table Saw', 'SawStop', 'PCS')
        resp = staff_client.get(f'/equipment/{eq.id}')
        assert resp.status_code == 200
        assert b'Table Saw' in resp.data
        assert b'SawStop' in resp.data
        assert b'PCS' in resp.data

    def test_technician_sees_detail(self, tech_client, make_equipment):
        """Technicians can access equipment detail page."""
        eq = make_equipment('Drill Press', 'JET', 'JDP-17')
        resp = tech_client.get(f'/equipment/{eq.id}')
        assert resp.status_code == 200
        assert b'Drill Press' in resp.data

    def test_not_found_returns_404(self, staff_client):
        """Non-existent equipment returns 404."""
        resp = staff_client.get('/equipment/99999')
        assert resp.status_code == 404

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated users are redirected to login."""
        resp = client.get('/equipment/1')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_edit_button_staff_only(self, tech_client, make_equipment):
        """Technicians do not see the Edit button."""
        eq = make_equipment('Item', 'Co', 'M')
        resp = tech_client.get(f'/equipment/{eq.id}')
        assert b'Edit' not in resp.data


class TestEditEquipment:
    """Tests for GET/POST /equipment/<id>/edit."""

    def test_staff_sees_edit_form(self, staff_client, make_area, make_equipment):
        """Staff can access the edit form."""
        area = make_area('Woodshop', '#wood')
        eq = make_equipment('Table Saw', 'SawStop', 'PCS', area=area)
        resp = staff_client.get(f'/equipment/{eq.id}/edit')
        assert resp.status_code == 200
        assert b'Edit Equipment' in resp.data

    def test_technician_gets_403(self, tech_client, make_equipment):
        """Technicians cannot access the edit form."""
        eq = make_equipment('Table Saw', 'SawStop', 'PCS')
        resp = tech_client.get(f'/equipment/{eq.id}/edit')
        assert resp.status_code == 403

    def test_updates_equipment(self, staff_client, make_area, make_equipment):
        """Staff can update equipment."""
        area = make_area('Woodshop', '#wood')
        eq = make_equipment('Old Name', 'OldCo', 'OldModel', area=area)
        resp = staff_client.post(f'/equipment/{eq.id}/edit', data={
            'name': 'New Name',
            'manufacturer': 'NewCo',
            'model': 'NewModel',
            'area_id': area.id,
        }, follow_redirects=False)
        assert resp.status_code == 302

        updated = _db.session.get(Equipment, eq.id)
        assert updated.name == 'New Name'
        assert updated.manufacturer == 'NewCo'

    def test_redirects_to_detail_after_edit(self, staff_client, make_area, make_equipment):
        """After editing equipment, redirects to detail page."""
        area = make_area('Woodshop', '#wood')
        eq = make_equipment('Item', 'Co', 'M', area=area)
        resp = staff_client.post(f'/equipment/{eq.id}/edit', data={
            'name': 'Updated',
            'manufacturer': 'Co',
            'model': 'M',
            'area_id': area.id,
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert f'/equipment/{eq.id}' in resp.headers['Location']

    def test_validation_error_on_edit(self, staff_client, make_area, make_equipment):
        """Validation errors shown on edit form."""
        area = make_area('Woodshop', '#wood')
        eq = make_equipment('Item', 'Co', 'M', area=area)
        resp = staff_client.post(f'/equipment/{eq.id}/edit', data={
            'name': '',
            'manufacturer': 'Co',
            'model': 'M',
            'area_id': area.id,
        })
        assert resp.status_code == 200
        assert b'This field is required' in resp.data

    def test_not_found_returns_404(self, staff_client):
        """Non-existent equipment returns 404."""
        resp = staff_client.get('/equipment/99999/edit')
        assert resp.status_code == 404

    def test_unauthenticated_redirects(self, client):
        """Unauthenticated users are redirected to login."""
        resp = client.get('/equipment/1/edit')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']


class TestRBACAndEdgeCases:
    """Tests for RBAC and edge cases (Task 6)."""

    def test_staff_required_on_create(self, tech_client):
        """@role_required('staff') on create route returns 403 for technicians."""
        resp = tech_client.post('/equipment/new', data={
            'name': 'X', 'manufacturer': 'Y', 'model': 'Z', 'area_id': 1,
        })
        assert resp.status_code == 403

    def test_staff_required_on_edit(self, tech_client, make_equipment):
        """@role_required('staff') on edit route returns 403 for technicians."""
        eq = make_equipment('Item', 'Co', 'M')
        resp = tech_client.post(f'/equipment/{eq.id}/edit', data={
            'name': 'X', 'manufacturer': 'Y', 'model': 'Z', 'area_id': 1,
        })
        assert resp.status_code == 403

    def test_login_required_on_list(self, client):
        """@login_required on list redirects unauthenticated."""
        resp = client.get('/equipment/')
        assert resp.status_code == 302

    def test_login_required_on_detail(self, client):
        """@login_required on detail redirects unauthenticated."""
        resp = client.get('/equipment/1')
        assert resp.status_code == 302

    def test_area_dropdown_excludes_archived(self, staff_client, make_area):
        """Area dropdown on create form excludes archived areas."""
        make_area('Active Shop', '#active')
        archived = make_area('Old Shop', '#old')
        archived.is_archived = True
        _db.session.commit()

        resp = staff_client.get('/equipment/new')
        assert b'Active Shop' in resp.data
        assert b'Old Shop' not in resp.data

    def test_archived_equipment_excluded_from_list(self, staff_client, make_equipment):
        """Archived equipment is excluded from the list view."""
        eq = make_equipment('Retired Laser', 'Epilog', 'Zing')
        eq.is_archived = True
        _db.session.commit()
        make_equipment('Active CNC', 'ShopBot', 'Desktop', area=eq.area)

        resp = staff_client.get('/equipment/')
        assert b'Retired Laser' not in resp.data
        assert b'Active CNC' in resp.data


class TestEquipmentMutationLogging:
    """Tests for mutation logging on equipment views."""

    def test_equipment_created_event_logged(self, staff_client, capture, make_area):
        """Equipment creation logs equipment.created mutation."""
        area = make_area('Woodshop', '#wood')
        staff_client.post('/equipment/new', data={
            'name': 'Laser Cutter',
            'manufacturer': 'Epilog',
            'model': 'Zing',
            'area_id': area.id,
        })
        created_entries = [
            json.loads(r.message) for r in capture.records
            if 'equipment.created' in r.message
        ]
        assert len(created_entries) == 1
        assert created_entries[0]['data']['name'] == 'Laser Cutter'

    def test_equipment_updated_event_logged(self, staff_client, capture, make_area, make_equipment):
        """Equipment edit logs equipment.updated mutation."""
        area = make_area('Woodshop', '#wood')
        eq = make_equipment('Old Name', 'Co', 'M', area=area)
        capture.records.clear()
        staff_client.post(f'/equipment/{eq.id}/edit', data={
            'name': 'New Name',
            'manufacturer': 'Co',
            'model': 'M',
            'area_id': area.id,
        })
        updated_entries = [
            json.loads(r.message) for r in capture.records
            if 'equipment.updated' in r.message
        ]
        assert len(updated_entries) == 1
        assert updated_entries[0]['data']['changes']['name'] == ['Old Name', 'New Name']
