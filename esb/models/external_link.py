"""ExternalLink model for links attached to equipment records."""

from datetime import UTC, datetime

from esb.extensions import db


class ExternalLink(db.Model):
    """External link attached to an equipment record."""

    __tablename__ = 'external_links'

    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(
        db.Integer, db.ForeignKey('equipment.id'), nullable=False, index=True
    )
    title = db.Column(db.String(200), nullable=False)
    url = db.Column(db.String(2000), nullable=False)
    created_by = db.Column(db.String(150), nullable=False)
    created_at = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )

    equipment = db.relationship(
        'Equipment', backref=db.backref('links', lazy='dynamic')
    )

    def __repr__(self):
        return f'<ExternalLink {self.title!r}>'
