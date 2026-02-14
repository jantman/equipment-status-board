"""Tests for mutation logging utility."""

import json
import logging

import pytest

from esb.utils.logging import log_mutation, mutation_logger


class _CaptureHandler(logging.Handler):
    """Test handler that captures log records."""

    def __init__(self):
        super().__init__()
        self.records = []

    def emit(self, record):
        self.records.append(record)


@pytest.fixture
def capture():
    """Add a capture handler to the mutation logger for testing."""
    handler = _CaptureHandler()
    mutation_logger.addHandler(handler)
    yield handler
    mutation_logger.removeHandler(handler)


class TestLogMutation:
    """Tests for log_mutation function."""

    def test_outputs_valid_json(self, capture):
        """log_mutation writes valid JSON."""
        log_mutation('equipment.created', 'admin', {'id': 1, 'name': 'SawStop'})
        entry = json.loads(capture.records[-1].message)
        assert isinstance(entry, dict)

    def test_contains_required_fields(self, capture):
        """Output contains timestamp, event, user, and data."""
        log_mutation('equipment.created', 'admin', {'id': 1})
        entry = json.loads(capture.records[-1].message)
        assert 'timestamp' in entry
        assert 'event' in entry
        assert 'user' in entry
        assert 'data' in entry

    def test_event_field_matches_input(self, capture):
        """Event field matches the provided event string."""
        log_mutation('repair_record.status_changed', 'marcus', {'id': 42})
        entry = json.loads(capture.records[-1].message)
        assert entry['event'] == 'repair_record.status_changed'

    def test_user_field_matches_input(self, capture):
        """User field matches the provided username."""
        log_mutation('area.created', 'dana', {'name': 'Woodshop'})
        entry = json.loads(capture.records[-1].message)
        assert entry['user'] == 'dana'

    def test_data_field_matches_input(self, capture):
        """Data field contains the provided data dict."""
        data = {'id': 7, 'name': 'Drill Press', 'area_id': 2}
        log_mutation('equipment.updated', 'admin', data)
        entry = json.loads(capture.records[-1].message)
        assert entry['data'] == data

    def test_timestamp_is_iso8601(self, capture):
        """Timestamp is in ISO 8601 format."""
        log_mutation('user.created', 'system', {'username': 'newuser'})
        entry = json.loads(capture.records[-1].message)
        assert 'T' in entry['timestamp']

    def test_system_user(self, capture):
        """System user is accepted."""
        log_mutation('equipment.archived', 'system', {'id': 5})
        entry = json.loads(capture.records[-1].message)
        assert entry['user'] == 'system'

    def test_logger_name(self):
        """Mutation logger uses the correct logger name."""
        assert mutation_logger.name == 'esb.mutations'

    def test_propagate_is_false(self):
        """Mutation logger does not propagate to avoid duplicate output."""
        assert mutation_logger.propagate is False
