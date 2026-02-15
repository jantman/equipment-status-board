"""AuditLog model for application-level audit trail."""

from datetime import UTC, datetime

from esb.extensions import db


class AuditLog(db.Model):
    """Application-level audit trail for entity changes."""

    __tablename__ = 'audit_log'

    id = db.Column(db.Integer, primary_key=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True)
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(50), nullable=False)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id'), nullable=True,
    )
    changes = db.Column(db.JSON, nullable=True)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC),
    )

    # Relationships
    user = db.relationship('User', backref=db.backref('audit_logs', lazy='dynamic'))

    def __repr__(self):
        return f'<AuditLog {self.entity_type}:{self.entity_id} [{self.action}]>'
