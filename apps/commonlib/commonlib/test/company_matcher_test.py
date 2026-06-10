import pytest
from commonlib.company_matcher import search_partial_company, get_best_candidate


class TestSearchPartialCompany:
    @pytest.mark.parametrize("name,expected", [
        ("", []),
        ("Test", []),
        (" grupo", []),
        (" the", []),
        (" inc", []),
        ("Grupo Something", []),
    ])
    def test_returns_empty(self, name, expected):
        assert search_partial_company(name) == expected

    @pytest.mark.parametrize("name,expected", [
        ("ACME Corp", "(^| )ACME($| )"),
        ("the big company", "(^| )the\\ big($| )"),
        ("Grupo TECDATA Engineering", "(^| )Grupo\\ TECDATA($| )"),
    ])
    def test_returns_regex(self, name, expected):
        assert search_partial_company(name) == expected


class TestGetBestCandidate:
    @pytest.mark.parametrize("name", ["", None, "Test", "Grupo Digital", "GRUPO NS", "Grupo NS", "The Company", "Grupo Something"])
    def test_returns_none(self, name):
        assert get_best_candidate(name) is None

    @pytest.mark.parametrize("name,expected", [
        ("ACME Corp", "ACME"),
        ("the big company", "the big"),
        ("Grupo TECDATA Engineering", "Grupo TECDATA"),
        ("Experis IT", "Experis"),
        ("The White Team", "The White"),
        ("Big Tech Company Inc", "Big Tech Company"),
    ])
    def test_returns_candidate(self, name, expected):
        assert get_best_candidate(name) == expected
