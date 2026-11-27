from openai import OpenAI

from commonlib.cloud_llm import get_base_url

from .base import AIProvider, AnswerResult


class CloudProvider(AIProvider):
    """OpenAI-compatible provider for Gemini, Groq, Cerebras and HuggingFace Inference."""

    def __init__(self, provider: str, api_key: str, model: str):
        self.provider = provider
        self.model = model
        self.client = OpenAI(base_url=get_base_url(provider), api_key=api_key)

    def generate(self, system_prompt: str, user_message: str, timeout: float, max_tokens: int, temperature: float) -> AnswerResult:
        options = {"extra_body": {"reasoning": {"enabled": False}}} if self.model.endswith(":free") else {}
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=timeout,
            **options,
        )
        message = response.choices[0].message
        text = (message.content or getattr(message, "reasoning", None) or "").strip()
        is_clarification = text.upper().startswith("CLARIFICACIÓN:") or text.upper().startswith("CLARIFICATION:")
        return AnswerResult(text=text, is_clarification=is_clarification, provider=self.provider)
