"""PendingNotification model for the notification queue."""

from datetime import UTC, datetime

from esb.extensions import db


class PendingNotification(db.Model):
    """Queue table for outbound notifications and static page pushes."""

    __tablename__ = 'pending_notifications'

    id = db.Column(db.Integer, primary_key=True)
    notification_type = db.Column(db.String(50), nullable=False, index=True)
    target = db.Column(db.String(255), nullable=False)
    payload = db.Column(db.JSON, nullable=True)
    status = db.Column(db.String(20), nullable=False, default='pending', index=True)
    created_at = db.Column(
        db.DateTime, nullable=False,
        default=lambda: datetime.now(UTC),
    )
    next_retry_at = db.Column(db.DateTime, nullable=True)
    retry_count = db.Column(db.Integer, nullable=False, default=0)
    delivered_at = db.Column(db.DateTime, nullable=True)
    error_message = db.Column(db.Text, nullable=True)

    def __repr__(self):
        return f'<PendingNotification {self.id} type={self.notification_type!r} status={self.status!r}>'
