"""Public routes (QR pages, kiosk, status dashboard, problem report)."""

from flask import Blueprint

public_bp = Blueprint('public', __name__, url_prefix='/public')


@public_bp.route('/')
def index():
    """Public status page (placeholder)."""
    return 'Public status'
