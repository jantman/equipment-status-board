"""Repair record lifecycle management."""

from sqlalchemy import case
from sqlalchemy.orm import joinedload

from esb.extensions import db
from esb.models.audit_log import AuditLog
from esb.models.document import Document
from esb.models.equipment import Equipment
from esb.models.repair_record import REPAIR_SEVERITIES, REPAIR_STATUSES, RepairRecord
from esb.models.repair_timeline_entry import RepairTimelineEntry
from esb.models.user import User
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation


# Ordered tuple for deterministic timeline entry creation order.
# specialist_description is intentionally saved regardless of status -- the AC
# requires it available when status is "Needs Specialist", not restricted to it.
_REPAIR_UPDATABLE_FIELDS = ('status', 'severity', 'assignee_id', 'eta', 'specialist_description')


def _serialize(value):
    """Serialize a value for audit log JSON."""
    return str(value) if value is not None else None


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


CLOSED_STATUSES = ['Resolved', 'Closed - No Issue Found', 'Closed - Duplicate']

_SEVERITY_PRIORITY = case(
    (RepairRecord.severity == 'Down', 0),
    (RepairRecord.severity == 'Degraded', 1),
    (RepairRecord.severity == 'Not Sure', 2),
    else_=3,
)


def get_repair_queue(
    area_id: int | None = None,
    status: str | None = None,
) -> list[RepairRecord]:
    """Get open repair records for the technician queue.

    Returns records whose status is not in CLOSED_STATUSES, with eager-loaded
    equipment and area relationships. Default sort: severity priority (Down
    first) then age (oldest first via created_at ASC).

    Args:
        area_id: Optional filter by equipment's area ID.
        status: Optional filter by repair record status.

    Returns:
        List of RepairRecord instances.
    """
    query = (
        db.select(RepairRecord)
        .join(RepairRecord.equipment)
        .join(Equipment.area)
        .options(
            joinedload(RepairRecord.equipment).joinedload(Equipment.area),
            joinedload(RepairRecord.assignee),
        )
        .filter(RepairRecord.status.notin_(CLOSED_STATUSES))
        .order_by(_SEVERITY_PRIORITY, RepairRecord.created_at.asc())
    )
    if area_id is not None:
        query = query.filter(Equipment.area_id == area_id)
    if status is not None:
        query = query.filter(RepairRecord.status == status)
    return list(
        db.session.execute(query).scalars().unique().all()
    )


def update_repair_record(
    repair_record_id: int,
    updated_by: str,
    author_id: int | None = None,
    **changes,
) -> RepairRecord:
    """Update a repair record and create timeline entries for each change.

    Accepts keyword arguments for any updatable field. Only fields that
    actually differ from the current value will generate timeline entries.

    Updatable fields:
        status (str): New status value. Must be in REPAIR_STATUSES.
        severity (str | None): New severity value. Must be in REPAIR_SEVERITIES or None.
        assignee_id (int | None): New assignee user ID, or None to unassign.
        eta (date | None): New ETA date, or None to clear.
        specialist_description (str | None): Free-text description for specialist needs.
        note (str | None): Optional note text to add to timeline.

    Returns:
        The updated RepairRecord.

    Raises:
        ValidationError: if repair record not found, or invalid field values.
    """
    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    # Validate incoming values
    if 'status' in changes and changes['status'] not in REPAIR_STATUSES:
        raise ValidationError(f'Invalid status: {changes["status"]!r}')
    if 'severity' in changes and changes['severity'] is not None and changes['severity'] not in REPAIR_SEVERITIES:
        raise ValidationError(f'Invalid severity: {changes["severity"]!r}')
    if 'assignee_id' in changes and changes['assignee_id'] is not None:
        assignee = db.session.get(User, changes['assignee_id'])
        if assignee is None:
            raise ValidationError(f'User with id {changes["assignee_id"]} not found')

    # Extract note separately (not a model field)
    note = changes.pop('note', None)

    # Validate no unknown keys were passed
    unknown_keys = set(changes.keys()) - set(_REPAIR_UPDATABLE_FIELDS)
    if unknown_keys:
        raise ValidationError(f'Unknown fields: {", ".join(sorted(unknown_keys))}')

    # Detect changes and create timeline entries
    audit_changes = {}
    for field_name in _REPAIR_UPDATABLE_FIELDS:
        if field_name not in changes:
            continue
        new_value = changes[field_name]
        old_value = getattr(record, field_name)
        if old_value == new_value:
            continue

        # Record the change
        audit_changes[field_name] = [_serialize(old_value), _serialize(new_value)]
        setattr(record, field_name, new_value)

        # Create appropriate timeline entry
        if field_name == 'status':
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='status_change',
                author_id=author_id,
                author_name=updated_by,
                old_value=str(old_value),
                new_value=str(new_value),
            ))
        elif field_name == 'assignee_id':
            old_user = db.session.get(User, old_value) if old_value else None
            new_user = db.session.get(User, new_value) if new_value else None
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='assignee_change',
                author_id=author_id,
                author_name=updated_by,
                old_value=old_user.username if old_user else None,
                new_value=new_user.username if new_user else None,
            ))
        elif field_name == 'eta':
            db.session.add(RepairTimelineEntry(
                repair_record_id=record.id,
                entry_type='eta_update',
                author_id=author_id,
                author_name=updated_by,
                old_value=str(old_value) if old_value else None,
                new_value=str(new_value) if new_value else None,
            ))

    # Create note timeline entry if note provided
    if note and note.strip():
        db.session.add(RepairTimelineEntry(
            repair_record_id=record.id,
            entry_type='note',
            author_id=author_id,
            author_name=updated_by,
            content=note.strip(),
        ))
        audit_changes['note'] = [None, note.strip()]

    # Create audit log entry
    if audit_changes:
        db.session.add(AuditLog(
            entity_type='repair_record',
            entity_id=record.id,
            action='updated',
            user_id=author_id,
            changes=audit_changes,
        ))

    db.session.commit()

    if audit_changes:
        log_mutation('repair_record.updated', updated_by, {
            'id': record.id,
            'changes': audit_changes,
        })

    return record


