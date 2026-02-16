"""QR code generation service for equipment pages."""

import os

import qrcode
from flask import current_app

from esb.extensions import db
from esb.models.equipment import Equipment


def generate_qr_code(equipment_id: int, base_url: str) -> str:
    """Generate a QR code PNG for an equipment item.

    Args:
        equipment_id: The equipment ID to generate QR for.
        base_url: The base URL of the application (e.g., 'http://192.168.1.50:5000').

    Returns:
        Relative path to the generated QR code image (e.g., 'qrcodes/42.png').

    Raises:
        ValueError: if equipment_id does not exist in the database.
    """
    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        raise ValueError(f'Equipment with id {equipment_id} not found')

    url = f"{base_url}/public/equipment/{equipment_id}"
    qr = qrcode.make(url)

    qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
    os.makedirs(qr_dir, exist_ok=True)

    filename = f"{equipment_id}.png"
    filepath = os.path.join(qr_dir, filename)
    qr.save(filepath)

    return f"qrcodes/{filename}"


def get_qr_code_path(equipment_id: int) -> str | None:
    """Return the relative path to an equipment's QR code if it exists.

    Returns:
        Relative path string (e.g., 'qrcodes/42.png') or None if not found.
    """
    qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
    filepath = os.path.join(qr_dir, f"{equipment_id}.png")
    if os.path.isfile(filepath):
        return f"qrcodes/{equipment_id}.png"
    return None


def generate_all_qr_codes(base_url: str) -> int:
    """Generate QR codes for all non-archived equipment.

    Args:
        base_url: The base URL of the application.

    Returns:
        Number of QR codes generated.
    """
    equipment_list = db.session.execute(
        db.select(Equipment).filter_by(is_archived=False)
    ).scalars().all()

    for equip in equipment_list:
        generate_qr_code(equip.id, base_url)

    return len(equipment_list)
