import pytest
import json
import os
import tempfile
from unittest.mock import patch, mock_open, MagicMock
from scrapper.persistence_manager import PersistenceManager


class TestPersistenceManager:
    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing"""
        fd, path = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        yield path
        # Cleanup
        if os.path.exists(path):
            os.remove(path)
    
    @pytest.fixture
    def manager(self, temp_file):
        """Create PersistenceManager with temp file"""
        return PersistenceManager(temp_file)
    
    def test_initialization_with_new_file(self, temp_file):
        """Test initialization creates empty state for new file"""
        # Remove the temp file to simulate first run
        if os.path.exists(temp_file):
            os.remove(temp_file)
        
        manager = PersistenceManager(temp_file)
        assert manager.filepath == temp_file
        assert manager.state == {}
    
    def test_initialization_with_existing_file(self, temp_file):
        """Test initialization loads existing state"""
        test_data = {'LinkedIn': {'keyword': 'python', 'page': 3}}
        with open(temp_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = PersistenceManager(temp_file)
        assert manager.state == test_data
    
    def test_initialization_with_invalid_json(self, temp_file):
        """Test initialization handles invalid JSON gracefully"""
        with open(temp_file, 'w') as f:
            f.write('invalid json {')
        
        manager = PersistenceManager(temp_file)
        assert manager.state == {}
    
    def test_load_existing_file(self, temp_file):
        """Test load method with existing file"""
        test_data = {'Indeed': {'keyword': 'java', 'page': 2}}
        with open(temp_file, 'w') as f:
            json.dump(test_data, f)
        
        manager = PersistenceManager(temp_file)
        loaded = manager.load()
        assert loaded == test_data
    
    def test_load_nonexistent_file(self):
        """Test load method with non-existent file"""
        nonexistent_path = 'nonexistent_file_test_12345.json'
        manager = PersistenceManager(nonexistent_path)
        assert manager.state == {}
        # Cleanup
        if os.path.exists(nonexistent_path):
            os.remove(nonexistent_path)
    
    def test_load_corrupted_json(self, temp_file):
        """Test load method with corrupted JSON"""
        with open(temp_file, 'w') as f:
            f.write('{"incomplete": ')
        
        manager = PersistenceManager(temp_file)
        assert manager.load() == {}
    
    def test_save_creates_file(self, manager, temp_file):
        """Test save method creates file with state"""
        manager.state = {'Glassdoor': {'keyword': 'developer', 'page': 1}}
        manager.save()
        
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == manager.state
    
    def test_save_overwrites_existing(self, manager, temp_file):
        """Test save method overwrites existing file"""
        # Write initial data
        initial_data = {'site1': {'keyword': 'test1', 'page': 1}}
        with open(temp_file, 'w') as f:
            json.dump(initial_data, f)
        
        # Update and save
        manager.state = {'site2': {'keyword': 'test2', 'page': 2}}
        manager.save()
        
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data == {'site2': {'keyword': 'test2', 'page': 2}}
    
    def test_get_state_existing_site(self, manager):
        """Test get_state returns state for existing site"""
        manager.state = {'LinkedIn': {'keyword': 'python', 'page': 5}}
        result = manager.get_state('LinkedIn')
        assert result == {'keyword': 'python', 'page': 5}
    
    def test_get_state_nonexistent_site(self, manager):
        """Test get_state returns empty dict for non-existent site"""
        result = manager.get_state('NonExistentSite')
        assert result == {}
    
    def test_get_state_empty_manager(self, manager):
        """Test get_state with empty state"""
        manager.state = {}
        result = manager.get_state('AnySite')
        assert result == {}
    
    def test_update_state_new_site(self, manager, temp_file):
        """Test update_state adds new site"""
        manager.update_state('Indeed', 'java developer', 3)
        
        assert 'Indeed' in manager.state
        assert manager.state['Indeed'] == {'keyword': 'java developer', 'page': 3}
        
        # Verify it was saved to file
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['Indeed'] == {'keyword': 'java developer', 'page': 3}
    
    def test_update_state_existing_site(self, manager, temp_file):
        """Test update_state updates existing site"""
        manager.state = {'Glassdoor': {'keyword': 'old', 'page': 1}}
        manager.update_state('Glassdoor', 'new keyword', 10)
        
        assert manager.state['Glassdoor'] == {'keyword': 'new keyword', 'page': 10}
        
        # Verify persistence
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data['Glassdoor'] == {'keyword': 'new keyword', 'page': 10}
    
    def test_update_state_increments_page(self, manager, temp_file):
        """Test updating state with incremented page number"""
        manager.update_state('LinkedIn', 'python', 1)
        assert manager.state['LinkedIn']['page'] == 1
        
        manager.update_state('LinkedIn', 'python', 2)
        assert manager.state['LinkedIn']['page'] == 2
        
        manager.update_state('LinkedIn', 'python', 3)
        assert manager.state['LinkedIn']['page'] == 3
    
    def test_clear_state_existing_site(self, manager, temp_file):
        """Test clear_state removes existing site"""
        manager.state = {
            'LinkedIn': {'keyword': 'python', 'page': 3},
            'Indeed': {'keyword': 'java', 'page': 2}
        }
        manager.save()
        
        manager.clear_state('LinkedIn')
        
        assert 'LinkedIn' not in manager.state
        assert 'Indeed' in manager.state
        
        # Verify persistence
        with open(temp_file, 'r') as f:
            saved_data = json.load(f)
        assert 'LinkedIn' not in saved_data
        assert 'Indeed' in saved_data
    
    def test_clear_state_nonexistent_site(self, manager, temp_file):
        """Test clear_state with non-existent site does nothing"""
        initial_state = {'Indeed': {'keyword': 'java', 'page': 2}}
        manager.state = initial_state.copy()
        manager.save()
        
        manager.clear_state('NonExistent')
        
        assert manager.state == initial_state
    
    def test_clear_state_empty_manager(self, manager):
        """Test clear_state on empty state"""
        manager.state = {}
        manager.clear_state('AnySite')
        assert manager.state == {}
    
    def test_multiple_operations_workflow(self, manager, temp_file):
        """Test a realistic workflow with multiple operations"""
        # Start scraping LinkedIn
        manager.update_state('LinkedIn', 'python developer', 1)
        assert manager.get_state('LinkedIn') == {'keyword': 'python developer', 'page': 1}
        
        # Progress to page 2
        manager.update_state('LinkedIn', 'python developer', 2)
        assert manager.get_state('LinkedIn')['page'] == 2
        
        # Start scraping Indeed
        manager.update_state('Indeed', 'java engineer', 1)
        assert len(manager.state) == 2
        
        # Finish LinkedIn scraping
        manager.clear_state('LinkedIn')
        assert 'LinkedIn' not in manager.state
        assert 'Indeed' in manager.state
        
        # Verify persistence
        new_manager = PersistenceManager(temp_file)
        assert 'LinkedIn' not in new_manager.state
        assert new_manager.get_state('Indeed') == {'keyword': 'java engineer', 'page': 1}
    
    def test_concurrent_sites_handling(self, manager):
        """Test managing multiple sites simultaneously"""
        manager.update_state('LinkedIn', 'python', 5)
        manager.update_state('Indeed', 'java', 3)
        manager.update_state('Glassdoor', 'javascript', 2)
        
        assert len(manager.state) == 3
        assert manager.get_state('LinkedIn')['page'] == 5
        assert manager.get_state('Indeed')['page'] == 3
        assert manager.get_state('Glassdoor')['page'] == 2
    
    def test_edge_case_special_characters_in_keyword(self, manager):
        """Test handling special characters in keywords"""
        special_keyword = 'python/django developer (remote) - $150k+'
        manager.update_state('LinkedIn', special_keyword, 1)
        
        state = manager.get_state('LinkedIn')
        assert state['keyword'] == special_keyword
    
    def test_edge_case_large_page_number(self, manager):
        """Test handling large page numbers"""
        manager.update_state('Indeed', 'test', 99999)
        assert manager.get_state('Indeed')['page'] == 99999
    
    def test_state_persistence_across_instances(self, temp_file):
        """Test that state persists across different manager instances"""
        # Create first instance and save state
        manager1 = PersistenceManager(temp_file)
        manager1.update_state('LinkedIn', 'python', 7)
        
        # Create second instance and verify state is loaded
        manager2 = PersistenceManager(temp_file)
        assert manager2.get_state('LinkedIn') == {'keyword': 'python', 'page': 7}
        
        # Update from second instance
        manager2.update_state('LinkedIn', 'python', 8)
        
        # Create third instance and verify
        manager3 = PersistenceManager(temp_file)
        assert manager3.get_state('LinkedIn') == {'keyword': 'python', 'page': 8}
