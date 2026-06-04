from pydantic import BaseModel
from typing import Optional


class AnswerRequest(BaseModel):
    question: str
    provider: str = "auto"


class FollowUpRequest(BaseModel):
    original_question: str
    clarification_answer: str
    context_key: str | None = None


class AnswerResponse(BaseModel):
    type: str  # "answer" or "clarification"
    text: str
    provider: str
    confidence: str = "medium"


class HealthResponse(BaseModel):
    status: str
    provider: str
    cv_loaded: bool
    looking_for_loaded: bool


class BatchAnswerRequest(BaseModel):
    questions: list[str]
    provider: str = "auto"


class BatchAnswerItem(BaseModel):
    index: int
    type: str
    text: str
    provider: str
    confidence: str = "medium"


class BatchAnswerResponse(BaseModel):
    answers: list[BatchAnswerItem]
