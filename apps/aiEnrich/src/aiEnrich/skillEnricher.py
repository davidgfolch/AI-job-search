from commonlib.sql.mysqlUtil import MysqlUtil
from commonlib.skill_enricher_service import (
    process_skill_enrichment,
    parse_skill_llm_output,
)
from commonlib.environmentUtil import getEnvBool, getEnv
from commonlib.observability import get_logger
from .ollama_client import query_ollama

logger = get_logger("aiEnrich.skillEnricher")

AI_ENRICH_SKILL_CATEGORIES = getEnv("AI_ENRICH_SKILL_CATEGORIES", required=True)

SYSTEM_PROMPT = f"""You are an expert technical recruiter and software engineer.
Your task is to provide a structured description for a given technical skill.
The structure MUST be:
1. **Summary**: A concise 1-2 sentence overview of what the skill is.
2. **Deep Technical Details**: A detailed explanation including:
   - Core Functionality
   - Usage Types (library, framework, etc.)
   - Key Modules/Components
   - Integration with co-occurring technologies
3. **Category**: One or more of [{AI_ENRICH_SKILL_CATEGORIES}] (comma separated).
Output ONLY the structured text. Do not include any conversational text. Use 'Category: ' prefix for the category line."""


def generate_skill_description(skill_name, context="") -> tuple[str, str]:
    context_str = (
        f"\nContext (related technologies found in jobs): {context}" if context else ""
    )

    logger.info("skill.started", skill=skill_name, has_context=bool(context))

    prompt = f"Generate a deep technical description for the skill: {skill_name}. {context_str}\n{SYSTEM_PROMPT}"
    raw = query_ollama(
        prompt=prompt,
        model="ollama/llama3.2",
        base_url=getEnv("AI_ENRICH_OLLAMA_BASE_URL", "http://localhost:11434"),
        timeout=90,
        json_mode=False,
    )
    if raw is None:
        logger.error("skill.failed", skill=skill_name)
        return ("", "Other")

    result = raw.strip().strip('"').strip("'")
    parsed = parse_skill_llm_output(result)
    logger.info("skill.completed", skill=skill_name, has_description=bool(parsed[0]))
    return parsed


def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        return process_skill_enrichment(
            mysql,
            generate_skill_description,
            limit=10,
            check_empty_description_only=True,
        )
