import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import extension_packages as packages


class TestFirefoxManifest:
    def test_transforms_chrome_only_keys(self):
        manifest = packages.firefox_manifest()
        assert manifest["browser_specific_settings"]["gecko"]["id"] == packages.FIREFOX_ID
        assert manifest["background"] == {"scripts": ["background.js"]}
        assert manifest["sidebar_action"]["default_panel"] == "sidepanel/panel.html"
        assert "side_panel" not in manifest
        assert "sidePanel" not in manifest["permissions"]
        assert "service_worker" not in manifest["background"]

    def test_keeps_shared_permissions(self):
        manifest = packages.firefox_manifest()
        assert "activeTab" in manifest["permissions"]
        assert "http://127.0.0.1:8080/*" in manifest["host_permissions"]


class TestUpdateXml:
    def test_points_at_local_crx(self):
        xml = packages.update_xml("a" * 32, Path("/tmp/extension.crx"))
        assert "appid='" + "a" * 32 + "'" in xml
        assert "file:///tmp/extension.crx" in xml
        assert "version='" + json.loads((packages.SOURCE_DIR / "manifest.json").read_text())["version"] + "'" in xml
