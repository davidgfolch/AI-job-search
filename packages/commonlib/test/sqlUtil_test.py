import pytest
from commonlib.sqlUtil import (
    getAndFilter,
    formatSql,
    regexSubs,
    getColumnTranslated,
    updateFieldsQuery,
    deleteJobsQuery,
    emptyToNone,
    maxLen,
    inFilter,
    binaryColumnIgnoreCase
)
import re
from commonlib.sqlUtil import avoidInjection, scapeRegexChars


class TestSqlUtil:
    @pytest.mark.parametrize("filters,include,expected", [
        ([], None, ''),
        (['a=1'], None, ' and not (a=1)'),
        (['a=1', 'b=2'], None, ' and not (a=1 or b=2)'),
        (['a=1'], True, ' and (a=1)'),
        (['a=1', 'b=2'], True, ' and (a=1 and b=2)'),
    ])
    def test_getAndFilter(self, filters, include, expected):
        assert getAndFilter(filters, include) == expected

    def test_formatSql(self):
        query = "select * from table where a=1 and b=2"
        formatted = formatSql(query)
        assert "\n\t and " in formatted
        
        query_comma = "SELECT a,b FROM table"
        formatted_comma = formatSql(query_comma)
        assert "a, b" in formatted_comma

    def test_regexSubs(self):
        txt = "hello world"
        subs = [(r'hello', r'hi')]
        assert regexSubs(txt, subs) == "hi world"

    @pytest.mark.parametrize("column,expected", [
        ('`my_column`', 'My column'),
        ('user_name', 'User name'),
    ])
    def test_getColumnTranslated(self, column, expected):
        assert getColumnTranslated(column) == expected

    def test_updateFieldsQuery(self):
        ids = [1, 2]
        fields = {'name': 'New Name', 'age': 30}
        query, params = updateFieldsQuery(ids, fields)
        
        assert "UPDATE jobs SET" in query
        assert "name=%(name)s" in query
        assert "age=%(age)s" in query
        assert "WHERE id  in (1,2)" in query
        assert params == fields
        
        # Test merged=True
        query_merged, _ = updateFieldsQuery(ids, fields, merged=True)
        assert "merged=NOW()" in query_merged

    def test_updateFieldsQuery_empty_ids(self):
        assert updateFieldsQuery([], {}) == (None, None)

    def test_deleteJobsQuery(self):
        ids = ["1", "2"]
        query = deleteJobsQuery(ids)
        assert "DELETE FROM jobs" in query
        assert "WHERE id  in (1,2)" in query

    def test_deleteJobsQuery_empty(self):
        assert deleteJobsQuery([]) is None

    def test_emptyToNone(self):
        params = ("a", "", "b", "   ")
        expected = ("a", None, "b", None)
        assert emptyToNone(params) == expected

    def test_maxLen(self):
        params = ("short", "very long string")
        max_lens = (10, 5)
        # "[...]" length is 5. So if max is 5, it cuts a lot.
        # The logic is val[:(max-len('[...]'))]+'[...]'
        # If max=5, len('[...]')=5, so val[:0] + '[...]' -> '[...]'
        
        result = maxLen(params, max_lens)
        assert result[0] == "short"
        assert result[1] == "[...]"
        
        params2 = ("exact",)
        max_lens2 = (5,)
        # 5 - 5 = 0. "exact"[:0] + [...] -> [...]
        # Wait, if len("exact") > 5? No, len is 5. Logic: if len(val) > max.
        # 5 > 5 is False. So it returns val.
        assert maxLen(params2, max_lens2)[0] == "exact"
        
        params3 = ("longer",)
        max_lens3 = (5,)
        # 6 > 5. "longer"[:0] + [...] -> [...]
        assert maxLen(params3, max_lens3)[0] == "[...]"

    def test_inFilter(self):
        ids = [1, 2, 3]
        assert inFilter(ids) == " in (1,2,3)"

    @pytest.mark.parametrize("column,expected", [
        ('comments', 'CONVERT(comments USING utf8mb4) COLLATE utf8mb4_0900_ai_ci'),
        ('other', 'other'),
    ])
    def test_binaryColumnIgnoreCase(self, column, expected):
        assert binaryColumnIgnoreCase(column) == expected


