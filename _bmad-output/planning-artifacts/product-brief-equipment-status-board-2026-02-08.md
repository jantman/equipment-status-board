---
stepsCompleted: [1, 2, 3, 4, 5, 6]
workflow_completed: true
inputDocuments: ['docs/original_requirements_doc.md', '_bmad-output/brainstorming/brainstorming-session-2026-02-03.md']
date: 2026-02-08
author: Jantman
---

# Product Brief: equipment-status-board

## Executive Summary

The Equipment Status Board (ESB) is an on-premises web application purpose-built for Decatur Makers, a non-profit makerspace with approximately 600 members who have 24/7 facility access. The ESB solves a critical gap in the member experience: there is currently no reliable way for members to know whether equipment is operational before visiting the space. Status information is scattered across Slack channels, word of mouth, and handwritten signs -- leading to wasted trips, frustration, and reduced trust in the organization.

The ESB provides a centralized system for tracking equipment status, coordinating repairs between the part-time Makerspace Manager and volunteer Technicians, consolidating equipment documentation, and communicating with members through multiple channels (in-space kiosk displays, a public static status page, QR code-driven equipment pages, and a full-featured Slack App). It is designed to be maintainable by volunteers with general technology experience, with no dedicated IT staff required.

---

## Core Vision

### Problem Statement

Decatur Makers members arrive at the space only to discover that the equipment they planned to use is broken or degraded. No single source of truth exists for equipment status. Volunteer Technicians have difficulty coordinating repair efforts with the Makerspace Manager -- there is no structured way to track what's broken, who's working on it, what's been tried, or what parts are needed. Equipment documentation (manuals, service records, repair history) is not centralized or easily accessible. Members who notice problems have no easy way to report them.

### Problem Impact

- **Members** waste time and travel when equipment they planned to use is unavailable, eroding trust in the organization
- **The Makerspace Manager** lacks operational visibility -- no way to see at a glance what's broken, what's stuck, or where to direct volunteer effort
- **Volunteer Technicians** show up wanting to help but don't know what needs attention, what's already been tried, or whether parts have been ordered
- **The organization** loses member goodwill and equipment sits broken longer than necessary due to coordination failures

### Why Existing Solutions Fall Short

Current approaches are fragmented and informal:
- **Slack channels**: Messages get buried, not all members use Slack, no structured tracking from problem to resolution
- **Word of mouth**: Unreliable, doesn't scale, depends on talking to the right person
- **Handwritten signs**: Easy to miss, not removed when problems are fixed, no remote visibility
- **Institutional memory**: A few people "just know" what's broken, but that knowledge isn't shared or preserved

Off-the-shelf alternatives don't fit the makerspace context. Enterprise CMMS platforms (e.g., UpKeep, Fiix) are complex and expensive overkill for a volunteer-run organization. Generic status pages (e.g., Statuspage.io) are designed for SaaS services, not physical equipment with multi-step repair workflows involving parts ordering and volunteer coordination.

### Proposed Solution

A purpose-built web application that provides:
- A **centralized equipment registry** with documentation, status, and repair history
- A **structured repair workflow** tracking problems from discovery through resolution, with statuses that mirror real-world diagnostic outcomes (New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved)
- A **public-facing status dashboard** (kiosk display, static web page, Slack bot) so members can check equipment status before visiting
- **QR code-driven equipment pages** that serve as the physical-digital bridge -- scan to report a problem, check status, or access manuals and training materials
- A **full Slack App integration** for problem reporting, repair record management, and status notifications
- **Role-based experiences** tailored to each user type: Members see at-a-glance status, Technicians see a prioritized repair queue, Staff see a Kanban overview of all open work

### Key Differentiators

- **Built for the makerspace model**: Designed around volunteer Technicians, a part-time Manager, and a community that communicates via Slack -- not an enterprise maintenance team
- **Physical-digital bridge via QR codes**: Every piece of equipment becomes a gateway to status, documentation, and problem reporting with a single scan
- **Slack as a first-class interface**: Full two-way integration meets the community where they already communicate, without requiring Slack for access
- **On-premises and volunteer-maintainable**: Runs on local servers inside the space, deployed as a Docker container, with no cloud dependency for core functionality and no dedicated IT staff required
- **Structured yet lightweight workflow**: Repair statuses reflect how volunteers actually work (show up, diagnose, maybe need parts, maybe need a specialist) without imposing enterprise-grade process overhead

