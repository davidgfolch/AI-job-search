"""Ordered MySQL host candidates: the configured host first, then the container chain.

The chain is what makes the same code reach MySQL whether it runs in a container
(the `mysql_db` service), on the Docker host (`host.docker.internal`) or natively
(`127.0.0.1`), instead of depending on a host pinned in compose.
"""
import os

from commonlib.sql.connection_manager_parse import _parse_host_targets

# Appended after COMMONLIB_DB_HOST. `mysql_db` is the compose service name,
# `host.docker.internal` the Docker host gateway, `127.0.0.1` a native run.
DB_CANDIDATE_HOSTS = ('mysql_db', 'host.docker.internal', '127.0.0.1')
DB_AUTO_SPECS = ('auto', 'discover')


def db_candidate_hosts(raw: str | None = None) -> tuple[str, ...]:
    """Ordered, deduplicated MySQL hosts to try.

    The explicit `COMMONLIB_DB_HOST` value comes first (single IP, CIDR or
    `10-250` ranges still work, comma-separated groups included), then the
    container service name, the docker host gateway and loopback. `auto` /
    `discover` skip straight to the LAN scan.
    """
    raw = (os.getenv('COMMONLIB_DB_HOST', '') if raw is None else raw).strip()
    hosts: list[str] = []
    if raw and raw.lower() not in DB_AUTO_SPECS:
        for group in raw.split(','):
            group = group.strip()
            if group:
                hosts.extend(_parse_host_targets(group))
    for host in DB_CANDIDATE_HOSTS:
        if host not in hosts:
            hosts.append(host)
    return tuple(hosts)
