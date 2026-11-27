
import pytest

from commonlib.test.architecture.architecture_layers import _validate_dependencies, check_layer, get_file_imports
from commonlib.test.architecture.architecture_layer_rules import LayerRule, layer_from_filename


@pytest.mark.parametrize('imports, layer, package, expected', [
    ({'services'}, 'services', 'backend', []),
    ({'backend.services'}, 'services', 'backend', []),
    ({'aiEnrichSkill.services'}, 'services', 'aiEnrichSkill', []),
    ({'commonlib.sql.mysqlUtil'}, 'commonlib.sql.mysqlUtil', 'cron', []),
    ({'scrapper.core.scrapper_config'}, 'core', 'scrapper', []),
    ({'service_registry'}, 'services', 'backend', ['missing']),
])
def test_required_dependency_matches_qualified_and_bare_imports(imports, layer, package, expected):
    assert _validate_dependencies([(layer, 'missing')], imports, should_exist=True, package=package) == expected


@pytest.mark.parametrize('imports, layer, package, expected', [
    ({'services'}, 'services', 'backend', ['forbidden']),
    ({'backend.services'}, 'services', 'backend', ['forbidden']),
    ({'aiEnrichSkill.services'}, 'services', 'aiEnrichSkill', ['forbidden']),
    ({'scrapper.core.scrapper_config'}, 'core', 'scrapper', ['forbidden']),
    ({'commonlib.repositories.cron_state_repository'}, 'repositories', 'cron', ['forbidden']),
    ({'service_registry'}, 'services', 'backend', []),
])
def test_forbidden_dependency_uses_layer_boundaries(imports, layer, package, expected):
    assert _validate_dependencies([(layer, 'forbidden')], imports, should_exist=False, package=package) == expected


def test_relative_from_import_is_recorded(tmp_path):
    source = tmp_path / 'module.py'
    source.write_text('from . import services\n', encoding='utf-8')
    assert get_file_imports(source) == {'services'}


@pytest.mark.parametrize('filename, expected', [
    ('skill_enricher_service.py', 'services'),
    ('metricsService.py', 'services'),
    ('aiEnrichRepository.py', 'repositories'),
    ('salary_history_repository.py', 'repositories'),
    ('skill_repository.py', 'repositories'),
    ('skill_context.py', None),
    ('mysqlUtil.py', None),
])
def test_layer_from_filename(filename, expected):
    assert layer_from_filename(filename) == expected


def test_rule_includes_root_level_files_named_as_its_layer(tmp_path):
    package = tmp_path / 'apps' / 'commonlib' / 'commonlib'
    package.mkdir(parents=True)
    (package / 'stray_service.py').write_text('pass\n', encoding='utf-8')
    (package / 'skill_repository.py').write_text('pass\n', encoding='utf-8')
    (package / 'skill_context.py').write_text('pass\n', encoding='utf-8')
    rule = LayerRule('apps/commonlib/commonlib', 'commonlib', 'services')
    assert [path.name for path in rule.extra_files(tmp_path)] == ['stray_service.py']
    assert [path.name for path in LayerRule('apps/commonlib/commonlib', 'commonlib', 'repositories').extra_files(tmp_path)] == ['skill_repository.py']


def test_check_layer_flags_root_level_file_named_as_layer(tmp_path):
    package = tmp_path / 'apps' / 'demo' / 'demo'
    package.mkdir(parents=True)
    stray = package / 'stray_service.py'
    stray.write_text('from commonlib.sql.mysqlUtil import MysqlUtil\n', encoding='utf-8')
    error = check_layer(package / 'services', tmp_path, package='demo',
        forbidden_deps=[('commonlib.sql.mysqlUtil', 'DB in service')], extra_files=(stray,))
    assert 'stray_service.py' in error
    assert 'DB in service' in error
