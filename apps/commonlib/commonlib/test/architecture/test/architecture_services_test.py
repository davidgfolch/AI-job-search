from commonlib.test.architecture.architecture_services import get_misplaced_layer_symbols


def make_file(root, relative, source='pass\n'):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding='utf-8')
    return path


def test_misplaced_service_file_and_class_are_flagged(tmp_path):
    path = make_file(tmp_path, 'apps/demo/demo/stray_service.py', 'class StrayService:\n    pass\n')
    violations = get_misplaced_layer_symbols(tmp_path)
    assert (path, 'stray_service.py', 'services') in violations
    assert (path, 'StrayService', 'services') in violations


def test_service_in_services_layer_is_clean(tmp_path):
    make_file(tmp_path, 'apps/demo/demo/services/ok_service.py', 'class OkService:\n    pass\n')
    assert get_misplaced_layer_symbols(tmp_path) == []


def test_repository_in_sql_layer_is_allowed(tmp_path):
    make_file(tmp_path, 'apps/commonlib/commonlib/sql/job_repository.py', 'class JobRepository:\n    pass\n')
    assert get_misplaced_layer_symbols(tmp_path) == []


def test_repository_class_outside_repository_layers_is_flagged(tmp_path):
    path = make_file(tmp_path, 'apps/demo/demo/handlers/job_repository.py', 'class JobRepository:\n    pass\n')
    violations = get_misplaced_layer_symbols(tmp_path)
    assert (path, 'JobRepository', 'repositories') in violations


def test_test_files_are_ignored(tmp_path):
    make_file(tmp_path, 'apps/demo/demo/test/stray_service.py', 'class StrayService:\n    pass\n')
    assert get_misplaced_layer_symbols(tmp_path) == []


def test_unrelated_class_names_are_ignored(tmp_path):
    make_file(tmp_path, 'apps/demo/demo/service_helper.py', 'class ServiceHelper:\n    pass\n')
    assert get_misplaced_layer_symbols(tmp_path) == []
