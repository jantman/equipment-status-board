"""Equipment registry routes."""

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from esb.forms.equipment_forms import EquipmentCreateForm, EquipmentEditForm
from esb.services import equipment_service
from esb.utils.decorators import role_required
from esb.utils.exceptions import ValidationError

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@equipment_bp.route('/')
@login_required
def index():
    """Equipment registry list with optional area filter."""
    area_id = request.args.get('area_id', type=int)
    equipment = equipment_service.list_equipment(area_id=area_id)
    areas = equipment_service.list_areas()
    return render_template(
        'equipment/list.html',
        equipment=equipment,
        areas=areas,
        selected_area_id=area_id,
    )


@equipment_bp.route('/new', methods=['GET', 'POST'])
@role_required('staff')
def create():
    """Equipment creation form and handler."""
    form = EquipmentCreateForm()
    areas = equipment_service.list_areas()
    form.area_id.choices = [(0, '-- Select Area --')] + [
        (a.id, a.name) for a in areas
    ]

    if form.validate_on_submit():
        if form.area_id.data == 0:
            flash('Please select an area.', 'danger')
            return render_template(
                'equipment/form.html', form=form, title='Add Equipment',
            )
        try:
            eq = equipment_service.create_equipment(
                name=form.name.data,
                manufacturer=form.manufacturer.data,
                model=form.model.data,
                area_id=form.area_id.data,
                created_by=current_user.username,
                serial_number=form.serial_number.data or None,
                acquisition_date=form.acquisition_date.data,
                acquisition_source=form.acquisition_source.data or None,
                acquisition_cost=form.acquisition_cost.data,
                warranty_expiration=form.warranty_expiration.data,
                description=form.description.data or None,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template(
                'equipment/form.html', form=form, title='Add Equipment',
            )

        flash('Equipment created successfully.', 'success')
        return redirect(url_for('equipment.detail', id=eq.id))

    return render_template(
        'equipment/form.html', form=form, title='Add Equipment',
    )


@equipment_bp.route('/<int:id>')
@login_required
def detail(id):
    """Equipment detail page."""
    try:
        eq = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)

    return render_template('equipment/detail.html', equipment=eq)


@equipment_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@role_required('staff')
def edit(id):
    """Equipment edit form and handler."""
    try:
        eq = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)

    form = EquipmentEditForm(obj=eq)
    areas = equipment_service.list_areas()
    form.area_id.choices = [(0, '-- Select Area --')] + [
        (a.id, a.name) for a in areas
    ]

    if form.validate_on_submit():
        if form.area_id.data == 0:
            flash('Please select an area.', 'danger')
            return render_template(
                'equipment/form.html', form=form, title='Edit Equipment',
            )
        try:
            equipment_service.update_equipment(
                equipment_id=id,
                updated_by=current_user.username,
                name=form.name.data,
                manufacturer=form.manufacturer.data,
                model=form.model.data,
                area_id=form.area_id.data,
                serial_number=form.serial_number.data or None,
                acquisition_date=form.acquisition_date.data,
                acquisition_source=form.acquisition_source.data or None,
                acquisition_cost=form.acquisition_cost.data,
                warranty_expiration=form.warranty_expiration.data,
                description=form.description.data or None,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template(
                'equipment/form.html', form=form, title='Edit Equipment',
            )

        flash('Equipment updated successfully.', 'success')
        return redirect(url_for('equipment.detail', id=id))

    return render_template(
        'equipment/form.html', form=form, title='Edit Equipment',
    )
