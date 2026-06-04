from ..models.base import AIProvider, AnswerResult
from ..models.local_hf import LocalHFProvider
from ..models.openai_provider import OpenAIProvider
from ..models.openrouter import OpenRouterProvider
from ..context_loader import ContextLoader
from .. import config as cfg

SYSTEM_PROMPT_TEMPLATE = """Eres un asistente honesto que responde preguntas de formularios de trabajo.

Contexto del candidato:
{context}

Reglas:
1. Responde siempre en PRIMERA PERSONA. Directamente, sin explicar que inferiste la información.
2. Puedes INFERIR años de experiencia desde la sección "Professional experience" del CV: si una tecnología aparece mencionada en un rango de fechas (ej. "2021-2023 Apiumhub: Java11"), calcula los años desde la primera aparición hasta la fecha actual. Si el CV menciona una versión específica (ej. "Java 17" en 2023), puedes asumir experiencia con versiones anteriores compatibles (Java 11+) desde esa misma fecha. Aplica el mismo criterio para Spring Boot y otras tecnologías con versiones.
3. Responde en el MISMO IDIOMA de la pregunta.
4. Si UNA TECNOLOGÍA NO APARECE EN ABSOLUTO en el CV, responde comenzando con: CLARIFICACIÓN: [explica qué falta y pregunta por ello].
5. Sé conciso. Responde directamente sin justificarte ni añadir contexto no solicitado.
6. Usa las preferencias de LOOKING_FOR para preguntas de salario, rol, disponibilidad, etc."""


class QuestionAnsweringService:
    def __init__(self, context_loader: ContextLoader):
        self.context_loader = context_loader
        self._providers: dict[str, AIProvider] = {}

    def _get_provider(self, provider_name: str) -> AIProvider:
        if provider_name == "auto":
            provider_name = cfg.get_provider()
        if provider_name not in self._providers:
            self._providers[provider_name] = self._create_provider(provider_name)
        return self._providers[provider_name]

    def _create_provider(self, provider_name: str) -> AIProvider:
        if provider_name == "local":
            return LocalHFProvider(cfg.get_hf_model())
        elif provider_name == "openai":
            key = cfg.get_openai_api_key()
            if not key:
                raise ValueError("OPENAI_API_KEY not configured")
            return OpenAIProvider(key, cfg.get_openai_model())
        elif provider_name == "openrouter":
            key = cfg.get_openrouter_api_key()
            if not key:
                raise ValueError("OPENROUTER_API_KEY not configured")
            return OpenRouterProvider(key, cfg.get_openrouter_model())
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

    def answer(self, question: str, provider_name: str = "auto") -> AnswerResult:
        self.context_loader.reload_if_changed()
        context = self.context_loader.get_context_text()
        return self._answer_single(question, context, provider_name)

    def answer_batch(self, questions: list[str], provider_name: str = "auto") -> list[AnswerResult]:
        self.context_loader.reload_if_changed()
        context = self.context_loader.get_context_text()
        return [self._answer_single(q, context, provider_name) for q in questions]

    def _answer_single(self, question: str, context: str, provider_name: str) -> AnswerResult:
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        provider = self._get_provider(provider_name)
        return provider.generate(
            system_prompt=system_prompt,
            user_message=question,
            timeout=cfg.get_timeout(),
            max_tokens=cfg.get_max_tokens(),
            temperature=cfg.get_temperature(),
        )

    def follow_up(self, original_question: str, clarification_answer: str) -> AnswerResult:
        self.context_loader.reload_if_changed()
        context = self.context_loader.get_context_text()
        system_prompt = SYSTEM_PROMPT_TEMPLATE.format(context=context)
        provider = self._get_provider("auto")
        user_message = f"""Pregunta original: {original_question}

Información adicional proporcionada por el candidato: {clarification_answer}

Ahora responde la pregunta original usando esta información adicional."""
        return provider.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            timeout=cfg.get_timeout(),
            max_tokens=cfg.get_max_tokens(),
            temperature=cfg.get_temperature(),
        )
