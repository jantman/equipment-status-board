"""Tests for AppConfig model."""

import pytest

from esb.extensions import db as _db
from esb.models.app_config import AppConfig


class TestAppConfig:
    """Tests for the AppConfig model."""

    def test_create_with_key_and_value(self, app):
        """AppConfig can be created with key and value."""
        config = AppConfig(key='test_key', value='test_value')
        _db.session.add(config)
        _db.session.commit()

        found = _db.session.get(AppConfig, config.id)
        assert found is not None
        assert found.key == 'test_key'
        assert found.value == 'test_value'
        assert found.updated_at is not None

    def test_unique_constraint_on_key(self, app):
        """AppConfig enforces unique constraint on key."""
        config1 = AppConfig(key='unique_key', value='value1')
        _db.session.add(config1)
        _db.session.commit()

        config2 = AppConfig(key='unique_key', value='value2')
        _db.session.add(config2)
        with pytest.raises(Exception):
            _db.session.commit()

    def test_default_empty_string_for_value(self, app):
        """AppConfig value defaults to empty string."""
        config = AppConfig(key='no_value_key')
        _db.session.add(config)
        _db.session.commit()

        found = _db.session.get(AppConfig, config.id)
        assert found.value == ''

    def test_repr(self, app):
        """AppConfig __repr__ shows key."""
        config = AppConfig(key='repr_key', value='v')
        assert repr(config) == "<AppConfig 'repr_key'>"
