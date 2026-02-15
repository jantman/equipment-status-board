# CLAUDE.md - Project Intelligence for Claude Code

## Database Migrations

The MariaDB database runs in a Docker container (`docker-compose.yml`). There is no local MySQL/MariaDB installation. To generate or apply Alembic migrations:

1. Ensure the DB container is running: `docker compose up -d db`
2. Get the container's IP: `docker inspect equipment-status-board-db-1 --format '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}'`
3. Run flask db commands with the container IP:

```bash
source venv/bin/activate
DATABASE_URL="mysql+pymysql://root:esb_dev_password@<CONTAINER_IP>/esb" flask db migrate -m "Description"
DATABASE_URL="mysql+pymysql://root:esb_dev_password@<CONTAINER_IP>/esb" flask db upgrade
```

The container IP changes on restart, so always inspect it fresh. The DB port (3306) is **not** mapped to the host.
