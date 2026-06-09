from pymongo import MongoClient


class MongoDbProvider:
    """CQRS-style MongoDB connection provider.

    Separates read and write connections so read-heavy workloads
    can target secondary replicas while writes always go to the primary.

    For single-node setups both URIs point to the same instance.
    """

    def __init__(self, read_uri: str, write_uri: str, db_name: str):
        self._read_uri = read_uri
        self._write_uri = write_uri
        self._db_name = db_name
        self._read_client: MongoClient | None = None
        self._write_client: MongoClient | None = None

    @property
    def _reader(self) -> MongoClient:
        if not self._read_client:
            self._read_client = MongoClient(self._read_uri)
        return self._read_client

    @property
    def _writer(self) -> MongoClient:
        if not self._write_client:
            self._write_client = MongoClient(self._write_uri)
        return self._write_client

    def get_database(self, write: bool = False):
        client = self._writer if write else self._reader
        return client[self._db_name]


_providers: dict[str, MongoDbProvider] = {}


def get_mongo_provider(read_uri: str, write_uri: str, db_name: str) -> MongoDbProvider:
    key = f"{read_uri}|{write_uri}|{db_name}"
    if key not in _providers:
        _providers[key] = MongoDbProvider(read_uri, write_uri, db_name)
    return _providers[key]
