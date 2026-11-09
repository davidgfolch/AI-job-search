from unittest.mock import MagicMock

import pytest

from ..technology_grounding import filter_ungrounded_technologies


def extraction(required=(), optional=()):
    return {"required_technologies": list(required), "optional_technologies": list(optional), "salary": None, "modality": ["REMOTE"]}


@pytest.mark.parametrize("term, offer", [
    ("Java", "Backend en Java con Spring Boot"),
    ("Spring Boot", "experiencia en spring boot"),
    ("Node.js", "Desarrollo con Node.js y TypeScript"),
    ("CI/CD", "pipelines CI/CD"),
    ("C++", "programación en C++"),
    ("C#", "servicios en C#"),
    ("Fortran (90+)", "conocimientos de Fortran (90+)"),
    ("scikit-learn", "usando scikit-learn"),
    ("Programación", "programacion orientada a objetos"),
    ("Análisis", "analisis de datos"),
])
def test_grounded_technologies_are_kept(term, offer):
    assert filter_ungrounded_technologies(extraction(required=[term]), offer)["required_technologies"] == [term]


@pytest.mark.parametrize("term, offer", [
    ("Docker", "Backend en Java con Spring Boot"),
    ("Java", "Experiencia con JavaScript"),
    ("SQL", "bases de datos NoSQL"),
    ("Microservices architecture", "arquitecturas de microservicios"),
    ("AWS", ""),
])
def test_ungrounded_technologies_are_dropped(term, offer):
    assert filter_ungrounded_technologies(extraction(required=[term]), offer)["required_technologies"] == []


def test_accepts_comma_separated_string_fields():
    result = {"required_technologies": "Java, Docker", "optional_technologies": "Kubernetes"}
    assert filter_ungrounded_technologies(result, "Oferta con Java") == {"required_technologies": ["Java"], "optional_technologies": []}


def test_empty_offer_drops_every_technology():
    result = filter_ungrounded_technologies(extraction(required=["Java"], optional=["Docker"]), "")
    assert result["required_technologies"] == []
    assert result["optional_technologies"] == []


def test_logs_the_dropped_technologies():
    log = MagicMock()
    filter_ungrounded_technologies(extraction(required=["Java"], optional=["Docker", "AWS"]), "Oferta con Java", log=log)
    log.warning.assert_called_once_with("ai.ungrounded_technology", dropped=["Docker", "AWS"])


def test_does_not_log_when_everything_is_grounded():
    log = MagicMock()
    filter_ungrounded_technologies(extraction(required=["Java"]), "Oferta con Java", log=log)
    log.warning.assert_not_called()


def test_missing_fields_are_left_untouched():
    assert filter_ungrounded_technologies({"salary": None}, "Oferta con Java") == {"salary": None}
