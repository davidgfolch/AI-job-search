import pytest
from unittest.mock import MagicMock, patch, mock_open
from commonlib.json_helpers import (
    rawToJson, decode_unicode_escapes, fixJsonInvalidAttribute,
    fixJsonEndCurlyBraces, fixJsonStartCurlyBraces, LazyDecoder
)


class TestRawToJson:
    def test_valid_json(self):
        result = rawToJson('{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_thought_prefix(self):
        result = rawToJson('Thought: analysis\n{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_note_prefix(self):
        result = rawToJson('Note: careful\n{"key": "value"}')
        assert result == {"key": "value"}

    def test_json_with_markdown_code_block(self):
        result = rawToJson('```json\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_json_with_backticks_no_json(self):
        result = rawToJson('```\n{"key": "value"}\n```')
        assert result == {"key": "value"}

    def test_json_with_json_prefix(self):
        result = rawToJson('json object {"key": "value"}')
        assert result == {"key": "value"}

    def test_invalid_json_raises(self):
        with pytest.raises(Exception):
            rawToJson("not json at all {{{")

    def test_json_with_backslash_escape(self):
        result = rawToJson('{"key": "value\\.txt"}')
        assert "key" in result


class TestDecodeUnicodeEscapes:
    def test_decode_unicode(self):
        d = {"name": "caf\\u00e9"}
        decode_unicode_escapes(d)
        assert d["name"] == "café"

    def test_decode_no_unicode(self):
        d = {"name": "hello"}
        decode_unicode_escapes(d)
        assert d["name"] == "hello"

    def test_decode_non_string_value(self):
        d = {"count": 42}
        decode_unicode_escapes(d)
        assert d["count"] == 42


class TestFixJsonInvalidAttribute:
    def test_fix_string_concat(self):
        result = fixJsonInvalidAttribute('"salary": "xx" + "yy",')
        assert '"xx + yy"' in result or "xx + yy" in result

    def test_fix_merged_fields(self):
        result = fixJsonInvalidAttribute('"salary": "50,000€, modality": "REMOTE"')
        assert '"REMOTE"' in result

    def test_fix_tex_formula(self):
        result = fixJsonInvalidAttribute('"$\\text{Salary} \\\\$"')
        assert "Salary" in result

    def test_fix_trailing_comma_quote(self):
        result = fixJsonInvalidAttribute('"key": "value",')
        assert '"key": "value"' in result


class TestFixJsonEndCurlyBraces:
    def test_fix_double_closing(self):
        result = fixJsonEndCurlyBraces('{"key": "value"}}')
        assert result.endswith('}')

    def test_fix_trailing_comma(self):
        result = fixJsonEndCurlyBraces('{"key": "value",\n}')
        assert result == '{"key": "value"\n}'

    def test_fix_no_closing_brace(self):
        result = fixJsonEndCurlyBraces('{"key": "value"')
        assert result.endswith('}')

    def test_fix_extra_text_after_brace(self):
        result = fixJsonEndCurlyBraces('{"key": "value"} some extra text')
        assert result == '{"key": "value"}'

    def test_fix_parenthesis_ending(self):
        result = fixJsonEndCurlyBraces('{"key": "value")')
        assert result.endswith('}')


class TestFixJsonStartCurlyBraces:
    def test_fix_extra_text_before(self):
        result = fixJsonStartCurlyBraces('Some text {"key": "value"}')
        assert result.startswith('{')

    def test_already_correct(self):
        result = fixJsonStartCurlyBraces('{"key": "value"}')
        assert result == '{"key": "value"}'

    def test_no_opening_brace(self):
        result = fixJsonStartCurlyBraces('no braces here')
        assert result == 'no braces here'


class TestLazyDecoder:
    def test_fixes_unescaped_backslash(self):
        import json
        decoder = LazyDecoder()
        result = decoder.decode('{"path": "C:\\Users\\test"}')
        assert "path" in result

    def test_fixes_trailing_comma_in_array(self):
        import json
        decoder = LazyDecoder()
        result = decoder.decode('{"items": [1, 2, 3,]}')
        assert result["items"] == [1, 2, 3]
