import json
import logging
from typing import Optional, TypeVar, Type
from pydantic import BaseModel, ValidationError
from anthropic import AsyncAnthropic

from ..models.session import Session, PlanningStage
from ..models.stage_data import (
    OutcomeData, ConstraintsData, PhasesData, TasksData, RiskGovernanceData,
)
from .prompts import STAGE_SYSTEM_PROMPTS, STAGE_EXTRACTION_PROMPTS

logger = logging.getLogger(__name__)
T = TypeVar("T", bound=BaseModel)


class BaseStageHandler:
    stage: PlanningStage
    extraction_model: Type[T]

    def __init__(self, claude_client: AsyncAnthropic, model: str, max_tokens: int):
        self.claude = claude_client
        self.model = model
        self.max_tokens = max_tokens

    async def generate_reply(self, session: Session) -> str:
        """
        Call 1: Natural conversational reply.
        Uses the full message history and the stage-specific system prompt.
        """
        response = await self.claude.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=STAGE_SYSTEM_PROMPTS[self.stage],
            messages=session.get_claude_messages(),
        )
        return response.content[0].text

    async def attempt_extraction(self, session: Session) -> Optional[T]:
        """
        Call 2: Structured JSON extraction via tool use.
        Separate call so it doesn't interfere with the conversational reply.
        Returns None if required fields are missing (stage not yet complete).
        """
        schema = self.extraction_model.model_json_schema()

        extraction_messages = session.get_claude_messages() + [
            {
                "role": "user",
                "content": STAGE_EXTRACTION_PROMPTS[self.stage],
            }
        ]

        try:
            response = await self.claude.messages.create(
                model=self.model,
                max_tokens=2048,
                system=(
                    "You are a data extraction assistant. Extract structured data from "
                    "the conversation and return ONLY a valid JSON object matching the "
                    "provided schema. Do not include any explanation or markdown fencing. "
                    "If a required string field has no value in the conversation, use "
                    "the string 'MISSING'. For optional fields, use null."
                ),
                messages=extraction_messages,
                tools=[
                    {
                        "name": "extract_stage_data",
                        "description": "Extract structured planning data from the conversation",
                        "input_schema": schema,
                    }
                ],
                tool_choice={"type": "auto"},
            )

            # Find the tool use block
            tool_use_block = next(
                (b for b in response.content if b.type == "tool_use"), None
            )
            if tool_use_block is None:
                logger.debug("No tool use block returned during extraction")
                return None

            data = self.extraction_model.model_validate(tool_use_block.input)
            if self._has_required_fields(data):
                return data
            return None

        except (ValidationError, Exception) as exc:
            logger.warning(f"Extraction failed for stage {self.stage}: {exc}")
            return None

    def _has_required_fields(self, data: T) -> bool:
        raise NotImplementedError


# ─────────────────────────────────────────────────────────────────
# STAGE 1
# ─────────────────────────────────────────────────────────────────
class DefineOutcomeHandler(BaseStageHandler):
    stage = PlanningStage.DEFINE_OUTCOME
    extraction_model = OutcomeData

    def _has_required_fields(self, data: OutcomeData) -> bool:
        return (
            bool(data.project_name) and data.project_name != "MISSING"
            and bool(data.success_definition) and data.success_definition != "MISSING"
            and bool(data.measurable_result) and data.measurable_result != "MISSING"
            and data.project_type in ("general", "program")
        )


# ─────────────────────────────────────────────────────────────────
# STAGE 2
# ─────────────────────────────────────────────────────────────────
class StrategicConstraintsHandler(BaseStageHandler):
    stage = PlanningStage.STRATEGIC_CONSTRAINTS
    extraction_model = ConstraintsData

    def _has_required_fields(self, data: ConstraintsData) -> bool:
        return bool(data.deadline) or len(data.key_constraints) > 0


# ─────────────────────────────────────────────────────────────────
# STAGE 3
# ─────────────────────────────────────────────────────────────────
class PhasesAndMilestonesHandler(BaseStageHandler):
    stage = PlanningStage.PHASES_AND_MILESTONES
    extraction_model = PhasesData

    def _has_required_fields(self, data: PhasesData) -> bool:
        return len(data.phases) >= 2 and len(data.milestones) >= 1


# ─────────────────────────────────────────────────────────────────
# STAGE 4
# ─────────────────────────────────────────────────────────────────
class TasksAndSubtasksHandler(BaseStageHandler):
    stage = PlanningStage.TASKS_AND_SUBTASKS
    extraction_model = TasksData

    def _has_required_fields(self, data: TasksData) -> bool:
        return len(data.tasks) >= 1 and any(t.owner for t in data.tasks)


# ─────────────────────────────────────────────────────────────────
# STAGE 5
# ─────────────────────────────────────────────────────────────────
class RiskAndGovernanceHandler(BaseStageHandler):
    stage = PlanningStage.RISK_AND_GOVERNANCE
    extraction_model = RiskGovernanceData

    def _has_required_fields(self, data: RiskGovernanceData) -> bool:
        return len(data.risks) >= 1 and len(data.stakeholders) >= 1


# ─────────────────────────────────────────────────────────────────
# DISPATCH MAP
# ─────────────────────────────────────────────────────────────────
STAGE_HANDLER_CLASSES = {
    PlanningStage.DEFINE_OUTCOME: DefineOutcomeHandler,
    PlanningStage.STRATEGIC_CONSTRAINTS: StrategicConstraintsHandler,
    PlanningStage.PHASES_AND_MILESTONES: PhasesAndMilestonesHandler,
    PlanningStage.TASKS_AND_SUBTASKS: TasksAndSubtasksHandler,
    PlanningStage.RISK_AND_GOVERNANCE: RiskAndGovernanceHandler,
}
