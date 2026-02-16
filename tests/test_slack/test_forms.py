"""Tests for Slack Block Kit modal builder functions (esb/slack/forms.py)."""

import pytest

from tests.conftest import _create_area, _create_equipment, _create_user


class TestBuildEquipmentOptions:
    """Tests for build_equipment_options()."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db

    def test_returns_non_archived_equipment(self):
        area = _create_area(name='Woodshop')
        _create_equipment(name='SawStop', area=area)
        _create_equipment(name='Drill Press', area=area)

        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()

        assert len(options) == 2
        texts = [o['text']['text'] for o in options]
        assert 'Drill Press (Woodshop)' in texts
        assert 'SawStop (Woodshop)' in texts

    def test_excludes_archived_equipment(self):
        area = _create_area(name='Metalshop')
        _create_equipment(name='Active Lathe', area=area)
        _create_equipment(name='Old Mill', area=area, is_archived=True)

        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()

        assert len(options) == 1
        assert options[0]['text']['text'] == 'Active Lathe (Metalshop)'

    def test_returns_correct_option_format(self):
        area = _create_area(name='Lab')
        equip = _create_equipment(name='Oscilloscope', area=area)

        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()

        assert len(options) == 1
        opt = options[0]
        assert opt['text']['type'] == 'plain_text'
        assert opt['text']['text'] == 'Oscilloscope (Lab)'
        assert opt['value'] == str(equip.id)

    def test_returns_empty_list_when_no_equipment(self):
        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()
        assert options == []

    def test_options_ordered_by_name(self):
        area = _create_area(name='Shop')
        _create_equipment(name='Zebra Saw', area=area)
        _create_equipment(name='Alpha Drill', area=area)
        _create_equipment(name='Mike Lathe', area=area)

        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()

        texts = [o['text']['text'] for o in options]
        assert texts == ['Alpha Drill (Shop)', 'Mike Lathe (Shop)', 'Zebra Saw (Shop)']

    def test_truncates_long_names(self):
        area = _create_area(name='A' * 50)
        _create_equipment(name='B' * 50, area=area)

        from esb.slack.forms import build_equipment_options
        options = build_equipment_options()

        assert len(options[0]['text']['text']) <= 75


class TestBuildUserOptions:
    """Tests for build_user_options()."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db

    def test_returns_active_tech_and_staff(self):
        _create_user('staff', username='admin1')
        _create_user('technician', username='tech1')

        from esb.slack.forms import build_user_options
        options = build_user_options()

        assert len(options) == 2
        texts = [o['text']['text'] for o in options]
        assert 'admin1 (staff)' in texts
        assert 'tech1 (technician)' in texts

    def test_excludes_member_role(self):
        _create_user('staff', username='staffuser')
        _create_user('member', username='memberuser')

        from esb.slack.forms import build_user_options
        options = build_user_options()

        assert len(options) == 1
        assert options[0]['text']['text'] == 'staffuser (staff)'

    def test_excludes_inactive_users(self):
        user = _create_user('technician', username='inactive_tech')
        user.is_active = False
        self.db.session.commit()

        from esb.slack.forms import build_user_options
        options = build_user_options()

        assert len(options) == 0

    def test_returns_correct_option_format(self):
        user = _create_user('staff', username='admin2')

        from esb.slack.forms import build_user_options
        options = build_user_options()

        assert len(options) == 1
        opt = options[0]
        assert opt['text']['type'] == 'plain_text'
        assert opt['value'] == str(user.id)

    def test_ordered_by_username(self):
        _create_user('staff', username='zara')
        _create_user('technician', username='alice')
        _create_user('staff', username='mike')

        from esb.slack.forms import build_user_options
        options = build_user_options()

        texts = [o['text']['text'] for o in options]
        assert texts[0].startswith('alice')
        assert texts[1].startswith('mike')
        assert texts[2].startswith('zara')


