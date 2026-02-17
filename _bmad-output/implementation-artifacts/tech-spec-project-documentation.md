---
title: 'Project Documentation - README & GitHub Pages User Guides'
slug: 'project-documentation'
created: '2026-02-16'
status: 'implementation-complete'
stepsCompleted: [1, 2, 3, 4]
tech_stack:
  - mkdocs
  - mkdocs-material
  - github-actions
  - github-pages
files_to_modify:
  - README.md
  - LICENSE
  - mkdocs.yml
  - docs/images/placeholder.png
  - docs/index.md
  - docs/members.md
  - docs/technicians.md
  - docs/staff.md
  - docs/administrators.md
  - .github/workflows/docs.yml
  - pyproject.toml
  - requirements-dev.txt
code_patterns:
  - 'MkDocs Material with mkdocs.yml config at project root'
  - 'docs/ directory for markdown source files'
  - 'Image placeholders: ![Alt](images/placeholder.png) with <!-- SCREENSHOT: description --> comments'
  - 'GitHub Actions workflow in .github/workflows/docs.yml separate from CI'
test_patterns:
  - 'mkdocs build --strict to verify build and links'
---

# Tech-Spec: Project Documentation - README & GitHub Pages User Guides

**Created:** 2026-02-16

## Overview

### Problem Statement

The ESB project has completed initial development with zero documentation. Users (members, technicians, staff) and administrators have no guides for using or deploying the system. The README is a single line with no useful information.

### Solution

Create a comprehensive README with project overview, feature highlights, links to detailed docs, and MIT license info. Build a MkDocs (Material theme) documentation site deployed via GitHub Actions to GitHub Pages, with persona-focused user guides for Members, Technicians, Staff, and Administrators. Admin docs target technical volunteers with deployment, configuration, and maintenance content.

### Scope

**In Scope:**
- README rewrite with project description, feature highlights, links to detailed docs, MIT license
- MIT LICENSE file
- MkDocs Material setup with GitHub Actions deployment to GitHub Pages
- High-level intro/overview page
- Member guide (user-guide style: checking status, QR codes, reporting problems, Slack bot)
- Technician guide (repair queue, updating records, adding notes/photos, Slack commands)
- Staff guide (Kanban board, equipment registry, user management, notification config)
- Administrator guide (Docker deployment, env var reference, Slack App setup, basic maintenance)
- Image placeholders with hidden comments describing what screenshots should show

**Out of Scope:**
- Actual screenshots (deferred to automated screenshot generation later)
- Developer/contributor documentation (API docs, code architecture)
- Database backup procedures
- Sphinx or other doc frameworks

## Context for Development

### Codebase Patterns

- Project is a Flask web app for Decatur Makers makerspace (501(c)(3) non-profit, ~600 members with 24/7 access)
- Two authenticated roles: Technician (repairs + equipment view), Staff (full access). "Members" are unauthenticated public users — they do NOT have accounts or log in. Members interact via QR code pages, kiosk display, static status page, and Slack commands.
- Public unauthenticated surfaces: QR code equipment pages, kiosk display, static status page, problem report form
- Slack integration as a first-class interface (slash commands, modals, status bot)
- Docker Compose deployment (app + db + worker containers)
- Documentation should be written for a non-technical to semi-technical audience (members through technical volunteers)

**Route Structure (5 blueprints):**
- `public` blueprint: Status dashboard, kiosk display, QR equipment pages, problem reporting (mostly unauthenticated)
- `auth` blueprint: Login, logout, change password
- `equipment` blueprint: Equipment registry CRUD, document/photo/link management (staff + technician)
- `repairs` blueprint: Repair queue, Kanban board, repair record CRUD (technician + staff)
- `admin` blueprint: User management, area management, app configuration (staff only)

**Slack Commands:**
- `/esb-report` — Report a problem (all users)
- `/esb-status` — Check equipment status (all users)
- `/esb-repair` — Create repair record (technician+)
- `/esb-update <id>` — Update repair record (technician+)

**Role-Based Landing Pages:**
- Member → Status Dashboard (`/public/`)
- Technician → Repair Queue (`/repairs/queue`)
- Staff → Kanban Board (`/repairs/kanban`)

