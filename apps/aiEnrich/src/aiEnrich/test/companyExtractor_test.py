import json
import os
from unittest.mock import MagicMock, patch

import pytest

from commonlib.company_normalizer import UNSPECIFIED_COMPANY
from commonlib.ollama_client import OllamaResponse
from ..aiEnrich_config import get_max_validation_retries
from ..companyExtractor import MAX_COMPANY_INPUT_LEN, build_company_prompt, resolve_unspecified_company


@pytest.fixture
def repo():
    return MagicMock()


def query_returning(content: str):
    return MagicMock(return_value=json.dumps({"company": content}))


class TestBuildCompanyPrompt:
    def test_includes_title_and_markdown(self):
        prompt = build_company_prompt("Java Developer", "We are Acme")
        assert "# Java Developer" in prompt
        assert "We are Acme" in prompt

    def test_truncates_long_markdown(self):
        prompt = build_company_prompt("Java Developer", "Z" * (MAX_COMPANY_INPUT_LEN + 500))
        assert "Z" * (MAX_COMPANY_INPUT_LEN + 1) not in prompt
        assert prompt.count("Z") == MAX_COMPANY_INPUT_LEN


class TestResolveUnspecifiedCompany:
    def test_skips_job_with_known_company(self, repo):
        query = query_returning("Acme")
        assert resolve_unspecified_company(repo, 1, "Title", "Tech Corp", "Desc", query) is None
        query.assert_not_called()
        repo.update_unspecified_company.assert_not_called()

    @pytest.mark.parametrize("company", [None, "", UNSPECIFIED_COMPANY])
    def test_saves_and_relinks_duplicates(self, repo, company):
        query = query_returning("Acme")
        assert resolve_unspecified_company(repo, 1, "Title", company, "Desc", query) == "Acme"
        repo.update_unspecified_company.assert_called_once_with(1, "Acme")
        repo.refresh_duplicated_of.assert_called_once_with(1, "Title", "Acme")

    @pytest.mark.parametrize("answer", ["null", "", "unknown"])
    def test_keeps_company_when_not_determined(self, repo, answer):
        query = query_returning(answer)
        assert resolve_unspecified_company(repo, 1, "Title", UNSPECIFIED_COMPANY, "Desc", query) is None
        repo.update_unspecified_company.assert_not_called()
        repo.refresh_duplicated_of.assert_not_called()

    def test_keeps_company_when_backend_is_unavailable(self, repo):
        assert resolve_unspecified_company(repo, 1, "Title", UNSPECIFIED_COMPANY, "Desc", MagicMock(return_value=None)) is None
        repo.update_unspecified_company.assert_not_called()

    def test_never_raises_when_resolution_fails(self, repo):
        repo.update_unspecified_company.side_effect = ValueError("db down")
        query = query_returning("Acme")
        assert resolve_unspecified_company(repo, 1, "Title", UNSPECIFIED_COMPANY, "Desc", query) is None
        repo.refresh_duplicated_of.assert_not_called()

    def test_never_raises_on_invalid_response(self, repo):
        query = MagicMock(return_value="not json at all")
        assert resolve_unspecified_company(repo, 1, "Title", UNSPECIFIED_COMPANY, "Desc", query) is None
        repo.update_unspecified_company.assert_not_called()

    def test_retries_the_company_request(self, repo):
        query = MagicMock(side_effect=['{"company":', json.dumps({"company": "Acme"})])
        assert resolve_unspecified_company(repo, 1, "Title", UNSPECIFIED_COMPANY, "Desc", query) == "Acme"
        assert query.call_count == get_max_validation_retries() + 1


EXTRACTION_REPLY = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": "REMOTE"}'


def _ollama_reply(text: str) -> OllamaResponse:
    return OllamaResponse(text=text, url="http://ollama", done=True, done_reason="stop")


