import pytest
from unittest.mock import patch

ENV_DATA = {"KEY_A": "val_a", "KEY_B": "val_b"}
STATE_DATA = {"last_execution": "2024-01-01T00:00:00", "running": False}

SERVICE = "api.settings.service"


def test_get_env_settings(client):
    with patch(f"{SERVICE}.get_env_settings", return_value=ENV_DATA):
        response = client.get("/api/settings/env")
    assert response.status_code == 200
    assert response.json() == ENV_DATA


@pytest.mark.parametrize("key,value", [
    ("KEY_A", "new_val"),
    ("NEW_KEY", "fresh"),
], ids=["update_existing", "add_new"])
def test_update_env_setting(client, key, value):
    with patch(f"{SERVICE}.update_env_setting", return_value=ENV_DATA) as mock_svc:
        response = client.post("/api/settings/env", json={"key": key, "value": value})
    assert response.status_code == 200
    mock_svc.assert_called_once_with(key, value)


def test_update_env_settings_bulk(client):
    updates = {"KEY_A": "x", "KEY_B": "y"}
    with patch(f"{SERVICE}.update_env_settings_bulk", return_value=ENV_DATA) as mock_svc:
        response = client.post("/api/settings/env-bulk", json={"updates": updates})
    assert response.status_code == 200
    mock_svc.assert_called_once_with(updates)


def test_get_scrapper_state(client):
    with patch(f"{SERVICE}.get_scrapper_state", return_value=STATE_DATA):
        response = client.get("/api/settings/scrapper-state")
    assert response.status_code == 200
    assert response.json() == STATE_DATA


def test_update_scrapper_state(client):
    with patch(f"{SERVICE}.update_scrapper_state", return_value=STATE_DATA) as mock_svc:
        response = client.post("/api/settings/scrapper-state", json={"state": STATE_DATA})
    assert response.status_code == 200
    mock_svc.assert_called_once_with(STATE_DATA)
