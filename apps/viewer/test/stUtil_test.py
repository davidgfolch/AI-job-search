import pytest
from unittest.mock import patch
from pandas import DataFrame
from viewer.util.stUtil import (
    stripFields, sortFields, getTextAreaHeightByText,
    scapeLatex, pillsValuesToDict, getSelectedRowsIds
)

class TestStripFields:
    def test_strip_fields(self):
        assert stripFields("id,title,company") == ["id", "title", "company"]
        assert stripFields("id, title , company ") == ["id", "title", "company"]
        assert stripFields("id,\ntitle,\ncompany") == ["id", "title", "company"]

class TestSortFields:
    def test_sort_fields(self):
        assert sortFields("id,title,company", "company,id") == "company,id,title"
        assert sortFields("id,title,company,salary", "title") == "title,id,company,salary"
        with pytest.raises(ValueError):
            sortFields("id,title,company", "")

class TestGetTextAreaHeightByText:
    def test_height_calculation(self):
        assert getTextAreaHeightByText(None) == 140
        assert getTextAreaHeightByText("Single line") == 140
        assert getTextAreaHeightByText("Line 1\nLine 2\nLine 3\nLine 4\nLine 5\nLine 6\nLine 7") == 196
        assert getTextAreaHeightByText("\n" * 30) == 600
        assert getTextAreaHeightByText("test", defaultRows=3, defaultHeight=300) == 84

class TestScapeLatex:
    def test_scape_latex(self):
        data = {"title": "Price $100", "company": "Test Corp"}
        result = scapeLatex(data, ["title"])
        assert result["title"] == "Price \\$100"
        assert result["company"] == "Test Corp"
        
        data = {"title": "$100", "desc": "$200", "other": "$300"}
        result = scapeLatex(data, ["title", "desc"])
        assert result["title"] == "\\$100"
        assert result["desc"] == "\\$200"
        assert result["other"] == "$300"

class TestPillsValuesToDict:
    @patch('viewer.util.stUtil.getState')
    def test_pills_values(self, mock_get_state):
        mock_get_state.return_value = ["field1", "field3"]
        result = pillsValuesToDict("test_key", ["field1", "field2", "field3", "field4"])
        expected = {"field1": True, "field2": False, "field3": True, "field4": False}
        assert result == expected

class TestGetSelectedRowsIds:
    @patch('viewer.util.stUtil.getState')
    def test_get_selected_rows_ids(self, mock_get_state):
        df = DataFrame({"id": [1, 2, 3], "title": ["A", "B", "C"]})
        mock_get_state.return_value = df
        result = getSelectedRowsIds("test_key")
        assert result == [1, 2, 3]