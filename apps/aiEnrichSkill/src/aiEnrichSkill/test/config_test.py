import os
import pytest
from unittest.mock import patch

from ..config import (
    get_enabled,
    get_backend,
    get_ollama_model,
    get_ollama_base_url,
    get_max_new_tokens,
    get_hf_model_id,
    get_hf_temperature,
    get_hf_top_p,
    get_hf_repetition_penalty,
    get_batch_size,
    get_input_max_len,
    get_timeout,
    get_gpu_cleanup,
    get_skill_categories,
    get_enrich_limit,
    get_skill_system_prompt,
)


def test_get_enabled_default_true():
    os.environ.pop("AI_ENRICHSKILL_ENABLED", None)
    assert get_enabled() is True


@patch("aiEnrichSkill.config.getEnvBool")
def test_get_enabled_false(mock_env):
    mock_env.return_value = False
    assert get_enabled() is False


def test_get_backend_default_ollama():
    os.environ.pop("AI_ENRICHSKILL_BACKEND", None)
    assert get_backend() == "ollama"


@patch("aiEnrichSkill.config.getEnv")
def test_get_backend_huggingface(mock_env):
    mock_env.return_value = "huggingface"
    assert get_backend() == "huggingface"


@patch("aiEnrichSkill.config.getEnv")
def test_get_ollama_model_default(mock_env):
    mock_env.return_value = "ollama/qwen2.5:3b"
    assert get_ollama_model() == "ollama/qwen2.5:3b"


@patch("aiEnrichSkill.config.getEnv")
def test_get_ollama_base_url_default(mock_env):
    mock_env.return_value = "http://localhost:11434"
    assert get_ollama_base_url() == "http://localhost:11434"


@patch("aiEnrichSkill.config.getEnv")
def test_get_max_new_tokens_default(mock_env):
    mock_env.return_value = "2048"
    assert get_max_new_tokens() == 2048


@patch("aiEnrichSkill.config.getEnv")
def test_get_hf_model_id_default(mock_env):
    mock_env.return_value = "Qwen/Qwen2.5-1.5B-Instruct"
    assert get_hf_model_id() == "Qwen/Qwen2.5-1.5B-Instruct"


@patch("aiEnrichSkill.config.getEnv")
def test_get_hf_temperature_default(mock_env):
    mock_env.return_value = "0.1"
    assert get_hf_temperature() == 0.1


@patch("aiEnrichSkill.config.getEnv")
def test_get_hf_top_p_default(mock_env):
    mock_env.return_value = "0.9"
    assert get_hf_top_p() == 0.9


@patch("aiEnrichSkill.config.getEnv")
def test_get_hf_repetition_penalty_default(mock_env):
    mock_env.return_value = "1.1"
    assert get_hf_repetition_penalty() == 1.1


@patch("aiEnrichSkill.config.getEnv")
def test_get_batch_size_default(mock_env):
    mock_env.return_value = "10"
    assert get_batch_size() == 10


@patch("aiEnrichSkill.config.getEnv")
def test_get_input_max_len_default(mock_env):
    mock_env.return_value = "12000"
    assert get_input_max_len() == 12000


@patch("aiEnrichSkill.config.getEnv")
def test_get_timeout_default(mock_env):
    mock_env.return_value = "90"
    assert get_timeout() == 90.0


def test_get_gpu_cleanup_default_true():
    os.environ.pop("AI_ENRICHSKILL_GPU_CLEANUP", None)
    assert get_gpu_cleanup() is True


@patch("aiEnrichSkill.config.getEnv")
def test_get_skill_categories(mock_env):
    mock_env.return_value = "Language, Framework"
    assert get_skill_categories() == "Language, Framework"
    mock_env.assert_called_with("AI_ENRICHSKILL_CATEGORIES", required=True)


@patch("aiEnrichSkill.config.getEnv")
def test_get_enrich_limit_default(mock_env):
    mock_env.return_value = "10"
    assert get_enrich_limit() == 10


@patch("aiEnrichSkill.config.getEnv")
def test_get_skill_system_prompt_includes_categories(mock_env):
    mock_env.return_value = "Language, Framework"
    prompt = get_skill_system_prompt()
    assert "Language, Framework" in prompt
