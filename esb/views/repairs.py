"""Repair record routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user

from esb.forms.repair_forms import RepairRecordCreateForm, RepairRecordUpdateForm
from esb.models.repair_record import REPAIR_STATUSES
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.services import equipment_service, repair_service
from esb.utils.decorators import role_required
from esb.utils.exceptions import ValidationError

repairs_bp = Blueprint('repairs', __name__, url_prefix='/repairs')


@repairs_bp.route('/')
@role_required('technician')
def index():
    """Repair records list page (placeholder - redirects to create)."""
    return redirect(url_for('repairs.create'))


@repairs_bp.route('/new', methods=['GET', 'POST'])
@role_required('technician')
def create():
    """Create a new repair record."""
    form = RepairRecordCreateForm()

    # Populate equipment choices (active only)
    equipment_list = equipment_service.list_equipment()
    form.equipment_id.choices = [(0, '-- Select Equipment --')] + [
        (e.id, f'{e.name} ({e.area.name})') for e in equipment_list
    ]

    # Populate assignee choices (all active users who are tech or staff)
    from esb.services import user_service
    users = user_service.list_users()
    form.assignee_id.choices = [(0, '-- Unassigned --')] + [
        (u.id, u.username) for u in users
    ]

    # Support pre-selected equipment from query param
    preselected_equipment_id = request.args.get('equipment_id', type=int)
    if request.method == 'GET' and preselected_equipment_id:
        form.equipment_id.data = preselected_equipment_id

    if form.validate_on_submit():
        if form.equipment_id.data == 0:
            flash('Please select an equipment item.', 'danger')
            return render_template('repairs/create.html', form=form)

        try:
            record = repair_service.create_repair_record(
                equipment_id=form.equipment_id.data,
                description=form.description.data,
                created_by=current_user.username,
                severity=form.severity.data or None,
                assignee_id=form.assignee_id.data if form.assignee_id.data != 0 else None,
                has_safety_risk=form.has_safety_risk.data,
                is_consumable=form.is_consumable.data,
                author_id=current_user.id,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('repairs/create.html', form=form)

        flash('Repair record created successfully.', 'success')
        return redirect(url_for('repairs.detail', id=record.id))

    return render_template('repairs/create.html', form=form)


@repairs_bp.route('/<int:id>')
@role_required('technician')
def detail(id):
    """Repair record detail page with timeline."""
    try:
        record = repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    timeline = record.timeline_entries.order_by(
        RepairTimelineEntry.created_at.desc()
    ).all()

    return render_template(
        'repairs/detail.html',
        record=record,
        timeline=timeline,
    )


@repairs_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@role_required('technician')
def edit(id):
    """Edit a repair record."""
    try:
        record = repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairRecordUpdateForm(obj=record)

    # Populate dynamic choices
    form.status.choices = [(s, s) for s in REPAIR_STATUSES]

    from esb.services import user_service
    users = user_service.list_users()
    form.assignee_id.choices = [(0, '-- Unassigned --')] + [
        (u.id, u.username) for u in users
    ]

    if request.method == 'GET':
        form.status.data = record.status
        form.severity.data = record.severity or ''
        form.assignee_id.data = record.assignee_id or 0
        form.eta.data = record.eta
        form.specialist_description.data = record.specialist_description or ''
        form.note.data = ''

    if form.validate_on_submit():
        try:
            repair_service.update_repair_record(
                repair_record_id=id,
                updated_by=current_user.username,
                author_id=current_user.id,
                status=form.status.data,
                severity=form.severity.data or None,
                assignee_id=form.assignee_id.data if form.assignee_id.data != 0 else None,
                eta=form.eta.data,
                specialist_description=form.specialist_description.data or None,
                note=form.note.data or None,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('repairs/edit.html', form=form, record=record)

        flash('Repair record updated successfully.', 'success')
        return redirect(url_for('repairs.detail', id=id))

    return render_template('repairs/edit.html', form=form, record=record)
