
from commonlib.test.architecture.architecture_util import get_project_root, count_lines, iter_source_files

def getLongFiles():
    root_dir = get_project_root()
    result = []
    assert (root_dir / 'apps').exists(), f"Could not find apps dir at {root_dir}"
    for file_path in iter_source_files(root_dir):
        if (lines := count_lines(file_path)) > 200:
            result.append((str(file_path.relative_to(root_dir)), lines))
    return result
