"""Tests for upload service."""

import io
import json
import os

from esb.extensions import db as _db
from esb.models.document import Document
from esb.services import upload_service
from esb.utils.exceptions import ValidationError

import pytest


class TestSaveUpload:
    """Tests for save_upload function."""

    def _make_file(self, content=b'fake content', filename='test.pdf',
                   content_type='application/pdf'):
        """Create a fake FileStorage-like object."""
        from werkzeug.datastructures import FileStorage
        return FileStorage(
            stream=io.BytesIO(content),
            filename=filename,
            content_type=content_type,
        )

    def test_save_document_success(self, app, capture, tmp_path):
        """Successfully saves a document and creates a Document record."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file()
        doc = upload_service.save_upload(
            file=f,
            parent_type='equipment_doc',
            parent_id=42,
            uploaded_by='staffuser',
            category='owners_manual',
        )
        assert doc.id is not None
        assert doc.original_filename == 'test.pdf'
        assert doc.category == 'owners_manual'
        assert doc.parent_type == 'equipment_doc'
        assert doc.parent_id == 42
        assert doc.uploaded_by == 'staffuser'
        assert doc.size_bytes == len(b'fake content')
        # Verify file on disk
        subdir = tmp_path / 'equipment' / '42' / 'docs'
        assert subdir.exists()
        files = list(subdir.iterdir())
        assert len(files) == 1
        assert files[0].name == doc.stored_filename
        # Verify mutation log
        assert len(capture.records) == 1
        entry = json.loads(capture.records[0].message)
        assert entry['event'] == 'document.created'
        assert entry['user'] == 'staffuser'

    def test_save_photo_success(self, app, capture, tmp_path):
        """Successfully saves a photo."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file(filename='photo.jpg', content_type='image/jpeg')
        doc = upload_service.save_upload(
            file=f,
            parent_type='equipment_photo',
            parent_id=7,
            uploaded_by='staffuser',
        )
        assert doc.parent_type == 'equipment_photo'
        assert doc.category is None
        subdir = tmp_path / 'equipment' / '7' / 'photos'
        assert subdir.exists()

    def test_empty_file_rejected(self, app, tmp_path):
        """Empty file raises ValidationError."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file(filename='')
        with pytest.raises(ValidationError, match='No file selected'):
            upload_service.save_upload(
                file=f,
                parent_type='equipment_doc',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_none_file_rejected(self, app, tmp_path):
        """None file raises ValidationError."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        with pytest.raises(ValidationError, match='No file selected'):
            upload_service.save_upload(
                file=None,
                parent_type='equipment_doc',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_invalid_extension_rejected(self, app, tmp_path):
        """File with invalid extension raises ValidationError."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file(filename='script.exe')
        with pytest.raises(ValidationError, match='not allowed'):
            upload_service.save_upload(
                file=f,
                parent_type='equipment_doc',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_photo_extension_rejected_for_doc(self, app, tmp_path):
        """Photo extension rejected when parent_type is equipment_doc."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file(filename='image.jpg')
        with pytest.raises(ValidationError, match='not allowed'):
            upload_service.save_upload(
                file=f,
                parent_type='equipment_doc',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_doc_extension_rejected_for_photo(self, app, tmp_path):
        """Document extension rejected when parent_type is equipment_photo."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file(filename='manual.pdf')
        with pytest.raises(ValidationError, match='not allowed'):
            upload_service.save_upload(
                file=f,
                parent_type='equipment_photo',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_oversized_file_rejected(self, app, tmp_path):
        """File exceeding UPLOAD_MAX_SIZE_MB raises ValidationError."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        app.config['UPLOAD_MAX_SIZE_MB'] = 1  # 1 MB
        big_content = b'x' * (1 * 1024 * 1024 + 1)  # Just over 1 MB
        f = self._make_file(content=big_content)
        with pytest.raises(ValidationError, match='exceeds maximum size'):
            upload_service.save_upload(
                file=f,
                parent_type='equipment_doc',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_invalid_parent_type_rejected(self, app, tmp_path):
        """Invalid parent_type raises ValidationError."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file()
        with pytest.raises(ValidationError, match='Invalid parent_type'):
            upload_service.save_upload(
                file=f,
                parent_type='invalid',
                parent_id=1,
                uploaded_by='staffuser',
            )

    def test_stored_filename_is_uuid(self, app, tmp_path):
        """Stored filename uses UUID format."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        f = self._make_file()
        doc = upload_service.save_upload(
            file=f,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        name, ext = os.path.splitext(doc.stored_filename)
        assert len(name) == 32  # UUID hex is 32 chars
        assert ext == '.pdf'

    def test_directory_created_if_not_exists(self, app, tmp_path):
        """Upload directory is created if it doesn't exist."""
        app.config['UPLOAD_PATH'] = str(tmp_path / 'nonexistent')
        f = self._make_file()
        upload_service.save_upload(
            file=f,
            parent_type='equipment_doc',
            parent_id=99,
            uploaded_by='staffuser',
        )
        expected_dir = tmp_path / 'nonexistent' / 'equipment' / '99' / 'docs'
        assert expected_dir.exists()


class TestDeleteUpload:
    """Tests for delete_upload function."""

    def test_delete_success(self, app, capture, tmp_path):
        """Successfully deletes file from disk and removes Document record."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        # Create a document on disk
        doc_dir = tmp_path / 'equipment' / '1' / 'docs'
        doc_dir.mkdir(parents=True)
        file_path = doc_dir / 'stored.pdf'
        file_path.write_bytes(b'content')

        doc = Document(
            original_filename='manual.pdf',
            stored_filename='stored.pdf',
            content_type='application/pdf',
            size_bytes=7,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        _db.session.commit()
        doc_id = doc.id

        upload_service.delete_upload(doc_id, 'staffuser')

        assert _db.session.get(Document, doc_id) is None
        assert not file_path.exists()
        # Verify mutation log
        assert len(capture.records) == 1
        entry = json.loads(capture.records[0].message)
        assert entry['event'] == 'document.deleted'

    def test_delete_not_found(self, app):
        """Deleting non-existent document raises ValidationError."""
        with pytest.raises(ValidationError, match='not found'):
            upload_service.delete_upload(9999, 'staffuser')

    def test_delete_missing_file_still_removes_record(self, app, capture, tmp_path):
        """If file is already missing from disk, record is still deleted."""
        app.config['UPLOAD_PATH'] = str(tmp_path)
        doc = Document(
            original_filename='gone.pdf',
            stored_filename='nonexistent.pdf',
            content_type='application/pdf',
            size_bytes=100,
            parent_type='equipment_doc',
            parent_id=1,
            uploaded_by='staffuser',
        )
        _db.session.add(doc)
        _db.session.commit()
        doc_id = doc.id

        upload_service.delete_upload(doc_id, 'staffuser')
        assert _db.session.get(Document, doc_id) is None


class TestGetDocuments:
    """Tests for get_documents function."""

    def test_returns_filtered_documents(self, app):
        """Returns only documents matching parent_type and parent_id."""
        doc1 = Document(
            original_filename='a.pdf', stored_filename='a.pdf',
            content_type='application/pdf', size_bytes=100,
            parent_type='equipment_doc', parent_id=1, uploaded_by='user',
        )
        doc2 = Document(
            original_filename='b.jpg', stored_filename='b.jpg',
            content_type='image/jpeg', size_bytes=200,
            parent_type='equipment_photo', parent_id=1, uploaded_by='user',
        )
        doc3 = Document(
            original_filename='c.pdf', stored_filename='c.pdf',
            content_type='application/pdf', size_bytes=300,
            parent_type='equipment_doc', parent_id=2, uploaded_by='user',
        )
        _db.session.add_all([doc1, doc2, doc3])
        _db.session.commit()

        result = upload_service.get_documents('equipment_doc', 1)
        assert len(result) == 1
        assert result[0].original_filename == 'a.pdf'

    def test_returns_empty_list_when_none_found(self, app):
        """Returns empty list when no documents match."""
        result = upload_service.get_documents('equipment_doc', 999)
        assert result == []

    def test_ordered_by_created_at_desc(self, app):
        """Documents are returned ordered by created_at descending."""
        from datetime import UTC, datetime

        t1 = datetime(2025, 1, 1, tzinfo=UTC)
        t2 = datetime(2025, 1, 2, tzinfo=UTC)
        doc_old = Document(
            original_filename='old.pdf', stored_filename='old.pdf',
            content_type='application/pdf', size_bytes=100,
            parent_type='equipment_doc', parent_id=1, uploaded_by='user',
            created_at=t1,
        )
        doc_new = Document(
            original_filename='new.pdf', stored_filename='new.pdf',
            content_type='application/pdf', size_bytes=200,
            parent_type='equipment_doc', parent_id=1, uploaded_by='user',
            created_at=t2,
        )
        _db.session.add_all([doc_old, doc_new])
        _db.session.commit()

        result = upload_service.get_documents('equipment_doc', 1)
        assert len(result) == 2
        assert result[0].original_filename == 'new.pdf'
        assert result[1].original_filename == 'old.pdf'
