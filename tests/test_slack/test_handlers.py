"""Tests for Slack command and view submission handlers (esb/slack/handlers.py)."""

from unittest.mock import MagicMock

import pytest

from tests.conftest import _create_area, _create_equipment, _create_repair_record, _create_user


def _register_and_capture(app):
    """Register handlers on a mock Bolt app and capture the handler functions."""
    from esb.slack.handlers import register_handlers

    handlers = {}

    def capture_command(cmd):
        def decorator(fn):
            handlers[f'command:{cmd}'] = fn
            return fn
        return decorator

    def capture_view(callback_id):
        def decorator(fn):
            handlers[f'view:{callback_id}'] = fn
            return fn
        return decorator

    bolt_app = MagicMock()
    bolt_app.command = capture_command
    bolt_app.view = capture_view
    register_handlers(bolt_app)
    return handlers


class TestEsbReportCommand:
    """Tests for /esb-report command handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.handlers = _register_and_capture(app)

    def test_report_command_calls_ack_and_opens_modal(self):
        """5.1: /esb-report calls ack() and opens modal via client.views_open()."""
        ack = MagicMock()
        client = MagicMock()
        body = {
            'trigger_id': 'T123',
            'user_id': 'U123',
            'user_name': 'testuser',
            'channel_id': 'C123',
        }

        self.handlers['command:/esb-report'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.views_open.assert_called_once()
        modal = client.views_open.call_args.kwargs['view']
        assert modal['callback_id'] == 'problem_report_submission'

    def test_report_command_no_equipment_posts_error(self):
        """Report command posts error when no equipment available."""
        # Delete all equipment
        from esb.models.equipment import Equipment
        Equipment.query.delete()
        self.db.session.commit()

        ack = MagicMock()
        client = MagicMock()
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123'}

        self.handlers['command:/esb-report'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_called_once()
        assert 'No equipment' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()


class TestProblemReportSubmission:
    """Tests for problem_report_submission view handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.handlers = _register_and_capture(app)

    def _build_view(self, equipment_id=None, description='Machine is broken',
                    reporter_name='Test User', severity='Down',
                    safety_risk=False, consumable=False):
        equipment_id = equipment_id or self.equipment.id
        safety_options = [{'value': 'safety_risk'}] if safety_risk else []
        consumable_options = [{'value': 'consumable'}] if consumable else []
        return {
            'state': {
                'values': {
                    'equipment_block': {'equipment_select': {'selected_option': {'value': str(equipment_id)}}},
                    'name_block': {'reporter_name': {'value': reporter_name}},
                    'description_block': {'description': {'value': description}},
                    'severity_block': {'severity': {'selected_option': {'value': severity}}},
                    'safety_risk_block': {'safety_risk': {'selected_options': safety_options}},
                    'consumable_block': {'consumable': {'selected_options': consumable_options}},
                },
            },
        }

    def test_submission_creates_repair_record(self):
        """5.2: Problem report submission creates repair record via repair_service."""
        ack = MagicMock()
        client = MagicMock()
        view = self._build_view()
        body = {'user': {'id': 'U12345', 'username': 'testuser'}}

        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()

        from esb.models.repair_record import RepairRecord
        records = RepairRecord.query.all()
        assert len(records) == 1
        assert records[0].description == 'Machine is broken'
        assert records[0].severity == 'Down'
        assert records[0].reporter_name == 'Test User'
        assert records[0].status == 'New'

    def test_submission_posts_ephemeral_confirmation(self):
        """5.3: Problem report submission posts ephemeral confirmation."""
        ack = MagicMock()
        client = MagicMock()
        view = self._build_view()
        body = {'user': {'id': 'U12345', 'username': 'testuser'}}

        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        client.chat_postEphemeral.assert_called_once()
        msg = client.chat_postEphemeral.call_args.kwargs['text']
        assert 'Problem report submitted' in msg
        assert 'SawStop' in msg

    def test_submission_with_safety_risk(self):
        """Safety risk checkbox is correctly passed to service."""
        ack = MagicMock()
        client = MagicMock()
        view = self._build_view(safety_risk=True)
        body = {'user': {'id': 'U12345', 'username': 'testuser'}}

        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        from esb.models.repair_record import RepairRecord
        record = RepairRecord.query.first()
        assert record.has_safety_risk is True

    def test_submission_with_consumable(self):
        """Consumable checkbox is correctly passed to service."""
        ack = MagicMock()
        client = MagicMock()
        view = self._build_view(consumable=True)
        body = {'user': {'id': 'U12345', 'username': 'testuser'}}

        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        from esb.models.repair_record import RepairRecord
        record = RepairRecord.query.first()
        assert record.is_consumable is True

    def test_validation_error_returns_slack_error(self):
        """5.13: ValidationError in view handler returns Slack-formatted error."""
        ack = MagicMock()
        client = MagicMock()
        view = self._build_view(description='')  # Empty description triggers validation error
        body = {'user': {'id': 'U12345', 'username': 'testuser'}}

        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with(response_action='errors', errors={'description_block': 'Description is required'})
        client.chat_postEphemeral.assert_not_called()


