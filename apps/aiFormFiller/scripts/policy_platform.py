"""macOS plist and Windows registry helpers for browser policy registration."""
import plistlib
import subprocess
import tempfile
from pathlib import Path


def read_plist(path):
    try:
        return plistlib.loads(Path(path).read_bytes())
    except (FileNotFoundError, plistlib.InvalidFileException):
        return {}


def write_plist(path, data):
    with tempfile.NamedTemporaryFile(suffix=".plist", delete=False) as handle:
        plistlib.dump(data, handle)
        temp_path = handle.name
    try:
        subprocess.run(["sudo", "mkdir", "-p", str(Path(path).parent)], check=True)
        subprocess.run(["sudo", "install", "-m", "644", temp_path, str(path)], check=True)
    finally:
        Path(temp_path).unlink(missing_ok=True)


def registry_next_index(key):
    result = subprocess.run(["reg", "query", key], capture_output=True, text=True)
    names = [int(line.strip().split()[0]) for line in result.stdout.splitlines() if line.strip().split()[0].isdigit()]
    return max(names, default=0) + 1


def registry_matching_names(key, needle):
    result = subprocess.run(["reg", "query", key], capture_output=True, text=True)
    return [line.strip().split()[0] for line in result.stdout.splitlines() if needle in line and line.strip().split()[0].isdigit()]
