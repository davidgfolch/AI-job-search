import pytest
from unittest.mock import patch, MagicMock
from ..dataExtractor import (
    dataExtractor,
    extract_job_data,
    _save,
    retry_failed_jobs,
    _process_job_safe,
    _getJobIdsList,
)


def test_extract_job_data():
    pipe = MagicMock()
    pipe.return_value = [{"generated_text": '{"salary": "100k"}'}]
    pipe.tokenizer.apply_chat_template.return_value = "Prompt"

    with patch("aiEnrichNew.dataExtractor.rawToJson", return_value={"salary": "100k"}):
        res = extract_job_data(pipe, "Title", "Desc")
        assert res["salary"] == "100k"


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.get_pipeline")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_dataExtractor_flow(mock_repo_cls, mock_pipe, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.count_pending_enrichment.return_value = 1
    repo.get_pending_enrichment_ids.return_value = [1]
    repo.get_job_to_enrich.return_value = (1, "Title", b"Desc", "Comp")

    # pipe mock
    pipe = MagicMock()
    mock_pipe.return_value = pipe
    pipe.return_value = [{"generated_text": "JSON"}]

    with (
        patch("aiEnrichNew.dataExtractor.rawToJson", return_value={}),
        patch(
            "aiEnrichNew.dataExtractor.mapJob", return_value=("Title", "Comp", "Desc")
        ),
        patch("aiEnrichNew.dataExtractor._save") as mock_save,
        patch("aiEnrichNew.dataExtractor._getJobIdsList", return_value=[1]),
    ):
        dataExtractor()
        mock_save.assert_called()


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_retry_failed_jobs_no_errors(mock_repo_cls, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.get_enrichment_error_id_retry.return_value = None

    result = retry_failed_jobs()
    assert result == 0


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.get_pipeline")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_retry_failed_jobs_with_error(mock_repo_cls, mock_pipe, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.get_enrichment_error_id_retry.return_value = 123
    repo.get_job_to_retry.return_value = (123, "Title", b"Desc", "Comp")

    pipe = MagicMock()
    mock_pipe.return_value = pipe
    pipe.return_value = [{"generated_text": '{"salary": "100k"}'}]

    with (
        patch("aiEnrichNew.dataExtractor.rawToJson", return_value={"salary": "100k"}),
        patch(
            "aiEnrichNew.dataExtractor.mapJob", return_value=("Title", "Comp", "Desc")
        ),
        patch("aiEnrichNew.dataExtractor._save") as mock_save,
    ):
        retry_failed_jobs()
        mock_save.assert_called()


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_dataExtractor_no_pending_jobs(mock_repo_cls, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.count_pending_enrichment.return_value = 0

    result = dataExtractor()
    assert result == 0


def test_getJobIdsList():
    repo = MagicMock()
    repo.get_pending_enrichment_ids.return_value = [1, 2, 3]

    with patch("aiEnrichNew.dataExtractor.yellow", side_effect=lambda x: x):
        result = _getJobIdsList(repo)

    assert result == [1, 2, 3]
    repo.get_pending_enrichment_ids.assert_called_once()


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_process_job_safe_job_not_found(mock_repo_cls, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.get_job_to_enrich.return_value = None

    pipe = MagicMock()

    _process_job_safe(repo, pipe, 1, 1, 0, "enrich")
    repo.get_job_to_enrich.assert_called_once_with(1)


@patch("aiEnrichNew.dataExtractor.MysqlUtil")
@patch("aiEnrichNew.dataExtractor.get_pipeline")
@patch("aiEnrichNew.dataExtractor.AiEnrichRepository")
def test_process_job_safe_exception(mock_repo_cls, mock_pipe, mock_mysql):
    mysql = MagicMock()
    mock_mysql.return_value.__enter__.return_value = mysql

    repo = MagicMock()
    mock_repo_cls.return_value = repo
    repo.get_job_to_enrich.return_value = (1, "Title", b"Desc", "Comp")
    repo.update_enrichment_error.return_value = 1

    pipe = MagicMock()
    mock_pipe.return_value = pipe
    pipe.side_effect = Exception("Test error")

    with (
        patch(
            "aiEnrichNew.dataExtractor.rawToJson", side_effect=Exception("Parse error")
        ),
        patch(
            "aiEnrichNew.dataExtractor.mapJob", return_value=("Title", "Comp", "Desc")
        ),
    ):
        _process_job_safe(repo, pipe, 1, 1, 0, "enrich")
        repo.update_enrichment_error.assert_called()


def test_save_calls_update():
    repo = MagicMock()
    result = {
        "salary": "100k",
        "required_technologies": "python",
        "optional_technologies": "sql",
    }

    _save(repo, 1, "Company", result)
    repo.update_enrichment.assert_called_once_with(1, "100k", "python", "sql")
