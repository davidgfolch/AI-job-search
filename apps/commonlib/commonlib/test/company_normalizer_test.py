from commonlib.company_normalizer import normalize_company_name


def test_empty_name():
    assert normalize_company_name(None) == ""
    assert normalize_company_name("") == ""

def test_lowercases_and_trims():
    assert normalize_company_name("  ACME Corp  ") == "acme corp"

def test_removes_parentheticals():
    assert normalize_company_name("Company (Spain)") == "company"

def test_removes_suffixes():
    assert normalize_company_name("ACME Inc") == "acme"
    assert normalize_company_name("ACME, LLC") == "acme"
    assert normalize_company_name("Company S.L.") == "company"

def test_removes_special_chars():
    assert normalize_company_name("Tech@Corp!") == "techcorp"

def test_collapses_spaces():
    assert normalize_company_name("  Tech   Corp  ") == "tech corp"
