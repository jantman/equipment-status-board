"""Tests for equipment views."""

import io
import json

from esb.extensions import db as _db
from esb.models.document import Document
from esb.models.equipment import Equipment
from esb.models.external_link import ExternalLink


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


# --- Document Upload/Delete View Tests ---


class TestUploadDocument:
    """Tests for POST /equipment/<id>/documents."""

    def test_staff_uploads_document(self, staff_client, make_equipment, db, capture, tmp_path, app):
        """Staff can upload a document to an equipment item."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        data = {
            'file': (io.BytesIO(b'fake pdf content'), 'manual.pdf'),
            'category': 'owners_manual',
        }
        resp = staff_client.post(
            f'/equipment/{eq.id}/documents',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Document uploaded successfully' in resp.data
        doc = db.session.execute(
            db.select(Document).filter_by(parent_type='equipment_doc', parent_id=eq.id)
        ).scalar_one_or_none()
        assert doc is not None
        assert doc.original_filename == 'manual.pdf'

    def test_technician_gets_403(self, tech_client, make_equipment):
        """Technicians cannot upload documents."""
        eq = make_equipment()
        data = {
            'file': (io.BytesIO(b'content'), 'test.pdf'),
            'category': 'other',
        }
        resp = tech_client.post(
            f'/equipment/{eq.id}/documents',
            data=data,
            content_type='multipart/form-data',
        )
        assert resp.status_code == 403

    def test_404_for_nonexistent_equipment(self, staff_client):
        """Upload to non-existent equipment returns 404."""
        data = {
            'file': (io.BytesIO(b'content'), 'test.pdf'),
            'category': 'other',
        }
        resp = staff_client.post(
            '/equipment/99999/documents',
            data=data,
            content_type='multipart/form-data',
        )
        assert resp.status_code == 404

    def test_validation_error_no_file(self, staff_client, make_equipment):
        """No file selected shows validation error."""
        eq = make_equipment()
        resp = staff_client.post(
            f'/equipment/{eq.id}/documents',
            data={'category': 'other'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Please select a file' in resp.data


class TestUploadPhoto:
    """Tests for POST /equipment/<id>/photos."""

    def test_staff_uploads_photo(self, staff_client, make_equipment, db, tmp_path, app):
        """Staff can upload a photo."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        data = {
            'file': (io.BytesIO(b'fake image'), 'photo.jpg'),
        }
        resp = staff_client.post(
            f'/equipment/{eq.id}/photos',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Photo uploaded successfully' in resp.data

    def test_technician_gets_403(self, tech_client, make_equipment):
        """Technicians cannot upload photos."""
        eq = make_equipment()
        data = {
            'file': (io.BytesIO(b'content'), 'photo.jpg'),
        }
        resp = tech_client.post(
            f'/equipment/{eq.id}/photos',
            data=data,
            content_type='multipart/form-data',
        )
        assert resp.status_code == 403


class TestDeleteDocument:
    """Tests for POST /equipment/<id>/documents/<doc_id>/delete."""

    def test_staff_deletes_document(self, staff_client, make_equipment, db, capture, tmp_path, app):
        """Staff can delete a document."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        doc_dir = tmp_path / 'equipment' / str(eq.id) / 'docs'
        doc_dir.mkdir(parents=True)
        (doc_dir / 'stored.pdf').write_bytes(b'content')
        doc = Document(
            original_filename='manual.pdf', stored_filename='stored.pdf',
            content_type='application/pdf', size_bytes=7,
            parent_type='equipment_doc', parent_id=eq.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()

        resp = staff_client.post(
            f'/equipment/{eq.id}/documents/{doc.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Document deleted' in resp.data
        assert db.session.get(Document, doc.id) is None

    def test_technician_gets_403(self, tech_client, make_equipment, db):
        """Technicians cannot delete documents."""
        eq = make_equipment()
        doc = Document(
            original_filename='test.pdf', stored_filename='x.pdf',
            content_type='application/pdf', size_bytes=7,
            parent_type='equipment_doc', parent_id=eq.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()
        resp = tech_client.post(f'/equipment/{eq.id}/documents/{doc.id}/delete')
        assert resp.status_code == 403

    def test_cross_equipment_delete_rejected(self, staff_client, make_equipment, make_area, db):
        """Cannot delete a document belonging to another equipment."""
        area = make_area('Shop', '#shop')
        eq1 = make_equipment('Eq1', 'Co', 'M', area=area)
        eq2 = make_equipment('Eq2', 'Co', 'M', area=area)
        doc = Document(
            original_filename='test.pdf', stored_filename='x.pdf',
            content_type='application/pdf', size_bytes=7,
            parent_type='equipment_doc', parent_id=eq1.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()
        resp = staff_client.post(
            f'/equipment/{eq2.id}/documents/{doc.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert db.session.get(Document, doc.id) is not None


class TestDeletePhoto:
    """Tests for POST /equipment/<id>/photos/<photo_id>/delete."""

    def test_staff_deletes_photo(self, staff_client, make_equipment, db, tmp_path, app):
        """Staff can delete a photo."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        doc_dir = tmp_path / 'equipment' / str(eq.id) / 'photos'
        doc_dir.mkdir(parents=True)
        (doc_dir / 'stored.jpg').write_bytes(b'image')
        doc = Document(
            original_filename='photo.jpg', stored_filename='stored.jpg',
            content_type='image/jpeg', size_bytes=5,
            parent_type='equipment_photo', parent_id=eq.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()

        resp = staff_client.post(
            f'/equipment/{eq.id}/photos/{doc.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Photo deleted' in resp.data

    def test_technician_gets_403(self, tech_client, make_equipment, db):
        """Technicians cannot delete photos."""
        eq = make_equipment()
        doc = Document(
            original_filename='photo.jpg', stored_filename='x.jpg',
            content_type='image/jpeg', size_bytes=5,
            parent_type='equipment_photo', parent_id=eq.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()
        resp = tech_client.post(f'/equipment/{eq.id}/photos/{doc.id}/delete')
        assert resp.status_code == 403


# --- External Link View Tests ---


class TestAddLink:
    """Tests for POST /equipment/<id>/links."""

    def test_staff_adds_link(self, staff_client, make_equipment, db):
        """Staff can add an external link."""
        eq = make_equipment()
        resp = staff_client.post(
            f'/equipment/{eq.id}/links',
            data={'title': 'Manual', 'url': 'https://example.com/manual'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Link added successfully' in resp.data
        link = db.session.execute(
            db.select(ExternalLink).filter_by(equipment_id=eq.id)
        ).scalar_one_or_none()
        assert link is not None
        assert link.title == 'Manual'

    def test_technician_gets_403(self, tech_client, make_equipment):
        """Technicians cannot add links."""
        eq = make_equipment()
        resp = tech_client.post(
            f'/equipment/{eq.id}/links',
            data={'title': 'Test', 'url': 'https://example.com'},
        )
        assert resp.status_code == 403

    def test_404_for_nonexistent_equipment(self, staff_client):
        """Add link to non-existent equipment returns 404."""
        resp = staff_client.post(
            '/equipment/99999/links',
            data={'title': 'Test', 'url': 'https://example.com'},
        )
        assert resp.status_code == 404

    def test_validation_error_missing_title(self, staff_client, make_equipment):
        """Missing title shows validation error."""
        eq = make_equipment()
        resp = staff_client.post(
            f'/equipment/{eq.id}/links',
            data={'title': '', 'url': 'https://example.com'},
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'This field is required' in resp.data


class TestDeleteLink:
    """Tests for POST /equipment/<id>/links/<link_id>/delete."""

    def test_staff_deletes_link(self, staff_client, make_equipment, db, capture):
        """Staff can delete an external link."""
        eq = make_equipment()
        link = ExternalLink(
            equipment_id=eq.id, title='Old Link',
            url='https://example.com', created_by='staffuser',
        )
        db.session.add(link)
        db.session.commit()

        resp = staff_client.post(
            f'/equipment/{eq.id}/links/{link.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'Link deleted' in resp.data
        assert db.session.get(ExternalLink, link.id) is None

    def test_technician_gets_403(self, tech_client, make_equipment, db):
        """Technicians cannot delete links."""
        eq = make_equipment()
        link = ExternalLink(
            equipment_id=eq.id, title='Test',
            url='https://example.com', created_by='staffuser',
        )
        db.session.add(link)
        db.session.commit()
        resp = tech_client.post(f'/equipment/{eq.id}/links/{link.id}/delete')
        assert resp.status_code == 403

    def test_cross_equipment_delete_rejected(self, staff_client, make_equipment, make_area, db):
        """Cannot delete a link belonging to another equipment."""
        area = make_area('Shop', '#shop')
        eq1 = make_equipment('Eq1', 'Co', 'M', area=area)
        eq2 = make_equipment('Eq2', 'Co', 'M', area=area)
        link = ExternalLink(
            equipment_id=eq1.id, title='Test',
            url='https://example.com', created_by='staffuser',
        )
        db.session.add(link)
        db.session.commit()
        resp = staff_client.post(
            f'/equipment/{eq2.id}/links/{link.id}/delete',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert db.session.get(ExternalLink, link.id) is not None


# --- File Serving View Tests ---


class TestFileServing:
    """Tests for file serving routes."""

    def test_serve_document_requires_login(self, client):
        """Unauthenticated users are redirected on file serve."""
        resp = client.get('/equipment/1/files/docs/test.pdf')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_serve_photo_requires_login(self, client):
        """Unauthenticated users are redirected on photo serve."""
        resp = client.get('/equipment/1/files/photos/photo.jpg')
        assert resp.status_code == 302
        assert '/auth/login' in resp.headers['Location']

    def test_serve_document_authenticated(self, staff_client, make_equipment, tmp_path, app):
        """Authenticated user can download a document file."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        doc_dir = tmp_path / 'equipment' / str(eq.id) / 'docs'
        doc_dir.mkdir(parents=True)
        (doc_dir / 'test.pdf').write_bytes(b'PDF content')

        resp = staff_client.get(f'/equipment/{eq.id}/files/docs/test.pdf')
        assert resp.status_code == 200
        assert resp.data == b'PDF content'

    def test_serve_photo_authenticated(self, staff_client, make_equipment, tmp_path, app):
        """Authenticated user can download a photo file."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        photo_dir = tmp_path / 'equipment' / str(eq.id) / 'photos'
        photo_dir.mkdir(parents=True)
        (photo_dir / 'photo.jpg').write_bytes(b'JPEG content')

        resp = staff_client.get(f'/equipment/{eq.id}/files/photos/photo.jpg')
        assert resp.status_code == 200
        assert resp.data == b'JPEG content'


# --- 413 Error Handler Test ---


class TestRequestTooLarge:
    """Tests for 413 Request Entity Too Large handler."""

    def test_413_shows_flash_message(self, staff_client, make_equipment, app):
        """413 error shows flash message about file size limit."""
        app.config['MAX_CONTENT_LENGTH'] = 10  # 10 bytes
        app.config['UPLOAD_MAX_SIZE_MB'] = 1
        eq = make_equipment()
        big_data = b'x' * 100
        data = {
            'file': (io.BytesIO(big_data), 'big.pdf'),
            'category': 'other',
        }
        resp = staff_client.post(
            f'/equipment/{eq.id}/documents',
            data=data,
            content_type='multipart/form-data',
            follow_redirects=True,
        )
        assert resp.status_code == 200
        assert b'too large' in resp.data


# --- Document/Photo/Link Mutation Logging View Tests ---


class TestDocumentMutationLogging:
    """Tests for mutation logging on document/link operations."""

    def test_document_upload_logs_mutation(self, staff_client, make_equipment, capture, tmp_path, app):
        """Document upload logs document.created mutation."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        capture.records.clear()
        data = {
            'file': (io.BytesIO(b'content'), 'test.pdf'),
            'category': 'other',
        }
        staff_client.post(
            f'/equipment/{eq.id}/documents',
            data=data,
            content_type='multipart/form-data',
        )
        entries = [
            json.loads(r.message) for r in capture.records
            if 'document.created' in r.message
        ]
        assert len(entries) == 1
        assert entries[0]['event'] == 'document.created'
        assert entries[0]['user'] == 'staffuser'

    def test_document_delete_logs_mutation(self, staff_client, make_equipment, db, capture, tmp_path, app):
        """Document delete logs document.deleted mutation."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        eq = make_equipment()
        doc = Document(
            original_filename='test.pdf', stored_filename='x.pdf',
            content_type='application/pdf', size_bytes=7,
            parent_type='equipment_doc', parent_id=eq.id, uploaded_by='staffuser',
        )
        db.session.add(doc)
        db.session.commit()
        capture.records.clear()

        staff_client.post(f'/equipment/{eq.id}/documents/{doc.id}/delete')
        entries = [
            json.loads(r.message) for r in capture.records
            if 'document.deleted' in r.message
        ]
        assert len(entries) == 1

    def test_link_add_logs_mutation(self, staff_client, make_equipment, capture):
        """Link add logs equipment_link.created mutation."""
        eq = make_equipment()
        capture.records.clear()
        staff_client.post(
            f'/equipment/{eq.id}/links',
            data={'title': 'Support', 'url': 'https://support.example.com'},
        )
        entries = [
            json.loads(r.message) for r in capture.records
            if 'equipment_link.created' in r.message
        ]
        assert len(entries) == 1

    def test_link_delete_logs_mutation(self, staff_client, make_equipment, db, capture):
        """Link delete logs equipment_link.deleted mutation."""
        eq = make_equipment()
        link = ExternalLink(
            equipment_id=eq.id, title='Test',
            url='https://example.com', created_by='staffuser',
        )
        db.session.add(link)
        db.session.commit()
        capture.records.clear()

        staff_client.post(f'/equipment/{eq.id}/links/{link.id}/delete')
        entries = [
            json.loads(r.message) for r in capture.records
            if 'equipment_link.deleted' in r.message
        ]
        assert len(entries) == 1
