"""Auth routes (login, logout, change password)."""

from flask import Blueprint

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    """Login page (placeholder)."""
    return 'Login'


@auth_bp.route('/logout')
def logout():
    """Logout (placeholder)."""
    return 'Logged out'
