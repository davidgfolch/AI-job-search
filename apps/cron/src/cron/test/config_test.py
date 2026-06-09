def test_config_has_defaults():
    from cron import config
    assert config.MONGO_URI is not None
    assert config.MONGO_DATABASE == "jobs"
    assert config.CHECK_INTERVAL_SECONDS == 60
