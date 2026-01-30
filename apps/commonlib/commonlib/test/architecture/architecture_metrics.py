
from pathlib import Path
from commonlib.test.architecture.architecture_util import get_project_root, count_lines, EXTENSIONS, EXCLUDES
import os

def getLongFiles():
    root_dir = get_project_root()
    result = []
    assert (root_dir / 'apps').exists(), f"Could not find apps dir at {root_dir}"
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDES]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix not in EXTENSIONS:
                continue
            if (lines := count_lines(file_path)) > 200:
                result.append((str(file_path.relative_to(root_dir)), lines))
    return result
