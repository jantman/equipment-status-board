"""Tests for QR code generation service."""

import os

import pytest

from esb.services import qr_service


class TestGenerateQrCode:
    """Tests for generate_qr_code()."""

    def test_raises_for_nonexistent_equipment(self, app):
        """Raises ValueError when equipment_id does not exist."""
        with pytest.raises(ValueError, match='not found'):
            qr_service.generate_qr_code(99999, 'http://192.168.1.50:5000')

    def test_creates_png_file(self, app, make_area, make_equipment):
        """QR code generation creates a PNG file at the correct path."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Lathe', area=area)

        result = qr_service.generate_qr_code(equip.id, 'http://192.168.1.50:5000')

        assert result == f'qrcodes/{equip.id}.png'
        filepath = os.path.join(app.static_folder, 'qrcodes', f'{equip.id}.png')
        assert os.path.isfile(filepath)

    def test_qr_code_is_valid_png(self, app, make_area, make_equipment):
        """QR code file is a valid PNG image."""
        from PIL import Image

        area = make_area(name='Shop')
        equip = make_equipment(name='Drill', area=area)

        qr_service.generate_qr_code(equip.id, 'http://192.168.1.50:5000')
        filepath = os.path.join(app.static_folder, 'qrcodes', f'{equip.id}.png')

        img = Image.open(filepath)
        assert img.format == 'PNG'

    def test_overwrites_existing_qr_code(self, app, make_area, make_equipment):
        """Generating a QR code for an existing equipment overwrites the file."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Mill', area=area)

        qr_service.generate_qr_code(equip.id, 'http://old-url:5000')
        qr_service.generate_qr_code(equip.id, 'http://new-url:5000')

        filepath = os.path.join(app.static_folder, 'qrcodes', f'{equip.id}.png')
        assert os.path.isfile(filepath)


class TestGetQrCodePath:
    """Tests for get_qr_code_path()."""

    def test_returns_path_for_existing_qr_code(self, app, make_area, make_equipment):
        """Returns relative path when QR code exists."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Lathe', area=area)

        qr_service.generate_qr_code(equip.id, 'http://192.168.1.50:5000')
        result = qr_service.get_qr_code_path(equip.id)

        assert result == f'qrcodes/{equip.id}.png'

    def test_returns_none_for_missing_qr_code(self, app):
        """Returns None when no QR code exists for the equipment ID."""
        result = qr_service.get_qr_code_path(99999)
        assert result is None


class TestGenerateAllQrCodes:
    """Tests for generate_all_qr_codes()."""

    def test_generates_for_all_non_archived(self, app, make_area, make_equipment):
        """Generates QR codes for all non-archived equipment."""
        area = make_area(name='Shop')
        e1 = make_equipment(name='Lathe', area=area)
        e2 = make_equipment(name='Mill', area=area)
        e3 = make_equipment(name='Drill', area=area)

        count = qr_service.generate_all_qr_codes('http://192.168.1.50:5000')

        assert count == 3
        for equip in [e1, e2, e3]:
            filepath = os.path.join(app.static_folder, 'qrcodes', f'{equip.id}.png')
            assert os.path.isfile(filepath)

    def test_skips_archived_equipment(self, app, make_area, make_equipment):
        """Archived equipment does not get QR codes generated."""
        area = make_area(name='Shop')
        make_equipment(name='Active Tool', area=area)
        make_equipment(name='Retired Tool', area=area, is_archived=True)

        count = qr_service.generate_all_qr_codes('http://192.168.1.50:5000')

        assert count == 1

    def test_returns_zero_for_no_equipment(self, app):
        """Returns 0 when no equipment exists."""
        count = qr_service.generate_all_qr_codes('http://192.168.1.50:5000')
        assert count == 0
