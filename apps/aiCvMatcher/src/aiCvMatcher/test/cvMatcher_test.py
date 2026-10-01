import pytest
from contextlib import ExitStack, contextmanager
from unittest.mock import patch, MagicMock
from ..cvMatcher import FastCVMatcher


@pytest.fixture(autouse=True)
def reset_shared_state():
    job_errors, total_count = FastCVMatcher.jobErrors, FastCVMatcher.totalCount
    FastCVMatcher.jobErrors, FastCVMatcher.totalCount = set(), 0
    yield
    FastCVMatcher.jobErrors, FastCVMatcher.totalCount = job_errors, total_count


@contextmanager
def patched_matcher(*extras):
    with ExitStack() as stack:
        stack.enter_context(patch("aiCvMatcher.cvMatcher.SentenceTransformer"))
        stack.enter_context(patch("aiCvMatcher.cvMatcher.CVLoader"))
        stack.enter_context(patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=True))
        started = [stack.enter_context(extra) for extra in extras]
        FastCVMatcher._instance = None
        matcher = FastCVMatcher.instance()
        matcher._cv_loader.load_cv_content.return_value = True
        matcher._cv_loader.get_content.return_value = "CV"
        yield matcher, started


@pytest.fixture
def mock_all():
    with (
        patch("aiCvMatcher.cvMatcher.SentenceTransformer") as st,
        patch("aiCvMatcher.cvMatcher.CVLoader") as lc,
        patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=True),
    ):
        si = MagicMock()
        st.return_value = si
        si.encode.return_value = [[0.1, 0.2]]
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = True
        l.get_content.return_value = "CV"
        yield {"st": si, "loader": l}


def test_init(mock_all):
    FastCVMatcher._instance = None
    m = FastCVMatcher.instance()
    assert m._model is not None


def test_process_db(mock_all):
    FastCVMatcher._instance = None
    m = FastCVMatcher.instance()
    with patch("aiCvMatcher.cvMatcher.MysqlUtil") as mu:
        mysql = MagicMock()
        mu.return_value.__enter__.return_value = mysql
        mysql.count.return_value = 1
        mysql.fetchAll.return_value = [(1,)]
        mysql.fetchOne.return_value = (1, "T", b"D", "C")
        m.process_db_jobs()
        mysql.updateFromAI.assert_called()


def test_match(mock_all):
    FastCVMatcher._instance = None
    m = FastCVMatcher.instance()
    m._load_cv_content()
    res = m.match("JD")
    assert "cv_match_percentage" in res


def test_match_no_emb():
    with patched_matcher() as (m, _):
        m._cv_embedding = None
        assert m.match("JD")["cv_match_percentage"] == 0


def test_match_exc():
    cs = patch("aiCvMatcher.cvMatcher.cosine_similarity", side_effect=Exception("e"))
    with patched_matcher(cs) as (m, _):
        m._load_cv_content()
        assert m.match("JD")["cv_match_percentage"] == 0


def test_match_logs_exception():
    log = patch("aiCvMatcher.cvMatcher.logger")
    cs = patch("aiCvMatcher.cvMatcher.cosine_similarity", side_effect=Exception("boom"))
    with patched_matcher(log, cs) as (m, (log_mock, _)):
        m._load_cv_content()
        assert m.match("JD")["cv_match_percentage"] == 0
        log_mock.exception.assert_called_once_with("match.failed")


def test_save_err():
    with patched_matcher() as (m, _):
        r = MagicMock()
        m._save_error(r, 1, "T", "C", Exception("e"))
        r.update_enrichment_error.assert_called_once()


def test_save_error_logs_failure():
    with patched_matcher(patch("aiCvMatcher.cvMatcher.logger")) as (m, (log,)):
        r = MagicMock()
        m._save_error(r, 1, "T", "C", Exception("e"))
        r.update_enrichment_error.assert_called_once()
        log.exception.assert_called_once_with("job.failed", job_id=1, title="T", company="C")
        log.warning.assert_called_once_with("job.error_saved", job_id=1, cv_match_percentage=-1)


@pytest.mark.parametrize("with_errors, expected_event", [(True, "jobs.batch_errors"), (False, None)])
def test_footer_logs_summary(with_errors, expected_event):
    with patched_matcher(patch("aiCvMatcher.cvMatcher.logger")) as (m, (log,)):
        if with_errors:
            m.jobErrors.add((1, "e1"))
        m._print_footer(10, 5)
        log.info.assert_any_call("jobs.batch_completed", processed=6, total=10, total_processed=0)
        if expected_event is None:
            log.warning.assert_not_called()
        else:
            log.warning.assert_called_once_with("jobs.batch_errors", job_errors=1)


def test_disabled():
    FastCVMatcher._instance = None
    with (
        patch("aiCvMatcher.cvMatcher.SentenceTransformer"),
        patch("aiCvMatcher.cvMatcher.CVLoader"),
        patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=False),
    ):
        assert FastCVMatcher.instance().process_db_jobs() == 0


def test_no_cv():
    FastCVMatcher._instance = None
    with (
        patch("aiCvMatcher.cvMatcher.SentenceTransformer") as st,
        patch("aiCvMatcher.cvMatcher.CVLoader") as lc,
        patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=True),
        patch("aiCvMatcher.cvMatcher.MysqlUtil"),
    ):
        si = MagicMock()
        st.return_value = si
        si.encode.return_value = [[0.1]]
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = False
        assert FastCVMatcher.instance().process_db_jobs() == 0


def test_no_jobs():
    FastCVMatcher._instance = None
    with (
        patch("aiCvMatcher.cvMatcher.SentenceTransformer") as st,
        patch("aiCvMatcher.cvMatcher.CVLoader") as lc,
        patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=True),
        patch("aiCvMatcher.cvMatcher.MysqlUtil") as mu,
    ):
        si = MagicMock()
        st.return_value = si
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = True
        l.get_content.return_value = "CV"
        mysql = MagicMock()
        mu.return_value.__enter__.return_value = mysql
        mysql.count.return_value = 0
        assert FastCVMatcher.instance().process_db_jobs() == 0


def test_job_none():
    FastCVMatcher._instance = None
    with (
        patch("aiCvMatcher.cvMatcher.SentenceTransformer") as st,
        patch("aiCvMatcher.cvMatcher.CVLoader") as lc,
        patch("aiCvMatcher.cvMatcher.getEnvBool", return_value=True),
        patch("aiCvMatcher.cvMatcher.MysqlUtil") as mu,
    ):
        si = MagicMock()
        st.return_value = si
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = True
        l.get_content.return_value = "CV"
        mysql = MagicMock()
        mu.return_value.__enter__.return_value = mysql
        mysql.count.return_value = 1
        mysql.fetchAll.return_value = [(1,)]
        mysql.fetchOne.return_value = None
        assert FastCVMatcher.instance().process_db_jobs() == 1
