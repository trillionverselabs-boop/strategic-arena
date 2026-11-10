"""The desktop half has to reach the machine the window runs on.

A page reload cannot do that, and neither can a backend restart: the app reads
`desktop/plugin.js` from its own disk. These tests pin the one sanctioned way
to hand that file to a remote window — the gateway save bridge — and the honest
copy that tells the user so.
"""

import importlib.util
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent
API = ROOT / "dashboard" / "plugin_api.py"


def _client():
    spec = importlib.util.spec_from_file_location("upfront_dashboard_ui_dl", API)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    app = FastAPI()
    app.include_router(mod.router, prefix="/api/plugins/upfront")
    return TestClient(app)


def test_download_serves_the_file_the_repo_actually_ships():
    r = _client().get("/api/plugins/upfront/ui/download")
    assert r.status_code == 200
    body = r.json()
    src = (ROOT / "desktop" / "plugin.js").read_bytes()
    assert body["suggestedName"] == "plugin.js"
    assert body["build"].startswith("0.5.0")
    served = Path(body["path"]).read_bytes()
    assert served == src, "the saved file must be byte-identical to the shipped UI"


def test_the_served_path_is_one_the_gateway_may_download():
    """The managed-files surface refuses credential-store basenames and paths
    outside its root; if this path were refused, the save bridge would fail at
    click time. Checked against the same rules the host applies, without
    importing host code (the plugin must not depend on the checkout).
    """
    sensitive = {"auth.json", "auth.lock", "config.yaml", ".env", ".envrc"}
    body = _client().get("/api/plugins/upfront/ui/download").json()
    target = Path(body["path"])
    assert target.is_absolute()
    assert target.name == "plugin.js"
    assert target.name.lower() not in sensitive
    assert not any(part.lower() in {"mcp-tokens", "pairing"} for part in target.parts)
    assert target.exists(), "the save bridge needs a real file on the gateway"


def test_a_stale_window_gets_advice_that_can_actually_work():
    """The old hint said "Reload the page to pick it up" — impossible when the
    file is on another machine."""
    body = _client().get("/api/plugins/upfront/ui?build=0.0.1%20%C2%B7%20ui0").json()
    assert body["up_to_date"] is False
    assert "Reload the page" not in body["hint"]
    assert "Desktop target" in body["hint"]


def test_an_up_to_date_window_is_quiet():
    js = (ROOT / "desktop" / "plugin.js").read_text()
    build = js.split("const BUILD = '")[1].split("'")[0]
    from urllib.parse import quote

    body = _client().get(f"/api/plugins/upfront/ui?build={quote(build)}").json()
    assert body["up_to_date"] is True
    assert body["hint"] == ""
