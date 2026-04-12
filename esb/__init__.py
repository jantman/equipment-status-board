"""ESB application package."""

import os

from flask import Flask, flash, redirect, render_template, request, session, url_for

from esb.config import config
from esb.extensions import csrf, db, login_manager, migrate
from esb.utils.filters import register_filters
from esb.views import register_blueprints

_newrelic_initialized = False


def create_app(config_name='default'):
    """Create and configure the Flask application.

    Args:
        config_name: Configuration key ('development', 'testing', 'production', 'default').
    """
    global _newrelic_initialized
    nr_license = os.environ.get('NEW_RELIC_LICENSE_KEY', '')
    if nr_license and not _newrelic_initialized:
        import newrelic.agent
        settings = newrelic.agent.global_settings()
        settings.license_key = nr_license
        settings.app_name = os.environ.get('NEW_RELIC_APP_NAME', 'Equipment Status Board')
        settings.browser_monitoring.auto_instrument = False
        newrelic.agent.initialize()
        _newrelic_initialized = True

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

    # Initialize Slack integration (conditional on SLACK_BOT_TOKEN and SLACK_APP_TOKEN)
    from esb.slack import init_slack
    init_slack(app)

    # Register custom Jinja2 filters
    register_filters(app)

    # New Relic browser monitoring context processor
    if nr_license:
        @app.context_processor
        def newrelic_browser_snippets():
            import newrelic.agent
            return {
                'newrelic_browser_header': newrelic.agent.get_browser_timing_header(),
                'newrelic_browser_footer': newrelic.agent.get_browser_timing_footer(),
            }

    # Register error handlers
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(413)
    def request_entity_too_large(e):
        flash(
            f'File is too large. Maximum size is {app.config["UPLOAD_MAX_SIZE_MB"]} MB.',
            'danger',
        )
        return redirect(request.referrer or url_for('equipment.index')), 302

    @app.errorhandler(500)
    def internal_error(e):
        return render_template('errors/500.html'), 500

    # Health / index route
    @app.route('/')
    def index():
        return redirect(url_for('public.status_dashboard'))

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

    @app.cli.group()
    def worker():
        """Background worker commands."""
        pass

    @worker.command('run')
    @click.option('--poll-interval', default=30, type=int,
                  help='Seconds between polling cycles (default: 30)')
    def worker_run(poll_interval):
        """Run the background notification worker."""
        from esb.services import notification_service

        click.echo(f'Starting notification worker (poll interval: {poll_interval}s)')
        notification_service.run_worker_loop(poll_interval=poll_interval)

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
