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
    with patch("aiFormFiller.config.getEnv") as mock_get_env:
        mock_get_env.return_value = mock_val
        assert func() == expected
