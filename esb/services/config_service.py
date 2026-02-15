"""Config service layer for runtime application settings.

All AppConfig reads/writes go through this module.
"""

from sqlalchemy.exc import IntegrityError

from esb.extensions import db
from esb.models.app_config import AppConfig
from esb.utils.logging import log_mutation


def get_config(key: str, default: str = '') -> str:
    """Get a runtime config value by key.

    Args:
        key: Config key to look up.
        default: Value to return if key not found.

    Returns:
        The config value as a string, or default if not set.
    """
    config = db.session.execute(
        db.select(AppConfig).filter_by(key=key)
    ).scalar_one_or_none()
    if config is None:
        return default
    return config.value


def set_config(key: str, value: str, changed_by: str) -> AppConfig:
    """Set a runtime config value (upsert).

    Args:
        key: Config key to set.
        value: New value.
        changed_by: Username making the change.

    Returns:
        The created or updated AppConfig instance.
    """
    config = db.session.execute(
        db.select(AppConfig).filter_by(key=key)
    ).scalar_one_or_none()

    if config is not None:
        old_value = config.value
        config.value = value
    else:
        old_value = ''
        config = AppConfig(key=key, value=value)
        db.session.add(config)

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        config = db.session.execute(
            db.select(AppConfig).filter_by(key=key)
        ).scalar_one()
        old_value = config.value
        config.value = value
        db.session.commit()

    log_mutation('app_config.updated', changed_by, {
        'key': key,
        'old_value': old_value,
        'new_value': value,
    })

    return config
