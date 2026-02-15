"""Repair record lifecycle management."""

from esb.extensions import db
from esb.models.audit_log import AuditLog
from esb.models.equipment import Equipment
from esb.models.repair_record import REPAIR_SEVERITIES, RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.models.user import User
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation


def create_repair_record(
    equipment_id: int,
    description: str,
    created_by: str,
    severity: str | None = None,
    reporter_name: str | None = None,
    reporter_email: str | None = None,
    assignee_id: int | None = None,
    has_safety_risk: bool = False,
    is_consumable: bool = False,
    author_id: int | None = None,
) -> RepairRecord:
    """Create a new repair record with initial timeline entry.

    Args:
        equipment_id: ID of the equipment this repair is for.
        description: Description of the problem.
        created_by: Username of the person creating the record.
        severity: Optional severity level (Down, Degraded, Not Sure).
        reporter_name: Name of the person reporting (for member reports).
        reporter_email: Email of the reporter (for member reports).
        assignee_id: Optional user ID to assign the repair to.
        has_safety_risk: Whether this is a safety risk.
        is_consumable: Whether this involves consumables.
        author_id: User ID of the creator (None for anonymous reports).

    Returns:
        The created RepairRecord.

    Raises:
        ValidationError: if equipment not found, archived, or invalid input.
    """
    if not description or not description.strip():
        raise ValidationError('Description is required')

    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        raise ValidationError(f'Equipment with id {equipment_id} not found')
    if equipment.is_archived:
        raise ValidationError(f'Equipment {equipment.name!r} is archived and cannot have new repair records')

    if severity is not None and severity not in REPAIR_SEVERITIES:
        raise ValidationError(f'Invalid severity: {severity!r}')

    if assignee_id is not None:
        assignee = db.session.get(User, assignee_id)
        if assignee is None:
            raise ValidationError(f'User with id {assignee_id} not found')

    record = RepairRecord(
        equipment_id=equipment_id,
        description=description.strip(),
        status='New',
        severity=severity,
        reporter_name=reporter_name,
        reporter_email=reporter_email,
        assignee_id=assignee_id,
        has_safety_risk=has_safety_risk,
        is_consumable=is_consumable,
    )
    db.session.add(record)
    db.session.flush()

    # Create timeline creation entry
    timeline_entry = RepairTimelineEntry(
        repair_record_id=record.id,
        entry_type='creation',
        author_id=author_id,
        author_name=reporter_name or created_by,
        content=description.strip(),
    )
    db.session.add(timeline_entry)

    # Create audit log entry
    audit_entry = AuditLog(
        entity_type='repair_record',
        entity_id=record.id,
        action='created',
        user_id=author_id,
        changes={
            'equipment_id': equipment_id,
            'status': 'New',
            'severity': severity,
            'description': description.strip(),
        },
    )
    db.session.add(audit_entry)

    db.session.commit()

    log_mutation('repair_record.created', created_by, {
        'id': record.id,
        'equipment_id': record.equipment_id,
        'status': record.status,
        'severity': record.severity,
        'description': record.description,
        'reporter_name': record.reporter_name,
    })

    return record


def get_repair_record(repair_record_id: int) -> RepairRecord:
    """Get a repair record by ID.

    Raises:
        ValidationError: if not found.
    """
    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')
    return record


def list_repair_records(
    equipment_id: int | None = None,
    status: str | None = None,
) -> list[RepairRecord]:
    """List repair records, optionally filtered.

    Args:
        equipment_id: Filter by equipment ID.
        status: Filter by status.

    Returns:
        List of RepairRecord instances ordered by created_at desc.
    """
    query = db.select(RepairRecord).order_by(RepairRecord.created_at.desc())
    if equipment_id is not None:
        query = query.filter_by(equipment_id=equipment_id)
    if status is not None:
        query = query.filter_by(status=status)
    return list(db.session.execute(query).scalars().all())
