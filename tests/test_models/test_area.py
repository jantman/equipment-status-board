"""Tests for Area model."""

import pytest
from sqlalchemy.exc import IntegrityError

from esb.extensions import db as _db
from esb.models.area import Area


class TestAreaCreation:
    """Tests for Area model creation and fields."""

    def test_create_area_with_defaults(self, app):
        """Area created with name has correct defaults."""
        area = Area(name='Woodshop', slack_channel='#woodshop')
        _db.session.add(area)
        _db.session.commit()
        assert area.id is not None
        assert area.name == 'Woodshop'
        assert area.slack_channel == '#woodshop'
        assert area.is_archived is False

    def test_slack_channel_nullable(self, app):
        """slack_channel defaults to None when not provided."""
        area = Area(name='Metal Shop')
        _db.session.add(area)
        _db.session.commit()
        assert area.slack_channel is None

    def test_timestamps_set_on_create(self, app):
        """created_at and updated_at are set automatically."""
        area = Area(name='Electronics Lab')
        _db.session.add(area)
        _db.session.commit()
        assert area.created_at is not None
        assert area.updated_at is not None

    def test_repr(self, app):
        """Area __repr__ includes name."""
        area = Area(name='Laser Room')
        assert repr(area) == "<Area 'Laser Room'>"


class TestAreaUniqueConstraints:
    """Tests for unique constraints on Area model."""

    def test_duplicate_name_rejected(self, app):
        """Duplicate area name raises IntegrityError."""
        a1 = Area(name='Woodshop')
        a2 = Area(name='Woodshop')
        _db.session.add(a1)
        _db.session.commit()
        _db.session.add(a2)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()
