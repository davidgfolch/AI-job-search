from commonlib.modality_extractor import extract_modality


def test_extract_remote():
    assert extract_modality("Java dev", "Remote", "") == "REMOTE"


def test_extract_hybrid():
    assert extract_modality("Java dev", "Hybrid", "") == "HYBRID"


def test_extract_on_site():
    assert extract_modality("Java dev", "On site", "") == "ON_SITE"


def test_extract_unknown_returns_none():
    assert extract_modality("Java dev", "", "") is None


def test_explicit_modalidad_wins():
    assert extract_modality("Title", "", "Modalidad de trabajo: presencial") == "ON_SITE"