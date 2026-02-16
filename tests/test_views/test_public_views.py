"""Tests for public views (status dashboard)."""


class TestStatusDashboardView:
    """Tests for the status dashboard route."""

    def test_dashboard_renders_for_staff(self, staff_client, make_area, make_equipment):
        """Staff user can access the status dashboard."""
        area = make_area(name='Workshop')
        make_equipment(name='Table Saw', area=area)

        response = staff_client.get('/public/')
        assert response.status_code == 200
        assert b'Equipment Status' in response.data

    def test_dashboard_renders_for_technician(self, tech_client, make_area, make_equipment):
        """Technician user can access the status dashboard."""
        area = make_area(name='Lab')
        make_equipment(name='Oscilloscope', area=area)

        response = tech_client.get('/public/')
        assert response.status_code == 200
        assert b'Equipment Status' in response.data

    def test_dashboard_redirects_unauthenticated(self, client):
        """Unauthenticated user is redirected to login."""
        response = client.get('/public/')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_area_headings_displayed(self, staff_client, make_area, make_equipment):
        """Area names are displayed as section headings."""
        area1 = make_area(name='Metal Shop')
        area2 = make_area(name='Wood Shop')
        make_equipment(name='Welder', area=area1)
        make_equipment(name='Bandsaw', area=area2)

        response = staff_client.get('/public/')
        assert b'Metal Shop' in response.data
        assert b'Wood Shop' in response.data

    def test_equipment_names_displayed(self, staff_client, make_area, make_equipment):
        """Equipment names are displayed on the dashboard."""
        area = make_area(name='Shop')
        make_equipment(name='CNC Router', area=area)
        make_equipment(name='Drill Press', area=area)

        response = staff_client.get('/public/')
        assert b'CNC Router' in response.data
        assert b'Drill Press' in response.data

    def test_status_indicator_css_classes(
        self, staff_client, make_area, make_equipment, make_repair_record,
    ):
        """Status indicator CSS classes present for green, yellow, red."""
        area = make_area(name='Shop')
        make_equipment(name='Good Tool', area=area)
        yellow_equip = make_equipment(name='Iffy Tool', area=area)
        red_equip = make_equipment(name='Broken Tool', area=area)

        make_repair_record(equipment=yellow_equip, status='New', severity='Degraded')
        make_repair_record(equipment=red_equip, status='New', severity='Down')

        # green_equip has no records, so green
        response = staff_client.get('/public/')
        html = response.data.decode()

        assert 'bg-success' in html  # green
        assert 'bg-warning' in html  # yellow
        assert 'bg-danger' in html   # red

    def test_issue_description_for_degraded_equipment(
        self, staff_client, make_area, make_equipment, make_repair_record,
    ):
        """Yellow/red equipment shows issue description."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Lathe', area=area)
        make_repair_record(
            equipment=equip, status='New', severity='Degraded',
            description='Belt needs replacement',
        )

        response = staff_client.get('/public/')
        assert b'Belt needs replacement' in response.data

    def test_empty_state_no_areas(self, staff_client):
        """Empty state message when no areas/equipment exist."""
        response = staff_client.get('/public/')
        assert b'No equipment registered yet.' in response.data

    def test_archived_equipment_not_shown(
        self, staff_client, make_area, make_equipment,
    ):
        """Archived equipment is excluded from the dashboard."""
        area = make_area(name='Shop')
        make_equipment(name='Active Tool', area=area)
        make_equipment(name='Retired Tool', area=area, is_archived=True)

        response = staff_client.get('/public/')
        assert b'Active Tool' in response.data
        assert b'Retired Tool' not in response.data

    def test_status_indicator_aria_labels(
        self, staff_client, make_area, make_equipment, make_repair_record,
    ):
        """Status indicators include ARIA labels for accessibility."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Printer', area=area)
        make_repair_record(equipment=equip, status='New', severity='Down')

        response = staff_client.get('/public/')
        html = response.data.decode()
        assert 'aria-label="Equipment status: Down"' in html

    def test_operational_equipment_aria_label(
        self, staff_client, make_area, make_equipment,
    ):
        """Operational equipment has correct ARIA label."""
        area = make_area(name='Shop')
        make_equipment(name='Good Tool', area=area)

        response = staff_client.get('/public/')
        html = response.data.decode()
        assert 'aria-label="Equipment status: Operational"' in html

    def test_responsive_layout_classes(self, staff_client, make_area, make_equipment):
        """Dashboard grid has responsive column classes."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = staff_client.get('/public/')
        html = response.data.decode()
        assert 'col-12' in html
        assert 'col-sm-6' in html
        assert 'col-lg-4' in html
        assert 'col-xl-3' in html

    def test_issue_description_for_down_equipment(
        self, staff_client, make_area, make_equipment, make_repair_record,
    ):
        """Down (red) equipment shows issue description."""
        area = make_area(name='Shop')
        equip = make_equipment(name='CNC Mill', area=area)
        make_repair_record(
            equipment=equip, status='New', severity='Down',
            description='Spindle motor failed',
        )

        response = staff_client.get('/public/')
        assert b'Spindle motor failed' in response.data

    def test_not_sure_severity_displays_as_yellow(
        self, staff_client, make_area, make_equipment, make_repair_record,
    ):
        """'Not Sure' severity renders as yellow/bg-warning on dashboard (AC #3)."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Mystery Tool', area=area)
        make_repair_record(
            equipment=equip, status='New', severity='Not Sure',
            description='Making odd sounds',
        )

        response = staff_client.get('/public/')
        html = response.data.decode()
        assert 'bg-warning' in html
        assert 'Making odd sounds' in html


class TestKioskView:
    """Tests for the kiosk display route."""

    def test_kiosk_renders_without_authentication(self, client, make_area, make_equipment):
        """Kiosk page is accessible without login (AC #1)."""
        area = make_area(name='Workshop')
        make_equipment(name='Table Saw', area=area)

        response = client.get('/public/kiosk')
        assert response.status_code == 200
        assert b'Table Saw' in response.data

    def test_kiosk_area_headings_displayed(self, client, make_area, make_equipment):
        """Kiosk displays area headings (AC #2)."""
        area1 = make_area(name='Metal Shop')
        area2 = make_area(name='Wood Shop')
        make_equipment(name='Welder', area=area1)
        make_equipment(name='Bandsaw', area=area2)

        response = client.get('/public/kiosk')
        assert b'Metal Shop' in response.data
        assert b'Wood Shop' in response.data

    def test_kiosk_equipment_names_displayed(self, client, make_area, make_equipment):
        """Kiosk displays equipment names (AC #2)."""
        area = make_area(name='Shop')
        make_equipment(name='CNC Router', area=area)
        make_equipment(name='Drill Press', area=area)

        response = client.get('/public/kiosk')
        assert b'CNC Router' in response.data
        assert b'Drill Press' in response.data

    def test_kiosk_status_indicators(
        self, client, make_area, make_equipment, make_repair_record,
    ):
        """Kiosk displays compact status indicators with color classes (AC #7)."""
        area = make_area(name='Shop')
        make_equipment(name='Good Tool', area=area)
        yellow_equip = make_equipment(name='Iffy Tool', area=area)
        red_equip = make_equipment(name='Broken Tool', area=area)

        make_repair_record(equipment=yellow_equip, status='New', severity='Degraded')
        make_repair_record(equipment=red_equip, status='New', severity='Down')

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'bg-success' in html
        assert 'bg-warning' in html
        assert 'bg-danger' in html

    def test_kiosk_issue_description_degraded(
        self, client, make_area, make_equipment, make_repair_record,
    ):
        """Degraded equipment shows issue description on kiosk (AC #3)."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Lathe', area=area)
        make_repair_record(
            equipment=equip, status='New', severity='Degraded',
            description='Belt needs replacement',
        )

        response = client.get('/public/kiosk')
        assert b'Belt needs replacement' in response.data

    def test_kiosk_issue_description_down(
        self, client, make_area, make_equipment, make_repair_record,
    ):
        """Down equipment shows issue description on kiosk (AC #3)."""
        area = make_area(name='Shop')
        equip = make_equipment(name='CNC Mill', area=area)
        make_repair_record(
            equipment=equip, status='New', severity='Down',
            description='Spindle motor failed',
        )

        response = client.get('/public/kiosk')
        assert b'Spindle motor failed' in response.data

    def test_kiosk_empty_state(self, client):
        """Kiosk shows empty state when no areas/equipment (AC #1)."""
        response = client.get('/public/kiosk')
        assert response.status_code == 200
        assert b'No equipment registered yet.' in response.data

    def test_kiosk_excludes_archived_equipment(self, client, make_area, make_equipment):
        """Archived equipment is excluded from kiosk display."""
        area = make_area(name='Shop')
        make_equipment(name='Active Tool', area=area)
        make_equipment(name='Retired Tool', area=area, is_archived=True)

        response = client.get('/public/kiosk')
        assert b'Active Tool' in response.data
        assert b'Retired Tool' not in response.data

    def test_kiosk_meta_refresh_tag(self, client):
        """Kiosk includes meta refresh tag for auto-refresh (AC #4)."""
        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'meta http-equiv="refresh" content="60"' in html

    def test_kiosk_no_navbar(self, client, make_area, make_equipment):
        """Kiosk has no navbar elements (AC #1)."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert '<nav' not in html
        assert 'navbar' not in html

    def test_kiosk_status_aria_labels(
        self, client, make_area, make_equipment, make_repair_record,
    ):
        """Kiosk status indicators include ARIA labels (AC #7)."""
        area = make_area(name='Shop')
        equip = make_equipment(name='Printer', area=area)
        make_repair_record(equipment=equip, status='New', severity='Down')

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'aria-label="Equipment status: Down"' in html

    def test_kiosk_css_classes_large_fonts(self, client, make_area, make_equipment):
        """Kiosk uses CSS classes for large fonts (AC #2)."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'kiosk-area-heading' in html
        assert 'kiosk-equipment-name' in html

    def test_kiosk_grid_auto_fill_class(self, client, make_area, make_equipment):
        """Kiosk uses CSS Grid auto-fill for responsive layout (AC #6)."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'kiosk-equipment-grid' in html

    def test_kiosk_param_redirects_to_kiosk(self, staff_client):
        """?kiosk=true on dashboard redirects to /public/kiosk (AC #1)."""
        response = staff_client.get('/public/?kiosk=true')
        assert response.status_code == 302
        assert '/public/kiosk' in response.headers['Location']

    def test_kiosk_accessible_by_authenticated_user(
        self, staff_client, make_area, make_equipment,
    ):
        """Authenticated users can also access the kiosk route."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = staff_client.get('/public/kiosk')
        assert response.status_code == 200
        assert b'Tool' in response.data

    def test_kiosk_param_unauthenticated_redirects_to_login(self, client):
        """Unauthenticated user hitting ?kiosk=true is redirected to login, not kiosk."""
        response = client.get('/public/?kiosk=true')
        assert response.status_code == 302
        assert '/auth/login' in response.headers['Location']

    def test_kiosk_skips_empty_areas(self, client, make_area, make_equipment):
        """Areas with no equipment are not rendered on kiosk display."""
        populated_area = make_area(name='Busy Shop')
        make_area(name='Empty Room')
        make_equipment(name='Lathe', area=populated_area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'Busy Shop' in html
        assert 'Empty Room' not in html

    def test_kiosk_excludes_archived_areas(self, client, make_area, make_equipment):
        """Archived areas are excluded from kiosk display."""
        from esb.extensions import db

        active_area = make_area(name='Active Shop')
        archived_area = make_area(name='Closed Wing')
        archived_area.is_archived = True
        make_equipment(name='Drill', area=active_area)
        make_equipment(name='Old Saw', area=archived_area)
        db.session.commit()

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert 'Active Shop' in html
        assert 'Closed Wing' not in html

    def test_kiosk_has_visually_hidden_h1(self, client, make_area, make_equipment):
        """Kiosk page has a visually-hidden h1 for accessibility."""
        area = make_area(name='Shop')
        make_equipment(name='Tool', area=area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert '<h1 class="visually-hidden">Equipment Status</h1>' in html

    def test_kiosk_equipment_name_is_heading(self, client, make_area, make_equipment):
        """Equipment names use h3 elements for proper heading hierarchy."""
        area = make_area(name='Shop')
        make_equipment(name='CNC Router', area=area)

        response = client.get('/public/kiosk')
        html = response.data.decode()
        assert '<h3 class="kiosk-equipment-name' in html
