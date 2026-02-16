"""Slack App handlers package."""

import logging

from flask import Blueprint, request

logger = logging.getLogger(__name__)

slack_bp = Blueprint('slack', __name__, url_prefix='/slack')

# Module-level state (set during init_slack)
_bolt_app = None
_handler = None


def init_slack(app):
    """Initialize Slack Bolt app and register the Blueprint.

    Skips initialization if SLACK_BOT_TOKEN is not configured.
    Called from create_app() in esb/__init__.py.
    """
    global _bolt_app, _handler

    token = app.config.get('SLACK_BOT_TOKEN', '')
    signing_secret = app.config.get('SLACK_SIGNING_SECRET', '')

    if not token:
        logger.info('SLACK_BOT_TOKEN not configured, Slack module disabled')
        return

    if not signing_secret:
        logger.warning('SLACK_SIGNING_SECRET not configured, Slack module disabled')
        return

    from slack_bolt import App
    from slack_bolt.adapter.flask import SlackRequestHandler

    _bolt_app = App(token=token, signing_secret=signing_secret)
    _handler = SlackRequestHandler(_bolt_app)

    # Register minimal event handler (Bolt requires at least one to avoid warnings)
    @_bolt_app.event('message')
    def handle_message_events(body, bolt_logger):
        pass  # Inbound message handling is Story 6.2

    # Register the blueprint with the Flask app
    app.register_blueprint(slack_bp)

    # Exempt from CSRF (Slack uses signing secret validation)
    from esb.extensions import csrf
    csrf.exempt(slack_bp)

    logger.info('Slack App initialized successfully')


@slack_bp.route('/events', methods=['POST'])
def slack_events():
    """Handle incoming Slack events via Bolt's Flask adapter."""
    return _handler.handle(request)
