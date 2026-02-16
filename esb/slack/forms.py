"""Block Kit modal builder and message formatting functions for Slack commands."""


_STATUS_EMOJI = {
    'green': ':white_check_mark:',
    'yellow': ':warning:',
    'red': ':x:',
}


def format_status_summary(dashboard_data):
    """Format area status dashboard data as Slack mrkdwn text.

    Args:
        dashboard_data: List of dicts from status_service.get_area_status_dashboard().

    Returns:
        Formatted mrkdwn string for ephemeral Slack message.
    """
    if not dashboard_data or all(not area_data['equipment'] for area_data in dashboard_data):
        return 'No equipment has been registered yet.'

    lines = [':bar_chart: *Equipment Status Summary*\n']

    for area_data in dashboard_data:
        area = area_data['area']
        equipment_list = area_data['equipment']
        if not equipment_list:
            continue

        counts = {'green': 0, 'yellow': 0, 'red': 0}
        for equip_data in equipment_list:
            color = equip_data['status']['color']
            counts[color] = counts.get(color, 0) + 1

        lines.append(
            f"*{area.name}* — "
            f"{counts['green']} :white_check_mark: operational, "
            f"{counts['yellow']} :warning: degraded, "
            f"{counts['red']} :x: down"
        )

    return '\n'.join(lines)


def format_equipment_status_detail(equipment, status_detail):
    """Format single equipment status detail as Slack mrkdwn text.

    Args:
        equipment: Equipment model instance.
        status_detail: Dict from status_service.get_equipment_status_detail().

    Returns:
        Formatted mrkdwn string.
    """
    emoji = _STATUS_EMOJI.get(status_detail['color'], ':grey_question:')
    area_name = equipment.area.name if equipment.area else 'No Area'
    text = f"{emoji} *{equipment.name}* ({area_name}) — {status_detail['label']}"

    if status_detail['color'] != 'green':
        if status_detail.get('issue_description'):
            text += f"\n> {status_detail['issue_description']}"
        if status_detail.get('eta'):
            text += f"\n> ETA: {status_detail['eta'].strftime('%b %d, %Y')}"
        if status_detail.get('assignee_name'):
            text += f"\n> Assigned to: {status_detail['assignee_name']}"

    return text


def format_equipment_list(matches, search_term):
    """Format a list of matching equipment for disambiguation.

    Args:
        matches: List of Equipment model instances.
        search_term: Original search string from the user.

    Returns:
        Formatted mrkdwn string.
    """
    lines = [f'Multiple equipment items match "{search_term}":']
    for equip in matches:
        area_name = equip.area.name if equip.area else 'No Area'
        lines.append(f'\u2022 {equip.name} ({area_name})')
    lines.append('\nPlease be more specific. Try `/esb-status [full name]`')
    return '\n'.join(lines)


def build_equipment_options():
    """Build Slack static_select options for non-archived equipment.

    Returns:
        List of option dicts: [{"text": {"type": "plain_text", "text": "Name (Area)"}, "value": "id"}, ...]
    """
    from esb.extensions import db
    from esb.models.equipment import Equipment

    equipment_list = db.session.execute(
        db.select(Equipment)
        .filter(Equipment.is_archived.is_(False))
        .order_by(Equipment.name)
    ).scalars().all()

    options = []
    for e in equipment_list:
        area_name = e.area.name if e.area else 'No Area'
        options.append({
            'text': {'type': 'plain_text', 'text': f'{e.name} ({area_name})'[:75]},
            'value': str(e.id),
        })
    return options


def build_user_options():
    """Build Slack static_select options for active Technician/Staff users.

    Returns:
        List of option dicts.
    """
    from esb.extensions import db
    from esb.models.user import User

    users = db.session.execute(
        db.select(User)
        .filter(User.is_active.is_(True), User.role.in_(['technician', 'staff']))
        .order_by(User.username)
    ).scalars().all()

    return [
        {
            'text': {'type': 'plain_text', 'text': f'{u.username} ({u.role})'[:75]},
            'value': str(u.id),
        }
        for u in users
    ]


