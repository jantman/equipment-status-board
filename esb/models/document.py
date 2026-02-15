"""Document model for uploaded files (documents and photos)."""

from datetime import UTC, datetime

from esb.extensions import db

DOCUMENT_CATEGORIES = [
    ('owners_manual', "Owner's Manual"),
    ('service_manual', 'Service Manual'),
    ('quick_start', 'Quick Start Guide'),
    ('training_video', 'Training Video'),
    ('manufacturer_page', 'Manufacturer Product Page'),
    ('manufacturer_support', 'Manufacturer Support'),
    ('other', 'Other'),
]


class Document(db.Model):
    """File metadata for uploaded documents and photos."""

    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    original_filename = db.Column(db.String(255), nullable=False)
    stored_filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(100), nullable=False)
    size_bytes = db.Column(db.Integer, nullable=False)
    category = db.Column(db.String(50), nullable=True)
    parent_type = db.Column(db.String(50), nullable=False)
    parent_id = db.Column(db.Integer, nullable=False, index=True)
    uploaded_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    __table_args__ = (
        db.Index('ix_documents_parent', 'parent_type', 'parent_id'),
    )

    def __repr__(self):
        return f'<Document {self.original_filename!r}>'
