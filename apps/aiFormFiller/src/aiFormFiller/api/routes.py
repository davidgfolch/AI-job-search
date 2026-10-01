from fastapi import APIRouter, HTTPException
from commonlib.observability import get_logger
from .schemas import AnswerRequest, FollowUpRequest, AnswerResponse, HealthResponse, BatchAnswerRequest, BatchAnswerItem, BatchAnswerResponse
from ..services.question_answering_service import QuestionAnsweringService
from ..context_loader import ContextLoader
from .. import config as cfg

router = APIRouter()
_service: QuestionAnsweringService | None = None

logger = get_logger("aiFormFiller.routes")


def init_routes(context_loader: ContextLoader):
    global _service
    _service = QuestionAnsweringService(context_loader)


@router.post("/api/answer", response_model=AnswerResponse)
async def answer(req: AnswerRequest):
    if not _service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        result = _service.answer(req.question, req.provider)
        logger.debug("form.answered", endpoint="answer", provider=result.provider, is_clarification=result.is_clarification, question_length=len(req.question), answer_length=len(result.text))
        return AnswerResponse(
            type="clarification" if result.is_clarification else "answer",
            text=result.text,
            provider=result.provider,
            confidence="high" if not result.is_clarification else "low",
        )
    except ValueError as e:
        logger.warning("provider.rejected", endpoint="answer", provider=req.provider, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("provider.failed", endpoint="answer", provider=req.provider)
        raise HTTPException(status_code=500, detail=f"AI provider error: {str(e)}")


@router.post("/api/answer/follow-up", response_model=AnswerResponse)
async def follow_up(req: FollowUpRequest):
    if not _service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        result = _service.follow_up(req.original_question, req.clarification_answer)
        logger.debug("form.answered", endpoint="follow_up", provider=result.provider, is_clarification=result.is_clarification, question_length=len(req.original_question), answer_length=len(result.text))
        return AnswerResponse(
            type="answer",
            text=result.text,
            provider=result.provider,
            confidence="high",
        )
    except Exception as e:
        logger.exception("provider.failed", endpoint="follow_up", provider="auto")
        raise HTTPException(status_code=500, detail=f"Follow-up error: {str(e)}")


@router.post("/api/answer/batch", response_model=BatchAnswerResponse)
async def answer_batch(req: BatchAnswerRequest):
    if not _service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    try:
        results = _service.answer_batch(req.questions, req.provider)
        items = [
            BatchAnswerItem(
                index=i,
                type="clarification" if r.is_clarification else "answer",
                text=r.text,
                provider=r.provider,
                confidence="high" if not r.is_clarification else "low",
            )
            for i, r in enumerate(results)
        ]
        clarifications = sum(1 for r in results if r.is_clarification)
        question_length = sum(len(q) for q in req.questions)
        logger.debug("form.answered", endpoint="answer_batch", count=len(items), clarifications=clarifications, question_length=question_length)
        return BatchAnswerResponse(answers=items)
    except ValueError as e:
        logger.warning("provider.rejected", endpoint="answer_batch", provider=req.provider, error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.exception("provider.failed", endpoint="answer_batch", provider=req.provider)
        raise HTTPException(status_code=500, detail=f"AI provider error: {str(e)}")


@router.get("/api/health", response_model=HealthResponse)
async def health():
    if not _service:
        raise HTTPException(status_code=503, detail="Service not initialized")
    context_loader = _service.context_loader
    return HealthResponse(
        status="ok",
        provider=cfg.get_provider(),
        cv_loaded=context_loader.cv_content is not None,
        looking_for_loaded=context_loader.looking_for_content is not None,
    )
