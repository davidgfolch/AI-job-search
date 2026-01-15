import pytest
import json
import os
from scrapper.util.persistence_manager import PersistenceManager

@pytest.fixture
def manager(tmp_path):
    f = tmp_path / "state.json"
    return PersistenceManager(str(f))

def write_json(path, data):
    with open(path, 'w') as f:
        json.dump(data, f)

def read_json(path):
    if not os.path.exists(path): return {}
    with open(path, 'r') as f:
        return json.load(f)

@pytest.mark.parametrize("content, expected", [
    (None, {}),
    ({'LinkedIn': {'keyword': 'py', 'page': 3}}, {'LinkedIn': {'keyword': 'py', 'page': 3}}),
    ('invalid', {}) 
])
def test_init_and_load(tmp_path, content, expected):
    f = tmp_path / "test.json"
    if content is not None:
        if isinstance(content, dict): write_json(f, content)
        else: f.write_text(content, encoding='utf-8')
    
    pm = PersistenceManager(str(f))
    assert pm.state == expected
    assert pm.load() == expected

def test_save(manager):
    manager.state = {'S': {'k': 'v', 'p': 1}}
    manager.save()
    assert read_json(manager.filepath) == {'S': {'k': 'v', 'p': 1}}

@pytest.mark.parametrize("initial, site, kw, page, expected", [
    ({}, 'Indeed', 'java', 3, {'keyword': 'java', 'page': 3}),
    ({'G': {'keyword': 'old', 'page': 1}}, 'G', 'new', 10, {'keyword': 'new', 'page': 10}),
])
def test_update_state(manager, initial, site, kw, page, expected):
    manager.state = initial.copy()
    manager.update_state(site, kw, page)
    assert manager.state[site] == expected
    assert read_json(manager.filepath)[site] == expected

@pytest.mark.parametrize("initial, site, expected", [
    ({'A': {'keyword':'v','page':1}}, 'A', {'A': {}}),
    ({'A': {'keyword':'v','page':1}}, 'B', {'A': {'keyword':'v','page':1}})
])
def test_clear_state(manager, initial, site, expected):
    manager.state = initial.copy()
    manager.save()
    manager.clear_state(site)
    assert manager.state == expected
    assert read_json(manager.filepath) == expected

def test_finalize_scrapper_logic(manager):
    # 1. Clear
    manager.update_state('S1', 'k1', 1)
    if 'failed_keywords' in manager.state['S1']: del manager.state['S1']['failed_keywords']
    manager.finalize_scrapper('S1')
    assert manager.get_state('S1').get('keyword') is None
    
    # 2. Failed keywords -> Keep
    manager.update_state('S2', 'k2', 2)
    manager.add_failed_keyword('S2', 'fk')
    manager.finalize_scrapper('S2')
    assert manager.get_state('S2')['keyword'] == 'k2'
    
    # 3. Last error cleanup
    manager.set_error('S3', 'Err')
    manager.finalize_scrapper('S3')
    assert manager.get_state('S3').get('last_error') is None

def test_failed_keywords_crud(manager):
    site = "S"
    assert manager.get_failed_keywords(site) == []
    manager.add_failed_keyword(site, "k1")
    assert manager.get_failed_keywords(site) == ["k1"]
    # Dup check
    manager.add_failed_keyword(site, "k1")
    assert manager.get_failed_keywords(site) == ["k1"]
    manager.remove_failed_keyword(site, "k1")
    assert manager.get_failed_keywords(site) == []

def test_resume_logic(manager):
    site = "R"
    manager.update_state(site, "r_kw", 5)
    manager.prepare_resume(site)
    assert manager._resume_keyword == "r_kw"
    assert manager._resume_page == 5
    assert manager._is_skipping is True
    
    # Check skipping logic
    assert manager.should_skip_keyword("other")[0] is True
    skip, page = manager.should_skip_keyword("r_kw")
    assert not skip and page == 5
    assert manager.should_skip_keyword("next")[0] is False

def test_misc_getters_setters(manager):
    site = "M"
    manager.update_last_execution(site, "ts")
    assert manager.get_last_execution(site) == "ts"
    manager.set_error(site, "err")
    assert manager.get_state(site)['last_error'] == "err"
