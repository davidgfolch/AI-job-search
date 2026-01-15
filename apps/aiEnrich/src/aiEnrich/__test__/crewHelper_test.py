import pytest

from ..crewHelper import rawToJson, validateResult


@pytest.mark.parametrize("raw, expected", [
    ('{"key": "value"}', {"key": "value"}),
    ('\nThought: This is a thought\n{"key": "value"}', {"key": "value"}),
    ('json object {"key": "value"}', {"key": "value"}),
    ('```{"key": "value"}```', {"key": "value"}),
    ('some text before { "key": "value" }', {"key": "value"}),
    ('{"key": "value"} some text after', {"key": "value"}),
    ('{"salary": "xx" + "yy"}', {"salary": "xx + yy"}),
    ('{"key": "value\\&"}', {"key": "value&"}),
    ('{"key": "value"', {"key": "value"}),
    ('{"key": "value", "key2": "value2"', {"key": "value", "key2": "value2"}),
    ('{"key": "value"}}', {"key": "value"}),
    ('{"key": 10}}', {"key": 10}),
    ('{"cv_match_percentage": 0}}', {"cv_match_percentage": 0}),
    ('{"any_param": 0,}', {"any_param": 0}),
])
def test_rawToJson(raw, expected):
    assert rawToJson(raw) == expected


@pytest.mark.parametrize("raw", [
    '{"key": "value", "key2": "value2" some text after',  # Invalid JSON
])
def test_rawToJson_invalid_json(raw):
    with pytest.raises(Exception):
        rawToJson(raw)


@pytest.mark.parametrize("result, expected", [
    ({"salary": "50000"},
     {"salary": "50000", "required_technologies": None, "optional_technologies": None}),
    ({"salary": "sueldo: 50000"},
     {"salary": "50000", "required_technologies": None, "optional_technologies": None}),
    ({"salary": "salario: 50000"},
     {"salary": "50000", "required_technologies": None, "optional_technologies": None}),
    ({"salary": "según experiencia: 50000"},
     {"salary": "50000", "required_technologies": None, "optional_technologies": None}),
    ({"salary": "no numbers"},
     {"salary": None, "required_technologies": None, "optional_technologies": None}),
    ({"salary": "50000", "required_technologies": ["Python", "Django"]},
     {"salary": "50000", "required_technologies": "Python,Django", "optional_technologies": None}),
    ({"salary": "50000", "optional_technologies": ["Flask", "SQLAlchemy"]},
     {"salary": "50000", "optional_technologies": "Flask,SQLAlchemy", "required_technologies": None}),
    ({"salary": "50000", "required_technologies": [], "optional_technologies": []},
     {"salary": "50000", "required_technologies": None, "optional_technologies": None}),
])
def test_validateResult(result, expected):
    validateResult(result)
    assert result == expected
