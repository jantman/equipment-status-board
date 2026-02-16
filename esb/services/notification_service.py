"""Notification queue management and background worker."""

import logging
import signal
import time
from datetime import UTC, datetime, timedelta

from esb.extensions import db
from esb.models.pending_notification import PendingNotification
from esb.utils.logging import log_mutation

logger = logging.getLogger(__name__)

# Exponential backoff schedule (in seconds): 30s, 1m, 2m, 5m, 15m, 1h max
BACKOFF_SCHEDULE = [30, 60, 120, 300, 900, 3600]


def queue_notification(
    notification_type: str,
    target: str,
    payload: dict | None = None,
) -> PendingNotification:
    """Insert a notification into the queue for background delivery.

    Args:
        notification_type: Type of notification ('slack_message', 'static_page_push').
        target: Delivery target (Slack channel name, push destination).
        payload: JSON-serializable data for the notification.

    Returns:
        The created PendingNotification.
    """
    notification = PendingNotification(
        notification_type=notification_type,
        target=target,
        payload=payload,
        status='pending',
    )
    db.session.add(notification)
    db.session.commit()

    log_mutation('notification.queued', 'system', {
        'id': notification.id,
        'type': notification_type,
        'target': target,
    })

    return notification


def get_pending_notifications() -> list[PendingNotification]:
    """Get all notifications ready for delivery.

    Returns notifications where status is 'pending' and either
    next_retry_at is NULL (first attempt) or next_retry_at <= now.
    """
    now = datetime.now(UTC)
    return list(
        db.session.execute(
            db.select(PendingNotification)
            .filter_by(status='pending')
            .filter(
                db.or_(
                    PendingNotification.next_retry_at.is_(None),
                    PendingNotification.next_retry_at <= now,
                )
            )
            .order_by(PendingNotification.created_at.asc())
        ).scalars().all()
    )


def mark_delivered(notification_id: int) -> PendingNotification:
    """Mark a notification as successfully delivered."""
    notification = db.session.get(PendingNotification, notification_id)
    notification.status = 'delivered'
    notification.delivered_at = datetime.now(UTC)
    db.session.commit()

    log_mutation('notification.delivered', 'system', {
        'id': notification.id,
        'type': notification.notification_type,
        'target': notification.target,
    })

    return notification


def mark_failed(notification_id: int, error_message: str) -> PendingNotification:
    """Mark a notification delivery as failed with exponential backoff.

    Backoff schedule: 30s, 1m, 2m, 5m, 15m, max 1h.
    """
    notification = db.session.get(PendingNotification, notification_id)
    notification.retry_count += 1
    notification.error_message = error_message

    # Compute backoff delay
    backoff_index = min(notification.retry_count - 1, len(BACKOFF_SCHEDULE) - 1)
    backoff_seconds = BACKOFF_SCHEDULE[backoff_index]
    notification.next_retry_at = datetime.now(UTC) + timedelta(seconds=backoff_seconds)

    db.session.commit()

    log_mutation('notification.failed', 'system', {
        'id': notification.id,
        'type': notification.notification_type,
        'target': notification.target,
        'retry_count': notification.retry_count,
        'error': error_message,
        'next_retry_at': notification.next_retry_at.isoformat(),
    })

    return notification


def process_notification(notification: PendingNotification) -> None:
    """Dispatch a notification to the appropriate delivery handler.

    Args:
        notification: The PendingNotification to process.

    Raises:
        NotImplementedError: For notification types not yet implemented.
        ValueError: For unknown notification types.
    """
    handlers = {
        'slack_message': _deliver_slack_message,
        'static_page_push': _deliver_static_page_push,
    }

    handler = handlers.get(notification.notification_type)
    if handler is None:
        raise ValueError(f'Unknown notification type: {notification.notification_type!r}')

    handler(notification)


def _deliver_slack_message(notification: PendingNotification) -> None:
    """Deliver a Slack message notification.

    Stub -- actual Slack API delivery will be implemented in Epic 6 (Story 6.1).
    """
    raise NotImplementedError('Slack message delivery not yet implemented (Epic 6)')


def _deliver_static_page_push(notification: PendingNotification) -> None:
    """Deliver a static page push notification.

    Stub -- actual static page generation and push will be implemented
    in Story 5.2.
    """
    raise NotImplementedError('Static page push not yet implemented (Story 5.2)')


def run_worker_loop(poll_interval: int = 30) -> None:
    """Main worker polling loop.

    Polls the pending_notifications table every `poll_interval` seconds
    and processes each ready notification. Handles errors gracefully by
    marking failed notifications for retry.

    Args:
        poll_interval: Seconds between polling cycles (default 30).
    """
    _shutdown = False

    def _handle_signal(signum, frame):
        nonlocal _shutdown
        logger.info('Received signal %s, shutting down gracefully...', signum)
        _shutdown = True

    signal.signal(signal.SIGTERM, _handle_signal)
    signal.signal(signal.SIGINT, _handle_signal)

    logger.info('Worker started, polling every %d seconds', poll_interval)

    while not _shutdown:
        try:
            notifications = get_pending_notifications()
            if notifications:
                logger.info('Processing %d pending notification(s)', len(notifications))

            for notification in notifications:
                if _shutdown:
                    break
                try:
                    logger.info(
                        'Processing notification %d (type=%s, target=%s)',
                        notification.id, notification.notification_type, notification.target,
                    )
                    process_notification(notification)
                    mark_delivered(notification.id)
                    logger.info('Notification %d delivered successfully', notification.id)
                except NotImplementedError as e:
                    mark_failed(notification.id, str(e))
                    logger.warning('Notification %d: %s', notification.id, e)
                except Exception as e:
                    mark_failed(notification.id, str(e))
                    logger.error(
                        'Notification %d delivery failed: %s', notification.id, e,
                        exc_info=True,
                    )

        except Exception:
            logger.error('Error in worker polling loop', exc_info=True)

        if not _shutdown:
            time.sleep(poll_interval)

    logger.info('Worker shut down cleanly')
