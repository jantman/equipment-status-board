#!/usr/bin/env python
"""Generate documentation screenshots using Playwright.

Seeds a temporary SQLite database with realistic demo data, starts the Flask
dev server, captures 12 screenshots at various viewports and auth levels,
then updates the docs markdown files to reference the real images.
"""

import os
import subprocess
import sys
import time
from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from urllib.request import urlopen

BASE_DIR = Path(__file__).resolve().parent.parent
DOCS_DIR = BASE_DIR / 'docs'
IMAGES_DIR = DOCS_DIR / 'images'
DB_PATH = Path('/tmp/esb_screenshots.db')
UPLOADS_PATH = Path('/tmp/esb_screenshots_uploads')
PORT = 5199
BASE_URL = f'http://localhost:{PORT}'
PASSWORD = 'screenshot123'
SECRET = 'screenshot-secret-key'

VIEWPORTS = {
    'desktop': {'width': 1280, 'height': 800},
    'mobile': {'width': 390, 'height': 844},
    'widescreen': {'width': 1920, 'height': 1080},
}

# Markdown replacements: file -> ordered list of replacement filenames
MARKDOWN_REPLACEMENTS = {
    'index.md': ['status-dashboard.png'],
    'members.md': [
        'status-dashboard.png',
        'kiosk-display.png',
        'qr-equipment-page-mobile.png',
        'problem-report-form-mobile.png',
    ],
    'technicians.md': [
        'repair-queue-desktop.png',
        'repair-queue-mobile.png',
        'repair-record-detail.png',
    ],
    'staff.md': [
        'kanban-board.png',
        'equipment-detail.png',
        'user-management.png',
        'app-configuration.png',
    ],
}


# ---------------------------------------------------------------------------
# Seed data
# ---------------------------------------------------------------------------

