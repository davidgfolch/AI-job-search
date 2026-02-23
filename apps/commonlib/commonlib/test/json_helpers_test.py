import pytest
import json
from commonlib.json_helpers import rawToJson, fixJsonInvalidAttribute

@pytest.mark.parametrize("json_str, expected", [
    ('{"key": "value"}', {"key": "value"}),
    ('```json\n{"key": "value"}\n```', {"key": "value"}),
    ('Here is the json:\n```{"key": "value"}```', {"key": "value"}),
    ('Thought: thinking...\njson object\n{"key": "value"}', {"key": "value"}),
    (r'{"path": "C:\\Windows\\System32"}', {"path": r"C:\Windows\System32"}),
    ('{"key": "Dise\\u00f1o"}', {"key": "Diseño"}),
    ('{"salary": "\\u20ac 50k"}', {"salary": "€ 50k"}),
    ('{"key": "Dise\\\\u00f1o"}', {"key": "Diseño"}),
    ('{"salary": "\\\\u20ac 50k"}', {"salary": "€ 50k"}),
])
def test_rawToJson_valid_cases(json_str, expected):
    assert rawToJson(json_str) == expected

def test_rawToJson_exception():
    with pytest.raises(json.JSONDecodeError):
        rawToJson("{invalid json}")

def test_fixJsonInvalidAttribute():
    malformed = '{"salary": "100" + "k", "test": "val",",}'
    fixed = fixJsonInvalidAttribute(malformed)
    assert ' + ' in fixed
    assert 'val",' in fixed
