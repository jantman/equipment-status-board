"""AppConfig model for runtime-configurable settings."""

from datetime import UTC, datetime

from esb.extensions import db


class AppConfig(db.Model):
    """Key-value store for runtime-configurable settings."""

    __tablename__ = 'app_config'

    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False, index=True)
    value = db.Column(db.Text, nullable=False, default='')
    updated_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )

    def __repr__(self):
        return f'<AppConfig {self.key!r}>'