**Environment Variables (12 total, 11 in .env.example):**
- `SECRET_KEY`, `DATABASE_URL`, `MARIADB_ROOT_PASSWORD`
- `UPLOAD_PATH`, `UPLOAD_MAX_SIZE_MB`
- `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, `SLACK_OOPS_CHANNEL` (in config.py, not in .env.example — defaults to `#oops`)
- `STATIC_PAGE_PUSH_METHOD`, `STATIC_PAGE_PUSH_TARGET`
- `FLASK_APP`, `FLASK_DEBUG`

**AppConfig Settings:**
- `tech_doc_edit_enabled` — Allow technicians to edit equipment documentation
- `notify_new_report` — Slack notification on new problem report
- `notify_resolved` — Slack notification when repair resolved
- `notify_severity_changed` — Slack notification on severity change
- `notify_eta_updated` — Slack notification on ETA update

**Docker Services:**
- `app` — Flask via Gunicorn (port 5000), python:3.14-slim
- `db` — MariaDB 12.2.2, data persisted in named volume
- `worker` — Background notification processor (same image, `flask worker run`)

### Files to Reference

| File | Purpose |
| ---- | ------- |
| `_bmad-output/planning-artifacts/prd.md` | Full product requirements with user journeys and feature descriptions |
| `_bmad-output/planning-artifacts/architecture.md` | Architecture decisions, env vars, Docker topology, project structure |
| `_bmad-output/planning-artifacts/epics.md` | Epic and story breakdown with acceptance criteria |
| `_bmad-output/planning-artifacts/ux-design-specification.md` | UX patterns, component designs, responsive behavior |
| `docker-compose.yml` | Docker Compose service definitions (3 services) |
| `.env.example` | Environment variable template (11 vars, plus SLACK_OOPS_CHANNEL in config.py) |
| `Dockerfile` | Python 3.14-slim, gunicorn, 2 workers |
| `Makefile` | 10 dev workflow targets |
| `CLAUDE.md` | Project overview, commands, architecture summary |
| `pyproject.toml` | Python project metadata and dependencies |
| `requirements-dev.txt` | Dev dependencies (pytest, ruff) |

### Technical Decisions

- **MkDocs Material** for documentation framework — Python-native, markdown-based, zero learning curve for contributors
- **GitHub Actions** for automatic deployment to GitHub Pages on push to main
- **Separate docs workflow** from CI — `docs.yml` independent from `ci.yml`
- **Persona-focused structure** — separate pages per user role rather than feature-oriented docs
- **User-guide style** for Members, Technicians, Staff — task-oriented how-to content
- **Technical reference style** for Administrators — deployment, configuration, maintenance
- **Image placeholders** with HTML comments describing intended screenshots for future automation
- **docs/ directory** serves dual purpose: MkDocs source AND existing `original_requirements_doc.md` (excluded from nav)

## Implementation Plan

### Tasks

- [x] Task 1: Update MIT LICENSE file
  - File: `LICENSE` (already exists with copyright "Jason Antman")
  - Action: Verify the existing LICENSE file contains standard MIT license text with copyright holder "Jason Antman". Update the year to 2026 if needed. Do NOT change the copyright holder.
  - Notes: File already exists. This is a verification/update, not a creation.

- [x] Task 2: Add MkDocs dependencies to project
  - File: `pyproject.toml`
  - Action: Add `mkdocs>=1.6` and `mkdocs-material>=9.5` to the `[project.optional-dependencies] dev` list
  - File: `requirements-dev.txt`
  - Action: Add `mkdocs>=1.6` and `mkdocs-material>=9.5` after existing entries
  - Notes: These are dev-only dependencies, not needed in production.

- [x] Task 3: Create MkDocs configuration
  - File: `mkdocs.yml`
  - Action: Create MkDocs config with:
    - `site_name`: "Equipment Status Board Documentation"
    - `site_description`: "User guides and administrator documentation for the Equipment Status Board"
    - `theme`: material with appropriate palette (blue/amber or similar makerspace-friendly colors), features (navigation.tabs, navigation.sections, navigation.top, search.suggest, content.tabs.link)
    - `nav`: Explicit navigation with Home, Members Guide, Technicians Guide, Staff Guide, Administrators Guide
    - `markdown_extensions`: toc (with permalink), admonition, pymdownx.details, pymdownx.superfences, attr_list, md_in_html, tables
  - Notes: Must be created before docs pages since `mkdocs build --strict` needs it. The explicit `nav` list inherently excludes unlisted pages like `original_requirements_doc.md` from navigation. No `exclude_docs` directive needed — the explicit nav handles it.

