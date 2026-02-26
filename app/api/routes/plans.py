from fastapi import APIRouter, Depends, HTTPException

from ...models.api_schemas import PlanResponse
from ...agent.plan_compiler import PlanCompiler
from ...utils.markdown_renderer import MarkdownRenderer
from ...storage.base import SessionStore
from ...dependencies import get_session_store

router = APIRouter()


@router.get("/session/{session_id}/plan", response_model=PlanResponse)
async def get_plan(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = await store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    if not session.is_complete:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Plan not yet complete. Currently at stage: "
                f"{session.current_stage.value}. "
                "Continue the conversation to finish all 5 stages."
            ),
        )

    compiler = PlanCompiler()
    plan = compiler.compile(session)

    renderer = MarkdownRenderer()
    markdown = renderer.render(plan)

    return PlanResponse(
        session_id=session_id,
        plan_json=plan.model_dump(),
        plan_markdown=markdown,
    )
