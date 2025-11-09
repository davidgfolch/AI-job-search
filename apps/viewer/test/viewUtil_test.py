import pytest
from unittest.mock import patch
from datetime import datetime
from viewer.util.viewUtil import (
    mapDetailForm, getValueAsDict, formatDateTime, 
    fmtDetailOpField, gotoPageByUrl
)

class TestMapDetailForm:
    @patch('viewer.util.viewUtil.setState')
    def test_map_detail_form(self, mock_set_state):
        job_data = {
            'comments': 'Test comments', 'salary': '50000',
            'company': 'Test Corp', 'client': 'Test Client',
            'applied': True, 'interested': False
        }
        result = mapDetailForm(job_data, ['applied', 'interested', 'discarded'])
        bool_values, comments, salary, company, client = result
        assert bool_values == ['applied']
        assert comments == 'Test comments'
        assert salary == '50000'
        
        result = mapDetailForm(None, ['applied'])
        bool_values, comments, salary, company, client = result
        assert bool_values == []
        assert comments == ''

class TestGetValueAsDict:
    def test_get_value(self):
        assert getValueAsDict('markdown', b'# Test markdown') == '# Test markdown'
        assert getValueAsDict('comments', b'Test comments') == 'Test comments'
        assert getValueAsDict('title', '  Test Title  ') == 'Test Title'
        assert getValueAsDict('id', 123) == 123
        assert getValueAsDict('markdown', None) is None

class TestFormatDateTime:
    def test_format_datetime(self):
        data = {
            'created': datetime(2025, 1, 15, 10, 30),
            'merged': datetime(2025, 1, 16, 11, 45),
            'modified': datetime(2025, 1, 17, 12, 0)
        }
        formatDateTime(data)
        assert 'dates' in data
        assert '15-01-25 10:30' in data['dates']
        
        data = {'created': None, 'merged': None, 'modified': None}
        formatDateTime(data)
        assert data['dates'] == ''

class TestFmtDetailOpField:
    def test_fmt_detail_field(self):
        data = {'salary': '50000'}
        assert fmtDetailOpField(data, 'salary') == '- Salary: :green[50000]\n'
        assert fmtDetailOpField(data, 'salary', 'Annual Salary') == '- Annual Salary: :green[50000]\n'
        assert fmtDetailOpField(data, 'salary', None, 2) == '  - Salary: :green[50000]\n'
        assert fmtDetailOpField({'salary': None}, 'salary') == ''
        assert fmtDetailOpField({}, 'salary') == ''

class TestGotoPageByUrl:
    def test_goto_page_by_url(self):
        result = gotoPageByUrl(1, 'View Jobs', '1,2,3')
        expected = '[View Jobs](/?selectedIds=1,2,3&selectedPage=1&preSelectedRows=0)'
        assert result == expected
        
        result = gotoPageByUrl(2, 'Clean Data', [4, 5, 6])
        expected = '[Clean Data](/?selectedIds=4,5,6&selectedPage=2&preSelectedRows=0)'
        assert result == expected
        
        result = gotoPageByUrl(0, 'Home', '1', autoSelectFirst=False)
        expected = '[Home](/?selectedIds=1&selectedPage=0)'
        assert result == expected