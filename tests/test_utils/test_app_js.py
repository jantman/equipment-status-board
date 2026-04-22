"""Sanity-check assertions for esb/static/js/app.js."""

from pathlib import Path

APP_JS = Path(__file__).resolve().parents[2] / 'esb' / 'static' / 'js' / 'app.js'


def test_app_js_includes_qr_preview_updater():
    content = APP_JS.read_text()
    assert 'qr-form' in content
    assert 'qr-preview' in content
    assert 'data-preview-base' in content
