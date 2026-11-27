"""HTTP client for direct connections to LAN services.

`requests` honours HTTP(S)_PROXY from the environment, so a raw-IP URL used by
service discovery or remote log shipping can be routed through a proxy that
cannot reach the LAN. Every such call uses a session with ``trust_env=False``
and connects to the target host itself.
"""
import requests


def session() -> requests.Session:
    """A requests session that ignores proxy environment variables."""
    client = requests.Session()
    client.trust_env = False
    return client
