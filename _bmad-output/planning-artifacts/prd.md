---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional']
inputDocuments:
  - '_bmad-output/planning-artifacts/product-brief-equipment-status-board-2026-02-08.md'
  - '_bmad-output/brainstorming/brainstorming-session-2026-02-03.md'
  - 'docs/original_requirements_doc.md'
workflowType: 'prd'
documentCounts:
  briefs: 1
  research: 0
  brainstorming: 1
  projectDocs: 0
classification:
  projectType: 'web_app'
  domain: 'general'
  complexity: 'low'
  projectContext: 'greenfield'
---

# Product Requirements Document - equipment-status-board

**Author:** Jantman
**Date:** 2026-02-13

## Success Criteria

### User Success

- **Members check before visiting:** Members develop a habit of checking equipment status (via static page, Slack bot, or kiosk) before making trips to the space. Validated through member surveys and word of mouth. Optional: NewRelic analytics on static page post-MVP.
- **Frictionless problem reporting:** Members who encounter broken equipment report it via QR code or Slack without needing to ask "who do I tell?" -- the path is obvious and takes under 2 minutes.
- **Trust in status accuracy:** Members trust that the status information is current. When the board says "green," they believe it.

### Business Success

- **Reduced status inquiries in Slack:** Fewer "is the X working?" messages in area channels -- the ESB becomes the answer to that question.
- **Repair coordination replaces ad hoc messaging:** The Makerspace Manager uses the Kanban board as her primary coordination tool instead of tracking repairs mentally or through scattered Slack threads.
- **Volunteer time is well-spent:** Technicians report that the repair queue helps them find useful work and that their diagnostic notes prevent duplicated effort.

### Technical Success

- **System stays current:** Equipment status displayed across all channels (kiosk, static page, Slack) accurately reflects the latest known state.
- **Maintainable by volunteers:** The system can be administered, updated, and restarted by volunteers with general technology experience -- no dedicated IT staff required.
- **Reliability is "Monday-fix" grade:** Server downtime is not a crisis. The system is reliable enough for daily use but doesn't require on-call support or HA infrastructure.

### Measurable Outcomes

- Most equipment issues result in a repair record being created (qualitative threshold -- not 100%, but the norm)
- Repair records include diagnostic notes that are useful to the next person
- The Makerspace Manager reports improved visibility into what's broken and what's stuck
- Member surveys indicate awareness of and trust in the status board within 3 months of launch

## Product Scope

### MVP - Minimum Viable Product

- Equipment registry with full field set (name, manufacturer, model, serial, area, documentation, photos)
- Repair records with complete status workflow (New through Resolved/Closed)
- Member-facing QR code pages with problem reporting
- In-space kiosk display (per-area, color-coded, auto-refresh)
- Static status page pushed to cloud hosting on status change
- Role-based experiences (Member: status dashboard, Technician: repair queue, Staff: Kanban)
- Full Slack App integration (notifications, problem reporting, repair record CRUD)
- Local account authentication with role-based access
- Docker deployment with MySQL backend
- CI/CD via GitHub Actions with unit tests and Playwright browser tests

### Growth Features (Post-MVP)

- NewRelic or similar analytics on the static status page
- Parts inventory with stock tracking, low-stock indicators, and ordering workflow
- Consumable-specific routing to broader volunteer pool
- Smart Technician routing based on Area assignments and expertise
- Per-member notification preferences

### Vision (Future)

- Authentication provider integration (Slack OAuth or Neon One SSO)
- Reporting and analytics -- repair time trends, equipment reliability metrics, volunteer contribution tracking
- Automated equipment monitoring or IoT integration

## User Journeys

### Sarah's Journey: The Weekend Woodworker (Member)

**Who she is:** Sarah drives 20 minutes to Decatur Makers 2-3 times per week, primarily using the woodshop. She's not deeply technical and uses Slack intermittently. She's a good community member but won't jump through hoops to do the right thing.

