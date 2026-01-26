import pytest
from unittest.mock import MagicMock, patch
from commonlib.skill_enricher_service import process_skill_enrichment

@patch("commonlib.mysqlUtil.MysqlUtil")
@patch("commonlib.skill_enricher_service.get_skill_context")
def test_process_skill_enrichment_no_skills(mock_context, mock_mysql_cls):
    mysql = MagicMock()
    # mock_mysql_cls.return_value.__enter__.return_value = mysql # Not needed if passing instance
    
    mysql.fetchAll.return_value = []
    
    count = process_skill_enrichment(mysql, lambda n, c: "desc")
    assert count == 0

def test_process_skill_enrichment_success():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    
    # Mock get_skill_context to return something
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value="Description")
        
        count = process_skill_enrichment(mysql, gen_fn)
        
        assert count == 1
        gen_fn.assert_called_with("Skill1", "Context")
        mysql.executeAndCommit.assert_called_once()
        args = mysql.executeAndCommit.call_args[0]
        assert args[1] == ["Description", "Skill1"]

def test_process_skill_enrichment_gen_fail():
    mysql = MagicMock()
    mysql.fetchAll.return_value = [("Skill1",)]
    
    with patch("commonlib.skill_enricher_service.get_skill_context", return_value="Context"):
        gen_fn = MagicMock(return_value=None) # Fail gen
        
        count = process_skill_enrichment(mysql, gen_fn)
        
        assert count == 0
        mysql.executeAndCommit.assert_not_called()
