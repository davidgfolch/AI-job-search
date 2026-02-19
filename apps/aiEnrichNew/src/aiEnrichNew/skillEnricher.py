from commonlib.mysqlUtil import MysqlUtil
from commonlib.environmentUtil import getEnvBool
from .llm_client import get_pipeline
from .services.skill_enrichment_service import enrich_skills

def skillEnricher() -> int:
    with MysqlUtil() as mysql:
        # Check if skill enrichment is enabled is handled inside service, 
        # but prompt loading might happen if we get pipeline here.
        # However, enrich_skills checks env first.
        # We can pass pipeline loosely.
        
        # Optimization: check env before loading pipeline
        if not getEnvBool("AI_ENRICH_SKILL", True):
            return 0
            
        pipe = get_pipeline()
        return enrich_skills(mysql, pipe)
