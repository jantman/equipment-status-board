"""ESB application package."""

from flask import Flask, redirect, render_template, url_for

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

    # Placeholder user loader (replaced when User model is implemented)
    @login_manager.user_loader
    def load_user(user_id):
        return None

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

    return app
