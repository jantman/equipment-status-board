# Equipment Status Board (ESB)

*Functional Requirements Document*

Decatur Makers

Draft for Stakeholder Review

## Executive Summary

Decatur Makers is a non-profit makerspace with approximately 600 members who have 24/7 access to the facility. Equipment maintenance is currently handled by one part-time Makerspace Manager and a small team of volunteer Technicians.

The Equipment Status Board (ESB) addresses a critical gap in our member experience: **members currently have no reliable way to know whether equipment is operational before coming to the space**. This leads to wasted trips, frustration, and reduced trust in the organization.

The ESB will provide a centralized system for tracking equipment status, coordinating repairs, and communicating with members—ultimately making the makerspace more reliable and member-friendly.

## Problem Statement

- Members arrive at the space only to discover that the equipment they planned to use is broken or degraded
- No single source of truth exists for equipment status—information is scattered across Slack channels, word of mouth, and handwritten signs
- Volunteer Technicians have difficulty coordinating repair efforts with the Makerspace Manager
- Equipment documentation (manuals, service records, repair history) is not centralized or easily accessible
- Members who notice problems have no easy way to report them

## User Roles

| Role | Who | What They Can Do |
|------|-----|------------------|
| Member | Any of the ~600 paying members | View equipment status; report problems via QR code or Slack; receive Slack notifications |
| Technician | Volunteers with equipment expertise | All Member capabilities plus: create/update repair records; update equipment notes; log in to web interface |
| Staff | 4 paid employees including Makerspace Manager | All Technician capabilities plus: add/edit/remove equipment records; manage parts inventory; manage user accounts |

## Core Functionality

### 1. Equipment Registry

A central database of all equipment in the makerspace, including:

