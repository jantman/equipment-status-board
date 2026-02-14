"""Equipment registry routes."""

from flask import Blueprint

equipment_bp = Blueprint('equipment', __name__, url_prefix='/equipment')


@equipment_bp.route('/')
def index():
    """Equipment list page (placeholder)."""
    return 'Equipment list'
