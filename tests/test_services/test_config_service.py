"""Tests for config service."""

import json

from esb.extensions import db as _db
from esb.models.app_config import AppConfig


class TestGetConfig:
    """Tests for config_service.get_config()."""

    def test_returns_value_when_key_exists(self, app):
        """get_config() returns value when key exists."""
        from esb.services.config_service import get_config

        config = AppConfig(key='test_key', value='test_value')
        _db.session.add(config)
        _db.session.commit()

        result = get_config('test_key')
        assert result == 'test_value'

    def test_returns_default_when_key_missing(self, app):
        """get_config() returns default when key doesn't exist."""
        from esb.services.config_service import get_config

        result = get_config('nonexistent', 'fallback')
        assert result == 'fallback'

    def test_returns_empty_string_default(self, app):
        """get_config() returns empty string by default when key missing."""
        from esb.services.config_service import get_config

        result = get_config('missing')
        assert result == ''


class TestSetConfig:
    """Tests for config_service.set_config()."""

    def test_creates_new_entry(self, app):
        """set_config() creates new entry when key doesn't exist."""
        from esb.services.config_service import set_config

        result = set_config('new_key', 'new_value', 'staffuser')
        assert result.key == 'new_key'
        assert result.value == 'new_value'
        assert result.id is not None

        found = _db.session.execute(
            _db.select(AppConfig).filter_by(key='new_key')
        ).scalar_one_or_none()
        assert found is not None
        assert found.value == 'new_value'

    def test_updates_existing_entry(self, app):
        """set_config() updates existing entry when key exists."""
        from esb.services.config_service import set_config

        set_config('update_key', 'old_value', 'staffuser')
        result = set_config('update_key', 'new_value', 'staffuser')
        assert result.value == 'new_value'

        found = _db.session.execute(
            _db.select(AppConfig).filter_by(key='update_key')
        ).scalar_one_or_none()
        assert found.value == 'new_value'

    def test_mutation_logging_on_update(self, app, capture):
        """set_config() logs mutation with old and new values on update."""
        from esb.services.config_service import set_config

        set_config('log_key', 'old', 'staffuser')
        capture.records.clear()
        set_config('log_key', 'new', 'staffuser')

        entries = [
            json.loads(r.message) for r in capture.records
            if 'app_config.updated' in r.message
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry['event'] == 'app_config.updated'
        assert entry['user'] == 'staffuser'
        assert entry['data']['key'] == 'log_key'
        assert entry['data']['old_value'] == 'old'
        assert entry['data']['new_value'] == 'new'

    def test_mutation_logging_on_create(self, app, capture):
        """set_config() logs mutation when creating new entry (old_value is empty)."""
        from esb.services.config_service import set_config

        capture.records.clear()
        set_config('brand_new', 'value', 'staffuser')

        entries = [
            json.loads(r.message) for r in capture.records
            if 'app_config.updated' in r.message
        ]
        assert len(entries) == 1
        entry = entries[0]
        assert entry['data']['old_value'] == ''
        assert entry['data']['new_value'] == 'value'
