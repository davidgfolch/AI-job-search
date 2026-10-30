"""MongoDB URI resolution and fallback ordering, mirroring the MySQL chain.

`MONGO_URI` may point at a dockerized Mongo (`mongo_db`), a host-installed
server (`host.docker.internal` / `localhost`) or another LAN machine. The
configured host is tried first; the container service name, the docker host
gateway and loopback follow, then a cached LAN scan on port 27017. `auto` (or
`discover`) skips straight to the scan.

Credentials come from `MONGO_USERNAME` / `MONGO_PASSWORD` when the URI template
left them empty or unexpanded, so `.env`'s
`mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@host:27017/` works whether or not
dotenv could expand it.
"""
from urllib.parse import urlsplit

from commonlib.environmentUtil import getEnv
from commonlib.network.discovery_cache import cached_discover, write_entry
from commonlib.network.mongo_discovery import DEFAULT_MONGO_PORT, discover_mongo_hosts
from commonlib.observability import get_logger

logger = get_logger("commonlib.mongo_config")

DEFAULT_MONGO_URI = "mongodb://root:rootPass@localhost:27017/"
DEFAULT_MONGO_USER = "root"
DEFAULT_MONGO_PASSWORD = "rootPass"
MONGO_CANDIDATE_HOSTS = ("mongo_db", "host.docker.internal", "127.0.0.1")
AUTO_SPECS = ("auto", "discover")
PING_TIMEOUT_MS = int(getEnv("COMMONLIB_MONGO_PING_TIMEOUT_MS", "1500") or 1500)

_resolved: dict[str, str] = {}


def _credentials() -> tuple[str, str]:
    return (
        getEnv("MONGO_USERNAME", DEFAULT_MONGO_USER) or DEFAULT_MONGO_USER,
        getEnv("MONGO_PASSWORD", DEFAULT_MONGO_PASSWORD) or DEFAULT_MONGO_PASSWORD,
    )


def _split(uri: str) -> tuple[str, str, str]:
    """Split a Mongo URI into (scheme_prefix, userinfo, host/path part)."""
    scheme, sep, rest = uri.partition("://")
    userinfo, at, tail = rest.rpartition("@")
    prefix = f"{userinfo}@" if at else ""
    return f"{scheme}{sep}", prefix, tail


def normalize_mongo_uri(uri: str) -> str:
    """Fill missing/empty/unexpanded credentials so the URI can actually connect."""
    prefix, userinfo, tail = _split(uri)
    user, password = _credentials()
    creds = userinfo[:-1] if userinfo else ""
    if not creds or "${" in creds or creds == ":":
        return f"{prefix}{user}:{password}@{tail}"
    if creds.endswith(":"):
        return f"{prefix}{creds}{password}@{tail}"
    return uri


def mongo_uri_with_host(uri: str, host: str, port: int | None = None) -> str:
    """Same URI (credentials, path, options) pointing at `host`."""
    prefix, userinfo, tail = _split(uri)
    hostport, slash, path = tail.partition("/")
    configured_port = hostport.rsplit(":", 1)[1] if ":" in hostport else ""
    port = port or (int(configured_port) if configured_port.isdigit() else DEFAULT_MONGO_PORT)
    return f"{prefix}{userinfo}{host}:{port}{slash}{path}"


def configured_mongo_uri() -> str:
    raw = (getEnv("MONGO_URI", DEFAULT_MONGO_URI) or "").strip()
    return DEFAULT_MONGO_URI if not raw or raw.lower() in AUTO_SPECS else normalize_mongo_uri(raw)


def mongo_candidate_uris(uri: str | None = None) -> tuple[str, ...]:
    """Ordered, deduplicated URIs to try: configured host first, then the shared chain."""
    base = configured_mongo_uri() if uri is None else normalize_mongo_uri(uri)
    hosts = []
    configured = urlsplit(base).hostname
    if configured:
        hosts.append(configured)
    for host in MONGO_CANDIDATE_HOSTS:
        if host not in hosts:
            hosts.append(host)
    uris = []
    for host in hosts:
        candidate = mongo_uri_with_host(base, host)
        if candidate not in uris:
            uris.append(candidate)
    return tuple(uris)


def verify_mongo(uri: str, timeout_ms: int | None = None) -> bool:
    """True when the server answers a ping (no database is created or required)."""
    try:
        from pymongo import MongoClient
    except Exception:
        return False
    client = MongoClient(uri, serverSelectionTimeoutMS=timeout_ms or PING_TIMEOUT_MS)
    try:
        client.admin.command("ping")
        return True
    except Exception:
        return False
    finally:
        client.close()


def resolve_mongo_uri(uri: str | None = None) -> str:
    """Return the first reachable Mongo URI, falling back to cached LAN discovery.

    Falls back to the configured URI when nothing answers, so the caller fails
    with pymongo's own error (naming the host it could not reach) instead of a
    discovery error that hides the address it wanted.
    """
    base = configured_mongo_uri() if uri is None else normalize_mongo_uri(uri)
    if base in _resolved:
        return _resolved[base]
    auto = (getEnv("MONGO_URI", "") or "").strip().lower() in AUTO_SPECS
    candidates = () if auto else mongo_candidate_uris(base)
    tried = set()
    for candidate in candidates:
        host = urlsplit(candidate).hostname
        tried.add(host)
        if verify_mongo(candidate):
            write_entry("mongo", host)
            logger.info("mongo.host_resolved", uri=_redact(candidate))
            return _remember(base, candidate)
    host = cached_discover("mongo", verify=lambda h: verify_mongo(mongo_uri_with_host(base, h)),
                           scan=discover_mongo_hosts, log=logger, tried=tried)
    if host:
        return _remember(base, mongo_uri_with_host(base, host))
    logger.warning("mongo.unreachable", uri=_redact(base))
    return _remember(base, base)


def _remember(base: str, resolved: str) -> str:
    _resolved[base] = resolved
    return resolved


def _redact(uri: str) -> str:
    prefix, userinfo, tail = _split(uri)
    return f"{prefix}{'***@' if userinfo else ''}{tail}"
