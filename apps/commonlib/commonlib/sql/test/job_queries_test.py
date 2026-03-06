"""Tests for job_queries module."""
import pytest
from commonlib.sql.job_queries import (
    QRY_FIND_JOB_BY_JOB_ID,
    QRY_INSERT,
    QRY_SELECT_JOBS_VIEWER,
    QRY_SELECT_COUNT_JOBS,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY,
    SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT,
    SELECT_APPLIED_JOB_ORDER_BY,
    DB_FIELDS_BOOL,
    QRY_UPDATE_JOB_DIRECT_URL,
)


class TestJobQueries:
    """Tests for SQL query constants."""

    def test_qry_find_job_by_job_id_is_string(self):
        """QRY_FIND_JOB_BY_JOB_ID should be a non-empty string."""
        assert isinstance(QRY_FIND_JOB_BY_JOB_ID, str)
        assert len(QRY_FIND_JOB_BY_JOB_ID) > 0
        assert 'SELECT' in QRY_FIND_JOB_BY_JOB_ID

    def test_qry_insert_is_string(self):
        """QRY_INSERT should be a non-empty string."""
        assert isinstance(QRY_INSERT, str)
        assert len(QRY_INSERT) > 0
        assert 'INSERT' in QRY_INSERT

    def test_qry_select_jobs_viewer_is_string(self):
        """QRY_SELECT_JOBS_VIEWER should be a non-empty string."""
        assert isinstance(QRY_SELECT_JOBS_VIEWER, str)
        assert len(QRY_SELECT_JOBS_VIEWER) > 0
        assert 'SELECT' in QRY_SELECT_JOBS_VIEWER

    def test_qry_select_count_jobs_is_string(self):
        """QRY_SELECT_COUNT_JOBS should be a non-empty string."""
        assert isinstance(QRY_SELECT_COUNT_JOBS, str)
        assert len(QRY_SELECT_COUNT_JOBS) > 0
        assert 'count' in QRY_SELECT_COUNT_JOBS.lower()

    def test_select_applied_job_ids_by_company_is_string(self):
        """SELECT_APPLIED_JOB_IDS_BY_COMPANY should be a non-empty string."""
        assert isinstance(SELECT_APPLIED_JOB_IDS_BY_COMPANY, str)
        assert len(SELECT_APPLIED_JOB_IDS_BY_COMPANY) > 0
        assert 'select' in SELECT_APPLIED_JOB_IDS_BY_COMPANY.lower()

    def test_select_applied_job_ids_by_company_client_is_string(self):
        """SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT should be a non-empty string."""
        assert isinstance(SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT, str)
        assert len(SELECT_APPLIED_JOB_IDS_BY_COMPANY_CLIENT) > 0

    def test_select_applied_job_order_by_is_string(self):
        """SELECT_APPLIED_JOB_ORDER_BY should be a non-empty string."""
        assert isinstance(SELECT_APPLIED_JOB_ORDER_BY, str)
        assert len(SELECT_APPLIED_JOB_ORDER_BY) > 0
        assert 'order by' in SELECT_APPLIED_JOB_ORDER_BY.lower()

    def test_db_fields_bool_is_string(self):
        """DB_FIELDS_BOOL should be a non-empty string."""
        assert isinstance(DB_FIELDS_BOOL, str)
        assert len(DB_FIELDS_BOOL) > 0
        assert 'applied' in DB_FIELDS_BOOL

    def test_qry_update_job_direct_url_is_string(self):
        """QRY_UPDATE_JOB_DIRECT_URL should be a non-empty string."""
        assert isinstance(QRY_UPDATE_JOB_DIRECT_URL, str)
        assert len(QRY_UPDATE_JOB_DIRECT_URL) > 0
        assert 'UPDATE' in QRY_UPDATE_JOB_DIRECT_URL
