"""Tests for equipment service (area management)."""

import json

import pytest

from esb.extensions import db as _db
from esb.models.area import Area
from esb.utils.exceptions import ValidationError


class TestListAreas:
    """Tests for equipment_service.list_areas()."""

    def test_returns_active_areas_ordered(self, app, make_area):
        """list_areas() returns active areas ordered by name."""
        from esb.services.equipment_service import list_areas

        make_area('Woodshop', '#woodshop')
        make_area('Electronics Lab', '#electronics')
        make_area('Metal Shop', '#metal')

        areas = list_areas()
        assert len(areas) == 3
        names = [a.name for a in areas]
        assert names == ['Electronics Lab', 'Metal Shop', 'Woodshop']

    def test_excludes_archived_areas(self, app, make_area):
        """list_areas() excludes archived areas."""
        from esb.services.equipment_service import list_areas

        make_area('Active Area', '#active')
        archived = make_area('Archived Area', '#archived')
        archived.is_archived = True
        _db.session.commit()

        areas = list_areas()
        assert len(areas) == 1
        assert areas[0].name == 'Active Area'

    def test_returns_empty_list_when_no_areas(self, app):
        """list_areas() returns empty list when no areas exist."""
        from esb.services.equipment_service import list_areas

        areas = list_areas()
        assert areas == []


class TestGetArea:
    """Tests for equipment_service.get_area()."""

    def test_returns_area_by_id(self, app, make_area):
        """get_area() returns area when found."""
        from esb.services.equipment_service import get_area

        area = make_area('Woodshop', '#woodshop')
        result = get_area(area.id)
        assert result.name == 'Woodshop'

    def test_raises_on_not_found(self, app):
        """get_area() raises ValidationError when area not found."""
        from esb.services.equipment_service import get_area

        with pytest.raises(ValidationError, match='not found'):
            get_area(99999)


class TestCreateArea:
    """Tests for equipment_service.create_area()."""

    def test_creates_area_with_valid_data(self, app):
        """create_area() creates an area and returns it."""
        from esb.services.equipment_service import create_area

        area = create_area('Woodshop', '#woodshop', 'staffuser')
        assert area.name == 'Woodshop'
        assert area.slack_channel == '#woodshop'
        assert area.is_archived is False
        assert area.id is not None

    def test_area_persisted_to_db(self, app):
        """Created area is saved to the database."""
        from esb.services.equipment_service import create_area

        create_area('Woodshop', '#woodshop', 'staffuser')
        found = _db.session.execute(
            _db.select(Area).filter_by(name='Woodshop')
        ).scalar_one_or_none()
        assert found is not None
        assert found.slack_channel == '#woodshop'

    def test_duplicate_name_raises(self, app):
        """create_area() raises ValidationError on duplicate name."""
        from esb.services.equipment_service import create_area

        create_area('Woodshop', '#woodshop', 'staffuser')
        with pytest.raises(ValidationError, match='already exists'):
            create_area('Woodshop', '#woodshop2', 'staffuser')

    def test_duplicate_name_case_insensitive(self, app):
        """create_area() rejects duplicate names case-insensitively."""
        from esb.services.equipment_service import create_area

        create_area('Woodshop', '#woodshop', 'staffuser')
        with pytest.raises(ValidationError, match='already exists'):
            create_area('woodshop', '#woodshop2', 'staffuser')

    def test_logs_area_created_mutation(self, app, capture):
        """create_area() logs an area.created mutation event."""
        from esb.services.equipment_service import create_area

        create_area('Woodshop', '#woodshop', 'staffuser')
        created_entries = [
            json.loads(r.message) for r in capture.records
            if 'area.created' in r.message
        ]
        assert len(created_entries) == 1
        entry = created_entries[0]
        assert entry['event'] == 'area.created'
        assert entry['user'] == 'staffuser'
        assert entry['data']['name'] == 'Woodshop'
        assert entry['data']['slack_channel'] == '#woodshop'
        assert 'id' in entry['data']

    def test_duplicate_archived_name_shows_archived_message(self, app, make_area):
        """create_area() shows specific message when conflict is with archived area."""
        from esb.services.equipment_service import create_area

        area = make_area('Woodshop', '#woodshop')
        area.is_archived = True
        _db.session.commit()

        with pytest.raises(ValidationError, match='archived area'):
            create_area('Woodshop', '#new', 'staffuser')


