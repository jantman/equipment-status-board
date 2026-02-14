"""Admin routes (user management, area management, app config)."""

from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


@admin_bp.route('/')
def index():
    """Admin dashboard page (placeholder)."""
    return 'Admin dashboard'
