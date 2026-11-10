"""Admission rule 03 — no self-updating code.

"The exact SHA pin *is* the trust model; a self-updater lets an installed copy
move to a commit nobody reviewed. … Keep the updater in the standalone
distribution if you want one; strip it from the catalog build."

This plugin had an in-app "download the new UI file" affordance for a day. It
was manual and it copied a local file, but it is the shape rule 03 names, so it
is gone: the plugin now only *reports* that the window is behind and points at
the app's own install/update path. These tests keep it gone.
"""

import importlib.util
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
UI = (ROOT / "desktop" / "plugin.js").read_text()
API = ROOT / "dashboard" / "plugin_api.py"


def _client():
    spec = importlib.util.spec_from_file_location("upfront_dashboard_no_self_update", API)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/plugins/upfront")
    return TestClient(app)


def test_the_ui_ships_no_way_to_replace_itself():
    for banned in (
        "/ui/download",          # a route that writes our own file out for install
        "/ui/refresh",           # an in-app "refresh the plugin" call
        "captureGatewayFileDownload",   # the save bridge, i.e. the download button
        "Download the UI file",
        "check for updates",
    ):
        assert banned not in UI, f"rule 03: the shipped UI must not contain {banned!r}"


def test_the_ui_never_fetches_anything_but_its_own_backend():
    """The page talks to its own /api/plugins/upfront namespace through ctx.rest.
    A raw fetch() would be a second, unreviewed network path."""
    assert "fetch(" not in UI
    assert "XMLHttpRequest" not in UI


def test_the_backend_registers_no_update_routes():
    c = _client()
    for route in ("/api/plugins/upfront/ui/download", "/api/plugins/upfront/ui/refresh"):
        assert c.get(route).status_code in (404, 405), route
        assert c.post(route).status_code in (404, 405), route


def test_the_manifest_declares_no_updater():
    yaml = (ROOT / "plugin.yaml").read_text().lower()
    for banned in ("update_url", "updater", "auto_update"):
        assert banned not in yaml


def test_a_stale_window_is_still_told_and_still_has_a_way_forward():
    """Removing the updater must not remove the honesty: the page still says the
    window is behind, still opens the app's own plugin settings, and still says
    a restart is not needed."""
    assert "this window is behind" in UI
    assert "Open plugin settings" in UI
    assert "host.navigate('/capabilities?tab=plugins')" in UI
    assert "you do not need to restart the app" in UI


def test_the_status_route_is_a_read_only_report():
    body = _client().get("/api/plugins/upfront/ui?build=0.0.1").json()
    assert set(body) >= {"running", "installed", "up_to_date", "hint"}
    assert body["up_to_date"] is False
    assert "Reload the page" not in body["hint"]
