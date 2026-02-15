"""Tests for Equipment model."""

import pytest
from sqlalchemy.exc import IntegrityError

from esb.extensions import db as _db
from esb.models.equipment import Equipment


class TestEquipmentCreation:
    """Tests for Equipment model creation and fields."""

    def test_create_equipment_with_required_fields(self, app, make_area):
        """Equipment created with required fields has correct values."""
        area = make_area()
        eq = Equipment(
            name='3D Printer',
            manufacturer='Prusa',
            model='MK4',
            area_id=area.id,
        )
        _db.session.add(eq)
        _db.session.commit()
        assert eq.id is not None
        assert eq.name == '3D Printer'
        assert eq.manufacturer == 'Prusa'
        assert eq.model == 'MK4'
        assert eq.area_id == area.id
        assert eq.is_archived is False

    def test_optional_fields_default_to_none(self, app, make_area):
        """Optional fields default to None when not provided."""
        area = make_area()
        eq = Equipment(
            name='Laser',
            manufacturer='Epilog',
            model='Zing',
            area_id=area.id,
        )
        _db.session.add(eq)
        _db.session.commit()
        assert eq.serial_number is None
        assert eq.acquisition_date is None
        assert eq.acquisition_source is None
        assert eq.acquisition_cost is None
        assert eq.warranty_expiration is None
        assert eq.description is None

    def test_optional_fields_stored(self, app, make_area):
        """Optional fields are stored when provided."""
        from datetime import date
        from decimal import Decimal

        area = make_area()
        eq = Equipment(
            name='CNC Router',
            manufacturer='ShopBot',
            model='Desktop',
            area_id=area.id,
            serial_number='SN-12345',
            acquisition_date=date(2024, 6, 15),
            acquisition_source='Direct purchase',
            acquisition_cost=Decimal('4999.99'),
            warranty_expiration=date(2026, 6, 15),
            description='Desktop CNC router for woodworking',
        )
        _db.session.add(eq)
        _db.session.commit()
        assert eq.serial_number == 'SN-12345'
        assert eq.acquisition_date == date(2024, 6, 15)
        assert eq.acquisition_source == 'Direct purchase'
        assert eq.acquisition_cost == Decimal('4999.99')
        assert eq.warranty_expiration == date(2026, 6, 15)
        assert eq.description == 'Desktop CNC router for woodworking'

    def test_timestamps_set_on_create(self, app, make_area):
        """created_at and updated_at are set automatically."""
        area = make_area()
        eq = Equipment(
            name='Drill Press',
            manufacturer='JET',
            model='JDP-17',
            area_id=area.id,
        )
        _db.session.add(eq)
        _db.session.commit()
        assert eq.created_at is not None
        assert eq.updated_at is not None

    def test_repr(self, app, make_area):
        """Equipment __repr__ includes name."""
        eq = Equipment(name='Band Saw', manufacturer='X', model='Y', area_id=1)
        assert repr(eq) == "<Equipment 'Band Saw'>"


class TestEquipmentConstraints:
    """Tests for Equipment model constraints."""

    def test_area_id_required(self, app):
        """area_id column rejects NULL."""
        eq = Equipment(name='Orphan', manufacturer='X', model='Y')
        _db.session.add(eq)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_name_not_nullable(self, app, make_area):
        """name column rejects NULL."""
        area = make_area()
        eq = Equipment(manufacturer='X', model='Y', area_id=area.id)
        _db.session.add(eq)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_duplicate_names_allowed(self, app, make_area):
        """Multiple equipment can have the same name."""
        area = make_area()
        eq1 = Equipment(name='3D Printer', manufacturer='Prusa', model='MK4', area_id=area.id)
        eq2 = Equipment(name='3D Printer', manufacturer='Creality', model='Ender 3', area_id=area.id)
        _db.session.add_all([eq1, eq2])
        _db.session.commit()
        assert eq1.id != eq2.id

    def test_area_relationship(self, app, make_area):
        """Equipment.area relationship returns the associated Area."""
        area = make_area(name='Woodshop')
        eq = Equipment(name='Table Saw', manufacturer='SawStop', model='PCS', area_id=area.id)
        _db.session.add(eq)
        _db.session.commit()
        assert eq.area.name == 'Woodshop'
