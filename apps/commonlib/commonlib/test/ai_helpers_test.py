import pytest
from commonlib.ai_helpers import rawToJson, validateResult, listsToString, fixJsonInvalidAttribute

def test_rawToJson_valid():
    json_str = '{"key": "value"}'
    assert rawToJson(json_str) == {"key": "value"}

def test_rawToJson_with_markdown():
    json_str = '```json\n{"key": "value"}\n```'
    assert rawToJson(json_str) == {"key": "value"}

def test_rawToJson_with_text():
    json_str = 'Here is the json:\n```{"key": "value"}```'
    assert rawToJson(json_str) == {"key": "value"}

def test_fixJsonInvalidAttribute():
    malformed = '{"salary": "100" + "k", "test": "val",",}'
    fixed = fixJsonInvalidAttribute(malformed)
    assert ' + ' in fixed
    assert 'val",' in fixed

def test_listsToString():
    data = {
        "req": ["a", "b"],
        "opt": "c, d", 
        "none": None
    }
    listsToString(data, ["req", "opt", "none"])
    assert data["req"] == "a,b"
    assert data["opt"] == "c,d"
    assert data["none"] is None

def test_validateResult_salary_numbers():
    data = {"salary": "Competitive String with no numbers"}
    validateResult(data)
    assert data["salary"] is None

def test_validateResult_salary_with_numbers():
    data = {"salary": "50k-60k"}
    validateResult(data)
    assert data["salary"] == "50k-60k"

def test_validateResult_cv_match():
    data = {"cv_match_percentage": "85"}
    validateResult(data)
    assert data["cv_match_percentage"] == "85" # Should stay as string or be whatever validateResult leaves it as. 
    # Actually validateResult doesn't cast to int in place, it just validates it can be cast. 
    # Wait, looking at code: result.update({'cv_match_percentage': None}) if invalid. 
    # It does NOT update it to int if valid.
