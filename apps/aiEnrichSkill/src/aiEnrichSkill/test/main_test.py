from unittest.mock import patch, MagicMock

from ..main import run


@patch("aiEnrichSkill.main.consoleTimer")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_disabled(mock_cyan, mock_enabled, mock_mysql, mock_enrich, mock_timer):
    mock_enabled.return_value = False

    run()

    mock_mysql.assert_not_called()
    mock_enrich.assert_not_called()


@patch("aiEnrichSkill.main.consoleTimer")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_enriched_some_skills(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_timer):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [3, 0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    assert mock_enrich.call_count == 3


@patch("aiEnrichSkill.main.consoleTimer")
@patch("aiEnrichSkill.main.enrich_skills")
@patch("aiEnrichSkill.main.MysqlUtil")
@patch("aiEnrichSkill.main.get_enabled")
@patch("aiEnrichSkill.main.cyan", side_effect=lambda x: x)
def test_run_no_skills_waits(mock_cyan, mock_enabled, mock_mysql_cls, mock_enrich, mock_timer):
    mock_enabled.return_value = True
    mysql = MagicMock()
    mock_mysql_cls.return_value.__enter__.return_value = mysql
    mock_enrich.side_effect = [0, Exception("BreakLoop")]

    try:
        run()
    except Exception as e:
        if str(e) != "BreakLoop":
            raise e

    mock_timer.assert_called_once()