- **Identity:** Unique name (e.g., "SawStop #1"), manufacturer, model, serial number
- **Location:** Area within the space (Woodshop, Lasers, 3D Printers, Metal Shop, etc.)
- **Acquisition info:** Date acquired, vendor, cost, warranty details (if known)
- **Documentation:** Links or uploaded files (operator's manual, service manual, receipts); one can be designated as the "default document"
- **Notes:** Free-form field for tips, tricks, quirks, historical repair information
- **Description:** Human-written summary of what the equipment is and does

### 2. Repair Records

When equipment has a problem, a repair record is created to track it from discovery through resolution:

- **Severity:** "Down" (equipment cannot be used) or "Degraded" (equipment works but with limitations)
- **Status:** New → In Progress → Waiting for Parts → Resolved
- **Description:** Brief summary of the problem
- **Estimated resolution date:** When repair is expected to be complete
- **Notes:** Running log of repair attempts, findings, and updates
- **Audit trail:** All changes are logged with who made them and when

### 3. Spare Parts and Consumables Inventory (Optional)

For each piece of equipment, optionally track:

1. Spare/replacement parts to keep on hand or to expedite future orders: part name, part number, vendor, cost, and purchase links.
2. Consumables: description, purchase link, model, vendor, cost

### 4. Status Dashboard

A real-time display showing all equipment organized by area, intended to be shown on a kiosk screen or projector in the space:

- **Green:** No open repair records—equipment is operational
- **Yellow:** Open repair record with "Degraded" severity
- **Red:** Open repair record with "Down" severity

Each entry shows the estimated resolution date (if applicable) and optionally a QR code linking to the equipment's default documentation.

## Key User Flows

### Member Reports a Problem (via QR Code)

1. Member scans per-machine QR code physically attached to the equipment
2. Browser opens per-machine web page showing any open repair records, owners manual/educational links, and simple form to report a problem
3. Member describes the problem, provides contact info, and optionally uploads photos
4. System creates a new repair record with status "New"
5. Notification is sent to the Area-specific Slack channel

### Member Reports a Problem (via Slack)

Members can also report problems directly via Slack, either through a dedicated channel or Slack App form (depending on plan capabilities). The same information is captured and a repair record is created.

### Technician Updates Repair Status

1. Technician logs into the web interface (or uses Slack, if available)
2. Finds the repair record and updates status, adds notes, or changes estimated resolution date
3. System logs the change with timestamp and user
4. Dashboard updates automatically; Slack notification sent to Area channel if status changed meaningfully

### Member Checks Status Before Visiting

Member views current equipment status via one of: the in-space kiosk display, a Slack channel/bot, or a publicly accessible web page or cloud-hosted status file. (See Open Questions.)

## Slack Integration

Slack is our primary communication tool, though not all members use it. The ESB should integrate with Slack in the following ways:

- **Status notifications:** Post to Area-specific Slack channels when equipment status changes (becomes down, becomes degraded, is fixed, or has a change to estimated resolution date)
- **Problem reporting:** Members should be able to report equipment problems via Slack in addition to QR codes
- **Repair record creation:** Technicians and Staff should be able to create repair records from a private Slack channel (using a Slack App with forms would be ideal, if our plan supports it)
- **Repair record updates:** Technicians and Staff should be able to update repair records from Slack

## Open Questions for Stakeholders

The following questions need input before development can proceed:

### Remote Status Access

How should members access equipment status when not physically in the space? Options include:

- A Slack bot that responds to queries or posts periodic summaries
- A static status page uploaded to a public web server or cloud storage whenever status changes

### Slack Plan Capabilities

Does our current Slack plan support Slack Apps with forms (Workflow Builder)? This affects how we design the Technician/Staff experience for creating and updating repair records, as well as how members can report problems via Slack.

### User Authentication

How should Staff and Technicians authenticate to the web interface? Options include standalone accounts, integration with existing member management system (Neon One), or Slack-based authentication.

### Parts Inventory Priority

Is the spare parts inventory feature essential for initial release, or can it be deferred?

## Success Criteria

We'll know the ESB is successful when:

- Members can reliably check equipment status before visiting the space
- The in-space dashboard accurately reflects current equipment status at all times
- Repair records are created promptly when issues arise (reduced time from problem discovery to documentation)
- Technicians and the Makerspace Manager report improved coordination on repairs
- Equipment documentation is consolidated and accessible

## Constraints and Assumptions

- **No dedicated IT staff:** The system must be maintainable by volunteers with general technology experience
- **On-premises infrastructure:** We have servers in the space; the ESB can run locally without requiring external hosting
- **No public internet exposure:** Internal services are not directly accessible from outside the space; remote access will require a workaround
- **Variable Slack adoption:** Not all members use Slack, so it cannot be the only way to access status information

## Equipment Areas

Equipment is organized into Areas. The current list of Areas is:

- Woodshop
- Lasers
- 3D Printers
- Metal Shop

This list should be stored in a single configurable location so it can be updated over time as the space evolves. Each Area will have a corresponding Slack channel for notifications.

## Out of Scope (For Now)

The following are explicitly not part of this initial effort:

- Equipment reservation/scheduling system
- Member training tracking or certification management (handled by Neon One CRM)
- Financial/accounting integration
- Per-member notification preferences (notifications go to Area-specific channels)
- Automated equipment monitoring or IoT integration

## Next Steps

1. Review this document with Staff and key Technicians
2. Resolve open questions
3. Prioritize features for initial release vs. future phases
4. Begin technical design and development

## Technical Details

The following technical decisions have been made and should guide implementation:

### Behavior

- All incoming requests should be logged in JSON format to STDOUT as early as possible, so that data can be reconstructed from these logs if an application error occurs
- All actions that change data should result in a JSON audit log written to STDOUT

### Configuration

- Area-specific Slack channels already exist and will be provided via application configuration
- The list of Areas should be configurable without code changes

### Deployment

- The application will be deployed as a Docker container
- MySQL will be used as the database backend

### Build and Test

- GitHub Actions will be used for the CI/CD pipeline (build and test)
- Builds and tests must also be runnable locally
- Comprehensive unit tests are required
- Comprehensive Playwright browser tests covering all user flows are required

## Original Background

Decatur Makers is a small non-profit makerspace offering access to equipment and instruction for many maker activities from woodworking, 3D printing, laser engraving/cutting to metal machining and welding. We currently have approximately 600 paying members with 24x7 access to the space and varying levels of experience and engagement. We have four paid Staff members including the Makerspace Manager. Maintenance of tools and equipment is handled by a single part-time employee (the Makerspace Manager) and a handful of volunteer Technicians. One of the key difficulties in our member experience is a lack of clear, up-to-date information on the status of our tools/equipment, estimated date of completion of repairs, and ability of our volunteer Technicians to coordinate repair work with the Makerspace Manager. Our organization has no dedicated IT staff but a small number of volunteers with technology experience, and a few servers physically in the space. We rely heavily on Slack for communication, though Slack usage is not universal among our members.