---

## Target Users

### Primary Users

**Member (~600 people)**

*Persona: Sarah -- Weekend woodworker, 2-3 visits per week*

Sarah drives 20 minutes to the makerspace and primarily uses the woodshop. She's not deeply technical and uses Slack intermittently. Her core need is knowing whether equipment is available before she makes the trip. She also wants a frictionless way to report problems when she encounters them -- she's a good community member but won't jump through hoops to file a report.

- **Motivations:** Reliable access to working equipment; not wasting trips; contributing to the community by reporting issues
- **Frustrations today:** No way to check status remotely; arrives to find equipment broken; doesn't know who to tell or how
- **Success with ESB:** Checks status page before every visit; scans QR codes to access manuals and report problems; trusts the information is current and accurate

**Volunteer Technician (handful of people)**

*Persona: Marcus -- Retired engineer, volunteers a few hours per week*

Marcus has deep equipment expertise but limited time. He wants to make the most of his volunteer hours -- see what needs fixing, pick something in his wheelhouse, and leave good documentation so the next person can continue where he left off. He works from his phone while standing in the workshop.

- **Motivations:** Using his skills to help the community; efficient use of volunteer time; solving problems and seeing results
- **Frustrations today:** Doesn't know what needs attention until he shows up; repeats diagnostic work others already tried; can't easily communicate findings to the Manager or other Technicians
- **Success with ESB:** Checks the repair queue when he has free time; updates records from his phone mid-repair; his diagnostic notes prevent duplicated effort; the parts he identifies get ordered promptly by Staff

**Staff / Makerspace Manager (4 people)**

*Persona: Dana -- Part-time Makerspace Manager*

Dana juggles equipment maintenance alongside running classes, managing the space, and coordinating volunteers. She needs the operational big picture at a glance: what's broken, what's stuck, what needs her action to unblock (ordering parts, assigning specialists, provisioning accounts). She's the bridge between Technicians doing the work and the organizational resources needed to support them.

- **Motivations:** Keeping equipment operational; supporting volunteer Technicians effectively; spending less time tracking status and more time managing the space
- **Frustrations today:** No visibility into repair status across areas; relies on Slack messages and memory to track what's broken; parts ordering is ad hoc; can't easily see what's been stuck the longest
- **Success with ESB:** Monday morning Kanban check replaces her mental checklist; stuck items are immediately visible; parts ordering workflow is structured; Technician coordination happens through the system rather than scattered Slack threads

### Secondary Users

N/A -- All user segments interact directly with the system. There are no passive or indirect users that meaningfully affect product design.

### User Journeys

**Sarah (Member):**
- **Discovery:** Sees QR code stickers on equipment; hears about ESB through Slack or other members; finds link on makerspace website
- **Onboarding:** Scans a QR code out of curiosity; bookmarks the status page
- **Core usage:** Checks status page from home before visiting; scans QR codes at machines to access manuals; reports problems when found
- **Success moment:** Checks status Saturday morning, sees SawStop is degraded ("dust collection not working"), decides that's fine for her project, drives over with confidence
- **Long-term:** Checking status becomes habit before every visit; trusts the information is current

**Marcus (Volunteer Technician):**
- **Discovery:** Makerspace Manager creates his account and walks him through the system
- **Onboarding:** Logs in, sees the repair queue, picks something in his area of expertise
- **Core usage:** Checks repair queue when he has free time; updates records from his phone as he works; adds diagnostic notes and photos
- **Success moment:** His detailed notes ("tried replacing capacitor, not the issue -- problem is in the motor controller") let another Technician solve it in one visit
- **Long-term:** Repair queue is his go-to; volunteer time feels well-spent because nothing is duplicated

**Dana (Staff/Makerspace Manager):**
- **Discovery:** Stakeholder from day one
- **Onboarding:** Populates equipment registry; sets up Areas and Slack channel mappings; provisions Technician accounts
- **Core usage:** Monday morning Kanban check; orders parts when flagged; assigns specialist repairs; manages users
- **Success moment:** Spots a "Parts Received" card that's been waiting 3 days; pings the right Technician; fixed that afternoon
- **Long-term:** Kanban replaces mental checklist; less time tracking status, more time managing the space

---

## Success Metrics

_Deferred -- to be defined after initial deployment based on real usage patterns._

### Business Objectives

N/A -- Non-profit internal tool. Success is measured by adoption and operational improvement, not revenue.

