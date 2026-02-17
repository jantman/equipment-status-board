# Administrators Guide

This guide is for technical volunteers responsible for deploying and maintaining the Equipment Status Board. It covers Docker deployment, environment configuration, Slack App setup, and ongoing maintenance.

## Prerequisites

Before you begin, ensure you have:

- **Docker** and **Docker Compose** installed on the server
- **Git** for cloning the repository
- A server or machine on the makerspace local network (or accessible to members)
- A **Slack workspace** with a paid plan (Pro or higher) if you want to use Slack integration

## Installation & Deployment

### 1. Clone the Repository

```bash
git clone https://github.com/jantman/equipment-status-board.git
cd equipment-status-board
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set the required values. See the [Environment Variable Reference](#environment-variable-reference) below for details on each variable.

At minimum, you must change:

- `SECRET_KEY` — Set to a random string for production (e.g., `python3 -c "import secrets; print(secrets.token_hex(32))"`)
- `MARIADB_ROOT_PASSWORD` — Set a strong database password

### 3. Start All Services

```bash
docker compose up -d
```

This starts three containers: the web application, the MariaDB database, and the background notification worker.

### 4. Run Database Migrations

```bash
docker compose exec app flask db upgrade
```

This creates all required database tables.

### 5. Create the First Staff User

```bash
docker compose exec app flask seed-admin <username> <email> --password <password>
```

For example:

```bash
docker compose exec app flask seed-admin admin admin@example.com --password changeme123
```

This creates a user with the Staff role who can then log in and create additional users through the web interface.

### 6. Verify

Open `http://localhost:5000` in a browser (or the server's IP/hostname on port 5000). You should see the status dashboard. Log in with the Staff user you just created.

## Environment Variable Reference

| Variable | Description | Required | Default | Example |
|----------|-------------|----------|---------|---------|
| `SECRET_KEY` | Flask secret key for session signing. Must be random in production. | Yes | `dev-secret-change-me` | `a1b2c3d4e5f6...` (use `python3 -c "import secrets; print(secrets.token_hex(32))"`) |
| `DATABASE_URL` | SQLAlchemy database connection URL. In Docker, the hostname is `db`. | Yes | `mysql+pymysql://root:esb_dev_password@localhost/esb` | `mysql+pymysql://root:yourpassword@db/esb` |
| `MARIADB_ROOT_PASSWORD` | Root password for the MariaDB container. Must match the password in `DATABASE_URL`. | Yes | `esb_dev_password` | `strong-random-password` |
| `UPLOAD_PATH` | Directory for uploaded files (photos, documents). Relative to app root or absolute path. | No | `uploads` | `/app/uploads` |
| `UPLOAD_MAX_SIZE_MB` | Maximum upload file size in megabytes. | No | `500` | `100` |
| `SLACK_BOT_TOKEN` | Slack Bot User OAuth Token. Leave empty to disable Slack integration. | No | _(empty)_ | `xoxb-1234567890-...` |
| `SLACK_SIGNING_SECRET` | Slack Signing Secret for verifying requests from Slack. | No | _(empty)_ | `abc123def456...` |
| `SLACK_OOPS_CHANNEL` | Slack channel for cross-area notifications. Can be set in `.env` (not included in `.env.example` by default). | No | `#oops` | `#equipment-alerts` |
| `STATIC_PAGE_PUSH_METHOD` | How to publish the static status page. Options: `local` (write to directory) or `s3` (upload to S3 bucket via boto3). | No | `local` | `s3` |
| `STATIC_PAGE_PUSH_TARGET` | Target for static page push. For `local`: a directory path. For `s3`: an S3 bucket name. | No | _(empty)_ | `my-status-bucket` |
| `FLASK_APP` | Flask application entry point. Do not change. | No | `esb:create_app` | `esb:create_app` |
| `FLASK_DEBUG` | Enable Flask debug mode. Set to `0` in production. | No | `1` | `0` |
| `AWS_ACCESS_KEY_ID` | AWS access key for S3 static page push. Only needed if `STATIC_PAGE_PUSH_METHOD=s3` and not using an IAM role. | No | _(empty)_ | `AKIAIOSFODNN7EXAMPLE` |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key for S3 static page push. Only needed if `STATIC_PAGE_PUSH_METHOD=s3` and not using an IAM role. | No | _(empty)_ | `wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY` |

!!! warning
    Always set `SECRET_KEY` to a unique random value in production. The default value is insecure and only suitable for development.

!!! warning
    Set `FLASK_DEBUG=0` in production. Debug mode exposes detailed error pages and enables the interactive debugger.

## Docker Services

The application runs as three Docker containers defined in `docker-compose.yml`:

### App Service

The main web application. Runs Flask via Gunicorn with 2 worker processes on port 5000.

- **Image:** Built from the project `Dockerfile` (Python 3.14-slim base)
- **Port:** 5000 (mapped to host)
- **Volume:** `./uploads` bind mount for persistent file storage (uploaded photos and documents)
- **Depends on:** `db` service (waits for healthy database)

### Database Service

MariaDB 12.2.2 database server. Stores all application data.

- **Image:** `mariadb:12.2.2`
- **Volume:** `mariadb_data` named volume for persistent data storage
- **Health check:** Pings the database every 10 seconds to verify availability
- **Port:** Not mapped to host (only accessible from other containers)

### Worker Service

Background notification processor. Polls the database every 30 seconds for pending notifications and delivers them via Slack.

- **Image:** Same as the app service
- **Command:** `flask worker run`
- **Depends on:** `db` service

All three services have a restart policy of `unless-stopped`, meaning they automatically restart after crashes or host reboots (unless explicitly stopped).

### Runtime Dependencies

