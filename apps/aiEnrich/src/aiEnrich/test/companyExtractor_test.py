import json
from unittest.mock import MagicMock

import pytest

from commonlib.company_normalizer import UNSPECIFIED_COMPANY
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
