import shutil
import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import policy_platform as platform_utils


class TestPlistHelpers:
    def test_read_missing_plist_returns_empty_dict(self, tmp_path):
        assert platform_utils.read_plist(tmp_path / "missing.plist") == {}

    def test_plist_roundtrip(self, tmp_path):
        path = tmp_path / "policy.plist"
        expected = {"ExtensionInstallForcelist": ["a;file:///tmp/a.crx"]}

        def fake_run(command, **_kwargs):
            if command[1] == "install":
                shutil.copyfile(Path(command[-2]), Path(command[-1]))

        with patch.object(platform_utils.subprocess, "run", side_effect=fake_run):
            platform_utils.write_plist(path, expected)
        assert platform_utils.read_plist(path) == expected


class TestRegistryHelpers:
    @patch("policy_platform.subprocess.run")
    def test_next_index_uses_highest_existing_value(self, run):
        run.return_value.stdout = " HKEY\\Key\n   1 REG_SZ a\n   3 REG_SZ b\n"
        assert platform_utils.registry_next_index("HKEY\\Key") == 4

    @patch("policy_platform.subprocess.run")
    def test_matching_names_returns_only_numeric_values(self, run):
        run.return_value.stdout = " HKEY\\Key\n   1 REG_SZ id;url\n   2 REG_SZ other\n"
        assert platform_utils.registry_matching_names("HKEY\\Key", "id;") == ["1"]
