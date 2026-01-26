import traceback
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.terminalColor import yellow, magenta, cyan, red
from .llm_client import get_pipeline
from commonlib.environmentUtil import getEnvBool
from commonlib.skill_enricher_service import process_skill_enrichment

SYSTEM_PROMPT = """You are an expert technical recruiter and software engineer.
Your task is to provide a structured description for a given technical skill.
The structure MUST be:
1. **Summary**: A concise 1-2 sentence overview of what the skill is.
2. **Deep Technical Details**: A detailed explanation including:
   - Core Functionality
   - Usage Types (library, framework, etc.)
   - Key Modules/Components
   - Integration with co-occurring technologies
Output ONLY the structured text. Do not include any conversational text."""

def generate_skill_description(skill_name, context="") -> str:
    context_str = f"\nContext (related technologies found in jobs): {context}" if context else ""
    user_message = f"Skill: {skill_name}{context_str}\n\nProvide a deep technical description."
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message}
    ]
    prompt = get_pipeline().tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    output = get_pipeline()(prompt)
    generated_text = output[0]['generated_text']
    return generated_text.strip().strip('"').strip("'")


def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        # Note: aiEnrichNew logic was limiting to 3 and checking only ai_enriched = 0.
        # aiEnrich was limiting to 10 and checking also description is empty.
        # The common service now supports both modes but for consistency I will match logic to common unless specific requirement.
        # The user request was "abstract common functionalities".
        # I'll use the common service as configured for typical usage: limit can be parameter, check_empty can be False if that was the logic in New.
        
        # Original New logic: "SELECT name FROM job_skills WHERE ai_enriched = 0 LIMIT 3"
        return process_skill_enrichment(mysql, generate_skill_description, limit=3, check_empty_description_only=False)
