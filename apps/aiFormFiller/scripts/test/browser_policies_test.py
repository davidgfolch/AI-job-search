import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import browser_policies as policies


class TestFirefoxPolicies:
    def test_adds_install_entry_and_preserves_other_policies(self):
        result = policies.add_firefox_install({"policies": {"AppAutoUpdate": False}}, "/tmp/ai-form-filler.xpi")
        assert "/tmp/ai-form-filler.xpi" in result["policies"]["Extensions"]["Install"]
        assert result["policies"]["AppAutoUpdate"] is False

    def test_add_is_idempotent(self):
        policies_data = policies.add_firefox_install({}, "/tmp/ai-form-filler.xpi")
        policies_data = policies.add_firefox_install(policies_data, "/tmp/ai-form-filler.xpi")
        assert len(policies_data["policies"]["Extensions"]["Install"]) == 1

    def test_remove_keeps_unrelated_extensions(self):
        data = {"policies": {"Extensions": {"Install": ["/tmp/other.xpi", "/tmp/ai-form-filler.xpi"], "Locked": ["x@y"]}}}
        result = policies.remove_firefox_install(data)
        assert result["policies"]["Extensions"]["Install"] == ["/tmp/other.xpi"]
        assert result["policies"]["Extensions"]["Locked"] == ["x@y"]

    def test_remove_cleans_empty_sections(self):
        data = policies.add_firefox_install({}, "/tmp/ai-form-filler.xpi")
        assert policies.remove_firefox_install(data) == {"policies": {}}


class TestChromeRegistration:
    def test_uses_system_external_extension_directories_on_chrome(self):
        assert policies.CHROME_EXTERNAL_DIRS == ["/opt/google/chrome/extensions", "/usr/share/google-chrome/extensions"]
        assert policies.chrome_user_external_dir().endswith("/.config/google-chrome/External Extensions")

    @patch("browser_policies.system_text_write")
    def test_external_install_writes_crx_path_and_version(self, write):
        path = policies.chrome_external_install("a" * 32, "/tmp/extension.crx")
        assert str(path).startswith("/opt/google/chrome/extensions/")
        assert path.name == "a" * 32 + ".json"
        written = write.call_args.args[1]
        assert '"external_crx": "/tmp/extension.crx"' in written
        assert "external_version" in written

    @patch("browser_policies.system_remove")
    def test_external_uninstall_removes_known_locations(self, remove):
        identifier = "a" * 32
        with patch.object(policies, "CHROME_EXTERNAL_DIRS", ["/tmp/chrome-extensions"]):
            with patch.object(policies, "chrome_user_external_dir", return_value="/tmp/user-chrome-extensions"):
                with patch("pathlib.Path.exists", side_effect=lambda: True):
                    removed = policies.chrome_external_uninstall(identifier)
        assert "/tmp/chrome-extensions/" + identifier + ".json" in removed
        assert "/etc/opt/chrome/external_extensions/" + identifier + ".json" in removed
        assert "/tmp/user-chrome-extensions/" + identifier + ".json" in removed
        assert remove.call_count == 3


class TestBrowserDetection:
    @patch("browser_policies.shutil.which", side_effect=lambda name: "/usr/bin/" + name if name == "firefox" else None)
    def test_detects_available_browser(self, _which):
        assert policies.browser_installed(("chrome", "firefox")) is True
        assert policies.browser_installed(("chrome", "chromium")) is False
