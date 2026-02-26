from fastapi import APIRouter, Depends, HTTPException

from ...models.api_schemas import SessionSummary
from ...storage.base import SessionStore
from ...dependencies import get_session_store

router = APIRouter()


@router.get("/session/{session_id}", response_model=SessionSummary)
async def get_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = await store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return SessionSummary(
        session_id=session.session_id,
        current_stage=session.current_stage,
        is_complete=session.is_complete,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
    )


@router.delete("/session/{session_id}", status_code=204)
async def delete_session(
    session_id: str,
    store: SessionStore = Depends(get_session_store),
):
    session = await store.get(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    await store.delete(session_id)