**Opening Scene:** It's Saturday morning. Sarah has a half-built bookshelf project waiting at the space and plans to spend the afternoon on the SawStop and the planer. She's been burned before -- drove over last month only to find the SawStop had a tripped brake cartridge and nobody had replaced it. Wasted trip. She complained in Slack but isn't sure anyone saw it.

**Rising Action:** Before heading out, she pulls up the ESB status page on her phone. Green across the board in Woodshop except the planer -- yellow, "Dust collection hose disconnected, usable with shop vac." She can work with that. She drives over with confidence.

At the space, she's using the SawStop when she notices the fence isn't tracking square. She spots the QR code sticker on the machine, scans it with her phone. The page shows the SawStop is currently green, lists a link to the owner's manual, and has a simple form below. She taps in her name, types "Fence not tracking square -- cuts are off by about 1/8 inch at the end," leaves severity as "Not Sure," and hits submit. Done in 90 seconds. The confirmation tells her it's been posted to #woodshop and #oops on Slack.

**Climax:** Two days later, Sarah's back at the space. She scans the SawStop QR code out of curiosity -- there's a repair record showing Marcus looked at it, adjusted the fence alignment, and confirmed it's cutting true. Green. She doesn't need to ask anyone, track down a Slack message, or wonder. The information is just *there*.

**Resolution:** Checking the status page becomes Sarah's Saturday morning habit. She trusts it. When she encounters problems, she reports them because it's easy and she can see that reports actually lead to fixes. She tells other members about the QR codes.

### Marcus's Journey: The Volunteer Technician

**Who he is:** Marcus is a retired engineer who volunteers a few hours per week at Decatur Makers. He has deep equipment expertise but limited time. He works from his phone while standing in the workshop.

**Opening Scene:** Marcus has a free Tuesday afternoon and wants to put in a couple hours helping the space. In the old days, he'd show up and wander around looking for broken things, or text Dana to ask what needs attention. Half the time he'd start diagnosing something another volunteer had already looked at -- wasted effort.

**Rising Action:** He pulls up the ESB repair queue on his phone. Three open items: the drill press is Down ("motor makes grinding noise, won't start"), the band saw is Degraded ("blade tension adjustment stuck"), and a 3D printer has a "Parts Received" tag -- filament sensor replacement arrived yesterday. He picks the drill press because motors are his thing.

At the space, he opens the repair record on his phone. There's a note from another Technician last week: "Checked power connections, all good. Didn't get further -- suspect motor bearings or controller board." Marcus appreciates not having to repeat that diagnostic work. He digs in, confirms it's the motor controller, and updates the record from his phone: "Motor controller board failed. Need replacement -- see parts list." He sets the status to "Parts Needed," adds a photo of the model number plate, and adds the specific part to the notes.

**Climax:** He spots the 3D printer with "Parts Received" -- the filament sensor is sitting on the bench. Since he's already here, he swaps it in, tests it, and marks that record "Resolved" with a note: "Installed new filament sensor, tested with PLA and PETG, both detect correctly." Two fixes progressed in one visit, zero duplicated effort.

**Resolution:** Marcus checks the repair queue whenever he has free time. His volunteer hours feel productive because he always knows what needs attention, what's already been tried, and where he can make the most impact. His detailed notes become the institutional knowledge that used to exist only in people's heads.

### Dana's Journey: The Makerspace Manager (Staff)

**Who she is:** Dana is the part-time Makerspace Manager. She juggles equipment maintenance alongside running classes, managing the space, and coordinating volunteers. She's the bridge between Technicians doing the work and the organizational resources needed to support them.

**Opening Scene:** Monday morning. Dana used to start her week piecing together what happened over the weekend from scattered Slack messages, texts from Marcus, and sticky notes on machines. Equipment status lived in her head, and things fell through the cracks -- especially parts that needed ordering and repairs that got stuck.

