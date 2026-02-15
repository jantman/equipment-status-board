"""Equipment status derivation service.

Single source of truth for computing equipment operational status
from open repair records.
"""

from sqlalchemy.orm import joinedload

from esb.extensions import db
from esb.models.area import Area
from esb.models.equipment import Equipment
from esb.models.repair_record import RepairRecord
from esb.services.repair_service import CLOSED_STATUSES
from esb.utils.exceptions import EquipmentNotFound

# Severity to status mapping: priority order (lower = higher priority)
_SEVERITY_STATUS = {
    'Down': ('red', 'Down', 0),
    'Degraded': ('yellow', 'Degraded', 1),
    'Not Sure': ('yellow', 'Degraded', 2),
}


def compute_equipment_status(equipment_id: int) -> dict:
    """Compute equipment status from open repair records.

    Returns dict with keys:
        - color: 'green' | 'yellow' | 'red'
        - label: 'Operational' | 'Degraded' | 'Down'
        - issue_description: str | None (brief description from highest severity record)
        - severity: str | None (raw severity value from highest severity record)

    Raises:
        EquipmentNotFound: if equipment_id doesn't exist
    """
    equipment = db.session.get(Equipment, equipment_id)
    if equipment is None:
        raise EquipmentNotFound(f'Equipment with id {equipment_id} not found')

    open_records = (
        db.session.execute(
            db.select(RepairRecord)
            .filter(
                RepairRecord.equipment_id == equipment_id,
                RepairRecord.status.notin_(CLOSED_STATUSES),
            )
        )
        .scalars()
        .all()
    )

    if not open_records:
        return {
            'color': 'green',
            'label': 'Operational',
            'issue_description': None,
            'severity': None,
        }

    # Find the highest-severity open record
    best_record = None
    best_priority = 999

    for record in open_records:
        sev = record.severity
        if sev in _SEVERITY_STATUS:
            priority = _SEVERITY_STATUS[sev][2]
            if priority < best_priority:
                best_priority = priority
                best_record = record

    # If no records have a recognized severity, treat as degraded (unknown severity)
    if best_record is None:
        # Records exist but none have severity set — use first record's description
        return {
            'color': 'yellow',
            'label': 'Degraded',
            'issue_description': open_records[0].description,
            'severity': None,
        }

    color, label, _ = _SEVERITY_STATUS[best_record.severity]
    return {
        'color': color,
        'label': label,
        'issue_description': best_record.description,
        'severity': best_record.severity,
    }


def get_area_status_dashboard() -> list[dict]:
    """Get all non-archived areas with their non-archived equipment and computed statuses.

    Returns list of dicts:
        [
            {
                'area': Area instance,
                'equipment': [
                    {
                        'equipment': Equipment instance,
                        'status': {color, label, issue_description, severity}
                    },
                    ...
                ]
            },
            ...
        ]
    """
    areas = (
        db.session.execute(
            db.select(Area)
            .filter(Area.is_archived.is_(False))
            .order_by(Area.name)
        )
        .scalars()
        .all()
    )

    # Prefetch all open repair records for non-archived equipment in one query
    open_records = (
        db.session.execute(
            db.select(RepairRecord)
            .join(RepairRecord.equipment)
            .filter(
                Equipment.is_archived.is_(False),
                RepairRecord.status.notin_(CLOSED_STATUSES),
            )
            .options(joinedload(RepairRecord.equipment))
        )
        .scalars()
        .unique()
        .all()
    )

    # Group open records by equipment_id
    records_by_equipment: dict[int, list[RepairRecord]] = {}
    for record in open_records:
        records_by_equipment.setdefault(record.equipment_id, []).append(record)

    result = []
    for area in areas:
        equipment_list = (
            db.session.execute(
                db.select(Equipment)
                .filter(
                    Equipment.area_id == area.id,
                    Equipment.is_archived.is_(False),
                )
                .order_by(Equipment.name)
            )
            .scalars()
            .all()
        )

        equip_statuses = []
        for equip in equipment_list:
            equip_records = records_by_equipment.get(equip.id, [])
            if not equip_records:
                status = {
                    'color': 'green',
                    'label': 'Operational',
                    'issue_description': None,
                    'severity': None,
                }
            else:
                # Find highest-severity record
                best_record = None
                best_priority = 999
                for record in equip_records:
                    sev = record.severity
                    if sev in _SEVERITY_STATUS:
                        priority = _SEVERITY_STATUS[sev][2]
                        if priority < best_priority:
                            best_priority = priority
                            best_record = record
                if best_record is None:
                    status = {
                        'color': 'yellow',
                        'label': 'Degraded',
                        'issue_description': equip_records[0].description,
                        'severity': None,
                    }
                else:
                    color, label, _ = _SEVERITY_STATUS[best_record.severity]
                    status = {
                        'color': color,
                        'label': label,
                        'issue_description': best_record.description,
                        'severity': best_record.severity,
                    }

            equip_statuses.append({
                'equipment': equip,
                'status': status,
            })

        result.append({
            'area': area,
            'equipment': equip_statuses,
        })

    return result