class TestValidateSafeString:
    """Test the avoidInjection function for SQL injection protection"""

    @pytest.mark.parametrize("company_name", [
        "Tech Corp",
        "Google Inc.",
        "ABC-123",
        "Company & Co",
        "O'Reilly Media",
        "Company (USA)",
    ])
    def test_valid_inputs(self, company_name):
        """Test that valid company names pass validation"""
        assert avoidInjection(company_name, "company") == company_name
    
    def test_semicolon(self):
        """Test that semicolons are blocked"""
        with pytest.raises(ValueError, match="semicolon"):
            avoidInjection("Company; DROP TABLE jobs--", "company")
    
    @pytest.mark.parametrize("malicious_input,expected_pattern", [
        ("Company-- comment", "SQL comment"),
        ("Company /* comment */", "multi-line comment"),
    ])
    def test_sql_comment(self, malicious_input, expected_pattern):
        """Test that SQL comments are blocked"""
        with pytest.raises(ValueError, match=expected_pattern):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("malicious_input", [
        "Company UNION SELECT",
        "union all select",
    ])
    def test_union_keyword(self, malicious_input):
        """Test that UNION keyword is blocked"""
        with pytest.raises(ValueError, match="UNION keyword"):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("malicious_input", [
        "Company SELECT * FROM",
        "select * from jobs",
    ])
    def test_select_keyword(self, malicious_input):
        """Test that SELECT keyword is blocked"""
        with pytest.raises(ValueError, match="SELECT keyword"):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("malicious_input,expected_pattern", [
        ("DROP TABLE jobs", "DROP keyword"),
        ("DELETE FROM jobs", "DELETE keyword"),
        ("INSERT INTO jobs", "INSERT keyword"),
        ("UPDATE jobs SET", "UPDATE keyword"),
        ("EXEC sp_", "EXEC keyword"),
        ("EXECUTE procedure", "EXECUTE keyword"),
    ])
    def test_dangerous_keywords(self, malicious_input, expected_pattern):
        """Test that various dangerous SQL keywords are blocked"""
        with pytest.raises(ValueError, match=expected_pattern):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("malicious_input,expected_pattern", [
        ("Company id=1", "equals sign"),
        ("Company id<100", "less than sign"),
        ("Company id>0", "greater than sign"),
    ])
    def test_sql_operators(self, malicious_input, expected_pattern):
        """Test that SQL operators are blocked"""
        with pytest.raises(ValueError, match=expected_pattern):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("malicious_input,expected_pattern", [
        ("1 OR 1=1", "OR keyword"),
        ("1 AND 1=1", "AND keyword"),
    ])
    def test_logical_operators(self, malicious_input, expected_pattern):
        """Test that logical operators are blocked"""
        with pytest.raises(ValueError, match=expected_pattern):
            avoidInjection(malicious_input, "company")
    
    @pytest.mark.parametrize("empty_value", [
        "",
        None,
    ])
    def test_empty_input(self, empty_value):
        """Test that empty strings are rejected"""
        with pytest.raises(ValueError, match="must be a non-empty string"):
            avoidInjection(empty_value, "company")
    
    @pytest.mark.parametrize("malicious_input,expected_pattern", [
        ("SELECT * FROM jobs", "SELECT keyword"),
        ("UnIoN SeLeCt", "UNION keyword"),
    ])
    def test_case_insensitive(self, malicious_input, expected_pattern):
        """Test that validation is case-insensitive"""
        with pytest.raises(ValueError, match=expected_pattern):
            avoidInjection(malicious_input, "company")
    
    def test_custom_param_name(self):
        """Test that custom parameter names appear in error messages"""
        with pytest.raises(ValueError, match="client contains"):
            avoidInjection("DROP TABLE", "client")


class TestSqlRegexChars:
    """Test the scapeRegexChars function for regex escaping"""
    
    @pytest.mark.parametrize("input_str,expected", [
        ("Company (USA)", "Company \\(USA\\)"),
        ("Company[123]", "Company\\[123\\]"),
        ("A|B Company", "A\\|B Company"),
        ("Company*", "Company\\*"),
        ("C++ Developer", "C\\+\\+ Developer"),
        ("(A|B)*[123]+", "\\(A\\|B\\)\\*\\[123\\]\\+"),
        ("Regular Company Name", "Regular Company Name"),
    ])
    def test_sql_regex_chars(self, input_str, expected):
        """Test that regex special characters are properly escaped"""
        assert scapeRegexChars(input_str) == expected