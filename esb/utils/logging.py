"""Mutation logger for structured JSON logging to STDOUT.

All data-changing operations must be logged via log_mutation().
Event naming: {entity}.{action} in snake_case.
Actions: created, updated, deleted, status_changed, archived.
"""

import json
import logging
from datetime import datetime, timezone

mutation_logger = logging.getLogger('esb.mutations')


def _configure_mutation_logger():
    """Configure the mutation logger to output JSON to STDOUT."""
    if not mutation_logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(message)s'))
        mutation_logger.addHandler(handler)
        mutation_logger.setLevel(logging.INFO)
        mutation_logger.propagate = False


_configure_mutation_logger()


def log_mutation(event: str, user: str, data: dict) -> None:
    """Log a data-changing operation as structured JSON to STDOUT.

    Args:
        event: Entity.action string, e.g. 'repair_record.created'
        user: Username performing the action, or 'system'
        data: Dict of relevant data fields
    """
    entry = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'event': event,
        'user': user,
        'data': data,
    }
    mutation_logger.info(json.dumps(entry))