def seed_database():
    """Populate a temporary SQLite database with realistic demo data."""
    # Clean up any previous run
    if DB_PATH.exists():
        DB_PATH.unlink()
    if UPLOADS_PATH.exists():
        import shutil
        shutil.rmtree(UPLOADS_PATH)
    UPLOADS_PATH.mkdir(parents=True, exist_ok=True)

    os.environ['DATABASE_URL'] = f'sqlite:///{DB_PATH}'
    os.environ['SECRET_KEY'] = SECRET
    os.environ['UPLOAD_PATH'] = str(UPLOADS_PATH)

    from esb import create_app
    from esb.extensions import db
    from esb.models.app_config import AppConfig
    from esb.models.area import Area
    from esb.models.equipment import Equipment
    from esb.models.external_link import ExternalLink
    from esb.models.repair_record import RepairRecord
    from esb.models.repair_timeline_entry import RepairTimelineEntry
    from esb.models.user import User

    app = create_app('screenshot')
    now = datetime.now(UTC).replace(tzinfo=None)

    with app.app_context():
        db.create_all()

        # --- Users ---
        admin = User(username='admin', email='admin@decaturmakers.org', role='staff')
        admin.set_password(PASSWORD)
        jsmith = User(username='jsmith', email='jsmith@decaturmakers.org', role='technician',
                      slack_handle='@jsmith')
        jsmith.set_password(PASSWORD)
        mgarcia = User(username='mgarcia', email='mgarcia@decaturmakers.org', role='technician',
                       slack_handle='@mgarcia')
        mgarcia.set_password(PASSWORD)
        db.session.add_all([admin, jsmith, mgarcia])
        db.session.flush()

        # --- Areas ---
        areas = {}
        for name, channel in [
            ('Woodshop', '#woodshop-repairs'),
            ('Metal Shop', '#metalshop-repairs'),
            ('Electronics Lab', '#electronics-repairs'),
            ('Laser / CNC', '#laser-cnc-repairs'),
            ('3D Printing', '#3dprinting-repairs'),
        ]:
            a = Area(name=name, slack_channel=channel)
            db.session.add(a)
            areas[name] = a
        db.session.flush()

        # --- Equipment ---
        equip = {}
        equipment_data = [
            # (name, manufacturer, model, area, serial, description)
            ('SawStop PCS', 'SawStop', 'PCS175-TGP236', 'Woodshop', 'SS-2019-0042',
             '10" professional cabinet saw with flesh-detection safety system'),
            ('DeWalt Planer', 'DeWalt', 'DW735', 'Woodshop', 'DW-2021-1187',
             '13" three-knife two-speed thickness planer'),
            ('Rikon Bandsaw', 'Rikon', '10-326', 'Woodshop', 'RK-2020-0891',
             '14" deluxe bandsaw with fence'),
            ('Dust Collector', 'Jet', 'DC-1100VX-5M', 'Woodshop', 'JT-2018-0234',
             '1.5 HP dust collector with 5-micron bag filter'),
            ('Router Table', 'Bosch', 'RA1171', 'Woodshop', 'BS-2022-0567',
             'Benchtop router table with router'),
            ('Bridgeport Mill', 'Bridgeport', 'Series I', 'Metal Shop', 'BP-1985-4412',
             '2 HP vertical turret milling machine'),
            ('South Bend Lathe', 'South Bend', 'SB1001', 'Metal Shop', 'SB-2017-0098',
             '14" x 40" metal lathe'),
            ('Lincoln MIG Welder', 'Lincoln Electric', 'Power MIG 256', 'Metal Shop', 'LE-2023-0312',
             '250 amp MIG welder for steel and aluminum'),
            ('Horizontal Bandsaw', 'Jet', 'HVBS-712', 'Metal Shop', 'JT-2019-0445',
             '7" x 12" horizontal/vertical bandsaw'),
            ('Rigol Oscilloscope', 'Rigol', 'DS1054Z', 'Electronics Lab', 'RG-2022-1001',
             '50 MHz 4-channel digital oscilloscope'),
            ('Hakko Solder Station', 'Hakko', 'FX-951', 'Electronics Lab', 'HK-2021-0556',
             'Professional soldering station with T15 tips'),
            ('Reflow Oven', 'Puhui', 'T-962A', 'Electronics Lab', 'PH-2023-0088',
             'Infrared IC heater reflow oven for SMD work'),
            ('Epilog Laser 60W', 'Epilog', 'Zing 24', 'Laser / CNC', 'EP-2020-0234',
             '60 W CO2 laser engraver/cutter, 24" x 12" bed'),
            ('Shapeoko CNC', 'Carbide 3D', 'Shapeoko 4 XXL', 'Laser / CNC', 'C3-2022-0789',
             'CNC router with 33" x 17" cutting area'),
            ('K40 Laser', 'Generic', 'K40', 'Laser / CNC', 'K4-2019-0100',
             '40 W CO2 laser cutter with upgraded controller'),
            ('Prusa MK4 #1', 'Prusa Research', 'MK4', '3D Printing', 'PR-2024-0001',
             'FDM printer with input shaping and load cell'),
            ('Prusa MK4 #2', 'Prusa Research', 'MK4', '3D Printing', 'PR-2024-0002',
             'FDM printer with input shaping and load cell'),
            ('Bambu X1C', 'Bambu Lab', 'X1-Carbon', '3D Printing', 'BL-2024-0010',
             'Core XY enclosed printer with AMS'),
        ]

        for name, mfr, model, area_name, serial, desc in equipment_data:
            e = Equipment(
                name=name, manufacturer=mfr, model=model,
                area_id=areas[area_name].id,
                serial_number=serial, description=desc,
                acquisition_date=date(2023, 6, 15),
            )
            db.session.add(e)
            equip[name] = e
        db.session.flush()

        # --- External links (for equipment detail screenshot) ---
        for title, url in [
            ("Owner's Manual (PDF)", 'https://www.epiloglaser.com/assets/downloads/manuals/zing-manual-web.pdf'),
            ('Product Page', 'https://www.epiloglaser.com/laser-machines/zing-laser/'),
            ('Training Video', 'https://www.youtube.com/watch?v=example'),
        ]:
            db.session.add(ExternalLink(
                equipment_id=equip['Epilog Laser 60W'].id,
                title=title, url=url, created_by='admin',
            ))

        # --- Repair records with backdated timestamps ---
        def make_repair(equipment_name, status, severity, description, assignee=None,
                        days_in_column=1, has_safety_risk=False, eta=None,
                        specialist_description=None, timeline_extra=None):
            """Create a repair record with timeline entries and backdated timestamps.

            days_in_column: how many days the repair has been in its *current* status.
            Prior status transitions are placed in the day before that.
            """
            # The final status change happened days_in_column ago
            entered_current = now - timedelta(days=days_in_column)
            # Record was created 1 day before entering current status (or more for longer chains)
            created = entered_current - timedelta(days=1)
            eq = equip[equipment_name]
            r = RepairRecord(
                equipment_id=eq.id,
                status=status,
                severity=severity,
                description=description,
                reporter_name='Walk-in Member',
                reporter_email='member@example.com',
                assignee_id=assignee.id if assignee else None,
                eta=eta,
                has_safety_risk=has_safety_risk,
                specialist_description=specialist_description,
                created_at=created,
                updated_at=now - timedelta(hours=2),
            )
            db.session.add(r)
            db.session.flush()

            # Creation timeline entry
            db.session.add(RepairTimelineEntry(
                repair_record_id=r.id,
                entry_type='creation',
                author_name='Walk-in Member',
                content=description,
                created_at=created,
            ))

            # Status progression timeline entries
            # All prior transitions happen between created and entered_current
            status_progression = {
                'Assigned': ['New'],
                'In Progress': ['New', 'Assigned'],
                'Parts Needed': ['New', 'Assigned', 'In Progress'],
                'Parts Ordered': ['New', 'Assigned', 'In Progress', 'Parts Needed'],
                'Parts Received': ['New', 'Assigned', 'In Progress', 'Parts Needed', 'Parts Ordered'],
                'Needs Specialist': ['New', 'Assigned', 'In Progress'],
                'Resolved': ['New', 'Assigned', 'In Progress'],
            }

            if status in status_progression:
                steps = status_progression[status]
                # Space prior transitions in the 1-day window before entering current status
                prior_window = timedelta(days=1)
                for i, old_status in enumerate(steps):
                    new_status = steps[i + 1] if i + 1 < len(steps) else status
                    # Last entry (transition to current status) happens at entered_current
                    if new_status == status:
                        entry_time = entered_current
                    else:
                        entry_time = created + prior_window * (i + 1) / len(steps)
                    db.session.add(RepairTimelineEntry(
                        repair_record_id=r.id,
                        entry_type='status_change',
                        author_id=assignee.id if assignee else admin.id,
                        author_name=(assignee.username if assignee else 'admin'),
                        old_value=old_status,
                        new_value=new_status,
                        created_at=entry_time,
                    ))

            # Assignee change if assigned
            if assignee:
                db.session.add(RepairTimelineEntry(
                    repair_record_id=r.id,
                    entry_type='assignee_change',
                    author_id=admin.id,
                    author_name='admin',
                    new_value=assignee.username,
                    created_at=created + timedelta(hours=2),
                ))

            # Extra timeline entries
            if timeline_extra:
                for entry in timeline_extra:
                    entry['repair_record_id'] = r.id
                    db.session.add(RepairTimelineEntry(**entry))

            return r

        # Repair 1: Router Table - New (1 day, default aging)
        make_repair('Router Table', 'New', 'Down',
                     'Motor makes grinding noise and stops under load. Smells like burning.',
                     days_in_column=1)

        # Repair 2: Lincoln MIG Welder - Assigned (4 days, warm aging, safety risk)
        make_repair('Lincoln MIG Welder', 'Assigned', 'Down',
                     'Wire feed mechanism jammed. Sparks flying from feed roller area.',
                     assignee=jsmith, days_in_column=4, has_safety_risk=True)

        # Repair 3: Shapeoko CNC - In Progress (7 days, hot aging)
        make_repair(
            'Shapeoko CNC', 'In Progress', 'Down',
            'Z-axis stepper motor losing steps. Cuts are inconsistent depth.',
            assignee=jsmith, days_in_column=7,
            timeline_extra=[
                {'entry_type': 'note', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'content': 'Checked belt tension — seems fine. Suspect stepper driver overheating.',
                 'created_at': now - timedelta(days=5)},
                {'entry_type': 'note', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'content': 'Swapped stepper driver with spare. Running test cuts now.',
                 'created_at': now - timedelta(days=3)},
                {'entry_type': 'note', 'author_id': admin.id, 'author_name': 'admin',
                 'content': 'Ordered replacement stepper driver as backup. Should arrive Friday.',
                 'created_at': now - timedelta(days=1)},
            ],
        )

        # Repair 4: DeWalt Planer - Parts Needed (3 days, warm aging)
        make_repair('DeWalt Planer', 'Parts Needed', 'Degraded',
                     'Snipe on last 2 inches of every board. Infeed/outfeed rollers may need replacement.',
                     assignee=mgarcia, days_in_column=3)

        # Repair 5: South Bend Lathe - Parts Ordered (8 days, hot aging)
        make_repair('South Bend Lathe', 'Parts Ordered', 'Not Sure',
                     'Tailstock alignment off by ~0.003". May need new tailstock barrel.',
                     assignee=mgarcia, days_in_column=8,
                     eta=date.today() + timedelta(days=5))

        # Repair 6: Reflow Oven - Needs Specialist (6 days, hot aging)
        make_repair('Reflow Oven', 'Needs Specialist', 'Degraded',
                     'Temperature profile not matching setpoints. Heating elements may be degraded.',
                     days_in_column=6,
                     specialist_description='Need electronics tech to calibrate PID controller and test heating elements.')

        # Repair 7: Prusa MK4 #2 - In Progress (2 days, default aging)
        make_repair('Prusa MK4 #2', 'In Progress', 'Degraded',
                     'First layer adhesion issues. Possibly needs PINDA probe recalibration.',
                     assignee=jsmith, days_in_column=2)

        # Repair records for Epilog Laser 60W (used in the equipment-detail screenshot
        # to demonstrate the Repair History section)
        make_repair(
            'Epilog Laser 60W', 'Resolved', 'Down',
            'Laser not firing. Replaced tube and realigned mirrors.',
            assignee=jsmith, days_in_column=45,
        )
        make_repair(
            'Epilog Laser 60W', 'Closed - No Issue Found', 'Degraded',
            'Cuts appear inconsistent. On inspection, focus was simply set wrong.',
            assignee=mgarcia, days_in_column=18,
        )
        make_repair(
            'Epilog Laser 60W', 'Resolved', 'Degraded',
            'Exhaust fan rattling. Rebalanced blade and re-secured duct clamps.',
            assignee=jsmith, days_in_column=7,
        )
        make_repair(
            'Epilog Laser 60W', 'In Progress', 'Degraded',
            'Slight drift in X-axis homing. Investigating belt tension.',
            assignee=jsmith, days_in_column=2,
        )

        # Repair 8: Resolved example (for repair detail screenshot with rich timeline)
        resolved_repair = make_repair(
            'Horizontal Bandsaw', 'Resolved', 'Down',
            'Blade keeps drifting to one side. Blade guides need adjustment or replacement.',
            assignee=jsmith, days_in_column=12,
            timeline_extra=[
                {'entry_type': 'note', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'content': 'Inspected blade guides — upper guide bearing is worn out and has play.',
                 'created_at': now - timedelta(days=10)},
                {'entry_type': 'eta_update', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'old_value': '', 'new_value': (date.today() - timedelta(days=5)).isoformat(),
                 'created_at': now - timedelta(days=9)},
                {'entry_type': 'note', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'content': 'Replacement guide bearings arrived. Installing now.',
                 'created_at': now - timedelta(days=3)},
                {'entry_type': 'note', 'author_id': jsmith.id, 'author_name': 'jsmith',
                 'content': 'New bearings installed. Blade tracks perfectly now. Test cuts look great.',
                 'created_at': now - timedelta(days=2)},
            ],
        )

        # --- App config ---
        for key, value in [
            ('tech_doc_edit_enabled', 'true'),
            ('notify_new_report', 'true'),
            ('notify_resolved', 'true'),
            ('notify_severity_changed', 'false'),
            ('notify_eta_updated', 'true'),
        ]:
            db.session.add(AppConfig(key=key, value=value))

        db.session.commit()

        # Grab IDs while still in app context
        ids = {
            'qr_equipment_id': equip['Shapeoko CNC'].id,
            'detail_equipment_id': equip['Epilog Laser 60W'].id,
            'detail_repair_id': resolved_repair.id,
        }

    return ids


