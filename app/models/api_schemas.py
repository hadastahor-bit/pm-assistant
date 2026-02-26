from typing import Optional
from pydantic import BaseModel
from .session import PlanningStage


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    current_stage: PlanningStage
    stage_label: str
    is_complete: bool
    progress_percent: int


class SessionSummary(BaseModel):
    session_id: str
    current_stage: PlanningStage
    is_complete: bool
    created_at: str
    updated_at: str


class PlanResponse(BaseModel):
    session_id: str
    plan_json: dict
    plan_markdown: str
