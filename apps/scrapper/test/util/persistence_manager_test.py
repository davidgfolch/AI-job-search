import pytest
import json
import os
import tempfile
from scrapper.util.persistence_manager import PersistenceManager

class TestPersistenceManager:
    @pytest.fixture
    def temp_file(self):
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def manager(self, temp_file):
        return PersistenceManager(temp_file)

    def _write_to_file(self, filepath, content):
        if not isinstance(content, str):
            content = json.dumps(content)
        with open(filepath, 'w') as f:
            f.write(content)

    def _read_from_file(self, filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    
    @pytest.mark.parametrize("file_content, expected_state", [
        (None, {}),
        ({'LinkedIn': {'keyword': 'python', 'page': 3}}, {'LinkedIn': {'keyword': 'python', 'page': 3}}),
        ('invalid json {', {})
    ])
    def test_initialization(self, temp_file, file_content, expected_state):
        if file_content is not None:
            self._write_to_file(temp_file, file_content)
        elif os.path.exists(temp_file):
             os.remove(temp_file)
             
        manager = PersistenceManager(temp_file)
        assert manager.state == expected_state

    @pytest.mark.parametrize("file_content, expected_loaded", [
        ({'Indeed': {'keyword': 'java', 'page': 2}}, {'Indeed': {'keyword': 'java', 'page': 2}}),
        ('{"incomplete": ', {}),
        (None, {})
    ])
    def test_load(self, temp_file, file_content, expected_loaded):
        if file_content is not None:
             self._write_to_file(temp_file, file_content)
        elif os.path.exists(temp_file): # case for testing nonexistent file load logic if needed, but handled by manager init usually. 
             # For load() specifically on nonexistent, we need to pass a path that doesn't exist or ensure it's gone
             os.remove(temp_file)
             
        manager = PersistenceManager(temp_file)
        # If we just removed it, manager might init empty. load() check:
        if file_content is None:
             # Point to a definitely non-existent file for this specific test case if needed
             manager.filepath = "nonexistent_file_test.json"
        
        assert manager.load() == expected_loaded

    @pytest.mark.parametrize("initial_data, new_state, expected_saved", [
        (None, {'Glassdoor': {'keyword': 'dev', 'page': 1}}, {'Glassdoor': {'keyword': 'dev', 'page': 1}}),
        ({'site1': {'k': 'v1', 'p': 1}}, {'site2': {'k': 'v2', 'p': 2}}, {'site2': {'k': 'v2', 'p': 2}})
    ])
    def test_save(self, manager, temp_file, initial_data, new_state, expected_saved):
        if initial_data:
            self._write_to_file(temp_file, initial_data)
        manager.state = new_state
        manager.save()
        assert self._read_from_file(temp_file) == expected_saved

    @pytest.mark.parametrize("initial, site, expected", [
        ({'LinkedIn': {'keyword': 'python', 'page': 5}}, 'LinkedIn', {'keyword': 'python', 'page': 5}),
        ({'LinkedIn': {'keyword': 'python', 'page': 5}}, 'NonExistent', {}),
        ({}, 'Any', {})
    ])
    def test_get_state(self, manager, initial, site, expected):
        manager.state = initial
        assert manager.get_state(site) == expected

    @pytest.mark.parametrize("initial, site, kw, page, expected_entry", [
        ({}, 'Indeed', 'java', 3, {'keyword': 'java', 'page': 3}),
        ({'Glassdoor': {'keyword': 'old', 'page': 1}}, 'Glassdoor', 'new', 10, {'keyword': 'new', 'page': 10}),
        ({'LinkedIn': {'keyword': 'py', 'page': 1}}, 'LinkedIn', 'py', 2, {'keyword': 'py', 'page': 2}),
         ({}, 'Indeed', 'big_page', 99999, {'keyword': 'big_page', 'page': 99999}),
         ({}, 'LinkedIn', 'special/chars', 1, {'keyword': 'special/chars', 'page': 1})
    ])
    def test_update_state(self, manager, temp_file, initial, site, kw, page, expected_entry):
        manager.state = initial.copy()
        manager.update_state(site, kw, page)
        assert manager.state[site] == expected_entry
        assert self._read_from_file(temp_file)[site] == expected_entry

    @pytest.mark.parametrize("initial, site_to_clear, expected", [
        ({'A': {'keyword':'v','page':1}, 'B': {'keyword':'v','page':2}}, 'A', {'A': {}, 'B': {'keyword':'v','page':2}}),
        ({'B': {'keyword':'v','page':2}}, 'NonExistent', {'B': {'keyword':'v','page':2}}),
        ({}, 'Any', {})
    ])
    def test_clear_state(self, manager, temp_file, initial, site_to_clear, expected):
        manager.state = initial.copy()
        manager.save()
        manager.clear_state(site_to_clear)
        assert manager.state == expected
        assert self._read_from_file(temp_file) == expected

    def test_complex_scenarios(self, temp_file):
        """Combined workflow and concurrency tests"""
        # Workflow
        manager = PersistenceManager(temp_file)
        manager.update_state('LinkedIn', 'dev', 1)
        assert manager.get_state('LinkedIn') == {'keyword': 'dev', 'page': 1}
        manager.update_state('LinkedIn', 'dev', 2)
        assert manager.get_state('LinkedIn')['page'] == 2
        manager.clear_state('LinkedIn')
        assert manager.state['LinkedIn'] == {}
        
        # Concurrency/Multiple Sites
        manager.state = {}
        manager.update_state('S1', 'k1', 1)
        manager.update_state('S2', 'k2', 2)
        assert len(manager.state) == 2
        
        # Persistence across instances
        manager.save()
        manager2 = PersistenceManager(temp_file)
        assert manager2.state == manager.state

    def test_finalize_scrapper(self, manager):
        # Case 1: No failed keywords, should clear state
        site1 = 'Site1'
        manager.update_state(site1, 'kw1', 1)
        # Ensure no failed keywords
        if 'failed_keywords' in manager.state.get(site1, {}):
            del manager.state[site1]['failed_keywords']
        manager.finalize_scrapper(site1)
        assert manager.get_state(site1).get('keyword') is None
        assert manager.get_state(site1).get('page') is None
        # Case 2: With failed keywords, should NOT clear state
        site2 = 'Site2'
        manager.update_state(site2, 'kw2', 2)
        manager.add_failed_keyword(site2, 'failed_kw')
        manager.finalize_scrapper(site2)
        assert manager.get_state(site2).get('keyword') == 'kw2'
        assert manager.get_state(site2).get('page') == 2
        # Case 3: Verify last_error cleanup
        site3 = 'Site3'
        manager.update_state(site3, 'kw3', 3)
        manager.set_error(site3, "Some error")
        assert manager.get_state(site3).get('last_error') == "Some error"
        manager.finalize_scrapper(site3)
        assert manager.get_state(site3).get('last_error') is None

    def test_last_execution(self, manager):
        site = "SiteExec"
        assert manager.get_last_execution(site) is None
        
        ts = "2023-01-01 12:00:00"
        manager.update_last_execution(site, ts)
        assert manager.get_last_execution(site) == ts
        
        # Test persistence
        manager.save()
        manager2 = PersistenceManager(manager.filepath)
        assert manager2.get_last_execution(site) == ts

    def test_failed_keywords(self, manager):
        site = "SiteFailed"
        assert manager.get_failed_keywords(site) == []
        
        manager.add_failed_keyword(site, "kw1")
        assert manager.get_failed_keywords(site) == ["kw1"]
        
        manager.add_failed_keyword(site, "kw2")
        assert set(manager.get_failed_keywords(site)) == {"kw1", "kw2"}
        
        # Test duplicate addition
        manager.add_failed_keyword(site, "kw1")
        assert len(manager.get_failed_keywords(site)) == 2
        
        manager.remove_failed_keyword(site, "kw1")
        assert manager.get_failed_keywords(site) == ["kw2"]
        
        # Remove non-existent
        manager.remove_failed_keyword(site, "kw3") # should not error
        assert manager.get_failed_keywords(site) == ["kw2"]

    def test_resume_logic(self, manager):
        site = "SiteResume"
        manager.update_state(site, "resume_kw", 5)
        
        manager.prepare_resume(site)
        assert manager._resume_keyword == "resume_kw"
        assert manager._resume_page == 5
        assert manager._is_skipping is True
        
        # Test should_skip_keyword
        # Keyword comes before resume_kw -> skip
        skip, page = manager.should_skip_keyword("other_kw")
        assert skip is True
        assert page == 1
        
        # Keyword matches resume_kw -> do not skip, start at resume page
        skip, page = manager.should_skip_keyword("resume_kw")
        assert skip is False
        assert page == 5
        assert manager._is_skipping is False
        
        # Keyword comes after resume_kw -> do not skip, default page
        skip, page = manager.should_skip_keyword("next_kw")
        assert skip is False
        assert page == 1

    def test_set_error(self, manager):
        site = "SiteError"
        manager.set_error(site, "Error message")
        
        state = manager.get_state(site)
        assert state['last_error'] == "Error message"
        assert 'last_error_time' in state
        assert isinstance(state['last_error_time'], str)
