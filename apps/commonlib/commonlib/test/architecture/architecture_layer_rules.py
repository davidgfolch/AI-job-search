import os
from dataclasses import dataclass
from pathlib import Path

from commonlib.test.architecture.architecture_util import EXCLUDES

LAYER_DIRS = frozenset({
    'api', 'config', 'core', 'decorator', 'domain', 'executor', 'jobs', 'middleware', 'models',
    'navigator', 'network', 'orchestration', 'repositories', 'services', 'sql', 'sync', 'util', 'utils',
})
FILE_LAYER_SUFFIXES = {
    'services': ('_service.py', 'Service.py'),
    'repositories': ('_repository.py', 'Repository.py', 'repository.py'),
}


def layer_from_filename(name):
    for layer, suffixes in FILE_LAYER_SUFFIXES.items():
        if name.endswith(suffixes):
            return layer
    return None

NO_API = ('api', "Imports API layer (circular dependency risk).")
NO_SERVICES = ('services', "Imports Service layer (circular dependency risk).")
NO_REPOSITORIES = ('repositories', "Direct Repository layer import (skip Service layer).")
NO_DB = ('commonlib.sql.mysqlUtil', "Direct Database Access (should use Repository).")

BACKEND = 'apps/backend'
COMMONLIB = 'apps/commonlib/commonlib'
SCRAPPER = 'apps/scrapper/scrapper'
SKILL = 'apps/aiEnrichSkill/src/aiEnrichSkill'
FORM = 'apps/aiFormFiller/src/aiFormFiller'
ENRICH = 'apps/aiEnrich/src/aiEnrich'
CRON = 'apps/cron/src/cron'


@dataclass(frozen=True)
class LayerRule:
    module: str
    package: str
    layer: str
    forbidden: tuple = ()
    required: tuple = ()
    ignore_files: frozenset = frozenset({'__init__.py'})

    @property
    def key(self):
        return (self.module, self.layer)

    def path(self, root):
        return root / self.module / self.layer

    def extra_files(self, root):
        """Root-level files whose name declares a layer, so they cannot escape directory rules."""
        suffixes = FILE_LAYER_SUFFIXES.get(self.layer, ())
        package_dir = root / self.module
        if not suffixes or not package_dir.is_dir():
            return ()
        return tuple(path for path in sorted(package_dir.glob('*.py'))
            if path.name.endswith(suffixes) and path.name not in self.ignore_files)


LAYER_RULES = (
    LayerRule(BACKEND, 'backend', 'api', required=(('services', "Missing Service layer import."),), forbidden=(NO_REPOSITORIES,), ignore_files=frozenset({'__init__.py', 'main.py'})),
    LayerRule(BACKEND, 'backend', 'services', forbidden=(NO_API, NO_DB)),
    LayerRule(BACKEND, 'backend', 'repositories', forbidden=(NO_SERVICES, NO_API)),
    LayerRule(BACKEND, 'backend', 'middleware', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(BACKEND, 'backend', 'models', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(BACKEND, 'backend', 'utils', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(COMMONLIB, 'commonlib', 'decorator', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(COMMONLIB, 'commonlib', 'network', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES, ('sql', "Network layer must not import SQL layer."))),
    LayerRule(COMMONLIB, 'commonlib', 'repositories', forbidden=(NO_SERVICES, NO_API)),
    LayerRule(COMMONLIB, 'commonlib', 'services', forbidden=(NO_API, NO_DB)),
    LayerRule(COMMONLIB, 'commonlib', 'sql', forbidden=(NO_SERVICES, NO_API)),
    LayerRule(COMMONLIB, 'commonlib', 'sync', forbidden=(NO_API, NO_SERVICES, ('sql', "Sync layer must not import SQL layer."))),
    LayerRule(SCRAPPER, 'scrapper', 'core', forbidden=(('navigator', "Core layer must not import Navigator."), ('executor', "Core layer must not import Executor."), NO_SERVICES, ('util', "Core layer must not import Util."))),
    LayerRule(SCRAPPER, 'scrapper', 'executor', forbidden=()),
    LayerRule(SCRAPPER, 'scrapper', 'orchestration', forbidden=()),
    LayerRule(SCRAPPER, 'scrapper', 'navigator', forbidden=(('executor', "Navigator layer must not import Executor."),)),
    LayerRule(SCRAPPER, 'scrapper', 'services', forbidden=(('navigator', "Service layer must not import Navigator."), ('executor', "Service layer must not import Executor."))),
    LayerRule(SCRAPPER, 'scrapper', 'util', forbidden=(NO_SERVICES, ('navigator', "Util layer must not import Navigator."), ('executor', "Util layer must not import Executor."))),
    LayerRule(SKILL, 'aiEnrichSkill', 'domain', forbidden=(NO_SERVICES, NO_REPOSITORIES, NO_API)),
    LayerRule(SKILL, 'aiEnrichSkill', 'repositories', forbidden=(NO_SERVICES, NO_API)),
    LayerRule(SKILL, 'aiEnrichSkill', 'services', forbidden=(NO_API, NO_DB)),
    LayerRule(FORM, 'aiFormFiller', 'api', forbidden=(NO_REPOSITORIES, NO_DB)),
    LayerRule(FORM, 'aiFormFiller', 'models', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(FORM, 'aiFormFiller', 'services', forbidden=(NO_API, NO_DB)),
    LayerRule(ENRICH, 'aiEnrich', 'config', forbidden=(NO_API, NO_SERVICES, NO_REPOSITORIES)),
    LayerRule(CRON, 'cron', 'jobs', forbidden=(NO_API, NO_SERVICES, NO_DB)),
)


def discover_layer_keys(root):
    apps_dir = root / 'apps'
    keys = set()
    if not apps_dir.exists():
        return keys
    module_dirs = set()
    for app_dir in sorted(apps_dir.iterdir()):
        if not app_dir.is_dir() or app_dir.name in {'web', 'e2e'}:
            continue
        candidates = [app_dir, app_dir / app_dir.name]
        if (app_dir / 'src').is_dir():
            candidates.extend(path for path in (app_dir / 'src').iterdir() if path.is_dir())
        module_dirs.update(path for path in candidates if path.is_dir() and any(path.glob('*.py')))
        for current, dirs, _ in os.walk(app_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDES and d != 'test']
            for name in dirs:
                if name in LAYER_DIRS:
                    keys.add((Path(current).relative_to(root).as_posix(), name))
                    module_dirs.add(Path(current))
    for package_dir in module_dirs:
        for path in package_dir.glob('*.py'):
            layer = layer_from_filename(path.name)
            if layer and path.name != '__init__.py':
                keys.add((Path(package_dir).relative_to(root).as_posix(), layer))
    return keys