**Rising Action:** She opens the ESB Kanban board. At a glance: two items in "New" (weekend reports from members), one in "Parts Needed" (Marcus's drill press motor controller from Tuesday), one in "Parts Ordered" (laser tube she ordered last week), and the band saw still sitting in "New" from five days ago -- that's been stuck too long.

She clicks into the drill press record, sees Marcus's detailed diagnosis and the part photo. She searches for the motor controller, finds it on the vendor site, orders it, and updates the status to "Parts Ordered" with the order number and expected delivery. For the stuck band saw, she messages Marcus on Slack to see if he can look at it this week.

**Climax:** Thursday, the motor controller arrives. Dana marks it "Parts Received" in the system. Marcus gets a notification, comes in Friday, installs it, and marks it "Resolved." The drill press went from member report to fixed in 10 days, with a clear trail of every step. Dana didn't have to chase anyone or remember anything -- the system surfaced what needed her attention.

**Resolution:** The Monday morning Kanban check replaces Dana's mental checklist. Stuck items are immediately visible by how long they've been in a column. Parts ordering is structured instead of ad hoc. She spends less time tracking status and more time actually managing the space. When the board asks "what's the state of the woodshop?" at a staff meeting, she pulls up the dashboard instead of guessing.

### Journey Requirements Summary

These three journeys reveal distinct capability requirements:

**From Sarah's journey (Member):**
- Public-facing status page accessible remotely (static page + Slack bot)
- QR code equipment pages combining status, documentation, and problem reporting
- Simple problem report form (name, description, severity, optional photo)
- Post-submission confirmation with Slack channel links
- Existing issue display on QR pages to reduce duplicates

**From Marcus's journey (Technician):**
- Sortable/filterable repair queue as default landing page
- Mobile-friendly repair record editing (notes, status, photos from phone)
- Append-only notes log preserving diagnostic history
- Parts identification workflow (Parts Needed status + part details)
- Ability to claim and resolve records efficiently

**From Dana's journey (Staff/Manager):**
- Kanban board with columns by status and visual aging indicators
- Equipment registry management (create, edit, archive)
- Parts ordering workflow (Parts Needed → Parts Ordered → Parts Received)
- User account provisioning and role management
- Area and Slack channel configuration

**Cross-cutting requirements revealed:**
- Multi-channel status delivery (kiosk, static page, Slack, web UI)
- Role-based default views and permissions
- Real-time status updates across all channels
- Slack integration for notifications and two-way interaction
- Photo/video upload support for both reports and repairs

## Web Application Specific Requirements

### Project-Type Overview

The ESB is a traditional multi-page web application with a Python backend and MySQL database, deployed as a Docker container on local infrastructure. The application serves three distinct role-based experiences through server-rendered pages, with a separate static HTML status page pushed to cloud hosting for remote access. No SEO requirements. No real-time/WebSocket requirements -- all dynamic views use polling or manual refresh.

### Technical Architecture Considerations

**Application Architecture:**
- Multi-page application with server-rendered HTML
- Python backend (framework TBD during architecture phase)
- MySQL database
- Docker container deployment on local servers within the makerspace
- No public internet exposure for the main application; remote access via static page and Slack only

**Browser Support:**
- Modern/contemporary browsers only (Chrome, Firefox, Safari, Edge -- current and previous major versions)
- No IE11 or legacy browser support required

**Responsive Design:**
- All authenticated views must work on mobile devices (Technicians work from phones at the bench)
- Kiosk display optimized for large screens with stripped-down layout via URL parameter
- QR code landing pages optimized for mobile-first (phone scanning)

**Performance & Refresh:**
- Kiosk auto-refresh via 60-second polling
- Authenticated views (repair queue, Kanban) use manual refresh or standard page navigation
- Static status page regenerated and pushed on status change events

**Accessibility:**
- Follow best practices (semantic HTML, proper contrast, keyboard navigation)
- Not a primary design driver; no formal WCAG compliance target

### Implementation Considerations

**Skip sections (not applicable):**
- SEO strategy -- internal tool with no public-facing discoverable pages
- Native features -- browser-only, no native app wrappers
- CLI commands -- no command-line interface

**Key implementation factors:**
- Photo/video upload handling on local filesystem (configurable size limit, default 500MB)
- QR code generation for equipment pages
- Static page generation and push to cloud hosting on status change
- Slack App integration (OAuth, event subscriptions, interactive components)
- Role-based access control (Member/Technician/Staff) with local accounts
- All mutation requests logged in JSON to STDOUT for data reconstruction

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Problem-solving MVP -- deliver the complete v1.0 feature set as specified by stakeholders. This is an open-source volunteer project for a 501(c)(3) non-profit makerspace with defined requirements. Scope is driven by organizational needs, not market validation.

**Resource Model:** Volunteer open-source development. No dedicated team or timeline pressure -- quality and completeness over speed.

### MVP Feature Set (v1.0)

**All three user journeys fully supported:**
- Sarah (Member): status checking, QR code reporting, kiosk display, static page
- Marcus (Technician): repair queue, mobile-friendly record updates, diagnostic notes
- Dana (Staff/Manager): Kanban board, equipment registry, user management, parts workflow

**Must-Have Capabilities:**
- Equipment registry with full field set and document/photo management
- Repair records with complete 10-status workflow
- QR code equipment pages with problem reporting
- In-space kiosk display (per-area, color-coded, 60-second auto-refresh)
- Static status page pushed to cloud hosting on status change
- Role-based experiences with distinct default landing pages
- Full Slack App integration (notifications, problem reporting, repair record CRUD via rich forms)
- Local account authentication with role-based access (Member/Technician/Staff)
- Docker deployment with MySQL backend
- CI/CD via GitHub Actions with unit tests and Playwright browser tests
- All mutation requests logged in JSON to STDOUT

### Post-MVP Features

**Phase 2 (Growth):**
- Parts inventory with stock tracking, low-stock indicators, and ordering workflow (data model accommodated from day one)
- Consumable-specific routing to broader volunteer pool
- Smart Technician routing based on Area assignments and expertise
- NewRelic or similar analytics on the static status page
- Per-member notification preferences

**Phase 3 (Vision):**
- Authentication provider integration (Slack OAuth or Neon One SSO)
- Reporting and analytics -- repair time trends, equipment reliability metrics, volunteer contribution tracking
- Automated equipment monitoring or IoT integration

### Risk Mitigation Strategy

**Technical Risks:**
- *Slack App complexity:* The full Slack App (OAuth, event subscriptions, interactive components, rich forms) is the most complex integration. Mitigate by building the web UI first and adding Slack as a parallel interface to the same backend, not a separate system.
- *On-premises deployment:* No cloud dependency for core functionality, but the static page push and Slack integration require outbound internet access. Ensure graceful degradation if internet is unavailable (core app still works on local network).

**Operational Risks:**
- *Volunteer maintainability:* Docker deployment and clear documentation are essential. The system must be restartable and debuggable by someone who didn't build it.
- *Data durability:* MySQL on local servers with no HA. JSON mutation logging to STDOUT provides a data reconstruction path if something goes wrong. Regular database backups should be documented as an operational procedure.

**Adoption Risks:**
- *Member awareness:* QR code stickers on equipment are the primary discovery mechanism. Physical deployment of stickers is a non-technical dependency that must happen for the system to deliver value.
- *Technician buy-in:* The system only works if Technicians actually use it. The Slack integration (meeting them where they already are) is the key adoption lever -- validating why it's in v1.0.

## Functional Requirements

### Equipment Registry

- **FR1:** Staff can create equipment records with name, manufacturer, model, and area assignment (required fields)
- **FR2:** Staff can add optional equipment details including serial number, acquisition date, acquisition source, acquisition cost, warranty expiration, and description
- **FR3:** Staff can upload documents to equipment records with category labels (Owner's Manual, Service Manual, Quick Start Guide, Training Video, Manufacturer Product Page, Manufacturer Support, Other)
- **FR4:** Staff can upload photos and videos to equipment records
- **FR5:** Staff can add external links to equipment records (product page, support, manuals, training materials)
- **FR6:** Staff can edit all fields on equipment records
- **FR7:** Staff can archive equipment (soft delete, full history retained)
- **FR8:** Staff can manage Areas (add, edit, soft delete) with Slack channel mapping
- **FR9:** Staff can configure whether Technicians have edit rights for equipment documentation (global setting or per-individual)
- **FR10:** Technicians can edit equipment documentation when granted permission by Staff

### Repair Records

- **FR11:** Technicians and Staff can create repair records associated with an equipment item
- **FR12:** Members can submit problem reports via QR code page or Slack, which create repair records with status "New"
- **FR13:** Technicians and Staff can update repair record status through the full workflow: New, Assigned, In Progress, Parts Needed, Parts Ordered, Parts Received, Needs Specialist, Resolved, Closed - No Issue Found, Closed - Duplicate
- **FR14:** Technicians and Staff can set severity on repair records (Down, Degraded, Not Sure)
- **FR15:** Technicians and Staff can append notes to repair records with automatic author and timestamp logging
- **FR16:** Technicians and Staff can upload photos and videos to repair records
- **FR17:** Technicians and Staff can set and update an assignee on repair records
- **FR18:** Technicians and Staff can set and update an ETA on repair records
- **FR19:** Technicians and Staff can add free-text specialist description when setting status to Needs Specialist
- **FR20:** The system maintains an append-only audit trail of all changes to repair records
- **FR21:** The system resolves concurrent edits via last-write-wins with detailed audit trail

### Problem Reporting

- **FR22:** Members can report equipment problems via QR code page with required fields (name, description) and optional fields (severity defaulting to "Not Sure", safety risk flag, consumable checkbox, email, photo)
- **FR23:** Members can report equipment problems via Slack forms with the same field set
- **FR24:** The QR code equipment page displays existing open issues before the report form, with messaging to report only if the member's issue isn't already listed
- **FR25:** The system displays a confirmation after problem submission with links to relevant Slack channels (#area and #oops)
- **FR26:** Members can flag a safety risk on problem reports, which is highlighted in all notifications

### Status Display & Member Access

- **FR27:** Anyone can view the in-space kiosk display showing equipment status organized by area with color coding (green/yellow/red) and 60-second auto-refresh
- **FR28:** The kiosk display can be activated via URL parameter with stripped-down navigation
- **FR29:** Anyone can view the public static status page showing a summary of all areas and equipment status
- **FR30:** The system regenerates and pushes the static status page to cloud hosting whenever equipment status changes
- **FR31:** Anyone can view equipment information pages (manuals, training materials, educational links) via QR code or direct link
- **FR32:** The system generates QR codes for each equipment item linking to its equipment page
- **FR33:** "Not Sure" severity displays as yellow (degraded) on all status displays

### Role-Based Experiences

- **FR34:** Members see a status dashboard as their default view (two-tier: summary plus drill-down on internal network)
- **FR35:** Technicians see a sortable and filterable repair queue table as their default landing page (columns: equipment name, severity, area, age, status, assignee)
- **FR36:** Staff see a read-only Kanban board as their default landing page with columns by status, cards ordered by duration in column, and visual aging indicators
- **FR37:** Staff can click through from Kanban cards to full repair records

### Slack Integration

- **FR38:** The system sends notifications to area-specific Slack channels and #oops for configurable trigger events (defaults: new report, resolved, severity change, ETA update)
- **FR39:** The system highlights safety risk flags in Slack notifications
- **FR40:** Members can report equipment problems via Slack App forms
- **FR41:** Technicians and Staff can create repair records via Slack App with rich forms
- **FR42:** Technicians and Staff can update repair records via Slack App (status, notes, severity, assignee, ETA)
- **FR43:** Members can query equipment status via Slack bot
- **FR44:** Staff can configure notification triggers

### User Management & Authentication

- **FR45:** Staff can provision user accounts with username, email, Slack handle, and temporary password
- **FR46:** The system delivers temporary passwords via Slack message, with fallback to visible display for the account creator
- **FR47:** Staff can assign and change user roles (Technician/Staff)
- **FR48:** Staff can reset user passwords
- **FR49:** Users can change their own password
- **FR50:** The system authenticates users via local accounts with an abstracted auth layer for future provider integration
- **FR51:** Authenticated sessions last 12 hours

### System & Operations

- **FR52:** The system logs all mutation requests in JSON to STDOUT for data reconstruction
- **FR53:** The system deploys as a Docker container with MySQL backend
- **FR54:** The system supports CI/CD via GitHub Actions with locally runnable builds and tests
- **FR55:** The system includes comprehensive unit tests and Playwright browser tests covering all user flows

### Stretch Goals (Designed, Not Yet Scheduled)

**Parts Inventory & Stock Management:**

- **FR56:** Staff can maintain a parts catalog per equipment item (part name, part number, vendor, cost, purchase link)
- **FR57:** Staff can track part stock quantities on hand
- **FR58:** Technicians and Staff can decrement part stock when a part is used in a repair
- **FR59:** The system displays low-stock visual indicators with configurable reorder thresholds
- **FR60:** The system supports a parts workflow fork: check stock first, skip to Parts Received if in stock; otherwise proceed through Parts Ordered → Parts Received

**Technician-Area Assignment:**

- **FR61:** Staff can assign Technicians to Areas (many-to-many informational association)
- **FR62:** The system can filter repair queue by Technician's assigned Areas
- **FR63:** The system can route notifications to Technicians based on Area assignments

**Consumable Workflow:**

- **FR64:** The system supports a consumable-specific reporting path that can route to a broader volunteer pool beyond Technicians

**Notification Preferences:**

- **FR65:** Members can configure per-equipment or per-area notification preferences
- **FR66:** The system can send targeted notifications to individual members based on their preferences

**Authentication Providers:**

- **FR67:** The system can authenticate users via Slack OAuth as an alternative to local accounts
- **FR68:** The system can authenticate users via Neon One SSO as an alternative to local accounts

**Reporting & Analytics:**

- **FR69:** Staff can view repair time trend reports (mean time from New to Resolved)
- **FR70:** Staff can view equipment reliability metrics (frequency and duration of issues per equipment)
- **FR71:** Staff can view volunteer contribution tracking (repairs completed, notes added per Technician)

## Non-Functional Requirements

### Performance

- **NFR1:** Web UI pages load within standard web application response times (under 3 seconds on local network)
- **NFR2:** Kiosk display refreshes without visible flicker or layout shift during 60-second polling cycle
- **NFR3:** Static status page generation and push completes within 30 seconds of a status change event
- **NFR4:** The system supports concurrent usage by all active users (up to ~600 members, handful of Technicians/Staff) without degradation

### Security

- **NFR5:** Role-based access control enforced server-side -- unauthenticated users cannot access Technician or Staff functionality
- **NFR6:** Passwords stored using industry-standard hashing (never plaintext or reversible encryption)
- **NFR7:** Session tokens are not predictable or reusable after expiration
- **NFR8:** Public-facing pages (QR code pages, kiosk, static page) do not expose internal system details, user credentials, or administrative functionality
- **NFR9:** No encryption at rest required -- data is not sensitive and the server is on a private local network

### Integration

- **NFR10:** The Slack App integration operates independently from core web UI functionality -- Slack outages do not prevent web-based operations
- **NFR11:** When Slack is unreachable (API errors, network outage), the system queues outbound notifications for delivery when connectivity is restored
- **NFR12:** The static page push mechanism handles cloud hosting unavailability gracefully (retry with backoff, log failures)
- **NFR13:** The Slack App requires a paid Slack plan (Pro or higher)

### Reliability

- **NFR14:** Core application (web UI, database) operates fully on the local network with no internet dependency
- **NFR15:** The system recovers cleanly from restart (Docker container restart, server reboot) without data loss or corrupted state
- **NFR16:** All data-mutating operations are logged to STDOUT in sufficient detail to reconstruct data if the database is corrupted or lost
- **NFR17:** The system does not require high availability infrastructure, monitoring, or on-call support -- "Monday-fix" reliability grade

### Accessibility

- **NFR18:** Follow semantic HTML best practices (proper heading hierarchy, form labels, alt text)
- **NFR19:** Maintain sufficient color contrast for status indicators (green/yellow/red must be distinguishable; do not rely solely on color)
- **NFR20:** Support keyboard navigation for all authenticated workflows
- **NFR21:** No formal WCAG compliance target -- best practices, not certification
