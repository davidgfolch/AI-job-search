import pytest
from unittest.mock import patch
from ..config import (
    get_provider, get_port, get_hf_model, get_openai_api_key, get_openai_model,
    get_openrouter_api_key, get_openrouter_model, get_cv_path, get_looking_for_path,
    get_timeout, get_temperature, get_max_tokens,
)


@pytest.mark.parametrize("func, mock_val, expected", [
    (get_provider, "local", "local"),
    (get_provider, "openai", "openai"),
    (get_port, "9090", 9090),
    (get_hf_model, "Qwen/Qwen2.5-1.5B-Instruct", "Qwen/Qwen2.5-1.5B-Instruct"),
    (get_openai_api_key, None, None),
    (get_openai_model, "gpt-4o-mini", "gpt-4o-mini"),
    (get_openrouter_api_key, None, None),
    (get_openrouter_model, "openai/gpt-4o-mini", "openai/gpt-4o-mini"),
    (get_cv_path, "cv/cv.txt", "cv/cv.txt"),
    (get_looking_for_path, "cv/looking-for.txt", "cv/looking-for.txt"),
    (get_timeout, "30", 30.0),
    (get_temperature, "0.1", 0.1),
    (get_max_tokens, "512", 512),
])
def test_config_values(func, mock_val, expected):
    with patch("aiFormFiller.config.getEnv") as mock_get_env, patch("aiFormFiller.config.getEnvFile") as mock_get_env_file:
        mock_get_env.return_value = mock_val
        mock_get_env_file.return_value = mock_val
        assert func() == expected


def test_get_provider_reads_env_file_over_process_env():
    with patch("aiFormFiller.config.getEnv", return_value="local"), patch("aiFormFiller.config.getEnvFile", return_value="openai") as mock_get_env_file:
        assert get_provider() == "openai"
        mock_get_env_file.assert_called_once_with("AI_FORM_PROVIDER", "local")


@pytest.mark.parametrize("func, key", [
    (get_openai_api_key, "OPENAI_API_KEY"),
    (get_openrouter_api_key, "OPENROUTER_API_KEY"),
])
def test_api_keys_read_env_file_for_live_settings_edits(func, key):
    with patch("aiFormFiller.config.getEnv", return_value="from-startup"), patch("aiFormFiller.config.getEnvFile", return_value="from-settings") as mock_get_env_file:
        assert func() == "from-settings"
        mock_get_env_file.assert_called_once_with(key)