class TestBuildProblemReportModal:
    """Tests for build_problem_report_modal()."""

    def test_returns_valid_modal_structure(self):
        from esb.slack.forms import build_problem_report_modal

        options = [{'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'}]
        modal = build_problem_report_modal(options)

        assert modal['type'] == 'modal'
        assert modal['callback_id'] == 'problem_report_submission'
        assert modal['title']['text'] == 'Report a Problem'
        assert modal['submit']['text'] == 'Submit Report'
        assert modal['close']['text'] == 'Cancel'

    def test_has_correct_blocks(self):
        from esb.slack.forms import build_problem_report_modal

        options = [{'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'}]
        modal = build_problem_report_modal(options)

        block_ids = [b['block_id'] for b in modal['blocks']]
        assert 'equipment_block' in block_ids
        assert 'name_block' in block_ids
        assert 'description_block' in block_ids
        assert 'severity_block' in block_ids
        assert 'safety_risk_block' in block_ids
        assert 'consumable_block' in block_ids

    def test_severity_defaults_to_not_sure(self):
        from esb.slack.forms import build_problem_report_modal

        options = [{'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'}]
        modal = build_problem_report_modal(options)

        severity_block = [b for b in modal['blocks'] if b['block_id'] == 'severity_block'][0]
        initial = severity_block['element']['initial_option']
        assert initial['value'] == 'Not Sure'

    def test_equipment_options_passed_through(self):
        from esb.slack.forms import build_problem_report_modal

        options = [
            {'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'},
            {'text': {'type': 'plain_text', 'text': 'Drill (Lab)'}, 'value': '2'},
        ]
        modal = build_problem_report_modal(options)

        equip_block = [b for b in modal['blocks'] if b['block_id'] == 'equipment_block'][0]
        assert equip_block['element']['options'] == options


class TestBuildRepairCreateModal:
    """Tests for build_repair_create_modal()."""

    def test_returns_valid_modal_structure(self):
        from esb.slack.forms import build_repair_create_modal

        equip_opts = [{'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'}]
        user_opts = [{'text': {'type': 'plain_text', 'text': 'admin (staff)'}, 'value': '1'}]
        modal = build_repair_create_modal(equip_opts, user_opts)

        assert modal['type'] == 'modal'
        assert modal['callback_id'] == 'repair_create_submission'
        assert modal['title']['text'] == 'Create Repair Record'

    def test_has_equipment_and_user_selectors(self):
        from esb.slack.forms import build_repair_create_modal

        equip_opts = [{'text': {'type': 'plain_text', 'text': 'Saw (Shop)'}, 'value': '1'}]
        user_opts = [{'text': {'type': 'plain_text', 'text': 'admin (staff)'}, 'value': '1'}]
        modal = build_repair_create_modal(equip_opts, user_opts)

        block_ids = [b['block_id'] for b in modal['blocks']]
        assert 'equipment_block' in block_ids
        assert 'description_block' in block_ids
        assert 'severity_block' in block_ids
        assert 'assignee_block' in block_ids
        assert 'status_block' in block_ids

    def test_status_defaults_to_new(self):
        from esb.slack.forms import build_repair_create_modal

        equip_opts = [{'text': {'type': 'plain_text', 'text': 'Saw'}, 'value': '1'}]
        user_opts = [{'text': {'type': 'plain_text', 'text': 'admin'}, 'value': '1'}]
        modal = build_repair_create_modal(equip_opts, user_opts)

        status_block = [b for b in modal['blocks'] if b['block_id'] == 'status_block'][0]
        assert status_block['element']['initial_option']['value'] == 'New'

    def test_all_statuses_available(self):
        from esb.models.repair_record import REPAIR_STATUSES
        from esb.slack.forms import build_repair_create_modal

        equip_opts = [{'text': {'type': 'plain_text', 'text': 'Saw'}, 'value': '1'}]
        user_opts = [{'text': {'type': 'plain_text', 'text': 'admin'}, 'value': '1'}]
        modal = build_repair_create_modal(equip_opts, user_opts)

        status_block = [b for b in modal['blocks'] if b['block_id'] == 'status_block'][0]
        status_values = [o['value'] for o in status_block['element']['options']]
        assert status_values == REPAIR_STATUSES

    def test_no_assignee_block_when_no_users(self):
        """L2: Assignee block is excluded when no users available."""
        from esb.slack.forms import build_repair_create_modal

        equip_opts = [{'text': {'type': 'plain_text', 'text': 'Saw'}, 'value': '1'}]
        modal = build_repair_create_modal(equip_opts, [])

        block_ids = [b['block_id'] for b in modal['blocks']]
        assert 'assignee_block' not in block_ids


