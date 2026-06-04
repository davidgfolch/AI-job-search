import pytest
from ...api.schemas import (
    AnswerRequest, FollowUpRequest, AnswerResponse, HealthResponse,
    BatchAnswerRequest, BatchAnswerItem, BatchAnswerResponse,
)


@pytest.mark.parametrize("cls, kwargs, attr, expected", [
    (AnswerRequest, {"question": "Q?"}, "question", "Q?"),
    (AnswerRequest, {"question": "Q?"}, "provider", "auto"),
    (AnswerRequest, {"question": "Q?", "provider": "openai"}, "provider", "openai"),
    (FollowUpRequest, {"original_question": "Q?", "clarification_answer": "Sí"}, "original_question", "Q?"),
    (FollowUpRequest, {"original_question": "Q?", "clarification_answer": "Sí"}, "context_key", None),
    (BatchAnswerRequest, {"questions": ["Q1?", "Q2?"]}, "provider", "auto"),
])
def test_request_defaults(cls, kwargs, attr, expected):
    req = cls(**kwargs)
    assert getattr(req, attr) == expected


@pytest.mark.parametrize("cls, kwargs, attr, expected", [
    (AnswerResponse, {"type": "answer", "text": "5 años", "provider": "local"}, "confidence", "medium"),
    (BatchAnswerItem, {"index": 0, "type": "answer", "text": "5 años", "provider": "local"}, "confidence", "medium"),
])
def test_response_defaults(cls, kwargs, attr, expected):
    resp = cls(**kwargs)
    assert getattr(resp, attr) == expected


def test_health_response():
    resp = HealthResponse(status="ok", provider="local", cv_loaded=True, looking_for_loaded=False)
    assert resp.status == "ok"
    assert resp.cv_loaded is True
    assert resp.looking_for_loaded is False


def test_batch_answer_response():
    item = BatchAnswerItem(index=0, type="answer", text="5 años", provider="local")
    resp = BatchAnswerResponse(answers=[item])
    assert len(resp.answers) == 1
