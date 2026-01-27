from crewai import Agent, Task, Crew, Process
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_enricher_service import process_skill_enrichment
from commonlib.environmentUtil import getEnvBool, getEnv
import os

SKILL_CATEGORIES_DEFAULT = "Languages, Frameworks, Libraries, Tools, Databases, Platforms, AI, Big Data, Soft Skills, Other"
SKILL_CATEGORIES = getEnv("SKILL_CATEGORIES", SKILL_CATEGORIES_DEFAULT)

SYSTEM_PROMPT = f"""You are an expert technical recruiter and software engineer.
Your task is to provide a structured description for a given technical skill.
The structure MUST be:
1. **Summary**: A concise 1-2 sentence overview of what the skill is.
2. **Deep Technical Details**: A detailed explanation including:
   - Core Functionality
   - Usage Types (library, framework, etc.)
   - Key Modules/Components
   - Integration with co-occurring technologies
3. **Category**: One or more of [{SKILL_CATEGORIES}] (comma separated).
Output ONLY the structured text. Do not include any conversational text. Use 'Category: ' prefix for the category line."""

def generate_skill_description(skill_name, context="") -> tuple[str, str]:
    
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
        expected_output="A plain text string with sections for Summary, Deep Technical Details, and Category.",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=False,
        process=Process.sequential
    )
    
    result = str(crew.kickoff()).strip().strip('"').strip("'")
    
    # Simple parsing to extract category
    # Assumes Category is at the end or clearly marked
    category = "Other"
    description = result
    
    if "Category:" in result:
        parts = result.split("Category:")
        if len(parts) > 1:
            description = parts[0].strip()
            # Remove trailing ** or ## if present in description due to split
            category_part = parts[1].strip()
            # Cleanup category part (remove likely trailing chars or newlines)
            category = category_part.split('\n')[0].strip()
            # Remove ** if agent wrapped it
            category = category.replace("*", "").strip()
            
    return description, category


def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        return process_skill_enrichment(mysql, generate_skill_description, limit=10, check_empty_description_only=True)
