"""Repair record routes."""

import os
from datetime import UTC, datetime

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, send_from_directory, url_for
from flask_login import current_user

from esb.forms.repair_forms import RepairNoteForm, RepairPhotoUploadForm, RepairRecordCreateForm, RepairRecordUpdateForm
from esb.models.repair_record import REPAIR_STATUSES
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.services import equipment_service, repair_service, upload_service
from esb.services.repair_service import CLOSED_STATUSES
from esb.utils.decorators import role_required
from esb.utils.exceptions import ValidationError

repairs_bp = Blueprint('repairs', __name__, url_prefix='/repairs')


@repairs_bp.route('/')
@role_required('technician')
def index():
    """Repair records list page - redirects to queue."""
    return redirect(url_for('repairs.queue'))


@repairs_bp.route('/queue')
@role_required('technician')
def queue():
    """Technician repair queue page."""
    area_id = request.args.get('area', type=int)
    status_filter = request.args.get('status')

    areas = equipment_service.list_areas()
    open_statuses = [s for s in REPAIR_STATUSES if s not in CLOSED_STATUSES]
    records = repair_service.get_repair_queue(area_id=area_id, status=status_filter)

    return render_template(
        'repairs/queue.html',
        records=records,
        areas=areas,
        statuses=open_statuses,
        active_area=area_id,
        active_status=status_filter,
        # Strip tzinfo: db.DateTime stores naive datetimes so subtraction must match
        now_utc=datetime.now(UTC).replace(tzinfo=None),
    )


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

    note_form = RepairNoteForm()
    photo_form = RepairPhotoUploadForm()
    photos = upload_service.get_documents('repair_photo', id)
    photos_by_id = {str(p.id): p for p in photos}

    return render_template(
        'repairs/detail.html',
        record=record,
        timeline=timeline,
        note_form=note_form,
        photo_form=photo_form,
        photos=photos,
        photos_by_id=photos_by_id,
    )


@repairs_bp.route('/<int:id>/notes', methods=['POST'])
@role_required('technician')
def add_note(id):
    """Add a note to a repair record."""
    try:
        repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairNoteForm()
    if form.validate_on_submit():
        try:
            repair_service.add_repair_note(
                repair_record_id=id,
                note=form.note.data,
                author_name=current_user.username,
                author_id=current_user.id,
            )
            flash('Note added.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    return redirect(url_for('repairs.detail', id=id))


@repairs_bp.route('/<int:id>/photos', methods=['POST'])
@role_required('technician')
def upload_photo(id):
    """Upload a diagnostic photo to a repair record."""
    try:
        repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)

    form = RepairPhotoUploadForm()
    if form.validate_on_submit():
        try:
            repair_service.add_repair_photo(
                repair_record_id=id,
                file=form.file.data,
                author_name=current_user.username,
                author_id=current_user.id,
            )
            flash('Photo uploaded.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    else:
        for field, errors in form.errors.items():
            for error in errors:
                flash(error, 'danger')
    return redirect(url_for('repairs.detail', id=id))


@repairs_bp.route('/<int:id>/files/<path:filename>')
@role_required('technician')
def serve_photo(id, filename):
    """Serve an uploaded repair photo file."""
    try:
        repair_service.get_repair_record(id)
    except ValidationError:
        abort(404)
    upload_path = current_app.config['UPLOAD_PATH']
    directory = os.path.join(upload_path, 'repairs', str(id))
    return send_from_directory(directory, filename)


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
