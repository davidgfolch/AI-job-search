import errno
import shutil
import tempfile
from pathlib import Path
from dotenv import set_key


def _set_keys_in_place(path: Path, updates: dict[str, str]):
    """Rewrite a bind-mounted .env in place; os.replace() cannot target a mount"""
    with tempfile.TemporaryDirectory() as tmp_dir:
        copy = Path(tmp_dir) / path.name
        shutil.copy2(path, copy)
        for key, value in updates.items():
            set_key(str(copy), key, value)
        updated = copy.read_text(encoding='utf-8')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(updated)


def set_keys(path: Path, updates: dict[str, str]):
    """Write keys to an existing .env, falling back to in-place on bind mounts"""
    try:
        for key, value in updates.items():
            set_key(str(path), key, value)
    except OSError as e:
        if e.errno not in (errno.EBUSY, errno.EPERM):
            raise
        _set_keys_in_place(path, updates)
