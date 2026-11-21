"""Build browser-specific packages from the shared unpacked extension."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

from commonlib.observability import get_logger
from crx3 import crx3_public_key, extension_id

logger = get_logger("aiFormFiller.extension_packages")

APP_DIR = Path(__file__).resolve().parents[1]
SOURCE_DIR = APP_DIR / "extension"
FIREFOX_ID = "aiformfiller@local"
FIREFOX_SHIM = """if (!chrome.sidePanel) {
  chrome.sidePanel = { open: async () => { try { await chrome.sidebarAction.open(); } catch (e) {} } };
}
if (chrome.storage && !chrome.storage.session) {
  const cache = {};
  chrome.storage.session = {
    set: async (items) => Object.assign(cache, items),
    get: async (keys) => Object.fromEntries(Object.entries(cache).filter(([key]) => [].concat(keys).includes(key)))
  };
}
"""


class InstallError(Exception):
    pass


def artifact_dir():
    if os.name == "nt":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    else:
        base = Path.home()
    return base / ".ai-form-filler"


def manifest_version():
    return json.loads((SOURCE_DIR / "manifest.json").read_text(encoding="utf-8"))["version"]


def chrome_executable():
    if os.name == "nt":
        candidates = [Path(os.environ.get("PROGRAMFILES", "")) / "Google/Chrome/Application/chrome.exe",
                      Path(os.environ.get("PROGRAMFILES(X86)", "")) / "Google/Chrome/Application/chrome.exe",
                      Path(os.environ.get("LOCALAPPDATA", "")) / "Google/Chrome/Application/chrome.exe"]
    elif sys.platform == "darwin":
        candidates = [Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")]
    else:
        candidates = [Path("/opt/google/chrome/chrome"), Path("/usr/bin/google-chrome"), Path("/usr/bin/chromium")]
    return next((path for path in candidates if path.exists()), None)


def ensure_key(path):
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["openssl", "genrsa", "-out", str(path), "2048"], check=True, capture_output=True)


def pack_chrome():
    chrome = chrome_executable()
    if not chrome:
        raise InstallError("Google Chrome or Chromium is not installed")
    output = artifact_dir()
    output.mkdir(parents=True, exist_ok=True)
    ensure_key(output / "extension.pem")
    with tempfile.TemporaryDirectory(prefix="aiformfiller-") as tmp:
        build = Path(tmp) / "extension"
        shutil.copytree(SOURCE_DIR, build)
        command = [str(chrome), "--headless", "--disable-gpu", "--no-first-run", "--no-sandbox",
                   f"--user-data-dir={tmp}/profile", f"--pack-extension={build}",
                   f"--pack-extension-key={output / 'extension.pem'}"]
        subprocess.run(command, check=True, capture_output=True, text=True)
        crx = build.with_suffix(".crx")
        if not crx.exists():
            raise InstallError("Chrome packer did not create a CRX file")
        target = output / "ai-form-filler.crx"
        shutil.copyfile(crx, target)
    identifier = extension_id(crx3_public_key(target))
    (output / "update.xml").write_text(update_xml(identifier, target), encoding="utf-8")
    logger.info("extension.chrome_packed", extension_id=identifier, crx=str(target))
    return identifier, target


def update_xml(identifier, crx_path):
    url = crx_path.resolve().as_uri()
    return (f"<?xml version='1.0' encoding='UTF-8'?>\n"
            "<gupdate xmlns='http://www.google.com/update2/response' protocol='2.0'>\n"
            f"  <app appid='{identifier}'>\n"
            f"    <updatecheck codebase='{url}' version='{manifest_version()}' />\n"
            "  </app>\n</gupdate>\n")


def firefox_manifest():
    manifest = json.loads((SOURCE_DIR / "manifest.json").read_text(encoding="utf-8"))
    manifest["browser_specific_settings"] = {"gecko": {"id": FIREFOX_ID, "strict_min_version": "115.0"}}
    manifest["background"] = {"scripts": ["background.js"]}
    manifest["sidebar_action"] = {"default_panel": "sidepanel/panel.html", "default_title": "AI Form Filler",
                                  "default_icon": manifest.get("icons", {})}
    manifest["permissions"] = [permission for permission in manifest.get("permissions", []) if permission != "sidePanel"]
    manifest.pop("side_panel", None)
    return manifest


def state_file():
    return artifact_dir() / "install-state.json"


def stored_chrome_id():
    state = state_file()
    if state.exists():
        return json.loads(state.read_text(encoding="utf-8")).get("chrome_id")
    key = artifact_dir() / "extension.pem"
    if not key.exists():
        return None
    result = subprocess.run(["openssl", "rsa", "-in", str(key), "-pubout", "-outform", "DER"], check=True, capture_output=True)
    return extension_id(result.stdout)


def save_state(chrome_id):
    state_file().write_text(json.dumps({"chrome_id": chrome_id}, indent=2) + "\n", encoding="utf-8")


def clean_artifacts():
    for name in ("ai-form-filler.crx", "ai-form-filler.xpi", "update.xml", "install-state.json"):
        (artifact_dir() / name).unlink(missing_ok=True)


def pack_firefox():
    output = artifact_dir()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="aiformfiller-") as tmp:
        build = Path(tmp) / "extension"
        shutil.copytree(SOURCE_DIR, build)
        (build / "manifest.json").write_text(json.dumps(firefox_manifest(), indent=2) + "\n", encoding="utf-8")
        background = build / "background.js"
        background.write_text(FIREFOX_SHIM + background.read_text(encoding="utf-8"), encoding="utf-8")
        target = output / "ai-form-filler.xpi"
        with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in sorted(build.rglob("*")):
                if path.is_file():
                    archive.write(path, path.relative_to(build).as_posix())
    logger.info("extension.firefox_packed", extension_id=FIREFOX_ID, xpi=str(target))
    return FIREFOX_ID, target
