from typing import Optional
from transformers import pipeline
from aiEnrich3.domain.entities import ModalityType

class ModalityExtractor:
    def __init__(self, classifier=None):
        if classifier is None:
            # Load the zero-shot classification pipeline specifically for mDeBERTa
            self.classifier = pipeline(
                "zero-shot-classification",
                model="MoritzLaurer/mDeBERTa-v3-base-mnli-xnli")
        else:
            self.classifier = classifier
        # Using simplified singular words helps the zero-shot model generalize across languages perfectly
        self.candidate_labels = ["remote", "hybrid", "on-site", "not specified"]

    def extract(self, text: str) -> Optional[ModalityType]:
        if not text:
            return None
        # We don't need multi_label because a job is usually strictly one of these.
        # Ensure truncation is handled by the tokenizer if text exceeds model max length.
        result = self.classifier(text, candidate_labels=self.candidate_labels, truncation=True)
        
        # result contains 'labels' and 'scores' sorted by probability
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        # Only assign if the AI is fairly confident.
        if top_score > 0.40 and top_label != "not specified":
            if top_label == "remote":
                return ModalityType.REMOTE
            elif top_label == "hybrid":
                return ModalityType.HYBRID
            elif top_label == "on-site":
                return ModalityType.ON_SITE
        return None
