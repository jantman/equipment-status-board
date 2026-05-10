"""Prometheus metrics for the notification queue.

Exposes gauges that, together, catch a stuck worker, a bad Slack token,
or a Slack outage:

- ``esb_pending_notifications_count`` — count of rows with status='pending'.
- ``esb_oldest_pending_notification_timestamp_seconds`` — Unix epoch seconds
  of the oldest pending row's ``created_at``. **Omitted entirely** when the
  table has no pending rows; Prometheus alert rules should use ``absent()``
  rather than a sentinel value.
- ``esb_worker_last_iteration_timestamp_seconds`` — Unix epoch seconds of the
  worker's last successful poll cycle (read from ``AppConfig``). Omitted when
  the worker has never run or the underlying query fails.
- ``esb_socket_mode_enabled`` / ``esb_socket_mode_connected`` — Slack Socket
  Mode intent and binding state. Always emitted.

Alert rules belong in Prometheus, not here. Example::

    time() - esb_oldest_pending_notification_timestamp_seconds > 300
"""

import logging
from datetime import UTC, datetime

from prometheus_client import CollectorRegistry, generate_latest
from prometheus_client.core import GaugeMetricFamily
from prometheus_client.exposition import CONTENT_TYPE_LATEST
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

from esb.extensions import db
from esb.models.app_config import AppConfig
from esb.models.pending_notification import PendingNotification

logger = logging.getLogger(__name__)

# Per-process latch: the first AppConfig query failure logs a full traceback
# (diagnostically useful), subsequent failures log a one-line warning. Prevents
# log flooding on pre-migration deployments where /metrics is scraped every
# 15-30s and the app_config table doesn't yet exist.
_app_config_query_failed_once: bool = False


def _query_pending_stats() -> tuple[int, float | None]:
    """Return (pending_count, oldest_created_at_unix_seconds_or_None).

    Both aggregates come from a single SELECT so the count and oldest
    timestamp are guaranteed to be drawn from the same row snapshot
    (under any isolation level) and so each scrape is one DB round-trip
    rather than two.
    """
    count, oldest = db.session.execute(
        db.select(
            db.func.count(PendingNotification.id),
            db.func.min(PendingNotification.created_at),
        )
        .where(PendingNotification.status == 'pending')
    ).one()

    if oldest is None:
        return count, None

    # SQLAlchemy may return naive datetimes (SQLite) or aware datetimes
    # (MariaDB driver). Treat naive values as UTC -- created_at is always
    # written as datetime.now(UTC) by the model.
    if oldest.tzinfo is None:
        oldest = oldest.replace(tzinfo=UTC)

    return count, oldest.timestamp()


class _PendingNotificationsCollector:
    """Custom collector so the oldest-timestamp metric can be omitted entirely
    when the queue is empty (rather than emitting a misleading 0 sample).

    Each scrape runs one combined aggregate query against the live DB. With
    the default Dockerfile gunicorn config (1 worker, 2 threads) this is at
    most one query per scrape interval. If gunicorn is scaled to N workers
    the DB load multiplies by N, since each worker handles its own scrape
    with its own request-scoped DB session.
    """

    def collect(self):
        count, oldest_ts = _query_pending_stats()

        yield GaugeMetricFamily(
            'esb_pending_notifications_count',
            'Number of notifications in the queue with status=pending.',
            value=count,
        )

        if oldest_ts is not None:
            yield GaugeMetricFamily(
                'esb_oldest_pending_notification_timestamp_seconds',
                'Unix timestamp (seconds) of the oldest pending notification. '
                'Omitted when the queue is empty.',
                value=oldest_ts,
            )


