"""Tests for the ordered MySQL host chain."""
import pytest

from commonlib.sql import db_hosts


class TestDbCandidateHosts:
    def test_explicit_host_comes_first_then_the_container_chain(self, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_HOST', '10.0.0.1')
        assert db_hosts.db_candidate_hosts() == ('10.0.0.1', 'mysql_db', 'host.docker.internal', '127.0.0.1')

    @pytest.mark.parametrize('raw', ['', '  '], ids=['empty', 'blank'])
    def test_empty_falls_back_to_the_chain(self, monkeypatch, raw):
        monkeypatch.setenv('COMMONLIB_DB_HOST', raw)
        assert db_hosts.db_candidate_hosts() == db_hosts.DB_CANDIDATE_HOSTS

    @pytest.mark.parametrize('raw', ['auto', 'discover', 'AUTO'])
    def test_auto_uses_only_the_chain(self, monkeypatch, raw):
        monkeypatch.setenv('COMMONLIB_DB_HOST', raw)
        assert db_hosts.db_candidate_hosts() == db_hosts.DB_CANDIDATE_HOSTS

    def test_chain_host_is_not_duplicated(self):
        assert db_hosts.db_candidate_hosts('mysql_db') == db_hosts.DB_CANDIDATE_HOSTS

    def test_comma_groups_are_merged_in_order(self):
        hosts = db_hosts.db_candidate_hosts('10.0.0.1,10.0.0.2,127.0.0.1')
        assert hosts == ('10.0.0.1', '10.0.0.2', '127.0.0.1', 'mysql_db', 'host.docker.internal')

    def test_cidr_is_expanded(self):
        hosts = db_hosts.db_candidate_hosts('10.0.0.0/30')
        assert hosts[:2] == ('10.0.0.1', '10.0.0.2')

    def test_explicit_argument_overrides_the_env(self, monkeypatch):
        monkeypatch.setenv('COMMONLIB_DB_HOST', '192.168.1.1')
        assert db_hosts.db_candidate_hosts('10.0.0.9')[0] == '10.0.0.9'
