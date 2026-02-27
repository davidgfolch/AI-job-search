from crewai import Agent, Task, Crew, Process, LLM
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_enricher_service import (
    process_skill_enrichment,
    parse_skill_llm_output,
)
from commonlib.environmentUtil import getEnvBool, getEnv
import os

AI_ENRICH_SKILL_CATEGORIES = getEnv("AI_ENRICH_SKILL_CATEGORIES", required=True)

LLM_CFG = LLM(
    model="ollama/llama3.2",
    base_url=getEnv("AI_ENRICH_OLLAMA_BASE_URL", "http://localhost:11434"),
    temperature=0,
)

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

    agent = Agent(
        role="Skill Describer",
        goal="Generate precise descriptions for technical skills",
        backstory="You are an expert at defining technical skills for job matching.",
        verbose=False,
        allow_delegation=False,
        llm=LLM_CFG,
    )

    task = Task(
        description=f"Generate a deep technical description for the skill: {skill_name}. {context_str}\n{SYSTEM_PROMPT}",
        expected_output="A plain text string with sections for Summary, Deep Technical Details, and Category.",
        agent=agent,
    )

    crew = Crew(agents=[agent], tasks=[task], verbose=False, process=Process.sequential)

    result = str(crew.kickoff()).strip().strip('"').strip("'")
    return parse_skill_llm_output(result)


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
