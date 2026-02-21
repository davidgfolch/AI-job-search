from typing import Optional
from gliner import GLiNER

class SalaryExtractor:
    def __init__(self, model: Optional[GLiNER] = None):
        # Allow injecting a shared model instance to save memory
        if model is None:
            self.model = GLiNER.from_pretrained("urchade/gliner_multi-v2.1")
        else:
            self.model = model
        self.labels = ["salary", "remuneration", "pay"]

    def extract(self, text: str) -> Optional[str]:
        if not text:
            return None
            
        chunk_size = 1200
        overlap = 200
        all_entities = []
        
        for i in range(0, len(text), chunk_size - overlap):
            chunk = text[i:i + chunk_size]
            entities = self.model.predict_entities(chunk, self.labels, threshold=0.5)
            if entities:
                all_entities.extend(entities)
                
        if not all_entities:
            return None
            
        # Return the most confident or first salary entity found
        # (GLiNER usually returns them in sequence, we can pick the highest score)
        best_entity = max(all_entities, key=lambda e: e["score"])
        return best_entity["text"].strip()