- [x] Task 3b: Create docs image directory and placeholder image
  - File: `docs/images/placeholder.png`
  - Action: Create the `docs/images/` directory and add a simple placeholder image (e.g., a light gray rectangle with centered text "Screenshot coming soon"). This can be a minimal PNG file. All doc pages reference `images/placeholder.png` for screenshot placeholders.
  - Notes: Required for `mkdocs build --strict` to pass — strict mode fails on missing image references. This must be created before the doc pages (Tasks 4-8) that reference it.

- [x] Task 4: Create documentation overview page
  - File: `docs/index.md`
  - Action: Write the documentation home page with:
    - H1: "Equipment Status Board"
    - Brief project description (what it is, who it's for — Decatur Makers makerspace, ~600 members)
    - "What is the Equipment Status Board?" section explaining the problem it solves (scattered status info, wasted trips, no reliable way to know if equipment works)
    - Feature highlights organized by channel: Web Dashboard, QR Code Equipment Pages, Kiosk Display, Static Status Page, Slack Integration
    - "How to use this documentation" section with brief persona descriptions and links to each guide:
      - Members: checking status, reporting problems
      - Technicians: managing repairs, diagnostics
      - Staff: equipment registry, Kanban, user management
      - Administrators: deployment, configuration, maintenance
    - Status indicator explanation: green (Operational), yellow (Degraded), red (Down) — what each means
    - Image placeholder for status dashboard overview
  - Notes: This is the landing page for the docs site. Should be welcoming and orient users to the right guide. Draw content from PRD executive summary and user journeys.

- [x] Task 5: Create Member user guide
  - File: `docs/members.md`
  - Action: Write task-oriented member guide covering:
    - **Checking Equipment Status**
      - Using the Status Dashboard (web): navigating to the dashboard, reading the area-organized color-coded grid, understanding green/yellow/red indicators
      - Image placeholder for status dashboard
      - Using the Static Status Page (remote): accessing the public URL from anywhere, what information is shown
      - Using the Kiosk Display (in-space): what the large-screen displays show, auto-refresh behavior
      - Image placeholder for kiosk display
    - **Using QR Code Equipment Pages**
      - How to scan: point phone camera at QR code sticker on equipment, browser opens automatically
      - What you see: equipment name, area, large status indicator, issue description if not green
      - Checking known issues: the "Known Issues" section shows problems already being tracked
      - Accessing equipment documentation: manuals, training materials, links via "Equipment Info"
      - Image placeholder for QR code equipment page
    - **Reporting a Problem**
      - When to report: you found something broken or degraded that isn't in "Known Issues"
      - Via QR code page: scroll to report form, fill in name + description (required), optionally set severity, flag safety risk, attach photo
      - Via Slack: use `/esb-report` command, fill out the modal form with same fields
      - What happens after: confirmation page with Slack channel links, repair record created, technicians notified
      - Image placeholder for problem report form
    - **Checking Status via Slack**
      - `/esb-status` — see all areas and equipment status summary
      - `/esb-status [equipment name]` — check a specific piece of equipment
    - **Understanding Status Colors**
      - Green / Operational: no known issues, equipment is working normally
      - Yellow / Degraded: equipment works but has a known issue (or severity is "Not Sure")
      - Red / Down: equipment is not usable
  - Notes: Write in friendly, non-technical language. Assume the reader has never used the system. **Important:** Members are unauthenticated public users — they do NOT have accounts or log in. All member interactions (QR pages, kiosk, static page, problem reporting, Slack bot) work without authentication. Frame the guide accordingly — no "log in" steps, no account setup. The QR code scan is the signature interaction — make it prominent. Draw from PRD Sarah's Journey and UX spec member persona flow.

- [x] Task 6: Create Technician user guide
  - File: `docs/technicians.md`
  - Action: Write task-oriented technician guide covering:
    - **Getting Started**
      - Logging in: navigate to the ESB URL, enter username and password provided by Staff
      - Changing your password: first login with temp password, change via navbar menu
      - Your default view: Repair Queue — no navigation needed
    - **Working with the Repair Queue**
      - Reading the queue: columns (equipment name, severity, area, age, status, assignee), default sort (severity then age)
      - Sorting: click column headers to sort ascending/descending
      - Filtering: use area and status dropdowns to narrow the list
      - Mobile view: on phone, rows display as stacked cards
      - Image placeholder for repair queue (desktop)
      - Image placeholder for repair queue (mobile)
    - **Managing Repair Records**
      - Opening a record: click/tap a row in the queue
      - Reading the timeline: chronological history of notes, status changes, photos — newest first
      - Adding a note: type in the notes field, click Save — your name and timestamp are recorded automatically
      - Uploading diagnostic photos: attach photos from the repair record detail page, shown as thumbnails in the timeline
      - Changing status: select from the status dropdown (New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate)
      - Setting severity: Down (equipment unusable), Degraded (works but impaired), Not Sure
      - Assigning: pick a technician or staff member from the assignee dropdown, or assign to yourself
      - Setting an ETA: use the date picker to indicate when the repair is expected to be complete
      - Batching changes: you can make multiple changes (status + note + assignee) before clicking Save once
      - Image placeholder for repair record detail page
    - **Creating Repair Records**
      - Via web: navigate to Repairs > New, select equipment, fill in details
      - Via Slack: use `/esb-repair` command, fill out the modal
    - **Using Slack Commands**
      - `/esb-report` — Quick problem report (same as member)
      - `/esb-status` — Check equipment status
      - `/esb-repair` — Create a new repair record with full details
      - `/esb-update [id]` — Update an existing repair record (status, notes, severity, assignee, ETA)
    - **Viewing Equipment Details**
      - Equipment registry: browse all equipment, view details, documents, photos, links
      - Editing documentation: if enabled by Staff, you can upload documents, photos, and add links to equipment records
    - **Understanding the Repair Workflow**
      - Brief description of each status and when to use it:
        - New: just reported, not yet assessed
        - Assigned: someone is taking responsibility
        - In Progress: actively being worked on
        - Parts Needed: diagnosis complete, waiting on parts identification/ordering
        - Parts Ordered: parts have been ordered
        - Parts Received: parts are in hand, ready to install
        - Needs Specialist: requires expertise beyond current technician
        - Resolved: repair complete, equipment operational
        - Closed - No Issue Found: investigated, no problem detected
        - Closed - Duplicate: same issue already tracked in another record
  - Notes: Write for someone comfortable with tools and technology but not necessarily software. Emphasize mobile workflows since technicians work from phones at the bench. Draw from PRD Marcus's Journey and UX spec technician persona flow.

- [x] Task 7: Create Staff user guide
  - File: `docs/staff.md`
  - Action: Write task-oriented staff guide covering:
    - **Getting Started**
      - Logging in and your default view: Kanban Board
      - Navigation: Equipment, Kanban, Repairs, Admin, Status links in navbar
    - **Using the Kanban Board**
      - Reading the board: columns represent repair statuses (New through Needs Specialist), Resolved/Closed excluded
      - Card information: equipment name, area, severity indicator, time-in-column
      - Aging indicators: default styling (0-2 days), warm tint (3-5 days), strong indicator (6+ days) — stuck items are visually obvious
      - Taking action: click a card to open the full repair record, make changes there
      - Desktop vs mobile: horizontal scrolling columns on desktop, stacked/accordion on mobile
      - Image placeholder for Kanban board
    - **Managing Equipment**
      - Viewing the registry: Equipment link in navbar, filterable by area
      - Creating equipment: Add Equipment button, fill in name, manufacturer, model, area (required)
      - Editing equipment: click into detail page, Edit button for all fields
      - Adding documentation: upload manuals/documents with category labels (Owner's Manual, Service Manual, Quick Start Guide, Training Video, etc.)
      - Adding photos: upload equipment photos
      - Adding links: external URLs for product pages, support, training materials
      - Archiving equipment: soft-delete that preserves all history
      - Image placeholder for equipment detail page
    - **Managing Areas**
      - Navigate to Admin > Areas
      - Creating areas: name + Slack channel mapping
      - Editing areas: change name or Slack channel
      - Archiving areas: soft-delete, existing equipment retains association
    - **Managing Users**
      - Navigate to Admin > Users
      - User list: username, email, role, status
      - Creating users: username, email, Slack handle, role (Technician or Staff) — system generates temp password
      - Temp password delivery: sent via Slack DM if configured, otherwise displayed on-screen one time
      - Changing roles: change between Technician and Staff from the user list
      - Resetting passwords: generates new temp password with same delivery mechanism
      - Image placeholder for user management page
    - **Configuring the System**
      - Navigate to Admin > Config
      - Technician documentation editing: toggle whether Technicians can edit equipment docs/photos/links
      - Notification triggers: enable/disable which events send Slack notifications
        - New Report: when a member reports a problem
        - Resolved: when a repair is marked resolved
        - Severity Changed: when severity level changes
        - ETA Updated: when an ETA is set or changed
      - Image placeholder for app config page
    - **Working with Repairs**
      - Staff have full access to the Repair Queue (same as Technician view) via Repairs link
      - All repair record management capabilities from the Technician guide apply
      - Staff can also use all Slack commands
    - **Understanding Status**
      - Status Dashboard: accessible via Status link, shows all equipment organized by area with color coding
      - Static Status Page: auto-generated and pushed to cloud hosting whenever status changes — for remote access
  - Notes: Write for the Makerspace Manager persona — organized, task-oriented, juggles multiple responsibilities. Emphasize Kanban as the primary coordination tool. Draw from PRD Dana's Journey and UX spec staff persona flow.

- [x] Task 8: Create Administrator guide
  - File: `docs/administrators.md`
  - Action: Write technical reference guide covering:
    - **Prerequisites**
      - Docker and Docker Compose installed
      - Git for cloning the repository
      - A Slack workspace with a paid plan (Pro or higher) if using Slack integration
      - A server or machine on the makerspace local network
    - **Installation & Deployment**
      - Clone the repository
      - Copy `.env.example` to `.env`
      - Configure environment variables (reference to env var table below)
      - Run `docker compose up -d` to start all services
      - Run initial database migration: `docker compose exec app flask db upgrade`
      - Create the first Staff user: `docker compose exec app flask seed-admin <username> <email> --password <password>`
      - Verify the app is running at `http://localhost:5000`
    - **Environment Variable Reference**
      - Full table of all environment variables with:
        - Variable name
        - Description
        - Required/Optional
        - Default value
        - Example value
      - Variables: SECRET_KEY, DATABASE_URL, MARIADB_ROOT_PASSWORD, UPLOAD_PATH, UPLOAD_MAX_SIZE_MB, SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET, SLACK_OOPS_CHANNEL, STATIC_PAGE_PUSH_METHOD, STATIC_PAGE_PUSH_TARGET, FLASK_APP, FLASK_DEBUG
    - **Docker Services**
      - Overview of three services (app, db, worker) and what each does
      - Volumes: mariadb_data (database persistence), ./uploads (file uploads bind mount)
      - Port mapping: 5000 for the web app
      - Restart policy: unless-stopped on all services
    - **Slack App Configuration**
      - Creating a Slack App in the Slack API dashboard
      - Required Bot Token OAuth scopes: `chat:write`, `commands`, `users:read`, `users:read.email`, `im:write`
      - Setting up slash commands: /esb-report, /esb-status, /esb-repair, /esb-update — all Request URLs point to `https://<your-domain>/slack/events`
      - Enabling Event Subscriptions: Request URL also `https://<your-domain>/slack/events`, subscribe to `message.channels` bot event
      - Note: Slack commands and events require a publicly accessible URL — the on-premises ESB server needs a reverse proxy with a public domain or a tunnel (e.g., ngrok for testing)
      - Installing the app to the workspace
      - Copying Bot Token and Signing Secret to `.env` (SLACK_BOT_TOKEN, SLACK_SIGNING_SECRET)
      - Note: Slack integration is optional — the core web app works without it. Leave SLACK_BOT_TOKEN empty to disable.
    - **Static Status Page Setup**
      - STATIC_PAGE_PUSH_METHOD options: `local` (write to local directory), `s3` (upload to S3 bucket via boto3)
      - Configuring the push target
      - How the static page is triggered (on status changes, via background worker)
    - **Ongoing Maintenance**
      - Viewing logs: `docker compose logs -f app` / `docker compose logs -f worker`
      - Restarting services: `docker compose restart app` / `docker compose restart worker`
      - Applying updates: `git pull`, `docker compose build`, `docker compose up -d`, `docker compose exec app flask db upgrade`
      - Monitoring the worker: the background worker processes notifications every 30 seconds, check logs for delivery failures
      - Upload storage: files stored in `./uploads/` bind mount, monitor disk usage
      - Database: MariaDB data persisted in `mariadb_data` Docker volume
    - **Troubleshooting**
      - App won't start: check DATABASE_URL, verify db service is healthy
      - Slack commands not working: verify SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET, check that the request URL is reachable
      - Notifications not delivering: check worker logs, verify Slack token is valid
      - Static page not updating: check STATIC_PAGE_PUSH_METHOD and STATIC_PAGE_PUSH_TARGET, verify worker is running
  - Notes: Write for technical volunteers who are comfortable with Docker and CLI but didn't build the system. Be explicit about commands — don't assume they'll figure it out. The CLI command for initial admin user is `flask seed-admin <username> <email> --password <password>` (registered in `esb/__init__.py`). Runtime dependencies include `slack-bolt` and `slack_sdk` (Slack integration), `boto3` (S3 static page push), and `qrcode[pil]` (QR code generation) — these are installed automatically via Docker build but should be mentioned so admins understand what's running.

- [x] Task 9: Rewrite README.md
  - File: `README.md`
  - Action: Complete rewrite with:
    - H1: "Equipment Status Board"
    - Tagline/description: 1-2 sentences explaining what ESB is and who it's for
    - Feature highlights section with brief bullet points organized by capability:
      - Equipment Registry & Status Tracking
      - Repair Workflow (10-status lifecycle)
      - QR Code Equipment Pages
      - Kiosk Display
      - Static Status Page
      - Slack Integration (notifications, problem reporting, status queries)
      - Role-Based Access (Member, Technician, Staff)
    - Quick Start section: brief pointer to Administrator guide for deployment
    - Documentation link: link to GitHub Pages docs site
    - Tech stack summary: Python 3.14 / Flask, MariaDB, Docker, Slack Bolt SDK, boto3 (S3), qrcode
    - License section: MIT, link to LICENSE file
  - Notes: Keep the README concise — it's a landing page, not the full docs. Link to the detailed docs site for everything beyond the overview. Do NOT include development setup instructions (that's in CLAUDE.md and is out of scope).

- [x] Task 10: Create GitHub Actions workflow for docs deployment
  - File: `.github/workflows/docs.yml`
  - Action: Create GitHub Actions workflow that:
    - Triggers on push to `main` branch (only when docs files change: `docs/**`, `mkdocs.yml`)
    - Also allows manual trigger (`workflow_dispatch`)
    - Uses `actions/setup-python@v5` with Python 3.x
    - Installs `mkdocs` and `mkdocs-material`
    - Runs `mkdocs build --strict` to verify
    - Deploys to GitHub Pages using `mkdocs gh-deploy --force` (pushes to `gh-pages` branch)
    - Permissions: `contents: write` (needed for pushing to gh-pages branch)
  - Notes: Keep the workflow simple. Uses the `mkdocs gh-deploy` approach (pushes to `gh-pages` branch), NOT the newer `actions/deploy-pages` approach. GitHub Pages must be configured to deploy from the `gh-pages` branch (Settings > Pages > Source: Deploy from a branch > `gh-pages`). Separate from the existing `ci.yml` workflow.

- [x] Task 11: Verify MkDocs build
  - Action: Install mkdocs dependencies and run `mkdocs build --strict` to verify:
    - All pages render without errors
    - All internal links resolve
    - No warnings in strict mode
    - The `original_requirements_doc.md` is excluded from the build
  - Notes: This is the final verification step. Fix any build errors before considering the spec complete.

### Acceptance Criteria

- [x] AC 1: Given the project root, when I look for a LICENSE file, then a valid MIT license file exists with copyright holder "Jason Antman" and year 2026.

- [x] AC 2: Given the project dependencies, when I check `pyproject.toml` and `requirements-dev.txt`, then `mkdocs` and `mkdocs-material` are listed as dev dependencies.

- [x] AC 3: Given the project root, when I look for `mkdocs.yml`, then a valid MkDocs Material configuration exists with navigation pointing to all 5 documentation pages (index, members, technicians, staff, administrators).

- [x] AC 4: Given the MkDocs configuration, when `mkdocs build --strict` is run, then the build succeeds with no errors or warnings.

- [x] AC 5: Given the docs site, when I navigate to the home page, then I see a project overview, feature highlights, and links to all four persona-specific guides.

- [x] AC 6: Given the docs site, when I navigate to the Members guide, then I see task-oriented instructions for checking status (dashboard, static page, kiosk, QR codes), reporting problems (QR page and Slack), and using the Slack status bot, with image placeholders and HTML comments describing intended screenshots.

- [x] AC 7: Given the docs site, when I navigate to the Technicians guide, then I see task-oriented instructions for working with the repair queue, managing repair records (status, notes, photos, assignee, ETA), the full repair workflow with status descriptions, and Slack commands, with image placeholders.

- [x] AC 8: Given the docs site, when I navigate to the Staff guide, then I see task-oriented instructions for the Kanban board (including aging indicators), equipment management, area management, user management (provisioning, roles, password reset), and system configuration (notification triggers, technician permissions), with image placeholders.

- [x] AC 9: Given the docs site, when I navigate to the Administrators guide, then I see technical reference content covering Docker deployment steps, a complete environment variable reference table, Docker service descriptions, Slack App configuration steps, static page setup, ongoing maintenance commands, and troubleshooting tips.

- [x] AC 10: Given the README.md, when I view it on GitHub, then I see a project description, feature highlights, a link to the documentation site, tech stack summary, and MIT license reference.

- [x] AC 11: Given the `.github/workflows/docs.yml`, when changes are pushed to docs files on the main branch, then the workflow triggers, builds the MkDocs site, and deploys to GitHub Pages.

- [x] AC 12: Given the existing `docs/original_requirements_doc.md`, when the MkDocs site is built, then that file is excluded from the navigation and rendered site.

- [x] AC 13: Given any documentation page, when I look for image references, then each image placeholder includes an HTML comment (`<!-- SCREENSHOT: ... -->`) describing what the screenshot should capture for future automation.

- [x] AC 14: Given the `docs/images/` directory, when the MkDocs site is built, then a `placeholder.png` file exists so that image references in doc pages do not cause `mkdocs build --strict` to fail.

- [x] AC 15: Given a documentation page with a broken internal link or missing image, when `mkdocs build --strict` is run, then the build fails with an error identifying the broken reference.

## Additional Context

### Dependencies

- `mkdocs>=1.6` and `mkdocs-material>=9.5` Python packages (dev dependencies only)
- GitHub Pages must be enabled on the repository (Settings > Pages > Source: GitHub Actions or gh-pages branch)
- GitHub Actions available on the repository (already in use for CI)
- No runtime dependencies added — documentation is a build-time artifact

### Testing Strategy

- **Build verification:** `mkdocs build --strict` catches broken links, missing pages, and config errors
- **Manual review:** Visually inspect rendered docs with `mkdocs serve` locally
- **CI integration:** The docs workflow runs `mkdocs build --strict` before deploying, so broken docs never deploy
- **No automated content tests** — documentation correctness is verified by human review

### Notes

- Documentation content draws heavily from existing planning artifacts (PRD user journeys, architecture doc, epics, UX design spec). The dev agent should reference these files for accurate feature descriptions rather than inventing content.
- Image placeholders use the pattern: `![Description](images/placeholder.png)` followed by `<!-- SCREENSHOT: description of what to capture -->` on the next line. This allows future automation to find and replace placeholders. A `docs/images/placeholder.png` file must exist for `mkdocs build --strict` to pass.
- Administrator docs assume the audience is technical volunteers comfortable with Docker and CLI, not dedicated IT staff. Be explicit about commands; don't assume familiarity with the ESB codebase.
- The `docs/original_requirements_doc.md` already exists. The explicit `nav` list in `mkdocs.yml` inherently excludes unlisted pages from navigation. No `exclude_docs` directive needed.
- MIT license: copyright holder is "Jason Antman", year is 2026. LICENSE file already exists — verify/update, do not recreate.
- CLI command for initial admin user: `flask seed-admin <username> <email> --password <password>` (registered in `esb/__init__.py`).
- "Members" are unauthenticated public users — NOT an authenticated role. The RBAC system only has `staff` and `technician` roles. The Member guide should be framed as "for anyone using the space" without login steps.
- Static page push uses `s3` method (via boto3), NOT `scp`. The `.env.example` comment mentioning `scp` is stale relative to the actual code.
- Slack App requires a publicly accessible URL for slash commands and event subscriptions — the on-premises ESB server needs a reverse proxy with a public domain or a tunnel.
