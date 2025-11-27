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

class TestSqlUtil:
    def test_getAndFilter(self):
        assert getAndFilter([], None) == ''
        assert getAndFilter(['a=1'], None) == ' and not (a=1)'
        assert getAndFilter(['a=1', 'b=2'], None) == ' and not (a=1 or b=2)'
        assert getAndFilter(['a=1'], True) == ' and (a=1)'
        assert getAndFilter(['a=1', 'b=2'], True) == ' and (a=1 and b=2)'

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

    def test_getColumnTranslated(self):
        assert getColumnTranslated('`my_column`') == 'My column'
        assert getColumnTranslated('user_name') == 'User name'

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

    def test_binaryColumnIgnoreCase(self):
        assert binaryColumnIgnoreCase('comments') == 'CONVERT(comments USING utf8mb4) COLLATE utf8mb4_0900_ai_ci'
        assert binaryColumnIgnoreCase('other') == 'other'