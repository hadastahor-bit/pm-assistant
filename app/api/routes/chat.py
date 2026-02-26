import logging

from fastapi import APIRouter, Depends, HTTPException
from anthropic import APIStatusError, APIConnectionError

from ...models.api_schemas import ChatRequest, ChatResponse

logger = logging.getLogger(__name__)
from ...models.session import Session, STAGE_ORDER
from ...agent.state_machine import PlanningStateMachine
from ...storage.base import SessionStore
from ...dependencies import get_claude_client, get_session_store
from ...config import get_settings

router = APIRouter()

STAGE_LABELS = {
    "define_outcome": "Stage 1: Define Outcome",
    "strategic_constraints": "Stage 2: Strategic Constraints",
    "phases_and_milestones": "Stage 3: Phases & Milestones",
    "tasks_and_subtasks": "Stage 4: Tasks & Subtasks",
    "risk_and_governance": "Stage 5: Risk & Governance",
    "complete": "Complete",
}


def _progress(stage_value: str) -> int:
    stages = [s.value for s in STAGE_ORDER]
    try:
        idx = stages.index(stage_value)
    except ValueError:
        idx = len(stages) - 1
    return int((idx / (len(stages) - 1)) * 100)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    store: SessionStore = Depends(get_session_store),
    claude=Depends(get_claude_client),
):
    settings = get_settings()

    if request.session_id:
        session = await store.get(request.session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
    else:
        session = Session()
        await store.save(session)

    state_machine = PlanningStateMachine(
        claude_client=claude,
        model=settings.claude_model,
        max_tokens=settings.claude_max_tokens,
    )
    try:
        reply, updated_session = await state_machine.process_message(
            session=session,
            user_message=request.message,
        )
    except APIStatusError as exc:
        logger.error(f"Anthropic API error: {exc.status_code} {exc.message}")
        if exc.status_code == 400 and "credit" in str(exc.message).lower():
            raise HTTPException(
                status_code=503,
                detail=(
                    "The AI service is unavailable: insufficient API credits. "
                    "Please add credits at console.anthropic.com."
                ),
            )
        raise HTTPException(status_code=502, detail=f"AI service error: {exc.message}")
    except APIConnectionError as exc:
        logger.error(f"Anthropic connection error: {exc}")
        raise HTTPException(status_code=503, detail="Could not reach the AI service. Please retry.")

    await store.save(updated_session)

    return ChatResponse(
        session_id=updated_session.session_id,
        reply=reply,
        current_stage=updated_session.current_stage,
        stage_label=STAGE_LABELS.get(updated_session.current_stage.value, ""),
        is_complete=updated_session.is_complete,
        progress_percent=_progress(updated_session.current_stage.value),
    )
