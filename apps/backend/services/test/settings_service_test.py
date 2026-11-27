import pytest
from unittest.mock import patch
import services.settings_service as settings_service

MODELS = [{"id": "free/model:free", "label": "free/model:free", "free": True}]

ENV_DATA = {"KEY_A": "val_a", "KEY_B": "val_b"}
STATE_DATA = {"last_execution": "2024-01-01T00:00:00", "running": False}


@patch("services.settings_service.getEnvAll", return_value=ENV_DATA)
def test_get_env_settings(mock_get_all):
    result = settings_service.get_env_settings()
    assert result == ENV_DATA
    mock_get_all.assert_called_once()


@pytest.mark.parametrize("key,value", [
    ("KEY_A", "new_val"),
    ("NEW_KEY", "new_value"),
], ids=["update_existing", "add_new"])
@patch("services.settings_service.getEnvAll", return_value=ENV_DATA)
@patch("services.settings_service.setEnv")
def test_update_env_setting(mock_set, mock_get_all, key, value, log_records):
    result = settings_service.update_env_setting(key, value)
    mock_set.assert_called_once_with(key, value)
    assert result == ENV_DATA
    records = log_records(event="settings.updated")
    assert [record["level"] for record in records] == ["info"]
    assert records[0]["key"] == key
    assert records[0]["count"] == 1
    assert value not in records[0].values()


@patch("services.settings_service.getEnvAll", return_value=ENV_DATA)
def test_update_env_settings_bulk(mock_get_all, log_records):
    updates = {"KEY_A": "x", "KEY_B": "y"}
    with patch("commonlib.environmentUtil.setEnvBulk"):
        result = settings_service.update_env_settings_bulk(updates)
        assert result == ENV_DATA
    records = log_records(event="settings.updated")
    assert [record["count"] for record in records] == [2]
    assert all(update not in record.values() for record in records for update in updates.values())


@patch("services.settings_service.list_models", return_value=MODELS)
@patch("services.settings_service.getEnv", return_value="604800")
def test_get_provider_models_caches_for_ttl(_env, mock_list):
    settings_service._models_cache.clear()
    first = settings_service.get_provider_models("groq")
    second = settings_service.get_provider_models("groq")
    assert first["source"] == "live" and second["cached"] is True
    assert second["models"] == MODELS
    mock_list.assert_called_once_with("groq")


@patch("services.settings_service.list_models", return_value=MODELS)
@patch("services.settings_service.getEnv", return_value="604800")
def test_get_provider_models_refresh_bypasses_cache(_env, mock_list):
    settings_service._models_cache.clear()
    settings_service.get_provider_models("groq")
    refreshed = settings_service.get_provider_models("groq", refresh=True)
    assert refreshed["cached"] is False
    assert mock_list.call_count == 2


@patch("services.settings_service.list_models", side_effect=OSError("offline"))
def test_get_provider_models_falls_back_on_error(mock_list, log_records):
    settings_service._models_cache.clear()
    result = settings_service.get_provider_models("gemini")
    assert result == {"provider": "gemini", "models": [], "source": "fallback", "cached": False, "fetched_at": None}
    assert log_records(event="provider.models_fetch_failed")[0]["error"] == "offline"


@pytest.mark.parametrize("provider", ["bogus", "huggingface", "local"])
def test_get_provider_models_rejects_non_http_providers(provider):
    settings_service._models_cache.clear()
    with patch("services.settings_service.list_models") as mock_list:
        result = settings_service.get_provider_models(provider)
    assert result["source"] == "fallback"
    mock_list.assert_not_called()


@patch("services.settings_service._repo")
def test_get_scrapper_state_returns_state(mock_repo):
    mock_repo.get_all.return_value = STATE_DATA
    result = settings_service.get_scrapper_state()
    assert result == STATE_DATA


@patch("services.settings_service._repo")
def test_get_scrapper_state_returns_empty_on_error(mock_repo, log_records):
    mock_repo.get_all.side_effect = Exception("DB error")
    result = settings_service.get_scrapper_state()
    assert result == {}
    records = log_records(event="scrapper_state.read_failed")
    assert len(records) == 1
    assert records[0]["level"] == "error"
    assert records[0]["error"] == "DB error"
    assert "Exception" in records[0]["exception"]


@patch("services.settings_service._repo")
def test_update_scrapper_state(mock_repo):
    mock_repo.replace_all.return_value = STATE_DATA
    result = settings_service.update_scrapper_state(STATE_DATA)
    assert result == STATE_DATA
    mock_repo.replace_all.assert_called_once_with(STATE_DATA)


@patch("services.settings_service._repo")
def test_update_scrapper_state_returns_input_on_error(mock_repo, log_records):
    mock_repo.replace_all.side_effect = Exception("DB error")
    result = settings_service.update_scrapper_state(STATE_DATA)
    assert result == STATE_DATA
    records = log_records(event="scrapper_state.write_failed")
    assert len(records) == 1
    assert records[0]["level"] == "error"
    assert records[0]["error"] == "DB error"
    assert "Exception" in records[0]["exception"]