def _process_unspecified_job(repo, company: str | None):
    from aiEnrich.dataExtractor import _process_job_safe
    repo.get_job_to_enrich.return_value = (1, "Job", "Desc", company)
    with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", company, "Desc")), \
         patch("aiEnrich.dataExtractor.query_ollama", return_value=_ollama_reply(EXTRACTION_REPLY)), \
         patch("aiEnrich.dataExtractor._save"), \
         patch("aiEnrich.dataExtractor.validateResult"), \
         patch("aiEnrich.dataExtractor.footer"), \
         patch("aiEnrich.dataExtractor.stopWatch"):
        _process_job_safe(repo, 1, 1, 0, "enrich")


class TestCompanyRequestWiring:
    """The company request is a second, independent LLM call made by dataExtractor once a job is enriched."""

    @pytest.mark.parametrize("company", [None, UNSPECIFIED_COMPANY])
    def test_resolves_unspecified_company(self, company):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        repo = MagicMock()
        with patch("aiEnrich.companyExtractor.query_company", return_value=("Acme", None)) as mock_query:
            _process_unspecified_job(repo, company)
        mock_query.assert_called_once()
        repo.update_unspecified_company.assert_called_once_with(1, "Acme")
        repo.refresh_duplicated_of.assert_called_once_with(1, "Job", "Acme")

    def test_does_not_resolve_known_company(self):
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        repo = MagicMock()
        with patch("aiEnrich.companyExtractor.query_company") as mock_query:
            _process_unspecified_job(repo, "Tech Corp")
        mock_query.assert_not_called()
        repo.update_unspecified_company.assert_not_called()
        repo.refresh_duplicated_of.assert_not_called()

    def test_company_request_is_constrained_with_company_schema(self):
        """The company request must not be grammar-constrained with EXTRACTION_SCHEMA.

        EXTRACTION_SCHEMA sets additionalProperties=false, so Ollama could never emit `company` and
        every reply was rejected with "missing fields: company", leaving every tecnoempleo offer
        published without a company stuck on the `unspecified` sentinel.
        """
        os.environ["AI_ENRICH_BACKEND"] = "ollama"
        from aiEnrich.dataExtractor import _process_job_safe
        repo = MagicMock()
        repo.get_job_to_enrich.return_value = (1, "Job", "Desc", UNSPECIFIED_COMPANY)
        replies = [_ollama_reply(EXTRACTION_REPLY), _ollama_reply('{"company": "Acme"}')]
        with patch("aiEnrich.dataExtractor.mapJob", return_value=("Job", UNSPECIFIED_COMPANY, "Desc")), \
             patch("aiEnrich.dataExtractor.query_ollama", side_effect=replies) as mock_ollama, \
             patch("aiEnrich.dataExtractor._save"), \
             patch("aiEnrich.dataExtractor.validateResult"), \
             patch("aiEnrich.dataExtractor.footer"), \
             patch("aiEnrich.dataExtractor.stopWatch"):
            _process_job_safe(repo, 1, 1, 0, "enrich")
        assert mock_ollama.call_count == 2
        extraction_schema, company_schema = (call.kwargs["response_schema"] for call in mock_ollama.call_args_list)
        assert extraction_schema["required"] == ["required_technologies", "optional_technologies", "salary", "modality"]
        assert company_schema["required"] == ["company"]
        assert set(company_schema["properties"]) == {"company"}
        repo.update_unspecified_company.assert_called_once_with(1, "Acme")
        repo.refresh_duplicated_of.assert_called_once_with(1, "Job", "Acme")

    def test_company_request_routes_to_openrouter(self):
        os.environ["AI_ENRICH_BACKEND"] = "openrouter"
        from aiEnrich.dataExtractor import _query_company
        with patch("aiEnrich.dataExtractor.query_openrouter", return_value='{"company": "Acme"}') as mock_or:
            _query_company("prompt", "openrouter", "openrouter/free")
        mock_or.assert_called_once()
