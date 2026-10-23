import pytest

from commonlib.modality_extractor import extract_modalities, modalities_to_db, normalize_modalities


@pytest.mark.parametrize(
    "title,location,markdown,expected",
    [
        ("Java dev", "Remote", "", ["REMOTE"]),
        ("Java dev", "Hybrid", "", ["HYBRID"]),
        ("Java dev", "On site", "", ["ON_SITE"]),
        ("Java dev", "", "", []),
        ("Title", "", "Modalidad de trabajo: presencial", ["ON_SITE"]),
        ("Title", "", "Modalidad: remoto o híbrido", ["REMOTE", "HYBRID"]),
        ("Title", "", "Flexible: either remote or on-site", ["REMOTE", "ON_SITE"]),
        ("Title", "", "Teletrabajo, presencial o mixto", ["REMOTE", "HYBRID", "ON_SITE"]),
    ],
)
def test_extract_modalities(title, location, markdown, expected):
    assert extract_modalities(title, location, markdown) == expected


def test_multiple_cues_are_all_kept_and_ordered():
    assert extract_modalities("Hybrid role", "", "You can also work remotely") == ["REMOTE", "HYBRID"]


def test_semipresencial_is_not_reported_as_on_site():
    assert extract_modalities("Dev", "", "Jornada semipresencial") == ["HYBRID"]


def test_explicit_modalidad_wins_over_the_whole_description():
    markdown = "Modalidad: presencial\n\nEl resto del equipo trabaja en remoto."
    assert extract_modalities("Dev", "", markdown) == ["ON_SITE"]


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, []),
        ("", []),
        ("REMOTE", ["REMOTE"]),
        ("REMOTE,HYBRID", ["REMOTE", "HYBRID"]),
        ("ON_SITE,HYBRID,REMOTE", ["REMOTE", "HYBRID", "ON_SITE"]),
        (["hybrid", " remote ", "hybrid"], ["REMOTE", "HYBRID"]),
        (("ON_SITE",), ["ON_SITE"]),
        ("remote,bogus", ["REMOTE"]),
        (["REMOTE,HYBRID"], ["REMOTE", "HYBRID"]),
        (42, []),
    ],
)
def test_normalize_modalities(value, expected):
    assert normalize_modalities(value) == expected


@pytest.mark.parametrize(
    "value,expected",
    [
        (None, None),
        ([], None),
        (["REMOTE"], "REMOTE"),
        ("HYBRID,REMOTE", "REMOTE,HYBRID"),
        (["REMOTE", "HYBRID", "ON_SITE"], "REMOTE,HYBRID,ON_SITE"),
        (["bogus"], None),
    ],
)
def test_modalities_to_db(value, expected):
    assert modalities_to_db(value) == expected
