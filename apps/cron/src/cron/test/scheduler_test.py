from cron.scheduler import _parse_cadency


def test_parse_cadency_seconds():
    assert _parse_cadency("30s") == 30

def test_parse_cadency_minutes():
    assert _parse_cadency("5m") == 300

def test_parse_cadency_hours():
    assert _parse_cadency("2h") == 7200

def test_parse_cadency_days():
    assert _parse_cadency("1d") == 86400

def test_parse_cadency_default():
    assert _parse_cadency("invalid") == 3600

def test_parse_cadency_strips_whitespace():
    assert _parse_cadency(" 10m ") == 600
