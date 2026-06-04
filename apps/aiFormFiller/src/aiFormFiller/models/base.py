from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class AnswerResult:
    text: str
    is_clarification: bool = False
    provider: str = "unknown"


class AIProvider(ABC):
    @abstractmethod
    def generate(self, system_prompt: str, user_message: str, timeout: float, max_tokens: int, temperature: float) -> AnswerResult:
        ...
