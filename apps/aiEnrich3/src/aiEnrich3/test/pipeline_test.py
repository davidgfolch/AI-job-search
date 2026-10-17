from unittest.mock import patch, MagicMock
import pytest
from aiEnrich3.pipeline import ExtractionPipeline

@pytest.fixture
def mock_pipeline_deps():
    with patch("aiEnrich3.pipeline.GLiNER") as mock_gliner, \
         patch("aiEnrich3.pipeline.SalaryExtractor") as mock_salary_ext, \
         patch("aiEnrich3.pipeline.SkillsExtractor") as mock_skills_ext, \
         patch("aiEnrich3.pipeline.extract_modality") as mock_modality_func:

        mock_shared_gliner = MagicMock()
        mock_gliner.from_pretrained.return_value = mock_shared_gliner

        mock_salary_instance = MagicMock()
        mock_salary_ext.return_value = mock_salary_instance

        mock_skills_instance = MagicMock()
        mock_skills_ext.return_value = mock_skills_instance

        yield {
            "gliner": mock_gliner,
            "salary_ext": mock_salary_instance,
            "skills_ext": mock_skills_instance,
            "modality_func": mock_modality_func
        }


def test_pipeline_init(mock_pipeline_deps):
    pipeline = ExtractionPipeline()
    mock_pipeline_deps["gliner"].from_pretrained.assert_called_once_with("urchade/gliner_multi-v2.1")


@pytest.mark.parametrize("text, salary_val, skills_val, has_modality, expected", [
    (None, None, ([], []), False, {"salary": None, "required_skills": [], "optional_skills": [], "modality": None}),
    ("", None, ([], []), False, {"salary": None, "required_skills": [], "optional_skills": [], "modality": None}),
    ("Some job text", "50k", (["Python"], ["Docker"]), True, {"salary": "50k", "required_skills": ["Python"], "optional_skills": ["Docker"], "modality": "REMOTE"}),
    ("Text no modality", None, ([], []), False, {"salary": None, "required_skills": [], "optional_skills": [], "modality": None}),
])
def test_pipeline_process_job(text, salary_val, skills_val, has_modality, expected, mock_pipeline_deps):
    mock_pipeline_deps["salary_ext"].extract.return_value = salary_val
    mock_pipeline_deps["skills_ext"].extract.return_value = skills_val
    mock_pipeline_deps["modality_func"].return_value = "REMOTE" if has_modality else None

    pipeline = ExtractionPipeline()
    result = pipeline.process_job(text)

    assert result == expected
    if text:
        mock_pipeline_deps["salary_ext"].extract.assert_called_once_with(text)
        mock_pipeline_deps["skills_ext"].extract.assert_called_once_with(text)
        mock_pipeline_deps["modality_func"].assert_called_once_with(title="", markdown=text)