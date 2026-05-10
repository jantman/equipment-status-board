"""Config-invariant tests: assertions about non-Python project files
(docker-compose.yml, mkdocs.yml) that the monitoring/alerting design
depends on. Paths are resolved relative to this file so the tests pass
regardless of pytest's CWD."""
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent


def test_compose_pythonunbuffered_set_on_app_and_worker():
    compose = yaml.safe_load((REPO_ROOT / 'docker-compose.yml').read_text())
    for service_name in ('app', 'worker'):
        env = compose['services'][service_name].get('environment', [])
        if isinstance(env, list):
            assert 'PYTHONUNBUFFERED=1' in env, (
                f"{service_name} missing PYTHONUNBUFFERED=1; log lines will buffer"
            )
        else:
            assert env.get('PYTHONUNBUFFERED') in ('1', 1), (
                f"{service_name} missing PYTHONUNBUFFERED=1; log lines will buffer"
            )


def test_mkdocs_enables_html_passthrough_for_anchor_preservation():
    cfg = yaml.safe_load((REPO_ROOT / 'mkdocs.yml').read_text())
    extensions = cfg.get('markdown_extensions', [])
    ext_names = {e if isinstance(e, str) else next(iter(e)) for e in extensions}
    assert 'attr_list' in ext_names, "anchor preservation depends on attr_list"
    assert 'md_in_html' in ext_names, "anchor preservation depends on md_in_html"
