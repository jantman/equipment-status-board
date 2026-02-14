"""Tests for Flask CLI commands."""

from esb.extensions import db as _db
from esb.models.user import User


class TestSeedAdmin:
    """Tests for the seed-admin CLI command."""

    def test_creates_staff_user(self, app):
        """seed-admin creates a staff user when none exists."""
        runner = app.test_cli_runner()
        result = runner.invoke(
            args=['seed-admin', 'admin', 'admin@example.com', '--password', 'secret']
        )
        assert result.exit_code == 0
        assert 'Created staff user: admin' in result.output

        user = _db.session.execute(
            _db.select(User).filter_by(username='admin')
        ).scalar_one()
        assert user.role == 'staff'
        assert user.email == 'admin@example.com'
        assert user.check_password('secret')

    def test_skips_if_staff_exists(self, app):
        """seed-admin does not create a duplicate if a staff user exists."""
        existing = User(username='boss', email='boss@example.com', role='staff')
        existing.set_password('pass')
        _db.session.add(existing)
        _db.session.commit()

        runner = app.test_cli_runner()
        result = runner.invoke(
            args=['seed-admin', 'admin2', 'admin2@example.com', '--password', 'secret']
        )
        assert result.exit_code == 0
        assert 'Staff user already exists: boss' in result.output

        # Verify no new user was created
        count = _db.session.execute(
            _db.select(_db.func.count()).select_from(User)
        ).scalar()
        assert count == 1

    def test_skips_with_multiple_staff_users(self, app):
        """seed-admin handles multiple existing staff users without crashing."""
        for name in ['boss1', 'boss2']:
            user = User(username=name, email=f'{name}@example.com', role='staff')
            user.set_password('pass')
            _db.session.add(user)
        _db.session.commit()

        runner = app.test_cli_runner()
        result = runner.invoke(
            args=['seed-admin', 'admin3', 'admin3@example.com', '--password', 'secret']
        )
        assert result.exit_code == 0
        assert 'Staff user already exists' in result.output