class TestBuildRepairUpdateModal:
    """Tests for build_repair_update_modal()."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db

    def _make_record(self, **kwargs):
        area = _create_area(name='Shop')
        equip = _create_equipment(name='Saw', area=area)
        defaults = {
            'equipment_id': equip.id,
            'status': 'In Progress',
            'severity': 'Down',
            'description': 'Broken blade',
        }
        defaults.update(kwargs)
        from esb.models.repair_record import RepairRecord
        record = RepairRecord(**defaults)
        self.db.session.add(record)
        self.db.session.commit()
        return record

    def test_returns_valid_modal_with_prepopulated_values(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record()
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]
        user_opts = [{'text': {'type': 'plain_text', 'text': 'admin (staff)'}, 'value': '1'}]

        modal = build_repair_update_modal(record, status_opts, severity_opts, user_opts)

        assert modal['type'] == 'modal'
        assert modal['callback_id'] == 'repair_update_submission'
        assert modal['private_metadata'] == str(record.id)

    def test_status_prepopulated(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record(status='Parts Needed')
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        status_block = [b for b in modal['blocks'] if b['block_id'] == 'status_block'][0]
        assert status_block['element']['initial_option']['value'] == 'Parts Needed'

    def test_severity_prepopulated_when_present(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record(severity='Degraded')
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        severity_block = [b for b in modal['blocks'] if b['block_id'] == 'severity_block'][0]
        assert severity_block['element']['initial_option']['value'] == 'Degraded'

    def test_severity_not_prepopulated_when_none(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record(severity=None)
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        severity_block = [b for b in modal['blocks'] if b['block_id'] == 'severity_block'][0]
        assert 'initial_option' not in severity_block['element']

    def test_eta_prepopulated_when_present(self):
        from datetime import date

        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record(eta=date(2026, 3, 15))
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        eta_block = [b for b in modal['blocks'] if b['block_id'] == 'eta_block'][0]
        assert eta_block['element']['initial_date'] == '2026-03-15'

    def test_specialist_description_prepopulated(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record(specialist_description='Needs electrician')
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        specialist_block = [b for b in modal['blocks'] if b['block_id'] == 'specialist_block'][0]
        assert specialist_block['element']['initial_value'] == 'Needs electrician'

    def test_assignee_prepopulated_when_present(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        user = _create_user('technician', username='tech_assign')
        record = self._make_record(assignee_id=user.id)
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]
        user_opts = [{'text': {'type': 'plain_text', 'text': f'{user.username} (technician)'}, 'value': str(user.id)}]

        modal = build_repair_update_modal(record, status_opts, severity_opts, user_opts)

        assignee_block = [b for b in modal['blocks'] if b['block_id'] == 'assignee_block'][0]
        assert assignee_block['element']['initial_option']['value'] == str(user.id)

    def test_note_block_always_empty(self):
        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal

        record = self._make_record()
        status_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_STATUSES]
        severity_opts = [{'text': {'type': 'plain_text', 'text': s}, 'value': s} for s in REPAIR_SEVERITIES]

        modal = build_repair_update_modal(record, status_opts, severity_opts, [])

        note_block = [b for b in modal['blocks'] if b['block_id'] == 'note_block'][0]
        assert 'initial_value' not in note_block['element']
