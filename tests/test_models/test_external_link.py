"""Tests for ExternalLink model."""

import pytest
from sqlalchemy.exc import IntegrityError

from esb.extensions import db as _db
from esb.models.external_link import ExternalLink


class TestExternalLinkCreation:
    """Tests for ExternalLink model creation and fields."""

    def test_create_link_with_all_fields(self, app, make_equipment):
        """ExternalLink created with all fields has correct values."""
        equipment = make_equipment()
        link = ExternalLink(
            equipment_id=equipment.id,
            title='User Manual',
            url='https://example.com/manual',
            created_by='staffuser',
        )
        _db.session.add(link)
        _db.session.commit()
        assert link.id is not None
        assert link.equipment_id == equipment.id
        assert link.title == 'User Manual'
        assert link.url == 'https://example.com/manual'
        assert link.created_by == 'staffuser'

    def test_created_at_set_automatically(self, app, make_equipment):
        """created_at is set automatically on creation."""
        equipment = make_equipment()
        link = ExternalLink(
            equipment_id=equipment.id,
            title='Test',
            url='https://example.com',
            created_by='staffuser',
        )
        _db.session.add(link)
        _db.session.commit()
        assert link.created_at is not None

    def test_long_url_stored(self, app, make_equipment):
        """URLs up to 2000 characters are stored correctly."""
        equipment = make_equipment()
        long_url = 'https://example.com/' + 'a' * 1970
        link = ExternalLink(
            equipment_id=equipment.id,
            title='Long URL',
            url=long_url,
            created_by='staffuser',
        )
        _db.session.add(link)
        _db.session.commit()
        assert link.url == long_url

    def test_repr(self, app):
        """ExternalLink __repr__ includes title."""
        link = ExternalLink(
            equipment_id=1,
            title='Support Page',
            url='https://example.com',
            created_by='staffuser',
        )
        assert repr(link) == "<ExternalLink 'Support Page'>"


class TestExternalLinkConstraints:
    """Tests for ExternalLink model constraints."""

    def test_title_not_nullable(self, app, make_equipment):
        """title column rejects NULL."""
        equipment = make_equipment()
        link = ExternalLink(
            equipment_id=equipment.id,
            url='https://example.com',
            created_by='staffuser',
        )
        _db.session.add(link)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_url_not_nullable(self, app, make_equipment):
        """url column rejects NULL."""
        equipment = make_equipment()
        link = ExternalLink(
            equipment_id=equipment.id,
            title='Test',
            created_by='staffuser',
        )
        _db.session.add(link)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_equipment_relationship(self, app, make_equipment):
        """ExternalLink.equipment relationship returns the associated Equipment."""
        equipment = make_equipment(name='Laser Cutter')
        link = ExternalLink(
            equipment_id=equipment.id,
            title='Manual',
            url='https://example.com',
            created_by='staffuser',
        )
        _db.session.add(link)
        _db.session.commit()
        assert link.equipment.name == 'Laser Cutter'

    def test_equipment_links_backref(self, app, make_equipment):
        """Equipment.links backref returns associated links."""
        equipment = make_equipment()
        link1 = ExternalLink(
            equipment_id=equipment.id,
            title='Link 1',
            url='https://example.com/1',
            created_by='staffuser',
        )
        link2 = ExternalLink(
            equipment_id=equipment.id,
            title='Link 2',
            url='https://example.com/2',
            created_by='staffuser',
        )
        _db.session.add_all([link1, link2])
        _db.session.commit()
        assert equipment.links.count() == 2
