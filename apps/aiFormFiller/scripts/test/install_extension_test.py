import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import install_extension as installer


class TestArguments:
    def test_defaults_to_all_browsers(self):
        args = installer.parse_args([])
        assert (args.browser, args.uninstall, args.dry_run) == ("all", False, False)

    def test_uninstall_flag(self):
        args = installer.parse_args(["--uninstall", "--browser", "firefox"])
        assert args.uninstall is True
        assert args.browser == "firefox"


class TestSelection:
    @patch("install_extension.policies.browser_installed", return_value=True)
    def test_all_returns_installed_browsers(self, _installed):
        assert installer.selected_browsers("all") == ["chrome", "firefox"]

    @patch("install_extension.policies.browser_installed", return_value=False)
    def test_all_returns_empty_when_none_installed(self, _installed):
        assert installer.selected_browsers("all") == []

    def test_explicit_browser_is_respected(self):
        assert installer.selected_browsers("chrome") == ["chrome"]


class TestMain:
    @patch("install_extension.report")
    @patch("install_extension.policies.browser_installed", return_value=True)
    def test_dry_run_does_not_pack_or_register(self, _installed, report):
        with patch.object(installer.packages, "pack_chrome") as pack, patch.object(installer.policies, "firefox_install") as register:
            assert installer.main(["--dry-run"]) == 0
        pack.assert_not_called()
        register.assert_not_called()
        assert any("dry-run" in call.args[0] for call in report.call_args_list)

    @patch("install_extension.report")
    @patch("install_extension.policies.browser_installed", return_value=True)
    def test_uninstall_cleans_artifacts(self, _installed, _report):
        with patch.object(installer.packages, "clean_artifacts") as clean, patch.object(installer.packages, "stored_chrome_id", return_value="a" * 32), \
             patch.object(installer.policies, "chrome_external_uninstall", return_value=[]), \
             patch.object(installer.policies, "chrome_policy_uninstall", return_value=[]), \
             patch.object(installer.policies, "firefox_uninstall", return_value=[]):
            assert installer.main(["--uninstall"]) == 0
        clean.assert_called_once()
