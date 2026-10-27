"""Patches, payloads and test doubles shared by the dataExtractor tests."""

from contextlib import contextmanager, nullcontext
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from commonlib.ollama_client import OllamaResponse

ENRICHMENT_JSON = '{"required_technologies": [], "optional_technologies": [], "salary": "100k", "modality": ["REMOTE"]}'
JOB_ROW = (1, "Job", "Desc", "Comp")
MAPPED_JOB = ("Job", "Comp", "Desc")


def enrich_repo(job_id=1):
    """Repository double whose enrichment/retry lookups return a job and whose config map is a real dict."""
    repo = MagicMock()
    repo.count_pending_enrichment.return_value = 0
    repo.get_job_to_enrich.return_value = (job_id,) + JOB_ROW[1:]
    repo.get_job_to_retry.return_value = (job_id,) + JOB_ROW[1:]
    repo._job_configs = {}
    return repo


def selector(config_names, matched_ids):
    """FilterConfigSelector double reporting `config_names` as watched and `matched_ids` as matches."""
    fake = MagicMock()
    fake.load_configs.return_value = [{"name": name, "filters": {}} for name in config_names]
    fake.match_ids.return_value = matched_ids
    return fake


def ollama_response(payload=ENRICHMENT_JSON):
    return OllamaResponse(text=payload, url="http://ollama", done=True, done_reason="stop")


@contextmanager
def selector_patches(fake_selector):
    """Patch the DB, the selector factory and the clock used by dataExtractor/retry_failed_jobs."""
    with patch("aiEnrich.dataExtractor.MysqlUtil") as mysql_util, \
         patch("commonlib.sql.filter_config_selector.FilterConfigSelector", return_value=fake_selector), \
         patch("aiEnrich.dataExtractor.stopWatch"), \
         patch("aiEnrich.dataExtractor._batch_start", 0):
        mysql_util.return_value.__enter__.return_value = MagicMock()
        yield


@contextmanager
def process_job_patches(*, backend="ollama", fake_save=True, fake_parse=False):
    """Patch every collaborator of _process_job_safe (DB, network, clock)."""
    save_patch = patch("aiEnrich.dataExtractor._save") if fake_save else nullcontext(None)
    parse_patch = patch("aiEnrich.dataExtractor.query_and_parse") if fake_parse else nullcontext(None)
    with patch("aiEnrich.dataExtractor.mapJob", return_value=MAPPED_JOB), \
         patch("aiEnrich.dataExtractor.ping_backend", return_value=True), \
         patch("aiEnrich.dataExtractor.get_backend", return_value=backend), \
         patch("aiEnrich.dataExtractor.resolve_unspecified_company"), \
         patch("aiEnrich.dataExtractor._notify_watcher_backend"), \
         patch("aiEnrich.dataExtractor.footer"), \
         patch("aiEnrich.dataExtractor.stopWatch"), \
         patch("aiEnrich.ollama_backend.query_openrouter") as openrouter, \
         patch("aiEnrich.ollama_backend.query_ollama") as ollama, \
         parse_patch as query_and_parse, save_patch as save:
        yield SimpleNamespace(save=save, openrouter=openrouter, ollama=ollama, query_and_parse=query_and_parse)
