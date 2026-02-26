from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field
import uuid


class PlanningStage(str, Enum):
    DEFINE_OUTCOME = "define_outcome"
    STRATEGIC_CONSTRAINTS = "strategic_constraints"
    PHASES_AND_MILESTONES = "phases_and_milestones"
    TASKS_AND_SUBTASKS = "tasks_and_subtasks"
    RISK_AND_GOVERNANCE = "risk_and_governance"
    COMPLETE = "complete"


STAGE_ORDER = [
    PlanningStage.DEFINE_OUTCOME,
    PlanningStage.STRATEGIC_CONSTRAINTS,
    PlanningStage.PHASES_AND_MILESTONES,
    PlanningStage.TASKS_AND_SUBTASKS,
    PlanningStage.RISK_AND_GOVERNANCE,
    PlanningStage.COMPLETE,
]


class ProjectType(str, Enum):
    GENERAL = "general"
    PROGRAM = "program"


class ConversationMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class Session(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    project_type: Optional[ProjectType] = None
    current_stage: PlanningStage = PlanningStage.DEFINE_OUTCOME
    messages: List[ConversationMessage] = Field(default_factory=list)
    stage_data: dict = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    is_complete: bool = False

    def get_claude_messages(self) -> List[dict]:
        return [{"role": m.role, "content": m.content} for m in self.messages]

    def advance_stage(self) -> None:
        idx = STAGE_ORDER.index(self.current_stage)
        if idx < len(STAGE_ORDER) - 1:
            self.current_stage = STAGE_ORDER[idx + 1]
        self.updated_at = datetime.utcnow()
