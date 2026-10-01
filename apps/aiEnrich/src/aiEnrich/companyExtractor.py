from typing import Callable

from commonlib.observability import get_logger
from commonlib.company_normalizer import is_unspecified_company
from .aiEnrich_config import get_max_validation_retries
from .extraction_contract import query_company

logger = get_logger("aiEnrich.companyExtractor")

MAX_COMPANY_INPUT_LEN = 4000

COMPANY_PROMPT = """Identify the company publishing the following job offer.
Return only one valid JSON object with exactly one field: company.
Company must be the company name as written in the offer, or null when the offer does not state it.
Do not return the recruiting agency, the platform, a placeholder such as "unspecified", markdown, or any other field.

Job Offer:
{markdown}"""


def build_company_prompt(title: str, markdown: str) -> str:
    return COMPANY_PROMPT.format(markdown=f"# {title} \n {markdown[:MAX_COMPANY_INPUT_LEN]}")


def resolve_unspecified_company(
    repo,
    id: int,
    title: str,
    company: str | None,
    markdown: str,
    query: Callable[[str], object],
    log=None,
) -> str | None:
    """Infers the company of a job saved as unspecified and re-runs duplicate detection with it.

    Best effort: any failure leaves the company as unspecified, so a failed guess never
    marks the job as failed to enrich.
    """
    log = log or logger
    if not is_unspecified_company(company):
        return None
    try:
        company, _ = query_company(query, build_company_prompt(title, markdown), max_attempts=get_max_validation_retries() + 1)
        if not company:
            log.info("company.unresolved", job_id=id, title=title)
            return None
        repo.update_unspecified_company(id, company)
        repo.refresh_duplicated_of(id, title, company)
        log.info("company.resolved", job_id=id, title=title, company=company)
        return company
    except Exception as ex:
        log.warning("company.resolution_failed", job_id=id, title=title, error=str(ex))
        return None
