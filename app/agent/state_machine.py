import logging
from typing import Tuple
from anthropic import AsyncAnthropic

from ..models.session import Session, PlanningStage, ConversationMessage, STAGE_ORDER
from .stage_handlers import STAGE_HANDLER_CLASSES
from .contradiction_detector import ContradictionDetector
from .prompts import get_stage_transition_message

logger = logging.getLogger(__name__)


class PlanningStateMachine:
    """
    Orchestrates the 5-stage planning conversation.

    Per-turn flow:
    1. Append user message to session history
    2. Select handler for current stage
    3. Claude call 1 → conversational reply
    4. Claude call 2 → structured extraction attempt
    5. If extraction passes: run contradiction check
       a. Contradiction found → inject clarification question, do NOT advance
       b. No contradiction → store stage data, advance stage
    6. Append assistant reply to session history
    7. Return (reply_text, updated_session)
    """

    def __init__(self, claude_client: AsyncAnthropic, model: str, max_tokens: int):
        self.claude = claude_client
        self.model = model
        self.max_tokens = max_tokens
        self.contradiction_detector = ContradictionDetector()

    async def process_message(
        self, session: Session, user_message: str
    ) -> Tuple[str, Session]:
        if session.current_stage == PlanningStage.COMPLETE:
            reply = (
                "Your project plan is already complete! "
                "Use `GET /api/v1/session/{session_id}/plan` to retrieve it."
            )
            session.messages.append(ConversationMessage(role="user", content=user_message))
            session.messages.append(ConversationMessage(role="assistant", content=reply))
            return reply, session

        # Step 1: Record user message
        session.messages.append(ConversationMessage(role="user", content=user_message))

        # Step 2: Get handler for current stage
        handler_class = STAGE_HANDLER_CLASSES[session.current_stage]
        handler = handler_class(self.claude, self.model, self.max_tokens)

        # Step 3: Generate conversational reply
        reply = await handler.generate_reply(session)

        # Step 4: Attempt structured extraction
        extraction_result = await handler.attempt_extraction(session)

        if extraction_result is not None:
            # Step 5a: Contradiction check
            contradiction = self.contradiction_detector.check(
                stage=session.current_stage,
                new_data=extraction_result,
                existing_stage_data=session.stage_data,
            )

            if contradiction:
                logger.info(
                    f"Contradiction detected at stage {session.current_stage}: "
                    f"{contradiction.description}"
                )
                reply = (
                    f"I noticed a potential conflict: {contradiction.description}\n\n"
                    f"{contradiction.clarification_question}"
                )
            else:
                # Step 5b: Commit data and advance stage
                session.stage_data[session.current_stage.value] = (
                    extraction_result.model_dump(mode="json")
                )
                session.advance_stage()

                if session.current_stage == PlanningStage.COMPLETE:
                    session.is_complete = True
                    transition = get_stage_transition_message(PlanningStage.COMPLETE)
                else:
                    transition = get_stage_transition_message(session.current_stage)

                reply = reply + "\n\n---\n" + transition

        # Step 6: Record assistant reply
        session.messages.append(ConversationMessage(role="assistant", content=reply))
        return reply, session