def build_problem_report_modal(equipment_options):
    """Build Block Kit modal for member problem reports.

    Args:
        equipment_options: List of equipment option dicts from build_equipment_options().

    Returns:
        Block Kit modal view dict.
    """
    from esb.models.repair_record import REPAIR_SEVERITIES

    return {
        'type': 'modal',
        'callback_id': 'problem_report_submission',
        'title': {'type': 'plain_text', 'text': 'Report a Problem'},
        'submit': {'type': 'plain_text', 'text': 'Submit Report'},
        'close': {'type': 'plain_text', 'text': 'Cancel'},
        'blocks': [
            {
                'type': 'input',
                'block_id': 'equipment_block',
                'element': {
                    'type': 'static_select',
                    'action_id': 'equipment_select',
                    'placeholder': {'type': 'plain_text', 'text': 'Select equipment'},
                    'options': equipment_options,
                },
                'label': {'type': 'plain_text', 'text': 'Equipment'},
            },
            {
                'type': 'input',
                'block_id': 'name_block',
                'element': {
                    'type': 'plain_text_input',
                    'action_id': 'reporter_name',
                    'placeholder': {'type': 'plain_text', 'text': 'Your name'},
                },
                'label': {'type': 'plain_text', 'text': 'Your Name'},
            },
            {
                'type': 'input',
                'block_id': 'description_block',
                'element': {
                    'type': 'plain_text_input',
                    'action_id': 'description',
                    'multiline': True,
                    'placeholder': {'type': 'plain_text', 'text': 'Describe the problem'},
                },
                'label': {'type': 'plain_text', 'text': 'Description'},
            },
            {
                'type': 'input',
                'block_id': 'severity_block',
                'optional': True,
                'element': {
                    'type': 'static_select',
                    'action_id': 'severity',
                    'initial_option': {
                        'text': {'type': 'plain_text', 'text': 'Not Sure'},
                        'value': 'Not Sure',
                    },
                    'options': [
                        {'text': {'type': 'plain_text', 'text': s}, 'value': s}
                        for s in REPAIR_SEVERITIES
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Severity'},
            },
            {
                'type': 'input',
                'block_id': 'safety_risk_block',
                'optional': True,
                'element': {
                    'type': 'checkboxes',
                    'action_id': 'safety_risk',
                    'options': [
                        {
                            'text': {'type': 'plain_text', 'text': 'This is a safety risk'},
                            'value': 'safety_risk',
                        },
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Safety Risk'},
            },
            {
                'type': 'input',
                'block_id': 'consumable_block',
                'optional': True,
                'element': {
                    'type': 'checkboxes',
                    'action_id': 'consumable',
                    'options': [
                        {
                            'text': {'type': 'plain_text', 'text': 'This is a consumable item'},
                            'value': 'consumable',
                        },
                    ],
                },
                'label': {'type': 'plain_text', 'text': 'Consumable'},
            },
        ],
    }


def build_repair_create_modal(equipment_options, user_options):
    """Build Block Kit modal for technician/staff repair record creation.

    Args:
        equipment_options: List of equipment option dicts from build_equipment_options().
        user_options: List of user option dicts from build_user_options().

    Returns:
        Block Kit modal view dict.
    """
    from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES

    blocks = [
        {
            'type': 'input',
            'block_id': 'equipment_block',
            'element': {
                'type': 'static_select',
                'action_id': 'equipment_select',
                'placeholder': {'type': 'plain_text', 'text': 'Select equipment'},
                'options': equipment_options,
            },
            'label': {'type': 'plain_text', 'text': 'Equipment'},
        },
        {
            'type': 'input',
            'block_id': 'description_block',
            'element': {
                'type': 'plain_text_input',
                'action_id': 'description',
                'multiline': True,
                'placeholder': {'type': 'plain_text', 'text': 'Describe the issue'},
            },
            'label': {'type': 'plain_text', 'text': 'Description'},
        },
        {
            'type': 'input',
            'block_id': 'severity_block',
            'optional': True,
            'element': {
                'type': 'static_select',
                'action_id': 'severity',
                'placeholder': {'type': 'plain_text', 'text': 'Select severity'},
                'options': [
                    {'text': {'type': 'plain_text', 'text': s}, 'value': s}
                    for s in REPAIR_SEVERITIES
                ],
            },
            'label': {'type': 'plain_text', 'text': 'Severity'},
        },
    ]

    if user_options:
        blocks.append({
            'type': 'input',
            'block_id': 'assignee_block',
            'optional': True,
            'element': {
                'type': 'static_select',
                'action_id': 'assignee',
                'placeholder': {'type': 'plain_text', 'text': 'Select assignee'},
                'options': user_options,
            },
            'label': {'type': 'plain_text', 'text': 'Assignee'},
        })

    blocks.append({
        'type': 'input',
        'block_id': 'status_block',
        'optional': True,
        'element': {
            'type': 'static_select',
            'action_id': 'status',
            'initial_option': {
                'text': {'type': 'plain_text', 'text': 'New'},
                'value': 'New',
            },
            'options': [
                {'text': {'type': 'plain_text', 'text': s}, 'value': s}
                for s in REPAIR_STATUSES
            ],
        },
        'label': {'type': 'plain_text', 'text': 'Status'},
    })

    return {
        'type': 'modal',
        'callback_id': 'repair_create_submission',
        'title': {'type': 'plain_text', 'text': 'Create Repair Record'},
        'submit': {'type': 'plain_text', 'text': 'Create Record'},
        'close': {'type': 'plain_text', 'text': 'Cancel'},
        'blocks': blocks,
    }


def build_repair_update_modal(repair_record, status_options, severity_options, user_options):
    """Build Block Kit modal for updating an existing repair record.

    Args:
        repair_record: RepairRecord model instance with current values.
        status_options: List of status option dicts (all REPAIR_STATUSES).
        severity_options: List of severity option dicts (all REPAIR_SEVERITIES).
        user_options: List of user option dicts from build_user_options().

    Returns:
        Block Kit modal view dict with pre-populated values and private_metadata.
    """
    blocks = [
        {
            'type': 'input',
            'block_id': 'status_block',
            'element': {
                'type': 'static_select',
                'action_id': 'status',
                'initial_option': {
                    'text': {'type': 'plain_text', 'text': repair_record.status},
                    'value': repair_record.status,
                },
                'options': status_options,
            },
            'label': {'type': 'plain_text', 'text': 'Status'},
        },
        {
            'type': 'input',
            'block_id': 'severity_block',
            'optional': True,
            'element': {
                'type': 'static_select',
                'action_id': 'severity',
                'placeholder': {'type': 'plain_text', 'text': 'Select severity'},
                'options': severity_options,
            },
            'label': {'type': 'plain_text', 'text': 'Severity'},
        },
    ]

    # Set initial severity if present
    if repair_record.severity:
        blocks[1]['element']['initial_option'] = {
            'text': {'type': 'plain_text', 'text': repair_record.severity},
            'value': repair_record.severity,
        }

    # Assignee block (only shown when assignable users exist)
    if user_options:
        assignee_block = {
            'type': 'input',
            'block_id': 'assignee_block',
            'optional': True,
            'element': {
                'type': 'static_select',
                'action_id': 'assignee',
                'placeholder': {'type': 'plain_text', 'text': 'Select assignee'},
                'options': user_options,
            },
            'label': {'type': 'plain_text', 'text': 'Assignee'},
        }

        # Set initial assignee if present
        if repair_record.assignee_id:
            for opt in user_options:
                if opt['value'] == str(repair_record.assignee_id):
                    assignee_block['element']['initial_option'] = opt
                    break

        blocks.append(assignee_block)

    # ETA block
    eta_block = {
        'type': 'input',
        'block_id': 'eta_block',
        'optional': True,
        'element': {
            'type': 'datepicker',
            'action_id': 'eta',
            'placeholder': {'type': 'plain_text', 'text': 'Select a date'},
        },
        'label': {'type': 'plain_text', 'text': 'ETA'},
    }
    if repair_record.eta:
        eta_block['element']['initial_date'] = repair_record.eta.strftime('%Y-%m-%d')
    blocks.append(eta_block)

    # Specialist description block
    specialist_block = {
        'type': 'input',
        'block_id': 'specialist_block',
        'optional': True,
        'element': {
            'type': 'plain_text_input',
            'action_id': 'specialist_description',
            'placeholder': {'type': 'plain_text', 'text': 'Specialist details'},
        },
        'label': {'type': 'plain_text', 'text': 'Specialist Description'},
    }
    if repair_record.specialist_description:
        specialist_block['element']['initial_value'] = repair_record.specialist_description
    blocks.append(specialist_block)

    # Note block (always empty - for adding a new note)
    blocks.append({
        'type': 'input',
        'block_id': 'note_block',
        'optional': True,
        'element': {
            'type': 'plain_text_input',
            'action_id': 'note',
            'multiline': True,
            'placeholder': {'type': 'plain_text', 'text': 'Add a note'},
        },
        'label': {'type': 'plain_text', 'text': 'Note'},
    })

    return {
        'type': 'modal',
        'callback_id': 'repair_update_submission',
        'title': {'type': 'plain_text', 'text': 'Update Repair'},
        'submit': {'type': 'plain_text', 'text': 'Update Record'},
        'close': {'type': 'plain_text', 'text': 'Cancel'},
        'private_metadata': str(repair_record.id),
        'blocks': blocks,
    }
