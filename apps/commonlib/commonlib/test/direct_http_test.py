from commonlib import direct_http as sut


def test_session_ignores_proxy_environment():
    client = sut.session()
    try:
        assert client.trust_env is False
    finally:
        client.close()
