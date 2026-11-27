import stat
import sys
from commonlib.test.architecture.architecture_util import get_project_root

def get_non_executable_scripts():
    # Only POSIX checkouts carry a meaningful executable bit; Windows always reports none.
    if sys.platform.startswith('win'):
        return []
    root_dir = get_project_root()
    scripts_dir = root_dir / 'scripts'
    if not scripts_dir.exists():
        return []
    violations = []
    for path in sorted(scripts_dir.rglob('*.sh')):
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                shebang = handle.readline()
        except OSError:
            continue
        if not shebang.startswith('#!'):
            continue
        if not path.stat().st_mode & stat.S_IXUSR:
            violations.append(str(path.relative_to(root_dir)))
    return violations
