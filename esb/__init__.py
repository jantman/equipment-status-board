"""ESB application package."""

from flask import Flask, redirect, render_template, session, url_for

from esb.config import config
from esb.extensions import csrf, db, login_manager, migrate
from esb.utils.filters import register_filters
from esb.views import register_blueprints


def create_app(config_name='default'):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration key ('development', 'testing', 'production', 'default').
    """
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Import models so Alembic can detect them
    import esb.models  # noqa: F401

    from esb.services import auth_service

    @login_manager.user_loader
    def load_user(user_id):
        return auth_service.load_user(user_id)

    login_manager.login_message_category = 'warning'

    @app.before_request
    def enforce_permanent_session():
        session.permanent = True

    # Register blueprints
    register_blueprints(app)

    # Register custom Jinja2 filters
    register_filters(app)

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    # Health / index route
    @app.route('/')
    def index():
        return redirect(url_for('health'))

    @app.route('/health')
    def health():
        return 'ok'

    # CLI commands
    _register_cli(app)

    return app


def _register_cli(app):
    """Register Flask CLI commands."""
    import click

    from esb.extensions import db as _db
    from esb.models.user import User

    @app.cli.command('seed-admin')
    @click.argument('username')
    @click.argument('email')
    @click.option('--password', prompt=True, hide_input=True,
                  confirmation_prompt=True, help='Password for the new admin user.')
    def seed_admin(username, email, password):
        """Create an initial staff user if none exists."""
        existing = _db.session.execute(
            _db.select(User).filter_by(role='staff')
        ).scalars().first()
        if existing:
            click.echo(f'Staff user already exists: {existing.username}')
            return
        user = User(username=username, email=email, role='staff')
        user.set_password(password)
        _db.session.add(user)
        _db.session.commit()
        click.echo(f'Created staff user: {username}')
