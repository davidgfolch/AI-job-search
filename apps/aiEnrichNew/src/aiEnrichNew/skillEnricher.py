from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.observability import get_logger
from .llm_client import get_pipeline
from .services.skill_enrichment_service import enrich_skills
from .config import get_skill_enabled

logger = get_logger("aiEnrichNew.skillEnricher")


def skillEnricher() -> int:
    if not get_skill_enabled():
        return 0
    with MysqlUtil() as mysql:
        pipe = get_pipeline()
        return enrich_skills(mysql, pipe)
