from commonlib.mongodb_provider import MongoDbProvider, get_mongo_provider


def test_provider_creates_read_and_write_clients():
    provider = MongoDbProvider("mongodb://localhost:27017/", "mongodb://localhost:27017/", "test_db")
    assert provider is not None

def test_get_mongo_provider_caches():
    p1 = get_mongo_provider("uri1", "uri2", "db")
    p2 = get_mongo_provider("uri1", "uri2", "db")
    assert p1 is p2

def test_get_mongo_provider_different_keys():
    p1 = get_mongo_provider("uri1", "uri2", "db")
    p2 = get_mongo_provider("other", "uri2", "db")
    assert p1 is not p2

def test_get_database_returns_database():
    provider = MongoDbProvider("mongodb://localhost:27017/", "mongodb://localhost:27017/", "test_db")
    db = provider.get_database(write=False)
    assert db.name == "test_db"

def test_get_database_write_returns_writer():
    provider = MongoDbProvider("mongodb://localhost:27017/", "mongodb://localhost:27017/", "test_db")
    db = provider.get_database(write=True)
    assert db.name == "test_db"