# ---------------------------------------------------------------------------
# Server management
# ---------------------------------------------------------------------------

def start_server():
    """Start Flask dev server as a subprocess."""
    env = os.environ.copy()
    env['DATABASE_URL'] = f'sqlite:///{DB_PATH}'
    env['SECRET_KEY'] = SECRET
    env['FLASK_APP'] = 'esb:create_app'
    env['UPLOAD_PATH'] = str(UPLOADS_PATH)
    proc = subprocess.Popen(
        [sys.executable, '-m', 'flask', 'run', '--port', str(PORT)],
        env=env,
        cwd=str(BASE_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return proc


def wait_for_server(timeout=15):
    """Poll the health endpoint until the server is ready."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = urlopen(f'{BASE_URL}/health', timeout=2)
            if resp.status == 200:
                print('  Server is ready.')
                return
        except Exception:
            pass
        time.sleep(0.3)
    raise TimeoutError(f'Server did not become ready within {timeout}s')


# ---------------------------------------------------------------------------
# Screenshot capture
# ---------------------------------------------------------------------------

def login(page, username):
    """Authenticate via the login form."""
    page.goto(f'{BASE_URL}/auth/login')
    page.fill('input[name="username"]', username)
    page.fill('input[name="password"]', PASSWORD)
    page.click('input[type="submit"]')
    page.wait_for_load_state('networkidle')


def capture_screenshots(ids):
    """Capture all 12 screenshots using Playwright."""
    from playwright.sync_api import sync_playwright

    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch()

        # -- 1. Status dashboard (desktop, logged in as staff) --
        print('  Capturing: status-dashboard.png')
        ctx = browser.new_context(viewport=VIEWPORTS['desktop'])
        page = ctx.new_page()
        login(page, 'admin')
        page.goto(f'{BASE_URL}/public/')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'status-dashboard.png'))
        ctx.close()

        # -- 2. Kiosk display (widescreen, no login) --
        print('  Capturing: kiosk-display.png')
        ctx = browser.new_context(viewport=VIEWPORTS['widescreen'])
        page = ctx.new_page()
        page.goto(f'{BASE_URL}/public/kiosk')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'kiosk-display.png'))
        ctx.close()

        # -- 3. QR equipment page (mobile, no login) --
        print('  Capturing: qr-equipment-page-mobile.png')
        ctx = browser.new_context(viewport=VIEWPORTS['mobile'])
        page = ctx.new_page()
        page.goto(f'{BASE_URL}/public/equipment/{ids["qr_equipment_id"]}')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'qr-equipment-page-mobile.png'))

        # -- 4. Problem report form (mobile, scroll to form) --
        print('  Capturing: problem-report-form-mobile.png')
        page.locator('#report-form').scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        page.screenshot(path=str(IMAGES_DIR / 'problem-report-form-mobile.png'))
        ctx.close()

        # -- 5. Repair queue desktop (technician) --
        print('  Capturing: repair-queue-desktop.png')
        ctx = browser.new_context(viewport=VIEWPORTS['desktop'])
        page = ctx.new_page()
        login(page, 'jsmith')
        page.goto(f'{BASE_URL}/repairs/queue')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'repair-queue-desktop.png'))
        ctx.close()

        # -- 6. Repair queue mobile (technician) --
        print('  Capturing: repair-queue-mobile.png')
        ctx = browser.new_context(viewport=VIEWPORTS['mobile'])
        page = ctx.new_page()
        login(page, 'jsmith')
        page.goto(f'{BASE_URL}/repairs/queue')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'repair-queue-mobile.png'))
        ctx.close()

        # -- 7. Repair record detail (technician, desktop) --
        print('  Capturing: repair-record-detail.png')
        ctx = browser.new_context(viewport=VIEWPORTS['desktop'])
        page = ctx.new_page()
        login(page, 'jsmith')
        page.goto(f'{BASE_URL}/repairs/{ids["detail_repair_id"]}')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'repair-record-detail.png'))
        ctx.close()

        # -- 8. Kanban board (staff, desktop) --
        print('  Capturing: kanban-board.png')
        ctx = browser.new_context(viewport=VIEWPORTS['desktop'])
        page = ctx.new_page()
        login(page, 'admin')
        page.goto(f'{BASE_URL}/repairs/kanban')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'kanban-board.png'))

        # -- 9. Equipment detail (staff, desktop) --
        # full_page=True so the Repair History table (below the fold) is visible.
        print('  Capturing: equipment-detail.png')
        page.goto(f'{BASE_URL}/equipment/{ids["detail_equipment_id"]}')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'equipment-detail.png'), full_page=True)

        # -- 10. User management (staff, desktop) --
        print('  Capturing: user-management.png')
        page.goto(f'{BASE_URL}/admin/users')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'user-management.png'))

        # -- 11. App configuration (staff, desktop) --
        print('  Capturing: app-configuration.png')
        page.goto(f'{BASE_URL}/admin/config')
        page.wait_for_load_state('networkidle')
        page.screenshot(path=str(IMAGES_DIR / 'app-configuration.png'))

        ctx.close()
        browser.close()


# ---------------------------------------------------------------------------
# Markdown updates
# ---------------------------------------------------------------------------

def update_markdown_files():
    """Replace placeholder.png references with real screenshot filenames."""
    import re

    for filename, replacements in MARKDOWN_REPLACEMENTS.items():
        filepath = DOCS_DIR / filename
        content = filepath.read_text()

        # Remove <!-- SCREENSHOT: ... --> comment lines
        content = re.sub(r'\n<!-- SCREENSHOT:.*?-->\n', '\n', content)

        # Replace placeholder.png references sequentially
        idx = 0
        for replacement in replacements:
            old = 'placeholder.png'
            pos = content.find(old, idx)
            if pos == -1:
                print(f'  WARNING: Could not find placeholder #{replacements.index(replacement) + 1} in {filename}')
                continue
            content = content[:pos] + replacement + content[pos + len(old):]
            idx = pos + len(replacement)

        filepath.write_text(content)
        print(f'  Updated {filename}')


def cleanup():
    """Remove placeholder image and temporary files."""
    placeholder = IMAGES_DIR / 'placeholder.png'
    if placeholder.exists():
        placeholder.unlink()
        print('  Removed placeholder.png')

    if DB_PATH.exists():
        DB_PATH.unlink()
        print('  Removed temporary database')

    if UPLOADS_PATH.exists():
        import shutil
        shutil.rmtree(UPLOADS_PATH)
        print('  Removed temporary uploads directory')


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print('Step 1/5: Seeding database...')
    ids = seed_database()

    print('Step 2/5: Starting server...')
    proc = start_server()

    try:
        wait_for_server()

        print('Step 3/5: Capturing screenshots...')
        capture_screenshots(ids)

        print('Step 4/5: Updating markdown files...')
        update_markdown_files()

        print('Step 5/5: Cleaning up...')
        cleanup()

    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()

    # Summary
    screenshots = list(IMAGES_DIR.glob('*.png'))
    print(f'\nDone! Generated {len(screenshots)} screenshots:')
    for s in sorted(screenshots):
        print(f'  {s.name}')


if __name__ == '__main__':
    main()
