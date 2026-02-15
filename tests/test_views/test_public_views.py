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
