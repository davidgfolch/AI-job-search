from crewai import Agent, Task, Crew, Process
from commonlib.mysqlUtil import MysqlUtil
from commonlib.skill_context import get_skill_context
from commonlib.terminalColor import yellow, magenta, cyan

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
    # crewai result is usually a string, or CrewOutput object.
    # We need to parse it. 
    # If standard crewai usage, kickoff returns the result of the last task as string if configured properly.
    return str(result).strip().strip('"').strip("'")

from commonlib.environmentUtil import getEnvBool

def skillEnricher() -> int:
    if not getEnvBool("AI_ENRICH_SKILL", True):
        return 0
    with MysqlUtil() as mysql:
        # Check for skills needing enrichment
        query_find = "SELECT name FROM job_skills WHERE (ai_enriched IS NULL OR ai_enriched = 0) AND (description IS NULL OR description = '') LIMIT 10"
        rows = mysql.fetchAll(query_find)
        if not rows:
            return 0
        print(cyan(f"Found {len(rows)} skills to enrich..."))
        count = 0
        for row in rows:
            name = row[0]
            print("Enriching skill: ", yellow(name))
            try:
                context = get_skill_context(mysql, name)
                description = generate_skill_description(name, context)
                if description and "Error" not in description:
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
