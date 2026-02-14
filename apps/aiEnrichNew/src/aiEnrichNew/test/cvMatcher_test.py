import pytest
from unittest.mock import patch, MagicMock
from ..cvMatcher import FastCVMatcher


@pytest.fixture
def mock_all():
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
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
    with patch("aiEnrichNew.cvMatcher.MysqlUtil") as mu:
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
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
    ):
        si = MagicMock()
        st.return_value = si
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = True
        l.get_content.return_value = "CV"
        m = FastCVMatcher.instance()
        m._cv_embedding = None
        assert m.match("JD")["cv_match_percentage"] == 0


def test_match_exc():
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
        patch("aiEnrichNew.cvMatcher.cosine_similarity") as cs,
    ):
        si = MagicMock()
        st.return_value = si
        si.encode.return_value = [[0.1, 0.2]]
        l = MagicMock()
        lc.return_value = l
        l.load_cv_content.return_value = True
        l.get_content.return_value = "CV"
        m = FastCVMatcher.instance()
        cs.side_effect = Exception("e")
        assert m.match("JD")["cv_match_percentage"] == 0


def test_save_err():
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
    ):
        si = MagicMock()
        st.return_value = si
        l = MagicMock()
        lc.return_value = l
        m = FastCVMatcher.instance()
        r = MagicMock()
        m._save_error(r, 1, "T", "C", Exception("e"))
        r.update_enrichment_error.assert_called_once()


def test_footer_err():
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
        patch("aiEnrichNew.cvMatcher.print"),
    ):
        si = MagicMock()
        st.return_value = si
        l = MagicMock()
        lc.return_value = l
        m = FastCVMatcher.instance()
        m.jobErrors.add((1, "e1"))
        with (
            patch("aiEnrichNew.cvMatcher.yellow"),
            patch("aiEnrichNew.cvMatcher.red"),
            patch("aiEnrichNew.cvMatcher.green"),
        ):
            m._print_footer(10, 5)


def test_disabled():
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer"),
        patch("aiEnrichNew.cvMatcher.CVLoader"),
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=False),
    ):
        assert FastCVMatcher.instance().process_db_jobs() == 0


def test_no_cv():
    FastCVMatcher._instance = None
    with (
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
        patch("aiEnrichNew.cvMatcher.MysqlUtil"),
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
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
        patch("aiEnrichNew.cvMatcher.MysqlUtil") as mu,
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
        patch("aiEnrichNew.cvMatcher.SentenceTransformer") as st,
        patch("aiEnrichNew.cvMatcher.CVLoader") as lc,
        patch("aiEnrichNew.cvMatcher.getEnvBool", return_value=True),
        patch("aiEnrichNew.cvMatcher.MysqlUtil") as mu,
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
