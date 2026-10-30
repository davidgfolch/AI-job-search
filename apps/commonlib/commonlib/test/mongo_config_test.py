"""Tests for MongoDB URI normalization, the candidate chain and LAN resolution."""
from unittest.mock import MagicMock, patch

import pytest

from commonlib import mongo_config


@pytest.fixture(autouse=True)
def clean_resolution_memo(monkeypatch):
    monkeypatch.setattr(mongo_config, "_resolved", {})


@pytest.fixture
def mongo_env(monkeypatch):
    values = {
        "MONGO_USERNAME": "root",
        "MONGO_PASSWORD": "rootPass",
        "MONGO_DATABASE": "jobs",
        "MONGO_URI": "mongodb://root:rootPass@localhost:27017/",
    }
    for key, value in values.items():
        monkeypatch.setenv(key, value)
    return values


class TestNormalizeMongoUri:
    @pytest.mark.parametrize("uri, expected", [
        ("mongodb://root:rootPass@localhost:27017/", "mongodb://root:rootPass@localhost:27017/"),
        ("mongodb://admin:s3cret@10.0.0.9:27017/jobs", "mongodb://admin:s3cret@10.0.0.9:27017/jobs"),
        ("mongodb://:@localhost:27017/", "mongodb://root:rootPass@localhost:27017/"),
        ("mongodb://localhost:27017/", "mongodb://root:rootPass@localhost:27017/"),
        ("mongodb://root:@localhost:27017/", "mongodb://root:rootPass@localhost:27017/"),
        ("mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017/", "mongodb://root:rootPass@localhost:27017/"),
        ("mongodb://${USER}@mongo_db:27017/jobs?retryWrites=true", "mongodb://root:rootPass@mongo_db:27017/jobs?retryWrites=true"),
    ], ids=[
        "already-valid", "lan-credentials-kept", "empty-user-and-password", "no-userinfo",
        "missing-password", "unexpanded-template", "unexpanded-partial",
    ])
    def test_credentials_are_filled(self, mongo_env, uri, expected):
        assert mongo_config.normalize_mongo_uri(uri) == expected


class TestMongoUriWithHost:
    @pytest.mark.parametrize("uri, host, port, expected", [
        ("mongodb://root:pw@localhost:27017/jobs?x=1", "mongo_db", None, "mongodb://root:pw@mongo_db:27017/jobs?x=1"),
        ("mongodb://root:pw@localhost:27017/", "10.0.0.9", 27018, "mongodb://root:pw@10.0.0.9:27018/"),
        ("mongodb://root:pw@localhost/jobs", "mongo_db", None, "mongodb://root:pw@mongo_db:27017/jobs"),
    ], ids=["keeps-path-and-options", "explicit-port", "default-port-when-missing"])
    def test_host_is_replaced(self, uri, host, port, expected):
        assert mongo_config.mongo_uri_with_host(uri, host, port) == expected

    def test_credentials_are_preserved(self):
        uri = mongo_config.mongo_uri_with_host("mongodb://root:rootPass@localhost:27017/", "10.0.0.9")
        assert "root:rootPass@" in uri


class TestConfiguredMongoUri:
    @pytest.mark.parametrize("raw, expected", [
        ("mongodb://root:pw@mongo_db:27017/", "mongodb://root:pw@mongo_db:27017/"),
        ("", mongo_config.DEFAULT_MONGO_URI),
        ("auto", mongo_config.DEFAULT_MONGO_URI),
        ("discover", mongo_config.DEFAULT_MONGO_URI),
    ], ids=["configured", "empty", "auto", "discover"])
    def test_env_specs(self, mongo_env, monkeypatch, raw, expected):
        monkeypatch.setenv("MONGO_URI", raw)
        assert mongo_config.configured_mongo_uri() == expected

    def test_unexpanded_template_is_repaired(self, mongo_env, monkeypatch):
        monkeypatch.setenv("MONGO_URI", "mongodb://${MONGO_USERNAME}:${MONGO_PASSWORD}@localhost:27017/")
        assert mongo_config.configured_mongo_uri() == "mongodb://root:rootPass@localhost:27017/"

    def test_missing_env_uses_default(self, mongo_env, monkeypatch):
        monkeypatch.delenv("MONGO_URI", raising=False)
        assert mongo_config.configured_mongo_uri() == mongo_config.DEFAULT_MONGO_URI


