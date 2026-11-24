import os
import pytest
from unittest.mock import patch

from commonlib.test.ollama_constants import OLLAMA_TEST_URL

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
    get_learning_paths_enabled,
    get_learning_path_max,
    get_learning_path_batch,
    get_learning_path_timeout,
    get_learning_path_search_enabled,
    get_learning_path_search_results,
    get_learning_path_max_failures,
    get_learning_path_retry_seconds,
    get_learning_domains,
    get_learning_path_system_prompt,
    DEFAULT_LEARNING_DOMAINS,
)


def test_get_enabled_default_true():
    os.environ.pop("AI_ENRICHSKILL_ENABLED", None)
    assert get_enabled() is True


@patch("aiEnrichSkill.config.getEnvBool")
def test_get_enabled_false(mock_env):
    mock_env.return_value = False
    assert get_enabled() is False


@patch("aiEnrichSkill.config.getEnvFile", return_value="ollama")
def test_get_backend_default_ollama(_mock_env):
    assert get_backend() == "ollama"


@patch("aiEnrichSkill.config.getEnvFile", return_value="huggingface")
def test_get_backend_huggingface(_mock_env):
    assert get_backend() == "huggingface"


@pytest.mark.parametrize("getter, raw, expected", [
    (get_ollama_model, "ollama/qwen2.5:3b", "ollama/qwen2.5:3b"),
    (get_ollama_base_url, OLLAMA_TEST_URL, OLLAMA_TEST_URL),
    (get_max_new_tokens, "2048", 2048),
    (get_hf_model_id, "Qwen/Qwen2.5-1.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"),
    (get_hf_temperature, "0.1", 0.1),
    (get_hf_top_p, "0.9", 0.9),
    (get_hf_repetition_penalty, "1.1", 1.1),
    (get_batch_size, "10", 10),
    (get_input_max_len, "12000", 12000),
    (get_timeout, "90", 90.0),
    (get_enrich_limit, "10", 10),
])
@patch("aiEnrichSkill.config.getEnv")
def test_getenv_backed_getters(mock_env, getter, raw, expected):
    mock_env.return_value = raw
    assert getter() == expected


def test_get_gpu_cleanup_default_true():
    os.environ.pop("AI_ENRICHSKILL_GPU_CLEANUP", None)
    assert get_gpu_cleanup() is True


@patch("aiEnrichSkill.config.getEnv")
def test_get_skill_categories(mock_env):
    mock_env.return_value = "Language, Framework"
    assert get_skill_categories() == "Language, Framework"
    mock_env.assert_called_with("AI_ENRICHSKILL_CATEGORIES", required=True)


@patch("aiEnrichSkill.config.get_learning_path_max", return_value=3)
@patch("aiEnrichSkill.config.get_learning_paths_enabled", return_value=False)
@patch("aiEnrichSkill.config.get_skill_categories", return_value="Language, Framework")
def test_get_skill_system_prompt_includes_categories(_categories, _enabled, _max):
    prompt = get_skill_system_prompt()
    assert "Language, Framework" in prompt


def test_get_learning_paths_enabled_default_true():
    os.environ.pop("AI_ENRICHSKILL_LEARNING_PATHS", None)
    assert get_learning_paths_enabled() is True


@patch("aiEnrichSkill.config.getEnvBool", return_value=False)
def test_get_learning_paths_enabled_false(mock_env):
    assert get_learning_paths_enabled() is False
    mock_env.assert_called_once_with("AI_ENRICHSKILL_LEARNING_PATHS", True)


def test_get_learning_path_search_enabled_default_true():
    os.environ.pop("AI_ENRICHSKILL_LEARNING_PATH_SEARCH", None)
    assert get_learning_path_search_enabled() is True


@patch("aiEnrichSkill.config.getEnvBool", return_value=False)
def test_get_learning_path_search_enabled_false(mock_env):
    assert get_learning_path_search_enabled() is False
    mock_env.assert_called_once_with("AI_ENRICHSKILL_LEARNING_PATH_SEARCH", True)


@pytest.mark.parametrize("getter, env_name, raw, expected, default", [
    (get_learning_path_max, "AI_ENRICHSKILL_LEARNING_PATH_MAX", "5", 5, "3"),
    (get_learning_path_batch, "AI_ENRICHSKILL_LEARNING_PATH_BATCH", "2", 2, "1"),
    (get_learning_path_timeout, "AI_ENRICHSKILL_LEARNING_PATH_TIMEOUT", "9", 9, "5"),
    (get_learning_path_search_results, "AI_ENRICHSKILL_LEARNING_PATH_SEARCH_RESULTS", "7", 7, "10"),
    (get_learning_path_max_failures, "AI_ENRICHSKILL_LEARNING_PATH_MAX_FAILURES", "4", 4, "3"),
    (get_learning_path_retry_seconds, "AI_ENRICHSKILL_LEARNING_PATH_RETRY_SECONDS", "60", 60, "900"),
])
@patch("aiEnrichSkill.config.getEnv")
def test_learning_path_int_getters(mock_env, getter, env_name, raw, expected, default):
    mock_env.return_value = raw
    assert getter() == expected
    mock_env.assert_called_once_with(env_name, default)


@patch("aiEnrichSkill.config.getEnv", return_value="")
def test_get_learning_domains_defaults(_mock_env):
    assert get_learning_domains() == DEFAULT_LEARNING_DOMAINS


@patch("aiEnrichSkill.config.getEnv", return_value="www.Python.org, docs.python.org ,,")
def test_get_learning_domains_configured_override(_mock_env):
    assert get_learning_domains() == ("python.org", "docs.python.org")


@patch("aiEnrichSkill.config.get_learning_path_max", return_value=3)
@patch("aiEnrichSkill.config.get_skill_categories", return_value="Language, Framework")
@patch("aiEnrichSkill.config.get_learning_paths_enabled", return_value=True)
def test_skill_system_prompt_includes_learning_path_when_enabled(_enabled, _categories, _max):
    prompt = get_skill_system_prompt()
    assert "Learning Path" in prompt
    assert "exactly 3 URLs" in prompt


@patch("aiEnrichSkill.config.get_learning_paths_enabled", return_value=False)
@patch("aiEnrichSkill.config.get_skill_categories", return_value="Language, Framework")
def test_skill_system_prompt_omits_learning_path_when_disabled(_categories, _enabled):
    prompt = get_skill_system_prompt()
    assert "Learning Path" not in prompt


@patch("aiEnrichSkill.config.get_learning_path_max", return_value=2)
def test_learning_path_system_prompt_requests_links_only(_max):
    prompt = get_learning_path_system_prompt()
    assert "List 2 learning resources" in prompt
    assert "Learning Path:" in prompt
    assert "No explanations" in prompt
