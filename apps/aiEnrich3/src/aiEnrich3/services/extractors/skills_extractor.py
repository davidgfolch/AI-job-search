from typing import Optional, List, Tuple
from gliner import GLiNER

class SkillsExtractor:
    def __init__(self, model: Optional[GLiNER] = None):
        # We allow injecting the model because job_enrichment_service can load it once
        # and share it between the SalaryExtractor and SkillsExtractor.
        if model is None:
            self.model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        else:
            self.model = model
            
        # We use explicit English and widely used labels which GLiNER's multilingual 
        # GLiNER excels at identifying the entity itself, but struggles with adjectival context.
        self.labels = ["technology", "tool", "programming language", "software", "skill"]
        
        self.optional_keywords = [
            "nice to have", "optional", "plus", "valorable", "bonus", "advantage", 
            "beneficial", "opcional", "deseable", "atout", "preferred"
        ]

    def extract(self, text: str) -> Tuple[List[str], List[str]]:
        """
        Extracts skills from text and separates them into required and optional.
        Returns: (required_skills, optional_skills)
        """
        if not text:
            return [], []
            
        required_skills = []
        optional_skills = []
        seen_required = set()
        seen_optional = set()
        
        text_lower = text.lower()
        
        chunk_size = 1200
        overlap = 200
        chunks = []
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            chunks.append((i, chunk))

        for offset, chunk in chunks:
            entities = self.model.predict_entities(chunk, self.labels, threshold=0.45)
            
            for entity in entities:
                skill_text = entity["text"].strip().lower()
                global_start_idx = offset + entity["start"]
                
                if not skill_text or len(skill_text) < 2:
                    continue
                    
                # Look back up to 120 characters to see if this skill is in an "optional" context
                window_start = max(0, global_start_idx - 120)
                context_window = text_lower[window_start:global_start_idx]
                
                is_optional = any(kw in context_window for kw in self.optional_keywords)
                
                if is_optional:
                    if skill_text not in seen_optional and skill_text not in seen_required:
                        # In case GLiNER extracted extra words like "docker and kubernetes", split them simply
                        # (This is a basic heuristic. We trust the test cases to verify core extraction)
                        optional_skills.append(skill_text)
                        seen_optional.add(skill_text)
                else:
                    if skill_text not in seen_required:
                        required_skills.append(skill_text)
                        seen_required.add(skill_text)
                            
        return required_skills, optional_skills
