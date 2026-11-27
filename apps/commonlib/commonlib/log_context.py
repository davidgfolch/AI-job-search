"""Contextual fields bound for the duration of a unit of work.

Split out of `observability` (which re-exports them): binding is a caller concern, while
`observability` owns the structlog configuration and the JSONL console rendering.
"""
from contextlib import contextmanager

import structlog


@contextmanager
def job_log_context(job_id: int):
    """Stamp `job_id` on every record logged inside the block.

    `merge_contextvars` runs first in the chain, so binding once per unit of work covers
    the records the call sites emit and the ones shared helpers emit on their behalf
    (`commonlib.sql.query_executor`, `commonlib.ollama_client`), with no change at either
    end. An explicit `job_id=` at a call site still wins over the bound value.

    The id is unbound on exit so it cannot leak into the batch-level records that follow
    the loop, which describe many jobs rather than one.
    """
    if job_id is None:
        yield
        return
    structlog.contextvars.bind_contextvars(job_id=job_id)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars("job_id")


@contextmanager
def keyword_log_context(site: str, keyword: str):
    """Stamp `scrapper` and `keyword` on every record logged inside the block.

    Wrapping one keyword of a scraper run attributes all the per-row records the site
    services emit (totals, loaded counts, inserts and already-in-DB detections) to the
    search that produced them, without changing the call sites. Explicit fields at a
    call site still win, and the values are unbound on exit so batch-level records that
    follow the loop do not inherit them.
    """
    structlog.contextvars.bind_contextvars(scrapper=site, keyword=keyword)
    try:
        yield
    finally:
        structlog.contextvars.unbind_contextvars("scrapper", "keyword")