def add_repair_note(
    repair_record_id: int,
    note: str,
    author_name: str,
    author_id: int | None = None,
) -> RepairTimelineEntry:
    """Add a note to a repair record's timeline.

    Args:
        repair_record_id: ID of the repair record.
        note: Text content of the note.
        author_name: Username of the person adding the note.
        author_id: User ID of the author (None for system notes).

    Returns:
        The created RepairTimelineEntry.

    Raises:
        ValidationError: if repair record not found or note is empty.
    """
    if not note or not note.strip():
        raise ValidationError('Note text is required')

    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    entry = RepairTimelineEntry(
        repair_record_id=record.id,
        entry_type='note',
        author_id=author_id,
        author_name=author_name,
        content=note.strip(),
    )
    db.session.add(entry)

    db.session.add(AuditLog(
        entity_type='repair_record',
        entity_id=record.id,
        action='note_added',
        user_id=author_id,
        changes={'note': note.strip()},
    ))

    db.session.commit()

    log_mutation('repair_record.note_added', author_name, {
        'id': record.id,
        'note': note.strip(),
    })

    return entry


def add_repair_photo(
    repair_record_id: int,
    file,
    author_name: str,
    author_id: int | None = None,
) -> tuple[Document, RepairTimelineEntry]:
    """Upload a photo to a repair record and add a timeline entry.

    Args:
        repair_record_id: ID of the repair record.
        file: Werkzeug FileStorage object from the form.
        author_name: Username of the person uploading.
        author_id: User ID of the uploader.

    Returns:
        Tuple of (Document, RepairTimelineEntry).

    Raises:
        ValidationError: if repair record not found or file invalid.
    """
    from esb.services import upload_service

    record = db.session.get(RepairRecord, repair_record_id)
    if record is None:
        raise ValidationError(f'Repair record with id {repair_record_id} not found')

    doc = upload_service.save_upload(
        file=file,
        parent_type='repair_photo',
        parent_id=record.id,
        uploaded_by=author_name,
    )

    entry = RepairTimelineEntry(
        repair_record_id=record.id,
        entry_type='photo',
        author_id=author_id,
        author_name=author_name,
        content=str(doc.id),
    )
    db.session.add(entry)

    db.session.add(AuditLog(
        entity_type='repair_record',
        entity_id=record.id,
        action='photo_added',
        user_id=author_id,
        changes={
            'document_id': doc.id,
            'filename': doc.original_filename,
        },
    ))

    db.session.commit()

    log_mutation('repair_record.photo_added', author_name, {
        'id': record.id,
        'document_id': doc.id,
        'filename': doc.original_filename,
    })

    return doc, entry
