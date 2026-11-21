"""Register the extension in existing browser installations without touching profiles."""
import json
import os
import platform
import shutil
import subprocess
import tempfile
from pathlib import Path

from commonlib.observability import get_logger
from extension_packages import FIREFOX_ID, InstallError, manifest_version
from policy_platform import read_plist, registry_matching_names, registry_next_index, write_plist

logger = get_logger("aiFormFiller.browser_policies")

CHROME_EXTERNAL_DIRS = ["/opt/google/chrome/extensions", "/usr/share/google-chrome/extensions"]
CHROME_LEGACY_EXTERNAL_DIRS = ["/etc/opt/chrome/external_extensions"]


def chrome_user_external_dir():
    return str(Path.home() / ".config/google-chrome/External Extensions")
CHROME_MAC_POLICY = "/Library/Preferences/com.google.chrome.plist"
CHROME_WIN_POLICY = r"HKCU\Software\Policies\Google\Chrome\ExtensionInstallForcelist"


def system_text_write(path, text):
    path = Path(path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return
    except (PermissionError, OSError):
        pass
    with tempfile.NamedTemporaryFile(mode="w", suffix=".tmp", delete=False, encoding="utf-8") as handle:
        handle.write(text)
        temp_path = handle.name
    subprocess.run(["sudo", "mkdir", "-p", str(path.parent)], check=True)
    subprocess.run(["sudo", "install", "-m", "644", temp_path, str(path)], check=True)
    Path(temp_path).unlink(missing_ok=True)


def system_remove(path):
    path = Path(path)
    try:
        path.unlink(missing_ok=True)
        return
    except (PermissionError, OSError):
        subprocess.run(["sudo", "rm", "-f", str(path)], check=True)


def read_json(path):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def chrome_external_install(identifier, crx_path):
    target_dir = next((path for path in CHROME_EXTERNAL_DIRS if Path(path).parent.is_dir()), CHROME_EXTERNAL_DIRS[0])
    path = Path(target_dir) / f"{identifier}.json"
    data = {"external_crx": str(crx_path), "external_version": manifest_version()}
    system_text_write(path, json.dumps(data, indent=2) + "\n")
    logger.info("chrome.external_registered", extension_id=identifier, path=str(path))
    return path


def chrome_external_uninstall(identifier):
    removed = []
    directories = [*CHROME_EXTERNAL_DIRS, *CHROME_LEGACY_EXTERNAL_DIRS, chrome_user_external_dir()]
    for directory in directories:
        path = Path(directory) / f"{identifier}.json"
        if path.exists():
            system_remove(path)
            removed.append(str(path))
    return removed


def chrome_policy_install(identifier, update_url):
    value = f"{identifier};{update_url}"
    system = platform.system()
    if system == "Linux":
        path = Path("/etc/opt/chrome/policies/managed/ai-form-filler.json")
        system_text_write(path, json.dumps({"ExtensionInstallForcelist": [value]}, indent=2) + "\n")
        return str(path)
    if system == "Darwin":
        path = Path(CHROME_MAC_POLICY)
        data = read_plist(path)
        entries = [entry for entry in data.get("ExtensionInstallForcelist", []) if not entry.startswith(identifier + ";")]
        data["ExtensionInstallForcelist"] = entries + [value]
        write_plist(path, data)
        return str(path)
    if system == "Windows":
        index = registry_next_index(CHROME_WIN_POLICY)
        subprocess.run(["reg", "add", CHROME_WIN_POLICY, "/v", str(index), "/d", value, "/f"], check=True, capture_output=True)
        return f"{CHROME_WIN_POLICY} /v {index}"
    raise InstallError(f"Chrome policy install is not supported on {system}")


def chrome_policy_uninstall(identifier):
    system = platform.system()
    removed = []
    if system == "Linux":
        path = Path("/etc/opt/chrome/policies/managed/ai-form-filler.json")
        if path.exists():
            system_remove(path)
            removed.append(str(path))
    elif system == "Darwin":
        path = Path(CHROME_MAC_POLICY)
        data = read_plist(path)
        entries = data.get("ExtensionInstallForcelist", [])
        kept = [entry for entry in entries if not entry.startswith(identifier + ";")]
        if len(kept) != len(entries):
            data["ExtensionInstallForcelist"] = kept
            write_plist(path, data)
            removed.append(str(path))
    elif system == "Windows":
        for name in registry_matching_names(CHROME_WIN_POLICY, identifier + ";"):
            subprocess.run(["reg", "delete", CHROME_WIN_POLICY, "/v", name, "/f"], check=True, capture_output=True)
            removed.append(name)
    return removed


def firefox_policy_path():
    system = platform.system()
    if system == "Windows":
        return Path(os.environ.get("PROGRAMFILES", "C:/Program Files")) / "Mozilla Firefox/distribution/policies.json"
    if system == "Darwin":
        return Path("/Applications/Firefox.app/Contents/Resources/distribution/policies.json")
    return Path("/etc/firefox/policies/policies.json")


def add_firefox_install(policies, xpi_path):
    extensions = policies.setdefault("policies", {}).setdefault("Extensions", {})
    installs = [entry for entry in extensions.get("Install", []) if "ai-form-filler.xpi" not in str(entry)]
    installs.append(str(xpi_path))
    extensions["Install"] = installs
    return policies


def remove_firefox_install(policies):
    extensions = policies.get("policies", {}).get("Extensions", {})
    installs = [entry for entry in extensions.get("Install", []) if "ai-form-filler.xpi" not in str(entry)]
    if installs:
        extensions["Install"] = installs
    else:
        extensions.pop("Install", None)
        if not extensions:
            policies["policies"].pop("Extensions", None)
    return policies


def firefox_install(xpi_path):
    path = firefox_policy_path()
    policies = add_firefox_install(read_json(path), xpi_path)
    system_text_write(path, json.dumps(policies, indent=2) + "\n")
    logger.info("firefox.policy_registered", extension_id=FIREFOX_ID, path=str(path))
    return path


def firefox_uninstall():
    path = firefox_policy_path()
    if not path.exists():
        return []
    policies = remove_firefox_install(read_json(path))
    if policies.get("policies"):
        system_text_write(path, json.dumps(policies, indent=2) + "\n")
    else:
        system_remove(path)
    return [str(path)]


def browser_installed(names):
    candidates = (names,) if isinstance(names, str) else names
    system = platform.system()
    for name in candidates:
        if shutil.which(name) is not None:
            return True
        if system == "Windows" and any(p.exists() for p in _windows_browser_paths(name)):
            return True
        if system == "Darwin" and Path(f"/Applications/{name}.app").exists():
            return True
    return False


def _windows_browser_paths(name):
    roots = [os.environ.get("PROGRAMFILES", ""), os.environ.get("PROGRAMFILES(X86)", ""), os.environ.get("LOCALAPPDATA", "")]
    return [Path(root) / f"{name}/Application/{name}.exe" for root in roots if root]
