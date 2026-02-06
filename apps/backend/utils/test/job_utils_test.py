"""Tests for domain utilities."""
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from job_utils import search_partial_company


class TestSearchPartialCompany:
    def test_returns_empty_for_empty_string(self):
        result = search_partial_company("")
        assert result == []

    def test_returns_regex_for_valid_company(self):
        # For "ACME Corp", the function removes the last word "Corp" first
        # then checks "ACME" which is > 2 chars and not a generic word
        result = search_partial_company("ACME Corp")
        assert result == "(^| )ACME($| )"

    def test_returns_empty_for_single_word(self):
        result = search_partial_company("Test")
        assert result == []

    def test_returns_empty_for_generic_words(self):
        # Generic words like "the", "inc" etc. when alone return empty
        # But with other words after, they get the last word stripped
        result = search_partial_company(" grupo")
        assert result == []
        result = search_partial_company(" the")
        assert result == []
        result = search_partial_company(" inc")
        assert result == []
