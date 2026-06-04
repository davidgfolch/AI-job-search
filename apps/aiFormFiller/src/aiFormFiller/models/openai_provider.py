from openai import OpenAI
from .base import AIProvider, AnswerResult


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str, model: str = "gpt-4o-mini"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def generate(self, system_prompt: str, user_message: str, timeout: float, max_tokens: int, temperature: float) -> AnswerResult:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
        )
        text = response.choices[0].message.content.strip()
        is_clarification = text.upper().startswith("CLARIFICACIÓN:") or text.upper().startswith("CLARIFICATION:")
        return AnswerResult(text=text, is_clarification=is_clarification, provider="openai")
