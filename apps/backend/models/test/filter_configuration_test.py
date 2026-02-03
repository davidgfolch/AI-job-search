import pytest
from models.filter_configuration import FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate
from datetime import datetime

def test_filter_configuration_create():
    config = FilterConfigurationCreate(name="Test Filter", filters={"key": "value"})
    assert config.name == "Test Filter"
    assert config.filters == {"key": "value"}
    assert config.notify == False

@pytest.mark.parametrize("notify", [True, False])
def test_filter_configuration_create_notify(notify):
    config = FilterConfigurationCreate(name="Test", filters={}, notify=notify)
    assert config.notify == notify

@pytest.mark.parametrize("field,value", [
    ("name", "Updated Name"),
    ("filters", {"updated": "filter"}),
    ("notify", True),
])
def test_filter_configuration_update_fields(field, value):
    config = FilterConfigurationUpdate(**{field: value})
    assert getattr(config, field) == value

def test_filter_configuration_update_all_optional():
    config = FilterConfigurationUpdate()
    assert config.name is None
    assert config.filters is None
    assert config.notify is None

def test_filter_configuration():
    now = datetime.now()
    config = FilterConfiguration(
        id=1,
        name="Test Filter",
        filters={"key": "value"},
        notify=True,
        created=now
    )
    assert config.id == 1
    assert config.name == "Test Filter"
    assert config.filters == {"key": "value"}
    assert config.notify == True
    assert config.created == now
    assert config.modified is None

def test_filter_configuration_with_modified():
    now = datetime.now()
    config = FilterConfiguration(
        id=1,
        name="Test",
        filters={},
        notify=False,
        created=now,
        modified=now
    )
    assert config.modified == now