class _WorkerStatusCollector:
    """Custom collector for worker-liveness and Slack Socket Mode state.

    Emits up to three gauges per scrape:
    - ``esb_worker_last_iteration_timestamp_seconds`` (omitted if absent or
      the AppConfig query fails)
    - ``esb_socket_mode_enabled`` (always emitted)
    - ``esb_socket_mode_connected`` (always emitted)

    Failures of the AppConfig query never propagate out of ``collect()`` — the
    worker-timestamp gauge is simply omitted. The Socket Mode gauges still
    emit so the actionable failure mode (enabled=1, connected=0) remains
    observable even when the DB is unavailable.
    """

    def collect(self):
        global _app_config_query_failed_once
        row = None
        try:
            row = db.session.execute(
                select(AppConfig).where(AppConfig.key == 'worker_last_iteration_at')
            ).scalar_one_or_none()
        except SQLAlchemyError as e:
            # CRITICAL: rollback the session before continuing. SQLAlchemy 2.x
            # marks the session as failed after a query error; subsequent
            # db.session.execute() calls in the same request (e.g. by the
            # _PendingNotificationsCollector that runs in the same scrape)
            # would otherwise raise PendingRollbackError.
            db.session.rollback()
            # Rate-limit: full traceback only on the first failure per
            # process; subsequent failures get a one-line warning so /metrics
            # scrapes (every 15-30s) on a pre-migration deployment do not
            # flood logs.
            if not _app_config_query_failed_once:
                logger.warning(
                    'Failed to query worker_last_iteration_at from AppConfig; '
                    'omitting metric',
                    exc_info=True,
                )
                _app_config_query_failed_once = True
            else:
                logger.warning(
                    'Failed to query worker_last_iteration_at from AppConfig: %s: %s',
                    type(e).__name__, e,
                )
        if row is not None:
            try:
                # datetime.fromisoformat accepts only str — None or wrong type
                # raises TypeError, malformed string raises ValueError. Both
                # are non-fatal here; omit the metric and log.
                ts = datetime.fromisoformat(row.value)
                yield GaugeMetricFamily(
                    'esb_worker_last_iteration_timestamp_seconds',
                    "Unix timestamp (seconds) of the worker's last successful "
                    'poll. Omitted if the worker has never run or the AppConfig '
                    'query failed.',
                    value=ts.timestamp(),
                )
            except (ValueError, TypeError):
                logger.warning(
                    'Failed to parse worker last-iteration timestamp value=%r',
                    row.value, exc_info=True,
                )

        # Lazy + dotted import inside collect(). Two reasons (NOT circular-
        # import avoidance — there is no circular-import risk):
        #   1. Defers Flask app-context dependencies that some test fixtures
        #      lazily install during early test setup.
        #   2. Preserves the monkeypatch surface: tests do
        #      monkeypatch.setattr('esb.slack.is_socket_mode_connected', ...)
        #      which only takes effect via attribute lookup at call time. A
        #      top-of-module `from esb.slack import is_socket_mode_connected`
        #      would bind the symbol locally and silently miss the patch.
        # If you "clean this up" by moving the import to module top, you will
        # break the test design. Don't.
        import esb.slack as _slack
        yield GaugeMetricFamily(
            'esb_socket_mode_enabled',
            '1 if init_slack entered the Socket Mode setup block (tokens set, '
            'not TESTING, opt-in flag true). 0 on any of the four early-return '
            'paths or if the setup block was never reached.',
            value=1.0 if _slack.is_socket_mode_enabled() else 0.0,
        )
        yield GaugeMetricFamily(
            'esb_socket_mode_connected',
            '1 if a Bolt SocketModeHandler is currently bound; 0 if never '
            'bound or released. Reflects handler-binding state, NOT live '
            'WebSocket connection state — Slack Bolt does not expose mid-life '
            'connection callbacks. Transitions 1->0 at process shutdown.',
            value=1.0 if _slack.is_socket_mode_connected() else 0.0,
        )


def render_metrics() -> tuple[bytes, str]:
    """Render the Prometheus exposition payload and content-type.

    Returns:
        Tuple of (body, content_type) suitable for a Flask response.
    """
    registry = CollectorRegistry()
    # Order is defensive: with the explicit db.session.rollback() in
    # _WorkerStatusCollector, registration order is no longer load-bearing
    # for correctness, but pinning it makes intent unambiguous.
    registry.register(_PendingNotificationsCollector())
    registry.register(_WorkerStatusCollector())
    return generate_latest(registry), CONTENT_TYPE_LATEST
