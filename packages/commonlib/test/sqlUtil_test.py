import pytest
from commonlib.sqlUtil import (getAndFilter, formatSql, regexSubs, getColumnTranslated, updateFieldsQuery,
    deleteJobsQuery, emptyToNone, maxLen, inFilter, binaryColumnIgnoreCase, avoidInjection, scapeRegexChars)


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

    @pytest.mark.parametrize("query,expected", [
        ("select * from table where a=1 and b=2", "\n\t and "),
        ("SELECT a,b FROM table", "a, b"),
    ])
    def test_formatSql(self, query, expected):
        assert expected in formatSql(query)

    def test_regexSubs(self):
        assert regexSubs("hello world", [(r'hello', r'hi')]) == "hi world"

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
        assert all(x in query for x in ["UPDATE jobs SET", "name=%(name)s", "age=%(age)s", "WHERE id  in (1,2)"])
        assert params == fields
        
        query_merged, _ = updateFieldsQuery(ids, fields, merged=True)
        assert "merged=NOW()" in query_merged

        assert updateFieldsQuery([], {}) == (None, None)

    @pytest.mark.parametrize("ids,expected_parts", [
        (["1", "2"], ["DELETE FROM jobs", "WHERE id  in (1,2)"]),
        ([], None)
    ])
    def test_deleteJobsQuery(self, ids, expected_parts):
        query = deleteJobsQuery(ids)
        if expected_parts is None:
            assert query is None
        else:
            assert all(part in query for part in expected_parts)

    def test_emptyToNone(self):
        assert emptyToNone(("a", "", "b", "   ")) == ("a", None, "b", None)

    @pytest.mark.parametrize("params,max_lens,expected", [
        (("short", "very long string"), (10, 5), ("short", "[...]")),
        (("exact",), (5,), ("exact",)),
        (("longer",), (5,), ("[...]",))
    ])
    def test_maxLen(self, params, max_lens, expected):
        assert maxLen(params, max_lens) == expected

    def test_inFilter(self):
        assert inFilter([1, 2, 3]) == " in (1,2,3)"

    @pytest.mark.parametrize("column,expected", [
        ('comments', 'CONVERT(comments USING utf8mb4) COLLATE utf8mb4_0900_ai_ci'),
        ('other', 'other'),
    ])
    def test_binaryColumnIgnoreCase(self, column, expected):
        assert binaryColumnIgnoreCase(column) == expected


class TestValidateSafeString:
    @pytest.mark.parametrize("company_name", [
        "Tech Corp", "Google Inc.", "ABC-123", "Company & Co", 
        "O'Reilly Media", "Company (USA)"
    ])
    def test_valid_inputs(self, company_name):
        assert avoidInjection(company_name, "company") == company_name

    @pytest.mark.parametrize("malicious_input,match", [
        ("Company; DROP TABLE jobs--", "semicolon"),
        ("Company-- comment", "SQL comment"),
        ("Company /* comment */", "multi-line comment"),
        ("Company UNION SELECT", "UNION keyword"),
        ("union all select", "UNION keyword"),
        ("Company SELECT * FROM", "SELECT keyword"),
        ("select * from jobs", "SELECT keyword"),
        ("DROP TABLE jobs", "DROP keyword"),
        ("DELETE FROM jobs", "DELETE keyword"),
        ("INSERT INTO jobs", "INSERT keyword"),
        ("UPDATE jobs SET", "UPDATE keyword"),
        ("EXEC sp_", "EXEC keyword"),
        ("EXECUTE procedure", "EXECUTE keyword"),
        ("Company id=1", "equals sign"),
        ("Company id<100", "less than sign"),
        ("Company id>0", "greater than sign"),
        ("1 OR 1=1", "OR keyword"),
        ("1 AND 1=1", "AND keyword"),
        ("", "must be a non-empty string"),
        (None, "must be a non-empty string"),
        ("UnIoN SeLeCt", "UNION keyword"),
    ])
    def test_invalid_inputs(self, malicious_input, match):
        with pytest.raises(ValueError, match=match):
            avoidInjection(malicious_input, "company")

    def test_custom_param_name(self):
        with pytest.raises(ValueError, match="client contains"):
            avoidInjection("DROP TABLE", "client")


class TestSqlRegexChars:
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
        assert scapeRegexChars(input_str) == expected