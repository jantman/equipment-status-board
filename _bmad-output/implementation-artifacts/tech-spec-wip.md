---
title: 'Built-in Docs/Help Site'
slug: 'built-in-docs-site'
created: '2026-06-07'
status: 'in-progress'
stepsCompleted: [1]
tech_stack: []
files_to_modify: []
code_patterns: []
test_patterns: []
---

# Tech-Spec: Built-in Docs/Help Site

**Created:** 2026-06-07

**GitHub Issue:** [#58 — Built-in docs/help site](https://github.com/jantman/equipment-status-board/issues/58)

## Overview

### Problem Statement

ESB documentation lives only on the project's GitHub Pages site, which is generic — it can't reference a given installation's actual URLs, Slack channel names, or other deployment-specific values, and there's no way to discover it from inside the running app.

### Solution

Serve the existing `docs/*.md` markdown files at a public `/docs/` route inside the app, rendered server-side with installation-specific config values interpolated, plus an About page (version, GitHub/license/issues/online-docs links). Add a docs link to the header of every non-kiosk page.

### Scope

**In Scope:**

- New public `/docs/` blueprint section: Home, Members, Technicians, Staff, Administrators guides + About page
- Runtime markdown rendering with placeholder interpolation (e.g., base URL, Slack channel, static page URL)
- Header link in `base.html` and `base_public.html` (not `base_kiosk.html`)
- About page: running version, GitHub repo link, license info, GH Pages docs link, report-an-issue link
- Ensuring `docs/*.md` (with any placeholder syntax added) still renders sensibly on the GitHub Pages site
- Shipping the `docs/` content in the Docker image

**Out of Scope:**

- Changing the GH Pages site theme/structure or the mkdocs workflow beyond what placeholder compatibility requires
- Docs search functionality
- Kiosk views
- Editing/CMS capability for docs content

## Context for Development

### Codebase Patterns

(To be filled in Step 2)

### Files to Reference

| File | Purpose |
| ---- | ------- |

### Technical Decisions

- **Content source:** Single source of truth — render the same `docs/*.md` files used by the mkdocs GitHub Pages site at runtime; ship them in the Docker image. No duplicated content.
- **Access:** Fully public, no login required (matches public status dashboard and QR pages).
- **Guides included:** All five (Home/index, Members, Technicians, Staff, Administrators) plus About.
- **About page contents:** running version, GitHub repo link, license info, link to GH Pages docs site, report-an-issue link.

## Implementation Plan

### Tasks

(To be filled in Step 3)

### Acceptance Criteria

(To be filled in Step 3)

## Additional Context

### Dependencies

(To be filled in Step 2)

### Testing Strategy

(To be filled in Step 2/3)

### Notes

(none yet)