class TestUpdateArea:
    """Tests for equipment_service.update_area()."""

    def test_updates_area_successfully(self, app, make_area):
        """update_area() updates area fields."""
        from esb.services.equipment_service import update_area

        area = make_area('Old Name', '#old')
        result = update_area(area.id, 'New Name', '#new', 'staffuser')
        assert result.name == 'New Name'
        assert result.slack_channel == '#new'

    def test_update_persists_to_db(self, app, make_area):
        """Area update is persisted to database."""
        from esb.services.equipment_service import update_area

        area = make_area('Old Name', '#old')
        update_area(area.id, 'New Name', '#new', 'staffuser')
        found = _db.session.get(Area, area.id)
        assert found.name == 'New Name'
        assert found.slack_channel == '#new'

    def test_not_found_raises(self, app):
        """update_area() raises ValidationError when area not found."""
        from esb.services.equipment_service import update_area

        with pytest.raises(ValidationError, match='not found'):
            update_area(99999, 'Name', '#channel', 'staffuser')

    def test_name_conflict_raises(self, app, make_area):
        """update_area() raises ValidationError on name conflict with another area."""
        from esb.services.equipment_service import update_area

        make_area('Existing', '#existing')
        area = make_area('Other', '#other')
        with pytest.raises(ValidationError, match='already exists'):
            update_area(area.id, 'Existing', '#other', 'staffuser')

    def test_same_name_allowed(self, app, make_area):
        """update_area() allows keeping the same name."""
        from esb.services.equipment_service import update_area

        area = make_area('Keep Name', '#channel')
        result = update_area(area.id, 'Keep Name', '#new-channel', 'staffuser')
        assert result.name == 'Keep Name'
        assert result.slack_channel == '#new-channel'

    def test_logs_area_updated_mutation(self, app, capture, make_area):
        """update_area() logs an area.updated mutation event with changes."""
        from esb.services.equipment_service import update_area

        area = make_area('Old Name', '#old')
        update_area(area.id, 'New Name', '#new', 'staffuser')
        updated_entries = [
            json.loads(r.message) for r in capture.records
            if 'area.updated' in r.message
        ]
        assert len(updated_entries) == 1
        entry = updated_entries[0]
        assert entry['event'] == 'area.updated'
        assert entry['user'] == 'staffuser'
        assert entry['data']['name'] == 'New Name'
        assert entry['data']['changes']['name'] == ['Old Name', 'New Name']
        assert entry['data']['changes']['slack_channel'] == ['#old', '#new']

    def test_no_log_when_no_changes(self, app, capture, make_area):
        """update_area() skips mutation log when nothing changed."""
        from esb.services.equipment_service import update_area

        area = make_area('Same', '#same')
        capture.records.clear()
        update_area(area.id, 'Same', '#same', 'staffuser')
        updated_entries = [
            json.loads(r.message) for r in capture.records
            if 'area.updated' in r.message
        ]
        assert len(updated_entries) == 0

    def test_name_conflict_with_archived_shows_archived_message(self, app, make_area):
        """update_area() shows specific message when conflict is with archived area."""
        from esb.services.equipment_service import update_area

        archived = make_area('Taken Name', '#old')
        archived.is_archived = True
        _db.session.commit()
        area = make_area('Current', '#current')

        with pytest.raises(ValidationError, match='archived area'):
            update_area(area.id, 'Taken Name', '#current', 'staffuser')


class TestArchiveArea:
    """Tests for equipment_service.archive_area()."""

    def test_archives_area_successfully(self, app, make_area):
        """archive_area() sets is_archived to True."""
        from esb.services.equipment_service import archive_area

        area = make_area('Woodshop', '#woodshop')
        result = archive_area(area.id, 'staffuser')
        assert result.is_archived is True

    def test_archive_persists_to_db(self, app, make_area):
        """Archive is persisted to database."""
        from esb.services.equipment_service import archive_area

        area = make_area('Woodshop', '#woodshop')
        archive_area(area.id, 'staffuser')
        found = _db.session.get(Area, area.id)
        assert found.is_archived is True

    def test_not_found_raises(self, app):
        """archive_area() raises ValidationError when area not found."""
        from esb.services.equipment_service import archive_area

        with pytest.raises(ValidationError, match='not found'):
            archive_area(99999, 'staffuser')

    def test_already_archived_raises(self, app, make_area):
        """archive_area() raises ValidationError when area already archived."""
        from esb.services.equipment_service import archive_area

        area = make_area('Woodshop', '#woodshop')
        area.is_archived = True
        _db.session.commit()

        with pytest.raises(ValidationError, match='already archived'):
            archive_area(area.id, 'staffuser')

    def test_logs_area_archived_mutation(self, app, capture, make_area):
        """archive_area() logs an area.archived mutation event."""
        from esb.services.equipment_service import archive_area

        area = make_area('Woodshop', '#woodshop')
        archive_area(area.id, 'staffuser')
        archived_entries = [
            json.loads(r.message) for r in capture.records
            if 'area.archived' in r.message
        ]
        assert len(archived_entries) == 1
        entry = archived_entries[0]
        assert entry['event'] == 'area.archived'
        assert entry['user'] == 'staffuser'
        assert entry['data']['id'] == area.id
        assert entry['data']['name'] == 'Woodshop'
