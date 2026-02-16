"""Slack command and view submission handlers."""

import logging

logger = logging.getLogger(__name__)


def _resolve_esb_user(client, slack_user_id):
    """Map a Slack user ID to an ESB User account.

    Strategy:
    1. Call Slack API to get user's email from their profile
    2. Look up ESB User by matching email

    Args:
        client: Slack WebClient instance (provided by Bolt).
        slack_user_id: Slack user ID (e.g., 'U12345678').

    Returns:
        User instance or None if no matching ESB account.
    """
    from esb.extensions import db
    from esb.models.user import User

    try:
        result = client.users_info(user=slack_user_id)
        email = result['user']['profile'].get('email')
        if not email:
            return None
        return db.session.execute(
            db.select(User).filter_by(email=email, is_active=True)
        ).scalars().first()
    except Exception:
        logger.warning('Failed to resolve ESB user for Slack user %s', slack_user_id, exc_info=True)
        return None


def register_handlers(bolt_app):
    """Register all Slack command and view submission handlers."""

    @bolt_app.command('/esb-report')
    def handle_esb_report(ack, body, client):
        ack()
        from esb.slack.forms import build_equipment_options, build_problem_report_modal

        options = build_equipment_options()
        if not options:
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=':x: No equipment available for reporting.',
            )
            return

        client.views_open(
            trigger_id=body['trigger_id'],
            view=build_problem_report_modal(options),
        )

    @bolt_app.view('problem_report_submission')
    def handle_problem_report_submission(ack, body, client, view):
        values = view['state']['values']

        equipment_id = int(values['equipment_block']['equipment_select']['selected_option']['value'])
        reporter_name = values['name_block']['reporter_name']['value']
        description = values['description_block']['description']['value']

        severity_data = values['severity_block']['severity'].get('selected_option')
        severity = severity_data['value'] if severity_data else 'Not Sure'

        safety_options = values['safety_risk_block']['safety_risk'].get('selected_options', [])
        has_safety_risk = any(o['value'] == 'safety_risk' for o in safety_options)

        consumable_options = values['consumable_block']['consumable'].get('selected_options', [])
        is_consumable = any(o['value'] == 'consumable' for o in consumable_options)

        from esb.utils.exceptions import ValidationError

        try:
            from esb.services import repair_service

            record = repair_service.create_repair_record(
                equipment_id=equipment_id,
                description=description,
                created_by=body['user']['username'],
                severity=severity,
                reporter_name=reporter_name,
                has_safety_risk=has_safety_risk,
                is_consumable=is_consumable,
            )
        except ValidationError as e:
            ack(response_action='errors', errors={
                'description_block': str(e),
            })
            return
        except Exception:
            logger.exception('Unexpected error in problem report submission')
            ack(response_action='errors', errors={
                'description_block': 'An unexpected error occurred. Please try again.',
            })
            return

        ack()

        from esb.extensions import db
        from esb.models.equipment import Equipment
        equipment = db.session.get(Equipment, equipment_id)
        equipment_name = equipment.name if equipment else f'ID {equipment_id}'

        client.chat_postEphemeral(
            channel=body['user']['id'],
            user=body['user']['id'],
            text=f':white_check_mark: Problem report submitted for *{equipment_name}* (Repair #{record.id})',
        )

    @bolt_app.command('/esb-repair')
    def handle_esb_repair(ack, body, client):
        ack()
        esb_user = _resolve_esb_user(client, body['user_id'])
        if esb_user is None or esb_user.role not in ('technician', 'staff'):
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=':x: You must have a Technician or Staff account linked to use this command.',
            )
            return

        from esb.slack.forms import build_equipment_options, build_repair_create_modal, build_user_options

        equipment_options = build_equipment_options()
        if not equipment_options:
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=':x: No equipment available.',
            )
            return

        user_options = build_user_options()
        client.views_open(
            trigger_id=body['trigger_id'],
            view=build_repair_create_modal(equipment_options, user_options),
        )

    @bolt_app.view('repair_create_submission')
    def handle_repair_create_submission(ack, body, client, view):
        values = view['state']['values']

        equipment_id = int(values['equipment_block']['equipment_select']['selected_option']['value'])
        description = values['description_block']['description']['value']

        severity_data = values['severity_block']['severity'].get('selected_option')
        severity = severity_data['value'] if severity_data else None

        assignee_block = values.get('assignee_block')
        assignee_data = assignee_block['assignee'].get('selected_option') if assignee_block else None
        assignee_id = int(assignee_data['value']) if assignee_data else None

        status_data = values['status_block']['status'].get('selected_option')
        status = status_data['value'] if status_data else 'New'

        # Resolve the Slack user to get author_id
        esb_user = _resolve_esb_user(client, body['user']['id'])

        from esb.utils.exceptions import ValidationError

        try:
            from esb.services import repair_service

            record = repair_service.create_repair_record(
                equipment_id=equipment_id,
                description=description,
                created_by=esb_user.username if esb_user else body['user']['username'],
                severity=severity,
                assignee_id=assignee_id,
                author_id=esb_user.id if esb_user else None,
            )

            # Note: Setting non-"New" status requires a second service call, which
            # may generate a duplicate notification. This is a known limitation of
            # the service layer not accepting status on creation.
            if status != 'New':
                repair_service.update_repair_record(
                    repair_record_id=record.id,
                    updated_by=esb_user.username if esb_user else body['user']['username'],
                    author_id=esb_user.id if esb_user else None,
                    status=status,
                )
        except ValidationError as e:
            ack(response_action='errors', errors={
                'description_block': str(e),
            })
            return
        except Exception:
            logger.exception('Unexpected error in repair creation submission')
            ack(response_action='errors', errors={
                'description_block': 'An unexpected error occurred. Please try again.',
            })
            return

        ack()

        from esb.extensions import db
        from esb.models.equipment import Equipment
        equipment = db.session.get(Equipment, equipment_id)
        equipment_name = equipment.name if equipment else f'ID {equipment_id}'

        client.chat_postEphemeral(
            channel=body['user']['id'],
            user=body['user']['id'],
            text=f':white_check_mark: Repair record #{record.id} created for *{equipment_name}*',
        )

    @bolt_app.command('/esb-update')
    def handle_esb_update(ack, body, client):
        ack()
        esb_user = _resolve_esb_user(client, body['user_id'])
        if esb_user is None or esb_user.role not in ('technician', 'staff'):
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=':x: You must have a Technician or Staff account linked to use this command.',
            )
            return

        command_text = body.get('text', '').strip()
        if not command_text:
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=':x: Usage: `/esb-update [repair-id]`',
            )
            return

        try:
            repair_id = int(command_text)
        except ValueError:
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=f':x: Invalid repair ID: `{command_text}`. Must be a number.',
            )
            return

        from esb.utils.exceptions import ValidationError

        try:
            from esb.services import repair_service
            record = repair_service.get_repair_record(repair_id)
        except ValidationError:
            client.chat_postEphemeral(
                channel=body['channel_id'],
                user=body['user_id'],
                text=f':x: Repair record #{repair_id} not found.',
            )
            return

        from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES
        from esb.slack.forms import build_repair_update_modal, build_user_options

        status_options = [
            {'text': {'type': 'plain_text', 'text': s}, 'value': s}
            for s in REPAIR_STATUSES
        ]
        severity_options = [
            {'text': {'type': 'plain_text', 'text': s}, 'value': s}
            for s in REPAIR_SEVERITIES
        ]
        user_options = build_user_options()

        client.views_open(
            trigger_id=body['trigger_id'],
            view=build_repair_update_modal(record, status_options, severity_options, user_options),
        )

    @bolt_app.view('repair_update_submission')
    def handle_repair_update_submission(ack, body, client, view):
        repair_record_id = int(view['private_metadata'])
        values = view['state']['values']

        # Extract changes
        changes = {}

        status_data = values['status_block']['status'].get('selected_option')
        if status_data:
            changes['status'] = status_data['value']

        severity_data = values['severity_block']['severity'].get('selected_option')
        changes['severity'] = severity_data['value'] if severity_data else None

        assignee_block = values.get('assignee_block')
        assignee_data = assignee_block['assignee'].get('selected_option') if assignee_block else None
        if assignee_data:
            changes['assignee_id'] = int(assignee_data['value'])
        else:
            changes['assignee_id'] = None

        eta_str = values['eta_block']['eta'].get('selected_date')
        if eta_str:
            from datetime import datetime
            changes['eta'] = datetime.strptime(eta_str, '%Y-%m-%d').date()
        else:
            changes['eta'] = None

        specialist_val = values['specialist_block']['specialist_description'].get('value')
        changes['specialist_description'] = specialist_val

        note_val = values['note_block']['note'].get('value')
        if note_val:
            changes['note'] = note_val

        # Resolve the Slack user
        esb_user = _resolve_esb_user(client, body['user']['id'])

        from esb.utils.exceptions import ValidationError

        try:
            from esb.services import repair_service

            repair_service.update_repair_record(
                repair_record_id=repair_record_id,
                updated_by=esb_user.username if esb_user else body['user']['username'],
                author_id=esb_user.id if esb_user else None,
                **changes,
            )
        except ValidationError as e:
            ack(response_action='errors', errors={
                'status_block': str(e),
            })
            return
        except Exception:
            logger.exception('Unexpected error in repair update submission')
            ack(response_action='errors', errors={
                'status_block': 'An unexpected error occurred. Please try again.',
            })
            return

        ack()

        client.chat_postEphemeral(
            channel=body['user']['id'],
            user=body['user']['id'],
            text=f':white_check_mark: Repair record #{repair_record_id} updated',
        )
