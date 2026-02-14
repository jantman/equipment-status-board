"""Repair record routes."""

from flask import Blueprint

repairs_bp = Blueprint('repairs', __name__, url_prefix='/repairs')


@repairs_bp.route('/')
def index():
    """Repair records list page (placeholder)."""
    return 'Repair records'
