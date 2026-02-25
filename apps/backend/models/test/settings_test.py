import pytest
from models.settings import SettingsEnvUpdateDto, SettingsEnvBulkUpdateDto, ScrapperStateUpdateDto


@pytest.mark.parametrize("key,value", [
    ("ENV_KEY", "some_value"),
    ("OPENAI_API_KEY", "sk-abc123"),
], ids=["generic_key", "openai_key"])
def test_settings_env_update_dto(key, value):
    sut = SettingsEnvUpdateDto(key=key, value=value)
    assert sut.key == key
    assert sut.value == value


@pytest.mark.parametrize("updates", [
    ({"KEY_A": "val_a"}),
    ({"KEY_A": "val_a", "KEY_B": "val_b"}),
], ids=["single_update", "multiple_updates"])
def test_settings_env_bulk_update_dto(updates):
    sut = SettingsEnvBulkUpdateDto(updates=updates)
    assert sut.updates == updates


@pytest.mark.parametrize("state", [
    ({}),
    ({"last_execution": "2024-01-01T00:00:00", "running": False}),
], ids=["empty_state", "populated_state"])
def test_scrapper_state_update_dto(state):
    sut = ScrapperStateUpdateDto(state=state)
    assert sut.state == state