class TestEsbRepairCommand:
    """Tests for /esb-repair command handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.staff_user = _create_user('staff', username='admin1')
        self.handlers = _register_and_capture(app)

    def test_rejects_non_tech_staff_users(self):
        """5.4: /esb-repair rejects non-tech/staff users with ephemeral error."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': 'nobody@test.com'}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U999', 'channel_id': 'C123'}

        self.handlers['command:/esb-repair'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_called_once()
        assert 'Technician or Staff' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()

    def test_opens_modal_for_authorized_user(self):
        """5.5: /esb-repair opens modal for authorized users."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123'}

        self.handlers['command:/esb-repair'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.views_open.assert_called_once()
        modal = client.views_open.call_args.kwargs['view']
        assert modal['callback_id'] == 'repair_create_submission'

    def test_rejects_member_role(self):
        """Member role users are rejected from /esb-repair."""
        member = _create_user('member', username='member1')
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': member.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123'}

        self.handlers['command:/esb-repair'](ack=ack, body=body, client=client)

        client.chat_postEphemeral.assert_called_once()
        client.views_open.assert_not_called()

    def test_repair_command_no_equipment_posts_error(self):
        """M4: /esb-repair posts error when no equipment available."""
        from esb.models.equipment import Equipment
        Equipment.query.delete()
        self.db.session.commit()

        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123'}

        self.handlers['command:/esb-repair'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.chat_postEphemeral.assert_called_once()
        assert 'No equipment' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()


class TestRepairCreateSubmission:
    """Tests for repair_create_submission view handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.staff_user = _create_user('staff', username='admin1')
        self.handlers = _register_and_capture(app)

    def _build_view(self, equipment_id=None, description='Broken blade',
                    severity=None, assignee_id=None, status='New'):
        equipment_id = equipment_id or self.equipment.id
        severity_opt = {'selected_option': {'value': severity}} if severity else {'selected_option': None}
        assignee_opt = {'selected_option': {'value': str(assignee_id)}} if assignee_id else {'selected_option': None}
        status_opt = {'selected_option': {'value': status}}
        return {
            'state': {
                'values': {
                    'equipment_block': {'equipment_select': {'selected_option': {'value': str(equipment_id)}}},
                    'description_block': {'description': {'value': description}},
                    'severity_block': {'severity': severity_opt},
                    'assignee_block': {'assignee': assignee_opt},
                    'status_block': {'status': status_opt},
                },
            },
        }

    def test_creates_record_with_correct_author_id(self):
        """5.6: Repair creation submission creates record with correct author_id."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view()
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_create_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()

        from esb.models.repair_record import RepairRecord
        records = RepairRecord.query.all()
        assert len(records) == 1
        assert records[0].description == 'Broken blade'
        assert records[0].status == 'New'

    def test_posts_ephemeral_confirmation(self):
        """Repair creation posts ephemeral confirmation."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view()
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_create_submission'](ack=ack, body=body, client=client, view=view)

        client.chat_postEphemeral.assert_called_once()
        msg = client.chat_postEphemeral.call_args.kwargs['text']
        assert 'Repair record #' in msg
        assert 'SawStop' in msg

    def test_creates_record_with_non_default_status(self):
        """M3: Repair creation with non-New status creates and then updates."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view(status='In Progress')
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_create_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()

        from esb.models.repair_record import RepairRecord
        records = RepairRecord.query.all()
        assert len(records) == 1
        assert records[0].status == 'In Progress'


class TestEsbUpdateCommand:
    """Tests for /esb-update command handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.staff_user = _create_user('staff', username='admin1')
        self.record = _create_repair_record(
            equipment=self.equipment, status='In Progress', description='Blade issue',
        )
        self.handlers = _register_and_capture(app)

    def test_parses_repair_id_and_opens_modal(self):
        """5.7: /esb-update 42 parses repair ID and opens pre-populated modal."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {
            'trigger_id': 'T123',
            'user_id': 'U123',
            'channel_id': 'C123',
            'text': str(self.record.id),
        }

        self.handlers['command:/esb-update'](ack=ack, body=body, client=client)

        ack.assert_called_once()
        client.views_open.assert_called_once()
        modal = client.views_open.call_args.kwargs['view']
        assert modal['callback_id'] == 'repair_update_submission'
        assert modal['private_metadata'] == str(self.record.id)

    def test_without_id_returns_error(self):
        """5.8: /esb-update without ID returns error message."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123', 'text': ''}

        self.handlers['command:/esb-update'](ack=ack, body=body, client=client)

        client.chat_postEphemeral.assert_called_once()
        assert 'Usage' in client.chat_postEphemeral.call_args.kwargs['text']

    def test_nonexistent_id_returns_error(self):
        """5.9: /esb-update 999 with non-existent ID returns error."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123', 'text': '99999'}

        self.handlers['command:/esb-update'](ack=ack, body=body, client=client)

        client.chat_postEphemeral.assert_called_once()
        assert 'not found' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()

    def test_invalid_id_format_returns_error(self):
        """M2: /esb-update with non-numeric ID returns error."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123', 'text': 'abc'}

        self.handlers['command:/esb-update'](ack=ack, body=body, client=client)

        client.chat_postEphemeral.assert_called_once()
        assert 'Invalid repair ID' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()

    def test_rejects_unauthorized_user(self):
        """Unauthorized user rejected from /esb-update."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': 'nobody@test.com'}},
        }
        body = {'trigger_id': 'T123', 'user_id': 'U999', 'channel_id': 'C123', 'text': '1'}

        self.handlers['command:/esb-update'](ack=ack, body=body, client=client)

        client.chat_postEphemeral.assert_called_once()
        assert 'Technician or Staff' in client.chat_postEphemeral.call_args.kwargs['text']
        client.views_open.assert_not_called()


class TestRepairUpdateSubmission:
    """Tests for repair_update_submission view handler."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.staff_user = _create_user('staff', username='admin1')
        self.record = _create_repair_record(
            equipment=self.equipment, status='New', description='Blade issue',
        )
        self.handlers = _register_and_capture(app)

    def _build_view(self, repair_record_id=None, status='In Progress',
                    severity=None, assignee_id=None, eta=None,
                    specialist_description=None, note=None):
        repair_record_id = repair_record_id or self.record.id
        severity_opt = {'selected_option': {'value': severity}} if severity else {'selected_option': None}
        assignee_opt = {'selected_option': {'value': str(assignee_id)}} if assignee_id else {'selected_option': None}
        return {
            'private_metadata': str(repair_record_id),
            'state': {
                'values': {
                    'status_block': {'status': {'selected_option': {'value': status}}},
                    'severity_block': {'severity': severity_opt},
                    'assignee_block': {'assignee': assignee_opt},
                    'eta_block': {'eta': {'selected_date': eta}},
                    'specialist_block': {'specialist_description': {'value': specialist_description}},
                    'note_block': {'note': {'value': note}},
                },
            },
        }

    def test_updates_repair_record(self):
        """5.10: Repair update submission calls update_repair_record() with correct changes."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view(status='In Progress', severity='Down')
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_update_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()

        from esb.extensions import db as _db
        from esb.models.repair_record import RepairRecord
        record = _db.session.get(RepairRecord, self.record.id)
        assert record.status == 'In Progress'
        assert record.severity == 'Down'

    def test_posts_ephemeral_confirmation(self):
        """Update submission posts ephemeral confirmation."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view(status='In Progress')
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_update_submission'](ack=ack, body=body, client=client, view=view)

        client.chat_postEphemeral.assert_called_once()
        msg = client.chat_postEphemeral.call_args.kwargs['text']
        assert f'Repair record #{self.record.id} updated' in msg

    def test_update_with_note(self):
        """Update with a note adds timeline entry."""
        ack = MagicMock()
        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }
        view = self._build_view(note='Fixed the blade')
        body = {'user': {'id': 'U123', 'username': 'slackuser'}}

        self.handlers['view:repair_update_submission'](ack=ack, body=body, client=client, view=view)

        ack.assert_called_once_with()

        from esb.models.repair_timeline_entry import RepairTimelineEntry
        notes = RepairTimelineEntry.query.filter_by(
            repair_record_id=self.record.id, entry_type='note',
        ).all()
        assert len(notes) == 1
        assert notes[0].content == 'Fixed the blade'


