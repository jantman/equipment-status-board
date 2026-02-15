"""Equipment service layer for area management and equipment CRUD.

All area/equipment business logic lives here. Views call these functions;
they never query models directly.
"""

from esb.extensions import db
from esb.models.area import Area
from esb.utils.exceptions import ValidationError
from esb.utils.logging import log_mutation


def list_areas() -> list[Area]:
    """Return all active (non-archived) areas ordered by name."""
    return list(
        db.session.execute(
            db.select(Area).filter_by(is_archived=False).order_by(Area.name)
        ).scalars().all()
    )


def get_area(area_id: int) -> Area:
    """Get a single area by ID.

    Raises:
        ValidationError: if area not found.
    """
    area = db.session.get(Area, area_id)
    if area is None:
        raise ValidationError(f'Area with id {area_id} not found')
    return area


def create_area(name: str, slack_channel: str, created_by: str) -> Area:
    """Create a new area.

    Raises:
        ValidationError: if name already exists (case-insensitive).
    """
    existing = db.session.execute(
        db.select(Area).filter(db.func.lower(Area.name) == name.lower())
    ).scalar_one_or_none()
    if existing is not None:
        raise ValidationError(f'An area with name {name!r} already exists')

    area = Area(name=name, slack_channel=slack_channel)
    db.session.add(area)
    db.session.commit()

    log_mutation('area.created', created_by, {
        'id': area.id,
        'name': area.name,
        'slack_channel': area.slack_channel,
    })

    return area


def update_area(area_id: int, name: str, slack_channel: str, updated_by: str) -> Area:
    """Update an area.

    Raises:
        ValidationError: if area not found or name conflicts with another area.
    """
    area = db.session.get(Area, area_id)
    if area is None:
        raise ValidationError(f'Area with id {area_id} not found')

    existing = db.session.execute(
        db.select(Area).filter(
            db.func.lower(Area.name) == name.lower(),
            Area.id != area_id,
        )
    ).scalar_one_or_none()
    if existing is not None:
        raise ValidationError(f'An area with name {name!r} already exists')

    changes = {}
    if area.name != name:
        changes['name'] = [area.name, name]
        area.name = name
    if area.slack_channel != slack_channel:
        changes['slack_channel'] = [area.slack_channel, slack_channel]
        area.slack_channel = slack_channel

    db.session.commit()

    log_mutation('area.updated', updated_by, {
        'id': area.id,
        'name': area.name,
        'slack_channel': area.slack_channel,
        'changes': changes,
    })

    return area


def archive_area(area_id: int, archived_by: str) -> Area:
    """Soft-delete an area.

    Raises:
        ValidationError: if area not found or already archived.
    """
    area = db.session.get(Area, area_id)
    if area is None:
        raise ValidationError(f'Area with id {area_id} not found')

    if area.is_archived:
        raise ValidationError(f'Area {area.name!r} is already archived')

    area.is_archived = True
    db.session.commit()

    log_mutation('area.archived', archived_by, {
        'id': area.id,
        'name': area.name,
    })

    return area
