from crewai import Agent, Task, Crew, Process
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_enricher_service import process_skill_enrichment
from commonlib.environmentUtil import getEnvBool

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
    
    agent = Agent(
        role='Skill Describer',
        goal='Generate precise descriptions for technical skills',
        backstory='You are an expert at defining technical skills for job matching.',
        verbose=False,
        allow_delegation=False
    )
    
    task = Task(
        description=f"Generate a deep technical description for the skill: {skill_name}. {context_str}\n{SYSTEM_PROMPT}",
        expected_output="A single plain text string containing only the skill description.",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
        process=Process.sequential
    )
    
    result = crew.kickoff()
    return str(result).strip().strip('"').strip("'")


def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        return process_skill_enrichment(mysql, generate_skill_description, limit=10, check_empty_description_only=True)