The application Docker image includes these key Python packages:

- **Flask** — Web framework
- **SQLAlchemy / Flask-SQLAlchemy** — Database ORM
- **PyMySQL** — MariaDB database driver
- **slack-bolt / slack_sdk** — Slack integration (slash commands, modals, events)
- **boto3** — AWS S3 client for static page push (when using `s3` method)
- **qrcode[pil]** — QR code generation for equipment pages
- **gunicorn** — Production WSGI server

## Slack App Configuration

Slack integration is optional — the core web application works without it. If you want Slack commands, notifications, and the status bot, follow these steps.

### 1. Create a Slack App

1. Go to [api.slack.com/apps](https://api.slack.com/apps) and click **Create New App**
2. Choose **From scratch**
3. Name the app (e.g., "Equipment Status Board") and select your workspace

### 2. Configure Bot Token Scopes

Under **OAuth & Permissions**, add these Bot Token OAuth Scopes:

- `chat:write` — Send messages and notifications
- `commands` — Register slash commands
- `users:read` — Look up user information
- `users:read.email` — Look up users by email
- `im:write` — Send direct messages (for temporary password delivery)

### 3. Set Up Slash Commands

Under **Slash Commands**, create four commands. All commands use the same Request URL:

```
https://<your-domain>/slack/events
```

| Command | Description |
|---------|-------------|
| `/esb-report` | Report an equipment problem |
| `/esb-status` | Check equipment status |
| `/esb-repair` | Create a repair record |
| `/esb-update` | Update a repair record |

### 4. Enable Event Subscriptions

Under **Event Subscriptions**:

1. Turn on **Enable Events**
2. Set the Request URL to `https://<your-domain>/slack/events`
3. Under **Subscribe to bot events**, add `message.channels`

### 5. Install the App

1. Go to **Install App** and click **Install to Workspace**
2. Authorize the permissions

### 6. Copy Credentials

After installation:

1. Copy the **Bot User OAuth Token** (starts with `xoxb-`) and set it as `SLACK_BOT_TOKEN` in your `.env`
2. Go to **Basic Information** and copy the **Signing Secret**, set it as `SLACK_SIGNING_SECRET` in your `.env`
3. Restart the app and worker: `docker compose restart app worker`

!!! note
    Slack slash commands and event subscriptions require a publicly accessible URL. If your ESB server is on a private network, you'll need a reverse proxy with a public domain or a tunnel service (e.g., ngrok for testing, Cloudflare Tunnel for production).

## Static Status Page Setup

The static status page provides a lightweight, externally accessible version of the equipment status dashboard. It is regenerated and pushed automatically whenever equipment status changes.

### Configuration

Set the push method via the `STATIC_PAGE_PUSH_METHOD` environment variable:

- **`local`** — Writes the static page to a local directory specified by `STATIC_PAGE_PUSH_TARGET`. Useful for serving from a local web server or shared drive.
- **`s3`** — Uploads the static page to an S3 bucket specified by `STATIC_PAGE_PUSH_TARGET`. Requires AWS credentials configured in the environment (via `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` or an IAM role).

The static page is pushed by the background worker whenever it detects a status change during its polling cycle.

## Ongoing Maintenance

### Viewing Logs

```bash
# Application logs
docker compose logs -f app

# Worker logs (notification delivery)
docker compose logs -f worker

# Database logs
docker compose logs -f db
```

### Restarting Services

```bash
# Restart the web application
docker compose restart app

# Restart the notification worker
docker compose restart worker

# Restart all services
docker compose restart
```

### Applying Updates

```bash
# Pull latest code
git pull

# Rebuild containers
docker compose build

# Restart with new images
docker compose up -d

# Apply any new database migrations
docker compose exec app flask db upgrade
```

### Monitoring the Worker

The background worker processes pending notifications every 30 seconds. It includes retry logic with backoff for failed deliveries. Check the worker logs for:

- Successful notification deliveries
- Failed delivery attempts and retry counts
- Slack API errors (usually indicate an expired or invalid token)

```bash
docker compose logs -f worker
```

### Upload Storage

Uploaded files (equipment photos, documents, diagnostic images) are stored in the `./uploads/` directory, which is bind-mounted into the app container. Monitor disk usage on the host:

```bash
du -sh ./uploads/
```

### Database

MariaDB data is persisted in the `mariadb_data` Docker volume. This volume survives container restarts and `docker compose down`. It is only removed if you explicitly run `docker compose down -v` (which deletes volumes — **do not do this unless you intend to lose all data**).

## Troubleshooting

### App won't start

- Check that `DATABASE_URL` is correct and uses `db` as the hostname (not `localhost`) when running in Docker
- Verify the `db` service is healthy: `docker compose ps`
- Check app logs: `docker compose logs app`

### Slack commands not working

- Verify `SLACK_BOT_TOKEN` and `SLACK_SIGNING_SECRET` are set correctly in `.env`
- Confirm the Request URL (`https://<your-domain>/slack/events`) is reachable from the internet
- Check that the Slack App has the required OAuth scopes
- Check app logs for Slack-related errors: `docker compose logs app | grep -i slack`

### Notifications not delivering

- Verify the worker is running: `docker compose ps worker`
- Check worker logs: `docker compose logs -f worker`
- Confirm `SLACK_BOT_TOKEN` is valid and the bot is installed to the workspace
- Check that notification triggers are enabled in Admin > Config

### Static page not updating

- Verify `STATIC_PAGE_PUSH_METHOD` and `STATIC_PAGE_PUSH_TARGET` are set
- Check that the worker is running (it handles the push)
- For `s3` method: verify AWS credentials and bucket permissions
- For `local` method: verify the target directory exists and is writable
- Check worker logs for push errors
