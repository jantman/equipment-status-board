"""Upload service for file storage and Document record management.

Handles all file I/O for uploads. Views never touch the filesystem directly.
"""

import os
import uuid

from flask import current_app
from werkzeug.utils import secure_filename

from esb.extensions import db
from esb.models.document import Document
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation

ALLOWED_DOC_EXTENSIONS = {
    'pdf', 'doc', 'docx', 'txt', 'rtf', 'odt', 'xls', 'xlsx', 'csv', 'ppt', 'pptx',
}
ALLOWED_PHOTO_EXTENSIONS = {
    'jpg', 'jpeg', 'png', 'gif', 'webp', 'mp4', 'mov', 'avi', 'webm',
}

_PARENT_TYPE_CONFIG = {
    'equipment_doc': {
        'allowed_extensions': ALLOWED_DOC_EXTENSIONS,
        'subdir': 'equipment/{parent_id}/docs',
    },
    'equipment_photo': {
        'allowed_extensions': ALLOWED_PHOTO_EXTENSIONS,
        'subdir': 'equipment/{parent_id}/photos',
    },
    'repair_photo': {
        'allowed_extensions': ALLOWED_PHOTO_EXTENSIONS,
        'subdir': 'repairs/{parent_id}',
    },
}


def save_upload(
    file,
    parent_type: str,
    parent_id: int,
    uploaded_by: str,
    category: str | None = None,
) -> Document:
    """Save an uploaded file to disk and create a Document record.

    Args:
        file: Werkzeug FileStorage object from the form.
        parent_type: 'equipment_doc', 'equipment_photo', or 'repair_photo'.
        parent_id: ID of the parent entity.
        uploaded_by: Username of the uploader.
        category: Document category (for equipment_doc only).

    Raises:
        ValidationError: if file is empty, has invalid extension, or exceeds size limit.

    Returns:
        The created Document instance.
    """
    if not file or not file.filename:
        raise ValidationError('No file selected.')

    if parent_type not in _PARENT_TYPE_CONFIG:
        raise ValidationError(f'Invalid parent_type: {parent_type}')

    config = _PARENT_TYPE_CONFIG[parent_type]
    original_filename = secure_filename(file.filename)
    if not original_filename:
        raise ValidationError('Invalid filename.')

    ext = os.path.splitext(original_filename)[1].lower().lstrip('.')
    if ext not in config['allowed_extensions']:
        raise ValidationError(
            f'File type .{ext} is not allowed. '
            f'Allowed types: {", ".join(sorted(config["allowed_extensions"]))}'
        )

    content = file.read()
    max_bytes = current_app.config['UPLOAD_MAX_SIZE_MB'] * 1024 * 1024
    if len(content) > max_bytes:
        raise ValidationError(
            f'File exceeds maximum size of {current_app.config["UPLOAD_MAX_SIZE_MB"]} MB.'
        )

    stored_filename = f'{uuid.uuid4().hex}{os.path.splitext(original_filename)[1].lower()}'
    subdir = config['subdir'].format(parent_id=parent_id)
    upload_dir = os.path.join(current_app.config['UPLOAD_PATH'], subdir)
    os.makedirs(upload_dir, exist_ok=True)

    file_path = os.path.join(upload_dir, stored_filename)
    with open(file_path, 'wb') as f:
        f.write(content)

    content_type = file.content_type or 'application/octet-stream'

    doc = Document(
        original_filename=original_filename,
        stored_filename=stored_filename,
        content_type=content_type,
        size_bytes=len(content),
        category=category,
        parent_type=parent_type,
        parent_id=parent_id,
        uploaded_by=uploaded_by,
    )
    db.session.add(doc)
    db.session.commit()

    log_mutation('document.created', uploaded_by, {
        'id': doc.id,
        'original_filename': doc.original_filename,
        'category': doc.category,
        'parent_type': doc.parent_type,
        'parent_id': doc.parent_id,
    })

    return doc


def delete_upload(
    document_id: int,
    deleted_by: str,
    *,
    parent_type: str | None = None,
    parent_id: int | None = None,
) -> None:
    """Delete an uploaded file from disk and remove the Document record.

    Args:
        document_id: ID of the Document to delete.
        deleted_by: Username performing the deletion.
        parent_type: If provided, verify document belongs to this parent_type.
        parent_id: If provided, verify document belongs to this parent_id.

    Raises:
        ValidationError: if document not found or ownership mismatch.
    """
    doc = db.session.get(Document, document_id)
    if doc is None:
        raise ValidationError(f'Document with id {document_id} not found')
    if parent_type is not None and doc.parent_type != parent_type:
        raise ValidationError(f'Document with id {document_id} not found')
    if parent_id is not None and doc.parent_id != parent_id:
        raise ValidationError(f'Document with id {document_id} not found')

    config = _PARENT_TYPE_CONFIG.get(doc.parent_type)
    if config:
        subdir = config['subdir'].format(parent_id=doc.parent_id)
        file_path = os.path.join(
            current_app.config['UPLOAD_PATH'], subdir, doc.stored_filename
        )
        if os.path.exists(file_path):
            os.remove(file_path)

    log_data = {
        'id': doc.id,
        'original_filename': doc.original_filename,
        'parent_type': doc.parent_type,
        'parent_id': doc.parent_id,
    }

    db.session.delete(doc)
    db.session.commit()

    log_mutation('document.deleted', deleted_by, log_data)


def get_documents(parent_type: str, parent_id: int) -> list[Document]:
    """Get all documents for a parent entity, ordered by created_at desc."""
    return list(
        db.session.execute(
            db.select(Document)
            .filter_by(parent_type=parent_type, parent_id=parent_id)
            .order_by(Document.created_at.desc())
        ).scalars().all()
    )