### Key Performance Indicators

N/A -- To be defined post-launch.

---

## MVP Scope

### Core Features

**Equipment Registry**
- Create, edit, archive equipment with all defined fields (name, manufacturer, model, serial, acquisition info, warranty, area assignment)
- Document and link management with category labels (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other)
- Photo/video uploads (local filesystem, configurable size limit, default 500MB)
- Equipment archival (Staff only), full history retained
- Area assignment required; Areas managed in UI (add, edit, soft delete)

**Repair Records**
- Full status workflow: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate
- Severity levels: Down, Degraded, Not Sure (displays as yellow)
- Append-only notes log with author and timestamp
- Photo/video upload for diagnostics
- Assignee field (optional)
- ETA tracking
- Concurrent edits: last write wins with detailed audit trail

**Member-Facing Status & Reporting**
- QR code equipment pages: info link at top, existing issues with "already known" messaging, problem report form below
- Problem report form: name (required), description (required), severity (defaults to Not Sure), safety risk flag, consumable checkbox, email (optional), photo upload (optional)
- Post-submission confirmation with Slack channel links
- Machine-specific information pages (manuals, training materials, educational links)
- In-space kiosk display: per-area grid, color-coded, auto-refresh every 60 seconds, kiosk mode via URL parameter
- Static status page: single page pushed to cloud hosting on status change, summary only, all areas

**Role-Based Experiences**
- Member: public status dashboard with two-tier depth (summary + drill-down on internal network)
- Technician: sortable/filterable repair queue table as default landing page
- Staff: read-only Kanban board with visual aging indicators as default landing page

**Slack Integration (Full Slack App)**
- Outbound notifications to area channels + #oops (configurable triggers; defaults: new report, resolved, severity change, ETA update)
- Safety risk flag highlighted in notifications
- Member problem reporting via Slack forms
- Technician/Staff repair record creation and updates via Slack with rich forms
- Status query bot
- Requires paid Slack plan (Pro or higher)

**User Management & Authentication**
- Local accounts with abstracted auth layer (future provider swap)
- 12-hour session duration
- User provisioning: username, email, Slack handle, temp password (via Slack message or visible to creator)
- Admin-only password reset; users can change own password
- Role assignment (Technician/Staff) changeable by Staff
- Configurable Technician edit rights for equipment documentation (global or per-individual)

**Technical & Operational**
- All mutation requests logged in JSON to STDOUT for data reconstruction
- Docker container deployment with MariaDB backend
- Responsive modern frontend for all device sizes
- Modern browser support only
- Accessibility follows best practices
- GitHub Actions CI/CD; locally runnable builds and tests
- Comprehensive unit tests and Playwright browser tests

### Out of Scope for MVP

- **Parts inventory and stock tracking** -- fully specified in requirements, data model should accommodate from day one, but UI/workflow deferred
- **Consumable-specific workflow** -- uses standard repair workflow for now; may route to broader volunteer pool in future
- **Technician-Area functional assignment** -- informational association stored but no filtering, routing, or notification logic built on it
- **Advanced authentication providers** -- Slack OAuth, Neon One integration deferred; local accounts serve initial needs
- **Equipment reservation/scheduling system**
- **Member training tracking or certification management** (handled by Neon One CRM)
- **Financial/accounting integration**
- **Per-member notification preferences** (notifications go to channels, not individuals)
- **Automated equipment monitoring or IoT integration**

### MVP Success Criteria

- Members actively use the status page and/or Slack bot to check equipment status before visiting
- Repair records are created consistently when equipment issues are discovered
- Technicians use the repair queue and leave diagnostic notes that reduce duplicated effort
- The Makerspace Manager uses the Kanban board as her primary operational coordination tool
- The kiosk displays in each area accurately reflect current equipment status

### Future Vision

- **Parts inventory** with stock tracking, low-stock indicators, and integrated ordering workflow
- **Consumable-specific routing** to a broader volunteer pool
- **Smart Technician routing** based on Area assignments and expertise
- **Authentication provider integration** (Slack OAuth or Neon One SSO)
- **Reporting and analytics** -- repair time trends, equipment reliability metrics, volunteer contribution tracking
- **Per-member notification preferences** for equipment or areas they care about

### Open Questions

1. **Authentication method** -- Local accounts implemented first; final provider TBD pending stakeholder input
2. **Consumable workflow** -- Same as standard repair for now; may diverge in future iteration
