"""Public routes (QR pages, kiosk, status dashboard, problem report).

Note: The status dashboard requires @login_required (FR34 member default view).
Story 4.2 kiosk routes on this blueprint will NOT require login.
"""

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
