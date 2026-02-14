"""Jinja2 custom template filters for ESB application."""

from datetime import datetime, timezone


def format_date(value, fmt='%Y-%m-%d'):
    """Format a datetime object as a date string.

    Args:
        value: A datetime object.
        fmt: strftime format string.
    """
    if value is None:
        return ''
    return value.strftime(fmt)


def format_datetime(value, fmt='%Y-%m-%d %H:%M'):
    """Format a datetime object as a date+time string.

    Args:
        value: A datetime object.
        fmt: strftime format string.
    """
    if value is None:
        return ''
    return value.strftime(fmt)


def relative_time(value):
    """Return a human-readable relative time string (e.g., '2 hours ago').

    Args:
        value: A datetime object (assumed UTC).
    """
    if value is None:
        return ''

    now = datetime.now(timezone.utc)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)

    diff = now - value
    seconds = int(diff.total_seconds())

    if seconds < 0:
        return 'just now'
    if seconds < 60:
        return 'just now'
    if seconds < 3600:
        minutes = seconds // 60
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    if seconds < 86400:
        hours = seconds // 3600
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    if seconds < 2592000:  # 30 days
        days = seconds // 86400
        return f'{days} day{"s" if days != 1 else ""} ago'
    if seconds < 31536000:  # 365 days
        months = seconds // 2592000
        return f'{months} month{"s" if months != 1 else ""} ago'
    years = seconds // 31536000
    return f'{years} year{"s" if years != 1 else ""} ago'


def register_filters(app):
    """Register all custom Jinja2 filters with the Flask app."""
    app.jinja_env.filters['format_date'] = format_date
    app.jinja_env.filters['format_datetime'] = format_datetime
    app.jinja_env.filters['relative_time'] = relative_time
