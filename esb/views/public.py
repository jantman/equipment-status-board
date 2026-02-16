"""Public routes (QR pages, kiosk, status dashboard, problem report).

Note: The status dashboard requires @login_required (FR34 member default view).
Story 4.2 kiosk routes on this blueprint will NOT require login.
"""

from collections import OrderedDict

from flask import Blueprint, abort, current_app, redirect, render_template, request, send_from_directory, url_for
from flask_login import login_required

from esb.models.document import DOCUMENT_CATEGORIES
from esb.utils.exceptions import ValidationError

public_bp = Blueprint('public', __name__, url_prefix='/public')

CATEGORY_DISPLAY_NAMES = dict(DOCUMENT_CATEGORIES)


@public_bp.route('/')
@login_required
def status_dashboard():
    """Status dashboard showing all equipment status by area."""
    if request.args.get('kiosk') == 'true':
        return redirect(url_for('public.kiosk'))
    from esb.services import status_service

    areas = status_service.get_area_status_dashboard()
    return render_template('public/status_dashboard.html', areas=areas)


@public_bp.route('/kiosk')
def kiosk():
    """Kiosk display -- full-screen equipment status for wall-mounted displays."""
    from esb.services import status_service

    areas = status_service.get_area_status_dashboard()
    return render_template('public/kiosk.html', areas=areas)


@public_bp.route('/equipment/<int:id>')
def equipment_page(id):
    """QR code equipment page -- public status, issues, and documentation link."""
    from esb.services import equipment_service, repair_service, status_service
    from esb.services.repair_service import CLOSED_STATUSES

    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)

    if equipment.is_archived:
        abort(404)

    status = status_service.compute_equipment_status(id)

    open_repairs = [
        r for r in repair_service.list_repair_records(equipment_id=id)
        if r.status not in CLOSED_STATUSES
    ]

    eta = None
    if open_repairs:
        for repair in sorted(
            open_repairs,
            key=lambda r: {'Down': 0, 'Degraded': 1, 'Not Sure': 2}.get(r.severity or '', 3),
        ):
            if repair.eta:
                eta = repair.eta
                break

    return render_template(
        'public/equipment_page.html',
        equipment=equipment,
        status=status,
        open_repairs=open_repairs,
        eta=eta,
    )


@public_bp.route('/equipment/<int:id>/info')
def equipment_info(id):
    """Equipment documentation page -- manuals, photos, and links."""
    from esb.services import equipment_service, upload_service

    try:
        equipment = equipment_service.get_equipment(id)
    except ValidationError:
        abort(404)

    if equipment.is_archived:
        abort(404)

    documents = upload_service.get_documents('equipment_doc', id)
    photos = upload_service.get_documents('equipment_photo', id)
    links = equipment_service.get_equipment_links(id)

    documents_by_category = OrderedDict()
    for doc in documents:
        cat_display = CATEGORY_DISPLAY_NAMES.get(doc.category, doc.category or 'Other')
        documents_by_category.setdefault(cat_display, []).append(doc)

    return render_template(
        'public/equipment_info.html',
        equipment=equipment,
        documents=documents,
        photos=photos,
        links=links,
        documents_by_category=documents_by_category,
    )


@public_bp.route('/uploads/<path:filepath>')
def serve_upload(filepath):
    """Serve uploaded files (documents, photos) publicly."""
    if '..' in filepath:
        abort(404)
    upload_path = current_app.config.get('UPLOAD_PATH', 'uploads')
    return send_from_directory(upload_path, filepath)
