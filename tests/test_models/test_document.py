"""Tests for Document model."""

import pytest
from sqlalchemy.exc import IntegrityError

from esb.extensions import db as _db
from esb.models.document import DOCUMENT_CATEGORIES, Document


class TestDocumentCreation:
    """Tests for Document model creation and fields."""

    def test_create_document_with_all_fields(self, app):
        """Document created with all fields has correct values."""
        doc = Document(
            original_filename='manual.pdf',
            stored_filename='abc123.pdf',
            content_type='application/pdf',
            size_bytes=1024,
            category='owners_manual',
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        _db.session.commit()
        assert doc.id is not None
        assert doc.original_filename == 'manual.pdf'
        assert doc.stored_filename == 'abc123.pdf'
        assert doc.content_type == 'application/pdf'
        assert doc.size_bytes == 1024
        assert doc.category == 'owners_manual'
        assert doc.parent_type == 'equipment_doc'
        assert doc.parent_id == 1
        assert doc.uploaded_by == 'staffuser'

    def test_created_at_set_automatically(self, app):
        """created_at is set automatically on creation."""
        doc = Document(
            original_filename='test.pdf',
            stored_filename='def456.pdf',
            content_type='application/pdf',
            size_bytes=512,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        _db.session.commit()
        assert doc.created_at is not None

    def test_category_nullable_for_photos(self, app):
        """category can be NULL for photo uploads."""
        doc = Document(
            original_filename='photo.jpg',
            stored_filename='ghi789.jpg',
            content_type='image/jpeg',
            size_bytes=2048,
            category=None,
            parent_type='equipment_photo',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        _db.session.commit()
        assert doc.category is None

    def test_parent_type_values(self, app):
        """Document supports different parent_type values."""
        for parent_type in ('equipment_doc', 'equipment_photo', 'repair_photo'):
            doc = Document(
                original_filename='test.pdf',
                stored_filename=f'{parent_type}.pdf',
                content_type='application/pdf',
                size_bytes=100,
                parent_type=parent_type,
                parent_id=1,
                uploaded_by='staffuser',
            )
            _db.session.add(doc)
        _db.session.commit()

    def test_repr(self, app):
        """Document __repr__ includes original_filename."""
        doc = Document(
            original_filename='manual.pdf',
            stored_filename='x.pdf',
            content_type='application/pdf',
            size_bytes=100,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        assert repr(doc) == "<Document 'manual.pdf'>"


class TestDocumentConstraints:
    """Tests for Document model constraints."""

    def test_original_filename_not_nullable(self, app):
        """original_filename column rejects NULL."""
        doc = Document(
            stored_filename='x.pdf',
            content_type='application/pdf',
            size_bytes=100,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_parent_type_not_nullable(self, app):
        """parent_type column rejects NULL."""
        doc = Document(
            original_filename='test.pdf',
            stored_filename='x.pdf',
            content_type='application/pdf',
            size_bytes=100,
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()

    def test_uploaded_by_not_nullable(self, app):
        """uploaded_by column rejects NULL."""
        doc = Document(
            original_filename='test.pdf',
            stored_filename='x.pdf',
            content_type='application/pdf',
            size_bytes=100,
            parent_type='equipment_doc',
            parent_id=1,
        )
        _db.session.add(doc)
        with pytest.raises(IntegrityError):
            _db.session.commit()
        _db.session.rollback()


class TestDocumentCategories:
    """Tests for DOCUMENT_CATEGORIES constant."""

    def test_categories_is_list_of_tuples(self):
        """DOCUMENT_CATEGORIES is a list of (value, label) tuples."""
        assert isinstance(DOCUMENT_CATEGORIES, list)
        for item in DOCUMENT_CATEGORIES:
            assert isinstance(item, tuple)
            assert len(item) == 2

    def test_expected_categories_present(self):
        """All expected category values are present."""
        values = [v for v, _ in DOCUMENT_CATEGORIES]
        assert 'owners_manual' in values
        assert 'service_manual' in values
        assert 'quick_start' in values
        assert 'training_video' in values
        assert 'manufacturer_page' in values
        assert 'manufacturer_support' in values
        assert 'other' in values
