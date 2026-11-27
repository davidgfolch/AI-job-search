from typing import Callable
from commonlib.observability import get_logger
from commonlib.stopWatch import StopWatch

logger = get_logger("commonlib.services.skill_enricher_service")


class BackendUnavailable(Exception):
    """Raised by a generator when the model server is down mid-batch.

    The batch stops on it: nothing is written, so the items still to do stay pending and are
    retried once the server answers again instead of being written off as unenrichable.
    """


def log_no_pending_skills(limit: int) -> None:
    """The one record an idle skill cycle logs, shared by the ollama and huggingface paths."""
    logger.info("jobs.skipped", message="No skills pending.", reason="no_pending_skills", limit=limit)


def process_skill_enrichment(
    repository,
    generate_description_fn: Callable[[str, str], tuple[str, str]],
    limit: int = 10,
    check_empty_description_only: bool = True
) -> int:
    """Run the shared enrichment loop over a repository, keeping DB access out of services."""
    names = repository.fetch_pending_skill_names(limit, check_empty_description_only)
    if not names:
        log_no_pending_skills(limit)
        return 0
    logger.info("skill.enrich_started", count=len(names), limit=limit, check_empty_description_only=check_empty_description_only)
    count = 0
    stop_watch = StopWatch()
    for i, name in enumerate(names):
        stop_watch.start()
        context = ""
        try:
            context = repository.fetch_skill_context(name)
        except Exception:
            pass # context fetching fail shouldn't stop flow
        logger.debug("skill.enriching", index=i + 1, total=len(names), name=name, input_length=len(context) + len(name))
        try:
            result = generate_description_fn(name, context)
            normalized = _normalize_generation_result(result)
            if normalized is None:
                logger.warning("skill.invalid_result", name=name, result_type=type(result).__name__)
                continue
            description, category, learning_path = normalized
            if description and "Error" not in description:
                result_log = {
                    "description": description[:100] + "..." if len(description) > 100 else description,
                    "category": category,
                    "learning_path": len(learning_path)
                }
                fields = ["description", "category"] + (["learning_path"] if learning_path else [])
                logger.debug("skill.enriched", name=name, result=result_log)
                logger.debug("skill.persisting", name=name, fields=fields)
                repository.save_skill_result(name, description, category, learning_path)
                count += 1
            else:
                logger.warning("skill.description_failed", name=name)
        except BackendUnavailable:
            # The server went away mid-batch: stop here and leave the rest pending.
            logger.error("skill.enrich_aborted", name=name, reason="backend_unavailable", remaining=len(names) - i - 1)
            break
        except Exception:
            logger.exception("skill.enrich_failed", name=name)
        stop_watch.end()
        logger.debug("skill.iteration_completed", index=i + 1, total=len(names))
    logger.info("skill.enrich_completed", updated=count, count=len(names))
    return count


def _normalize_generation_result(result) -> tuple[str, str | None, list] | None:
    """Accepts the (description, category[, learning_path]) tuple or a bare description string."""
    if isinstance(result, tuple) and len(result) in (2, 3):
        description, category = result[0], result[1]
        learning_path = result[2] if len(result) == 3 else []
        return description, category, list(learning_path or [])
    if isinstance(result, str):
        return result, None, []
    return None
