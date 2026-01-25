import traceback
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.terminalColor import yellow, magenta, cyan
from .llm_client import get_pipeline

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

from commonlib.environmentUtil import getEnvBool

def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        # Check for skills needing enrichment
        query_find = "SELECT name FROM job_skills WHERE ai_enriched = 0 LIMIT 3"
        rows = mysql.fetchAll(query_find)
        if not rows:
            print(yellow("No skills to enrich"))
            return 0
        print(cyan(f"Found {len(rows)} skills to enrich..."))
        count = 0
        for row in rows:
            name = row[0]
            print("Enriching skill: ", yellow(name))
            try:
                context = get_skill_context(mysql, name)
                description = generate_skill_description(name, context)
                if description:
                    print("Description: ", magenta(description))
                    update_query = "UPDATE job_skills SET description = %s, ai_enriched = 1 WHERE name = %s"
                    mysql.executeAndCommit(update_query, [description, name])
                    count += 1
                else:
                    print(yellow(f"Failed to generate description for {name}"))
            except Exception as e:
                print(yellow(f"Error enriching skill {name}"))
                print(red(traceback.format_exc()))
        return count
