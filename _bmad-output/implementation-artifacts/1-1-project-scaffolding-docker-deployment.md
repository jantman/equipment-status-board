# Story 1.1: Project Scaffolding & Docker Deployment

Status: done

## Story

As a developer,
I want the ESB application scaffolded with Flask, Docker, and CI/CD pipeline,
So that the team has a deployable foundation to build features on.

## Acceptance Criteria

1. **Given** a fresh repository checkout **When** I run `docker-compose up` **Then** the Flask app container and MySQL container start successfully **And** the app serves a basic page on localhost

2. **Given** the Flask app factory **When** I inspect the project structure **Then** it follows the Blueprint-based organization defined in the architecture doc (`esb/` package with `models/`, `services/`, `views/`, `templates/`, `static/`, `utils/` directories)

3. **Given** the Alembic migration setup **When** I run `flask db upgrade` **Then** the database schema is initialized (empty, ready for models)

4. **Given** the GitHub Actions CI pipeline **When** code is pushed to the repository **Then** lint, test, and Docker build stages execute

5. **Given** the Makefile **When** I run `make test` **Then** pytest runs the test suite locally

6. **Given** the mutation logging utility in `utils/logging.py` **When** a service function logs a data-changing operation **Then** structured JSON with timestamp, event, user, and data fields is written to STDOUT

7. **Given** the domain exception classes in `utils/exceptions.py` **When** a service raises ESBError, EquipmentNotFound, RepairRecordNotFound, UnauthorizedAction, or ValidationError **Then** the exception hierarchy is properly defined and importable

8. **Given** the base templates (`base.html`, `base_public.html`, `base_kiosk.html`) **When** I render any page **Then** Bootstrap 5 CSS and JS are loaded from bundled local files in `static/`

9. **Given** the `.env.example` file **When** a developer copies it to `.env` **Then** all required environment variables (`DATABASE_URL`, `SECRET_KEY`, `UPLOAD_PATH`, etc.) have documented defaults or placeholders

## Tasks / Subtasks

