"""Configuration classes for ESB application."""

import os
from datetime import timedelta


class Config:
    """Base configuration."""

    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        'DATABASE_URL', 'mysql+pymysql://root:password@localhost/esb'
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_PATH = os.environ.get('UPLOAD_PATH', 'uploads')
    UPLOAD_MAX_SIZE_MB = int(os.environ.get('UPLOAD_MAX_SIZE_MB', '500'))
    MAX_CONTENT_LENGTH = UPLOAD_MAX_SIZE_MB * 1024 * 1024
    PERMANENT_SESSION_LIFETIME = timedelta(hours=12)
    SLACK_BOT_TOKEN = os.environ.get('SLACK_BOT_TOKEN', '')
    SLACK_SIGNING_SECRET = os.environ.get('SLACK_SIGNING_SECRET', '')
    STATIC_PAGE_PUSH_METHOD = os.environ.get('STATIC_PAGE_PUSH_METHOD', 'local')
    STATIC_PAGE_PUSH_TARGET = os.environ.get('STATIC_PAGE_PUSH_TARGET', '')


class DevelopmentConfig(Config):
    """Development configuration."""

    DEBUG = True


class TestingConfig(Config):
    """Testing configuration."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class ProductionConfig(Config):
    """Production configuration."""

    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig,
}
