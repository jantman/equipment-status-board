"""Public routes (QR pages, kiosk, status dashboard, problem report)."""

from flask import Blueprint, render_template
from flask_login import login_required

public_bp = Blueprint('public', __name__, url_prefix='/public')


@public_bp.route('/')
@login_required
def status_dashboard():
    """Status dashboard showing all equipment status by area."""
    from esb.services import status_service

    areas = status_service.get_area_status_dashboard()
    return render_template('public/status_dashboard.html', areas=areas)
