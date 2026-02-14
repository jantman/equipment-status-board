"""Admin routes (user management, area management, app config)."""

from flask import Blueprint, flash, redirect, render_template, session, url_for
from flask_login import current_user

from esb.forms.admin_forms import RoleChangeForm, UserCreateForm
from esb.services import user_service
from esb.utils.decorators import role_required
from esb.utils.exceptions import ValidationError

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
@role_required('staff')
def index():
    """Admin dashboard -- redirects to user list."""
    return redirect(url_for('admin.list_users'))


@admin_bp.route('/users')
@role_required('staff')
def list_users():
    """User management table listing all users."""
    users = user_service.list_users()
    role_form = RoleChangeForm()
    return render_template('admin/users.html', users=users, role_form=role_form)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@role_required('staff')
def create_user():
    """User creation form and handler."""
    form = UserCreateForm()
    if form.validate_on_submit():
        try:
            user, temp_password, slack_delivered = user_service.create_user(
                username=form.username.data,
                email=form.email.data,
                role=form.role.data,
                slack_handle=form.slack_handle.data or None,
                created_by=current_user.username,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('admin/user_create.html', form=form)

        if slack_delivered:
            flash('User created. Temporary password sent via Slack DM.', 'success')
            return redirect(url_for('admin.list_users'))

        # Store temp password in session for one-time display
        session['_temp_password'] = temp_password
        return redirect(url_for('admin.user_created', id=user.id))

    return render_template('admin/user_create.html', form=form)


@admin_bp.route('/users/<int:id>/created')
@role_required('staff')
def user_created(id):
    """One-time temp password display page."""
    temp_password = session.pop('_temp_password', None)
    if temp_password is None:
        flash('Temporary password is no longer available.', 'warning')
        return redirect(url_for('admin.list_users'))

    user = user_service.get_user(id)
    return render_template(
        'admin/user_created.html',
        user=user,
        temp_password=temp_password,
    )


@admin_bp.route('/users/<int:id>/role', methods=['POST'])
@role_required('staff')
def change_role(id):
    """Change a user's role."""
    form = RoleChangeForm()
    if form.validate_on_submit():
        try:
            user_service.change_role(
                user_id=id,
                new_role=form.role.data,
                changed_by=current_user.username,
            )
            flash('User role updated successfully.', 'success')
        except ValidationError as e:
            flash(str(e), 'danger')
    return redirect(url_for('admin.list_users'))
