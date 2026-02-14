"""Tests for Jinja2 custom template filters."""

from datetime import datetime, timedelta, timezone

from flask import Flask

from esb.utils.filters import (
    format_date,
    format_datetime,
    register_filters,
    relative_time,
)


class TestFormatDate:
    """Tests for format_date filter."""

    def test_default_format(self):
        dt = datetime(2026, 2, 14, 10, 30, 0)
        assert format_date(dt) == '2026-02-14'

    def test_custom_format(self):
        dt = datetime(2026, 2, 14, 10, 30, 0)
        assert format_date(dt, '%m/%d/%Y') == '02/14/2026'

    def test_none_returns_empty(self):
        assert format_date(None) == ''


class TestFormatDatetime:
    """Tests for format_datetime filter."""

    def test_default_format(self):
        dt = datetime(2026, 2, 14, 10, 30, 0)
        assert format_datetime(dt) == '2026-02-14 10:30'

    def test_custom_format(self):
        dt = datetime(2026, 2, 14, 10, 30, 45)
        assert format_datetime(dt, '%H:%M:%S') == '10:30:45'

    def test_none_returns_empty(self):
        assert format_datetime(None) == ''


class TestRelativeTime:
    """Tests for relative_time filter."""

    def test_none_returns_empty(self):
        assert relative_time(None) == ''

    def test_just_now(self):
        now = datetime.now(timezone.utc)
        assert relative_time(now) == 'just now'

    def test_seconds_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(seconds=30)
        assert relative_time(dt) == 'just now'

    def test_one_minute_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(minutes=1)
        assert relative_time(dt) == '1 minute ago'

    def test_multiple_minutes_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(minutes=45)
        assert relative_time(dt) == '45 minutes ago'

    def test_one_hour_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(hours=1)
        assert relative_time(dt) == '1 hour ago'

    def test_multiple_hours_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(hours=5)
        assert relative_time(dt) == '5 hours ago'

    def test_one_day_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(days=1)
        assert relative_time(dt) == '1 day ago'

    def test_multiple_days_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(days=15)
        assert relative_time(dt) == '15 days ago'

    def test_one_month_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(days=35)
        assert relative_time(dt) == '1 month ago'

    def test_one_year_ago(self):
        dt = datetime.now(timezone.utc) - timedelta(days=400)
        assert relative_time(dt) == '1 year ago'

    def test_naive_datetime_treated_as_utc(self):
        """Timezone-naive datetimes are treated as UTC."""
        dt = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=2)
        result = relative_time(dt)
        assert 'hour' in result

    def test_future_time_returns_just_now(self):
        """Future timestamps return 'just now'."""
        dt = datetime.now(timezone.utc) + timedelta(hours=1)
        assert relative_time(dt) == 'just now'


class TestRegisterFilters:
    """Tests for register_filters function."""

    def test_filters_registered(self):
        app = Flask(__name__)
        register_filters(app)
        assert 'format_date' in app.jinja_env.filters
        assert 'format_datetime' in app.jinja_env.filters
        assert 'relative_time' in app.jinja_env.filters