class TestMongoCandidateUris:
    def test_configured_host_comes_first_then_the_chain(self, mongo_env):
        uris = mongo_config.mongo_candidate_uris("mongodb://root:pw@10.0.0.9:27017/jobs")
        hosts = [uri.split("@")[1].split(":")[0] for uri in uris]
        assert hosts == ["10.0.0.9", "mongo_db", "host.docker.internal", "127.0.0.1"]
        assert all(uri.endswith("/jobs") for uri in uris)

    def test_chain_host_is_not_duplicated(self, mongo_env):
        uris = mongo_config.mongo_candidate_uris("mongodb://root:pw@mongo_db:27017/")
        assert len(uris) == 3
        assert len(set(uris)) == 3

    def test_uses_configured_uri_when_none_given(self, mongo_env, monkeypatch):
        monkeypatch.setenv("MONGO_URI", "mongodb://root:pw@localhost:27017/")
        assert mongo_config.mongo_candidate_uris()[0] == "mongodb://root:pw@localhost:27017/"


class TestVerifyMongo:
    def test_reachable(self):
        client = MagicMock()
        with patch("pymongo.MongoClient", return_value=client):
            assert mongo_config.verify_mongo("mongodb://localhost:27017/") is True
        client.admin.command.assert_called_once_with("ping")
        client.close.assert_called_once()

    def test_unreachable(self):
        client = MagicMock()
        client.admin.command.side_effect = Exception("no server")
        with patch("pymongo.MongoClient", return_value=client):
            assert mongo_config.verify_mongo("mongodb://localhost:27017/") is False
        client.close.assert_called_once()

    def test_pymongo_missing(self):
        with patch.dict("sys.modules", {"pymongo": None}):
            assert mongo_config.verify_mongo("mongodb://localhost:27017/") is False

    def test_timeout_is_forwarded(self):
        client = MagicMock()
        with patch("pymongo.MongoClient", return_value=client) as client_class:
            mongo_config.verify_mongo("mongodb://localhost:27017/", timeout_ms=42)
        assert client_class.call_args[1]["serverSelectionTimeoutMS"] == 42


class TestResolveMongoUri:
    def test_first_reachable_candidate_wins(self, mongo_env):
        verify = MagicMock(return_value=True)
        with patch.object(mongo_config, "verify_mongo", verify), patch.object(mongo_config, "cached_discover") as discover:
            resolved = mongo_config.resolve_mongo_uri("mongodb://root:pw@10.0.0.9:27017/jobs")
        assert resolved == "mongodb://root:pw@10.0.0.9:27017/jobs"
        discover.assert_not_called()
        verify.assert_called_once()

    def test_falls_through_to_the_container_host(self, mongo_env):
        def verify(uri):
            return "host.docker.internal" in uri
        with patch.object(mongo_config, "verify_mongo", side_effect=verify) as verify_mock, \
             patch.object(mongo_config, "cached_discover") as discover:
            resolved = mongo_config.resolve_mongo_uri("mongodb://root:pw@10.0.0.9:27017/jobs")
        assert resolved == "mongodb://root:pw@host.docker.internal:27017/jobs"
        assert verify_mock.call_count == 3
        discover.assert_not_called()

    def test_falls_back_to_lan_discovery(self, mongo_env):
        with patch.object(mongo_config, "verify_mongo", return_value=False), \
             patch.object(mongo_config, "cached_discover", return_value="10.0.0.9") as discover:
            resolved = mongo_config.resolve_mongo_uri("mongodb://root:pw@localhost:27017/jobs")
        assert resolved == "mongodb://root:pw@10.0.0.9:27017/jobs"
        assert discover.call_args[0][0] == "mongo"

    def test_unreachable_returns_the_configured_uri(self, mongo_env):
        with patch.object(mongo_config, "verify_mongo", return_value=False), \
             patch.object(mongo_config, "cached_discover", return_value=None):
            assert mongo_config.resolve_mongo_uri("mongodb://root:pw@localhost:27017/") == "mongodb://root:pw@localhost:27017/"

    def test_auto_spec_skips_the_candidate_chain(self, mongo_env, monkeypatch):
        monkeypatch.setenv("MONGO_URI", "auto")
        with patch.object(mongo_config, "verify_mongo") as verify, \
             patch.object(mongo_config, "cached_discover", return_value="10.0.0.9") as discover:
            resolved = mongo_config.resolve_mongo_uri()
        verify.assert_not_called()
        assert discover.called
        assert resolved.startswith("mongodb://root:rootPass@10.0.0.9:27017/")

    def test_resolution_is_memoized(self, mongo_env):
        with patch.object(mongo_config, "verify_mongo", return_value=True) as verify, \
             patch.object(mongo_config, "cached_discover"):
            first = mongo_config.resolve_mongo_uri("mongodb://root:pw@localhost:27017/")
            second = mongo_config.resolve_mongo_uri("mongodb://root:pw@localhost:27017/")
        assert first == second
        verify.assert_called_once()
