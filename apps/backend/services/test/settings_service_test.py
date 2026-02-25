import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
import services.settings_service as settings_service

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
def test_update_env_setting(mock_set, mock_get_all, key, value):
    result = settings_service.update_env_setting(key, value)
    mock_set.assert_called_once_with(key, value)
    assert result == ENV_DATA


@patch("services.settings_service.getEnvAll", return_value=ENV_DATA)
def test_update_env_settings_bulk(mock_get_all):
    updates = {"KEY_A": "x", "KEY_B": "y"}
    with patch("commonlib.environmentUtil.setEnvBulk") as mock_bulk:
        result = settings_service.update_env_settings_bulk(updates)
        assert result == ENV_DATA


@patch("services.settings_service.SCRAPPER_STATE_PATH")
def test_get_scrapper_state_returns_empty_when_missing(mock_path):
    mock_path.exists.return_value = False
    result = settings_service.get_scrapper_state()
    assert result == {}


@patch("builtins.open", mock_open(read_data=json.dumps(STATE_DATA)))
@patch("services.settings_service.SCRAPPER_STATE_PATH")
def test_get_scrapper_state_returns_parsed_json(mock_path):
    mock_path.exists.return_value = True
    result = settings_service.get_scrapper_state()
    assert result == STATE_DATA


@patch("services.settings_service.SCRAPPER_STATE_PATH")
def test_get_scrapper_state_returns_empty_on_error(mock_path):
    mock_path.exists.return_value = True
    with patch("builtins.open", side_effect=OSError("read error")):
        result = settings_service.get_scrapper_state()
    assert result == {}


@patch("builtins.open", mock_open())
@patch("services.settings_service.SCRAPPER_STATE_PATH")
def test_update_scrapper_state(mock_path):
    mock_path.parent.mkdir = MagicMock()
    result = settings_service.update_scrapper_state(STATE_DATA)
    assert result == STATE_DATA
    mock_path.parent.mkdir.assert_called_once_with(parents=True, exist_ok=True)
