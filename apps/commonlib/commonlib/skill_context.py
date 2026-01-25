import re
import ast
from typing import Set
from commonlib.mysqlUtil import MysqlUtil

def get_skill_context(mysql: MysqlUtil, skill_name: str) -> str:
    """
    Fetches context for a skill by looking at required and optional technologies
    in jobs where the skill appears.
    Returns a comma-separated string of unique co-occurring technologies.
    """
    query = """
    SELECT required_technologies, optional_technologies 
    FROM jobs 
    WHERE required_technologies LIKE %s OR optional_technologies LIKE %s 
    LIMIT 20
    """
    search_term = f"%{skill_name}%"
    rows = mysql.fetchAll(query, (search_term, search_term))
    
    co_occurring: Set[str] = set()
    
    for row in rows:
        # row[0] is required_tech, row[1] is optional_tech
        for tech_str in row:
            if not tech_str:
                continue
                
            # Try to parse as list if it looks like one, otherwise split by comma
            try:
                # efficient check for list-like string
                if tech_str.strip().startswith('[') and tech_str.strip().endswith(']'):
                    techs = ast.literal_eval(tech_str)
                    if isinstance(techs, list):
                        for t in techs:
                            if isinstance(t, str):
                                co_occurring.add(t.strip())
                        continue
            except (ValueError, SyntaxError):
                pass
            
            # Fallback to comma separation
            for t in tech_str.split(','):
                cleaned = t.strip()
                if cleaned:
                    co_occurring.add(cleaned)

    # Remove the skill itself (case insensitive cleanup)
    lower_skill = skill_name.lower()
    final_techs = [t for t in co_occurring if t.lower() != lower_skill]
    
    # Sort for deterministic output
    final_techs.sort()
    
    # Return top 30 to avoid prompt overflow
    return ", ".join(final_techs[:30])