- [x] Task 1: Initialize Python project structure (AC: #2)
  - [x] 1.1: Create `esb/` package with `__init__.py` containing the Flask app factory (`create_app`)
  - [x] 1.2: Create `esb/config.py` with configuration classes (`DevelopmentConfig`, `TestingConfig`, `ProductionConfig`)
  - [x] 1.3: Create `esb/extensions.py` with Flask extension instances (`db`, `login_manager`, `migrate`, `csrf`)
  - [x] 1.4: Create empty Blueprint modules in `esb/views/` (`equipment.py`, `repairs.py`, `admin.py`, `public.py`, `auth.py`)
  - [x] 1.5: Create empty model packages in `esb/models/__init__.py`
  - [x] 1.6: Create empty service packages in `esb/services/__init__.py`
  - [x] 1.7: Create empty forms package in `esb/forms/__init__.py`
  - [x] 1.8: Create empty slack package in `esb/slack/__init__.py`
  - [x] 1.9: Create `esb/utils/__init__.py`

- [x] Task 2: Implement mutation logging utility (AC: #6)
  - [x] 2.1: Create `esb/utils/logging.py` with `log_mutation(event, user, data)` function
  - [x] 2.2: Configure a dedicated Python logger (`esb.mutations`) that outputs structured JSON to STDOUT
  - [x] 2.3: Mutation log format: `{"timestamp": "ISO8601", "event": "entity.action", "user": "username", "data": {...}}`
  - [x] 2.4: Write unit tests in `tests/test_utils/test_logging.py`

- [x] Task 3: Implement domain exception hierarchy (AC: #7)
  - [x] 3.1: Create `esb/utils/exceptions.py` with `ESBError` base class
  - [x] 3.2: Define subclasses: `EquipmentNotFound`, `RepairRecordNotFound`, `UnauthorizedAction`, `ValidationError`
  - [x] 3.3: Write unit tests in `tests/test_utils/test_exceptions.py`

- [x] Task 4: Implement RBAC decorators (AC: #2)
  - [x] 4.1: Create `esb/utils/decorators.py` with `@role_required(role)` decorator
  - [x] 4.2: Decorator checks `current_user.role` and returns 403 if insufficient
  - [x] 4.3: Role hierarchy: Staff > Technician (Staff can access Technician routes)
  - [x] 4.4: Write unit tests in `tests/test_utils/test_decorators.py`

- [x] Task 5: Implement Jinja2 custom filters (AC: #8)
  - [x] 5.1: Create `esb/utils/filters.py` with date formatting and relative time filters
  - [x] 5.2: Register filters with the Flask app in the app factory

- [x] Task 6: Create base templates with bundled Bootstrap 5 (AC: #8)
  - [x] 6.1: Download Bootstrap 5.3.x CSS and JS bundle to `esb/static/css/` and `esb/static/js/`
  - [x] 6.2: Create `esb/templates/base.html` -- authenticated layout (sticky navbar, Bootstrap, flash messages, footer)
  - [x] 6.3: Create `esb/templates/base_public.html` -- unauthenticated layout (no navbar, minimal chrome)
  - [x] 6.4: Create `esb/templates/base_kiosk.html` -- kiosk layout (no nav, full-width, large fonts, meta refresh 60s)
  - [x] 6.5: Create `esb/static/css/app.css` -- single custom stylesheet (empty/skeleton)
  - [x] 6.6: Create `esb/static/js/app.js` -- single custom JS file (empty/skeleton)
  - [x] 6.7: Create `esb/templates/components/_flash_messages.html` partial
  - [x] 6.8: Create `esb/templates/errors/403.html`, `404.html`, `500.html` error pages

- [x] Task 7: Flask app factory and Blueprint registration (AC: #2)
  - [x] 7.1: Implement `create_app(config_name)` in `esb/__init__.py`
  - [x] 7.2: Initialize all extensions (`db.init_app`, `login_manager.init_app`, `migrate.init_app`, `csrf.init_app`)
  - [x] 7.3: Register all Blueprints with URL prefixes (`/equipment`, `/repairs`, `/admin`, `/public`, `/auth`)
  - [x] 7.4: Register Flask error handlers for 404, 403, 500
  - [x] 7.5: Register Jinja2 custom filters
  - [x] 7.6: Create a basic index route that redirects to a placeholder "health" page

- [x] Task 8: Alembic/Flask-Migrate setup (AC: #3)
  - [x] 8.1: Initialize Flask-Migrate in the app factory via extensions.py
  - [x] 8.2: Generate initial (empty) migration with `flask db init` and `flask db migrate`
  - [x] 8.3: Verify `flask db upgrade` creates empty schema (tested with SQLite)

- [x] Task 9: Docker and Docker Compose configuration (AC: #1)
  - [x] 9.1: Create `Dockerfile` (Python 3.14-slim base, Gunicorn entrypoint, production-ready)
  - [x] 9.2: Create `docker-compose.yml` with `app`, `db` (MySQL 8.4), and `worker` containers
  - [x] 9.3: Configure volumes: `mysql_data` (named volume), `./uploads` (bind mount)
  - [x] 9.4: Configure `app` to depend on `db` with health check
  - [x] 9.5: Worker container: same image, different entrypoint (`flask worker run` placeholder)

- [x] Task 10: Environment configuration (AC: #9)
  - [x] 10.1: Create `.env.example` with all variables documented: `DATABASE_URL`, `SECRET_KEY`, `UPLOAD_PATH`, `UPLOAD_MAX_SIZE_MB`, `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `STATIC_PAGE_PUSH_METHOD`, `STATIC_PAGE_PUSH_TARGET`
  - [x] 10.2: Integrate `python-dotenv` for local development `.env` loading

- [x] Task 11: Project metadata and dependencies (AC: #5)
  - [x] 11.1: Create `pyproject.toml` with project metadata and dependencies
  - [x] 11.2: Create `requirements.txt` (pinned production dependencies)
  - [x] 11.3: Create `requirements-dev.txt` (pytest, ruff, etc.)

- [x] Task 12: Makefile for local development commands (AC: #5)
  - [x] 12.1: Create `Makefile` with targets: `setup`, `db-up`, `migrate`, `run`, `worker`, `test`, `test-e2e`, `lint`, `docker-build`, `docker-up`

- [x] Task 13: GitHub Actions CI pipeline (AC: #4)
  - [x] 13.1: Create `.github/workflows/ci.yml`
  - [x] 13.2: Stages: checkout, Python setup, install dependencies, lint, pytest (with MySQL service container), Docker build
  - [x] 13.3: Playwright stage can be placeholder (no e2e tests yet)

- [x] Task 14: Test infrastructure (AC: #5)
  - [x] 14.1: Create `tests/conftest.py` with app factory fixture, test DB setup/teardown, test client
  - [x] 14.2: Create directory structure: `tests/test_models/`, `tests/test_services/`, `tests/test_views/`, `tests/test_utils/`, `tests/e2e/`
  - [x] 14.3: Write smoke tests: app starts, health endpoint responds, blueprints registered
  - [x] 14.4: Write tests for mutation logging utility (done in Task 2)
  - [x] 14.5: Write tests for domain exception hierarchy (done in Task 3)
  - [x] 14.6: Write tests for RBAC decorators (done in Task 4)

- [x] Task 15: Git configuration (AC: #2)
  - [x] 15.1: Update `.gitignore` for Python/Flask project (venv, __pycache__, .env, uploads/, *.pyc, instance/)

## Dev Notes

### Architecture Compliance

**CRITICAL -- Follow these patterns exactly:**

- **App Factory Pattern:** `create_app(config_name)` in `esb/__init__.py`. All extensions initialized via `ext.init_app(app)`. Never create extension instances inside the factory.
- **Blueprint Organization:** 5 blueprints (`equipment`, `repairs`, `admin`, `public`, `auth`) registered with URL prefixes. Each blueprint is a single Python file in `esb/views/`.
- **Service Layer:** Business logic goes in `esb/services/`. Views are thin -- parse input, call service, render output. **No business logic in views or models.** Dependency flow: `views -> services -> models`. Never reverse.
- **Extension Instances in extensions.py:** `db = SQLAlchemy()`, `login_manager = LoginManager()`, `migrate = Migrate()`, `csrf = CSRFProtect()`. All in `esb/extensions.py`, imported by other modules as needed.
- **Configuration Classes:** `esb/config.py` with `DevelopmentConfig`, `TestingConfig`, `ProductionConfig` classes. All inherit from a base `Config` class. 12-factor: all settings from environment variables via `os.environ.get()`.

### Technical Stack -- Exact Versions

| Component | Package | Version | Notes |
|-----------|---------|---------|-------|
| Python | python | 3.14.x | Use `python:3.14-slim` Docker image |
| Web framework | Flask | 3.1.x (latest: 3.1.2) | App factory pattern |
| ORM | Flask-SQLAlchemy | 3.1.x | Session scoped to app context |
| Migrations | Flask-Migrate | 4.x | Auto-enables `compare_type=True` and `render_as_batch=True` |
| Auth/Sessions | Flask-Login | 0.7.x | Session management |
| Forms/CSRF | Flask-WTF | 1.2.x | CSRF protection on all forms |
| Password hashing | Werkzeug | Built-in | `generate_password_hash` / `check_password_hash` |
| WSGI Server | Gunicorn | Latest | 2-4 workers default |
| Database | MySQL | 8.4.x LTS | Docker image `mysql:8.4` |
| CSS Framework | Bootstrap | 5.3.x (latest: 5.3.8) | Bundled locally, NO CDN |
| MySQL driver | PyMySQL or mysqlclient | Latest | For SQLAlchemy MySQL connection |

**IMPORTANT -- Gunicorn/Python 3.14 Compatibility:**
Gunicorn may not yet officially support Python 3.14. If compatibility issues arise during Docker build or runtime, the developer should:
1. First try the latest Gunicorn release
2. If that fails, temporarily pin Python to 3.13.x in the Dockerfile until Gunicorn catches up
3. Document the version decision in a comment in `Dockerfile`

### File Structure Requirements

Create this exact directory structure. Do NOT add files beyond what's listed here unless required by a specific task:

```
equipment-status-board/
  Makefile
  pyproject.toml
  requirements.txt
  requirements-dev.txt
  .env.example
  .gitignore (update existing)
  Dockerfile
  docker-compose.yml
  .github/
    workflows/
      ci.yml
  esb/
    __init__.py              # App factory
    config.py                # Configuration classes
    extensions.py            # Extension instances
    models/
      __init__.py
    services/
      __init__.py
    views/
      __init__.py            # Blueprint registration helper
      equipment.py           # Stub blueprint
      repairs.py             # Stub blueprint
      admin.py               # Stub blueprint
      public.py              # Stub blueprint
      auth.py                # Stub blueprint
    forms/
      __init__.py
    slack/
      __init__.py
    templates/
      base.html
      base_public.html
      base_kiosk.html
      components/
        _flash_messages.html
      errors/
        403.html
        404.html
        500.html
    static/
      css/
        bootstrap.min.css    # Bootstrap 5.3.x
        app.css              # Single custom stylesheet
      js/
        bootstrap.bundle.min.js  # Bootstrap 5.3.x JS bundle
        app.js               # Single custom JS file
      img/                   # Empty dir (logo later)
      qrcodes/               # Empty dir (generated QR codes later)
    utils/
      __init__.py
      decorators.py          # @role_required
      logging.py             # Mutation logger
      exceptions.py          # ESBError hierarchy
      filters.py             # Jinja2 custom filters
  tests/
    conftest.py
    test_models/
    test_services/
    test_views/
    test_utils/
      test_logging.py
      test_exceptions.py
      test_decorators.py
    test_slack/
    e2e/
      conftest.py
  migrations/                # Generated by Flask-Migrate init
```

### Naming Conventions

**Database:** Tables plural, snake_case. Columns snake_case. Foreign keys `{table_singular}_id`. Booleans `is_`/`has_` prefix. Timestamps `created_at`/`updated_at` in UTC.

**Python:** PEP 8. Modules snake_case. Classes PascalCase. Functions/variables snake_case. Constants UPPER_SNAKE_CASE.

**Routes:** Lowercase with hyphens. Resource-oriented nouns. Blueprint prefixes: `/equipment/`, `/repairs/`, `/admin/`, `/public/`, `/auth/`.

**Templates:** snake_case. Partials prefixed with underscore. Per-blueprint directories.

### Mutation Logging Format

```json
{
  "timestamp": "2026-02-14T14:30:00Z",
  "event": "entity.action",
  "user": "username_or_system",
  "data": { ... }
}
```
Event naming: `{entity}.{action}` in snake_case. Actions: `created`, `updated`, `deleted`, `status_changed`, `archived`.

### Domain Exception Hierarchy

```python
class ESBError(Exception):
    """Base exception for all ESB errors."""

class EquipmentNotFound(ESBError):
    pass

class RepairRecordNotFound(ESBError):
    pass

class UnauthorizedAction(ESBError):
    pass

class ValidationError(ESBError):
    pass
```

### RBAC Decorator Pattern

```python
from functools import wraps
from flask import abort
from flask_login import current_user

ROLE_HIERARCHY = {'staff': 2, 'technician': 1}

def role_required(role):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if ROLE_HIERARCHY.get(current_user.role, 0) < ROLE_HIERARCHY.get(role, 0):
                abort(403)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
```

### Docker Compose Topology

```yaml
services:
  app:
    build: .
    ports: ["5000:5000"]
    depends_on:
      db:
        condition: service_healthy
    env_file: .env
    volumes:
      - ./uploads:/app/uploads

  db:
    image: mysql:8.4
    environment:
      MYSQL_ROOT_PASSWORD: ...
      MYSQL_DATABASE: esb
    volumes:
      - mysql_data:/var/lib/mysql
    healthcheck:
      test: ["CMD", "mysqladmin", "ping", "-h", "localhost"]
      interval: 10s
      retries: 5

  worker:
    build: .
    command: flask worker run
    depends_on:
      db:
        condition: service_healthy
    env_file: .env

volumes:
  mysql_data:
```

### Configuration Classes Pattern

```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-change-me')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:password@localhost/esb')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_PATH = os.environ.get('UPLOAD_PATH', 'uploads')
    UPLOAD_MAX_SIZE_MB = int(os.environ.get('UPLOAD_MAX_SIZE_MB', '500'))
    PERMANENT_SESSION_LIFETIME = 43200  # 12 hours in seconds

class DevelopmentConfig(Config):
    DEBUG = True

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    DEBUG = False
```

### Base Template Structure

**base.html:** Authenticated layout
- Bootstrap CSS/JS from bundled local files
- Sticky top navbar with role-appropriate links
- Flash messages partial include
- Content block
- Footer

**base_public.html:** Unauthenticated layout
- Bootstrap CSS/JS from bundled local files
- No navbar, minimal chrome
- Content block

**base_kiosk.html:** Kiosk layout
- Bootstrap CSS/JS from bundled local files
- No nav, no footer
- Full-width, large fonts
- `<meta http-equiv="refresh" content="60">`
- Content block

### Error Handling Pattern

Register error handlers in app factory:
```python
@app.errorhandler(404)
def not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

@app.errorhandler(500)
def internal_error(e):
    return render_template('errors/500.html'), 500
```

### Testing Strategy

- **Test DB:** Use SQLite in-memory for unit/integration tests (`TestingConfig`)
- **Fixtures:** App factory, test client, authenticated client helpers in `tests/conftest.py`
- **Smoke tests:** App starts, health endpoint responds 200, all blueprints registered
- **Utility tests:** Mutation logger outputs correct JSON, exceptions are properly defined, RBAC decorator enforces roles

### Project Structure Notes

- This is a greenfield project. The repo currently contains only BMAD planning artifacts, README, LICENSE, and .gitignore.
- No existing source code, no existing dependencies, no existing Docker configuration.
- The developer must create everything from scratch following the architecture document precisely.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md#Selected Stack: Flask 3.1.x with Extensions]
- [Source: _bmad-output/planning-artifacts/architecture.md#Structure Patterns - Project Organization]
- [Source: _bmad-output/planning-artifacts/architecture.md#Infrastructure & Deployment]
- [Source: _bmad-output/planning-artifacts/architecture.md#Implementation Patterns & Consistency Rules]
- [Source: _bmad-output/planning-artifacts/architecture.md#Naming Patterns]
- [Source: _bmad-output/planning-artifacts/epics.md#Story 1.1: Project Scaffolding & Docker Deployment]
- [Source: _bmad-output/planning-artifacts/prd.md#System & Operations]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Design System Foundation]
- [Source: _bmad-output/planning-artifacts/ux-design-specification.md#Component Implementation Strategy]

## Dev Agent Record

### Agent Model Used
Claude Opus 4.6

### Debug Log References
- Fixed mutation logger: kept `propagate = False` (correct for production), tests use custom _CaptureHandler instead of caplog
- Fixed ruff `target-version = "py314"` not supported (changed to `py313`)
- Added placeholder `user_loader` to app factory to fix Flask-Login error on error page rendering

### Code Review Fixes Applied
- **H1**: Rewrote RBAC decorator tests to verify actual HTTP 200/403 responses via test client with mocked current_user
- **H2**: Added 16 tests for Jinja2 custom filters (format_date, format_datetime, relative_time, register_filters)
- **H3**: Restored mutation logger `propagate = False`; tests use custom _CaptureHandler instead of caplog
- **M1**: Replaced deprecated `FLASK_ENV=development` with `FLASK_DEBUG=1` in .env.example
- **M2**: Removed unused MySQL service container from CI test job
- **M3**: Moved inline kiosk CSS to `app.css` with `.kiosk-body` class
- **M4**: Changed error templates (403/404/500) to extend `base_public.html` to avoid `current_user` dependency during DB errors

### Completion Notes List
- All 15 tasks complete, 55 tests passing, ruff lint clean
- Bootstrap 5.3.8 bundled locally (CSS + JS bundle)
- Flask-Login 0.6.3 installed (0.7.x not yet available)
- Alembic initialized but no migration versions yet (no models defined)
- Docker configuration uses Python 3.14-slim with Gunicorn compatibility note

### File List
- `esb/__init__.py` - App factory (`create_app`)
- `esb/config.py` - Configuration classes
- `esb/extensions.py` - Flask extension instances
- `esb/views/__init__.py` - Blueprint registration helper
- `esb/views/equipment.py` - Equipment blueprint stub
- `esb/views/repairs.py` - Repairs blueprint stub
- `esb/views/admin.py` - Admin blueprint stub
- `esb/views/public.py` - Public blueprint stub
- `esb/views/auth.py` - Auth blueprint stub
- `esb/models/__init__.py` - Models package
- `esb/services/__init__.py` - Services package
- `esb/forms/__init__.py` - Forms package
- `esb/slack/__init__.py` - Slack package
- `esb/utils/__init__.py` - Utils package
- `esb/utils/logging.py` - Mutation logging utility
- `esb/utils/exceptions.py` - Domain exception hierarchy
- `esb/utils/decorators.py` - RBAC decorators
- `esb/utils/filters.py` - Jinja2 custom filters
- `esb/templates/base.html` - Authenticated layout
- `esb/templates/base_public.html` - Public layout
- `esb/templates/base_kiosk.html` - Kiosk layout
- `esb/templates/components/_flash_messages.html` - Flash messages partial
- `esb/templates/errors/403.html` - Forbidden error page
- `esb/templates/errors/404.html` - Not found error page
- `esb/templates/errors/500.html` - Server error page
- `esb/static/css/bootstrap.min.css` - Bootstrap 5.3.8 CSS
- `esb/static/css/app.css` - Custom stylesheet
- `esb/static/js/bootstrap.bundle.min.js` - Bootstrap 5.3.8 JS
- `esb/static/js/app.js` - Custom JavaScript
- `tests/conftest.py` - Test fixtures
- `tests/test_app.py` - Smoke tests
- `tests/test_utils/test_logging.py` - Mutation logging tests
- `tests/test_utils/test_exceptions.py` - Exception hierarchy tests
- `tests/test_utils/test_decorators.py` - RBAC decorator tests
- `tests/test_utils/test_filters.py` - Jinja2 custom filter tests
- `tests/e2e/conftest.py` - E2E test fixtures placeholder
- `Dockerfile` - Production Docker image
- `docker-compose.yml` - Docker Compose config
- `.env.example` - Environment variable documentation
- `pyproject.toml` - Project metadata
- `requirements.txt` - Pinned production dependencies
- `requirements-dev.txt` - Development dependencies
- `Makefile` - Development commands
- `.github/workflows/ci.yml` - CI pipeline
- `.gitignore` - Updated with uploads/
- `migrations/` - Flask-Migrate/Alembic directory
