from commonlib.mysqlUtil import MysqlUtil
from .llm_client import get_pipeline
from .services.skill_enrichment_service import enrich_skills
from .config import get_skill_enabled


def skillEnricher() -> int:
    if not get_skill_enabled():
        return 0
    with MysqlUtil() as mysql:
        pipe = get_pipeline()
        return enrich_skills(mysql, pipe)
