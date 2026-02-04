import pytest
from models.filter_configuration import FilterConfiguration, FilterConfigurationCreate, FilterConfigurationUpdate
from datetime import datetime

def test_filter_configuration_create():
    config = FilterConfigurationCreate(name="Test Filter", filters={"key": "value"})
    assert config.name == "Test Filter"
    assert config.filters == {"key": "value"}
    assert config.notify == False
    assert config.pinned == False

@pytest.mark.parametrize("notify", [True, False])
def test_filter_configuration_create_notify(notify):
    config = FilterConfigurationCreate(name="Test", filters={}, notify=notify)
    assert config.notify == notify

@pytest.mark.parametrize("pinned", [True, False])
def test_filter_configuration_create_pinned(pinned):
    config = FilterConfigurationCreate(name="Test", filters={}, pinned=pinned)
    assert config.pinned == pinned

@pytest.mark.parametrize("field,value", [
    ("name", "Updated Name"),
    ("filters", {"updated": "filter"}),
    ("filters", {"updated": "filter"}),
    ("notify", True),
    ("pinned", True),
])
def test_filter_configuration_update_fields(field, value):
    config = FilterConfigurationUpdate(**{field: value})
    assert getattr(config, field) == value

def test_filter_configuration_update_all_optional():
    config = FilterConfigurationUpdate()
    assert config.name is None
    assert config.filters is None
    assert config.notify is None
    assert config.pinned is None

def test_filter_configuration():
    now = datetime.now()
    config = FilterConfiguration(
        id=1,
        name="Test Filter",
        filters={"key": "value"},
        notify=True,
        statistics=True,
        pinned=True,
        created=now
    )
    assert config.id == 1
    assert config.name == "Test Filter"
    assert config.filters == {"key": "value"}
    assert config.notify == True
    assert config.pinned == True
    assert config.created == now
    assert config.modified is None

def test_filter_configuration_with_modified():
    now = datetime.now()
    config = FilterConfiguration(
        id=1,
        name="Test",
        filters={},
        notify=False,
        statistics=True,
        pinned=False,
        created=now,
        modified=now
    )
    assert config.modified == now
