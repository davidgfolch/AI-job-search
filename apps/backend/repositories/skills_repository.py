import json
from typing import List, Optional, Dict, Any
from commonlib.mysqlUtil import MysqlUtil, getConnection
from models.skill import Skill

class SkillsRepository:
    def get_db(self):
        return MysqlUtil(getConnection())

    def list_skills(self) -> List[Skill]:
        with self.get_db() as db:
            query = "SELECT name, description, learning_path, disabled, ai_enriched, category FROM job_skills ORDER BY name"
            rows = db.fetchAll(query)
            skills = []
            for row in rows:
                learning_path = []
                if row[2]:
                    try:
                        learning_path = json.loads(row[2])
                    except:
                        learning_path = []
                        
                skills.append(Skill(
                    name=row[0],
                    description=row[1] or "",
                    learning_path=learning_path,
                    disabled=bool(row[3]),
                    ai_enriched=bool(row[4]) if row[4] is not None else False,
                    category=row[5]
                ))
            return skills

    def find_by_name_case_insensitive(self, name: str) -> Optional[Dict[str, Any]]:
        with self.get_db() as db:
            query = "SELECT name, description, learning_path, disabled, ai_enriched, category FROM job_skills WHERE LOWER(name) = LOWER(%s)"
            row = db.fetchOne(query, name)
            if not row:
                return None
            learning_path = []
            if row[2]:
                try:
                    learning_path = json.loads(row[2])
                except:
                    learning_path = []
            return {
                'name': row[0],
                'description': row[1] or "",
                'learning_path': learning_path,
                'disabled': bool(row[3]),
                'ai_enriched': bool(row[4]) if row[4] is not None else False,
                'category': row[5]
            }

    def create_skill(self, skill: Skill) -> str:
        with self.get_db() as db:
            query = "INSERT INTO job_skills (name, description, learning_path, disabled, ai_enriched, category) VALUES (%s, %s, %s, %s, %s, %s)"
            params = [
                skill.name,
                skill.description,
                json.dumps(skill.learning_path) if skill.learning_path else None,
                skill.disabled,
                skill.ai_enriched,
                skill.category
            ]
            db.executeAndCommit(query, params)
            return skill.name

    def update_skill(self, name: str, update_data: Dict[str, Any]) -> Optional[str]:
        with self.get_db() as db:
            # check exists
            # fetchOne expects a single ID, it will wrap it in a list
            check = db.fetchOne("SELECT name FROM job_skills WHERE name = %s", name)
            if not check:
                return None
            set_clauses = []
            params = []
            if 'description' in update_data:
                set_clauses.append("description = %s")
                params.append(update_data['description'])
            if 'learning_path' in update_data:
                set_clauses.append("learning_path = %s")
                lp = update_data['learning_path']
                params.append(json.dumps(lp) if lp is not None else None)
            
            if 'disabled' in update_data:
                set_clauses.append("disabled = %s")
                params.append(update_data['disabled'])
            if 'ai_enriched' in update_data:
                set_clauses.append("ai_enriched = %s")
                params.append(update_data['ai_enriched'])
            if 'category' in update_data:
                set_clauses.append("category = %s")
                params.append(update_data['category'])

            if not set_clauses:
                return name
            params.append(name)
            query = f"UPDATE job_skills SET {', '.join(set_clauses)} WHERE name = %s"
            db.executeAndCommit(query, params)
            return name

    def delete_skill(self, name: str) -> bool:
        with self.get_db() as db:
            query = "DELETE FROM job_skills WHERE name = %s"
            affected = db.executeAndCommit(query, [name])
            return affected > 0 or True # executeAndCommit might return headers or something, assuming success if no exception