class TestResolveEsbUser:
    """Tests for _resolve_esb_user() helper."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.staff_user = _create_user('staff', username='admin1')

    def test_maps_slack_user_to_esb_user_via_email(self):
        """5.11: _resolve_esb_user() maps Slack user to ESB user via email."""
        from esb.slack.handlers import _resolve_esb_user

        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }

        user = _resolve_esb_user(client, 'U12345')

        assert user is not None
        assert user.id == self.staff_user.id
        assert user.username == 'admin1'

    def test_returns_none_for_unmapped_user(self):
        """5.12: _resolve_esb_user() returns None for unmapped user."""
        from esb.slack.handlers import _resolve_esb_user

        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': 'nobody@notfound.com'}},
        }

        user = _resolve_esb_user(client, 'U99999')

        assert user is None

    def test_returns_none_when_api_fails(self):
        """_resolve_esb_user() returns None when Slack API call fails."""
        from esb.slack.handlers import _resolve_esb_user

        client = MagicMock()
        client.users_info.side_effect = Exception('API error')

        user = _resolve_esb_user(client, 'U12345')

        assert user is None

    def test_returns_none_for_no_email(self):
        """_resolve_esb_user() returns None when user has no email in profile."""
        from esb.slack.handlers import _resolve_esb_user

        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {}},
        }

        user = _resolve_esb_user(client, 'U12345')

        assert user is None

    def test_returns_none_for_inactive_user(self):
        """_resolve_esb_user() returns None for inactive ESB user."""
        self.staff_user.is_active = False
        self.db.session.commit()

        from esb.slack.handlers import _resolve_esb_user

        client = MagicMock()
        client.users_info.return_value = {
            'user': {'profile': {'email': self.staff_user.email}},
        }

        user = _resolve_esb_user(client, 'U12345')

        assert user is None


class TestHandlersWithFlaskAppContext:
    """5.14: Test all handlers work within Flask app context."""

    @pytest.fixture(autouse=True)
    def setup(self, app, db):
        self.app = app
        self.db = db
        self.area = _create_area(name='Woodshop', slack_channel='#woodshop')
        self.equipment = _create_equipment(name='SawStop', area=self.area)
        self.staff_user = _create_user('staff', username='admin1')
        self.handlers = _register_and_capture(app)

    def test_report_handler_in_app_context(self):
        """Command handler works within Flask app context."""
        ack = MagicMock()
        client = MagicMock()
        body = {'trigger_id': 'T123', 'user_id': 'U123', 'channel_id': 'C123'}

        # Should not raise any context errors
        self.handlers['command:/esb-report'](ack=ack, body=body, client=client)
        ack.assert_called_once()

    def test_view_handler_in_app_context(self):
        """View submission handler works within Flask app context."""
        ack = MagicMock()
        client = MagicMock()
        view = {
            'state': {
                'values': {
                    'equipment_block': {'equipment_select': {'selected_option': {'value': str(self.equipment.id)}}},
                    'name_block': {'reporter_name': {'value': 'Test User'}},
                    'description_block': {'description': {'value': 'Test problem'}},
                    'severity_block': {'severity': {'selected_option': {'value': 'Not Sure'}}},
                    'safety_risk_block': {'safety_risk': {'selected_options': []}},
                    'consumable_block': {'consumable': {'selected_options': []}},
                },
            },
        }
        body = {'user': {'id': 'U123', 'username': 'testuser'}}

        # Should not raise any context errors
        self.handlers['view:problem_report_submission'](ack=ack, body=body, client=client, view=view)
        ack.assert_called_once_with()
