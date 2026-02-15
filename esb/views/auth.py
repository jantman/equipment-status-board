"""Auth routes (login, logout)."""

from urllib.parse import urlparse

from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user

from esb.forms.auth_forms import ChangePasswordForm, LoginForm
from esb.services import auth_service, user_service
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login page and form handler."""
    if current_user.is_authenticated:
        return redirect(url_for('health'))

    form = LoginForm()
    if form.validate_on_submit():
        try:
            user = auth_service.authenticate(form.username.data, form.password.data)
        except ValidationError:
            log_mutation('user.login_failed', 'anonymous', {
                'username': form.username.data,
            })
            flash('Invalid username or password', 'danger')
            return render_template('auth/login.html', form=form)

        login_user(user, remember=False)
        session.permanent = True
        log_mutation('user.login', user.username, {
            'user_id': user.id,
            'username': user.username,
        })
        next_page = request.args.get('next')
        if next_page and urlparse(next_page).netloc == '':
            return redirect(next_page)
        if user.role == 'technician':
            return redirect(url_for('repairs.queue'))
        return redirect(url_for('health'))

    return render_template('auth/login.html', form=form)


@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password form and handler."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        try:
            user_service.change_password(
                current_user.id,
                form.current_password.data,
                form.new_password.data,
            )
        except ValidationError as e:
            flash(str(e), 'danger')
            return render_template('auth/change_password.html', form=form)

        flash('Your password has been changed.', 'success')
        return redirect(url_for('auth.change_password'))

    return render_template('auth/change_password.html', form=form)


@auth_bp.route('/logout')
@login_required
def logout():
    """Log the user out and redirect to login."""
    log_mutation('user.logout', current_user.username, {
        'user_id': current_user.id,
        'username': current_user.username,
    })
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('auth.login'))
