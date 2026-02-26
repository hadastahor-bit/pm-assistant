import logging
from dataclasses import dataclass
from typing import Optional, Any

from ..models.session import PlanningStage
from ..models.stage_data import ConstraintsData, TasksData

logger = logging.getLogger(__name__)


@dataclass
class Contradiction:
    description: str
    clarification_question: str


class ContradictionDetector:
    """
    Checks for cross-stage inconsistencies after each successful extraction.
    Returns a Contradiction if a problem is found, otherwise None.
    Contradictions block stage advancement and surface a clarification to the user.
    """

    def check(
        self,
        stage: PlanningStage,
        new_data: Any,
        existing_stage_data: dict,
    ) -> Optional[Contradiction]:
        if stage == PlanningStage.TASKS_AND_SUBTASKS:
            return self._check_tasks_vs_constraints(new_data, existing_stage_data)
        return None

    def _check_tasks_vs_constraints(
        self,
        tasks_data: TasksData,
        existing_stage_data: dict,
    ) -> Optional[Contradiction]:
        """
        Rule 1: Unique task owner count must not exceed stated team size.
        Rule 2: Sequential task duration sum should not dramatically exceed the deadline.
        """
        raw = existing_stage_data.get(PlanningStage.STRATEGIC_CONSTRAINTS.value)
        if not raw:
            return None

        try:
            constraints = ConstraintsData(**raw)
        except Exception as exc:
            logger.warning(f"Could not parse constraints for contradiction check: {exc}")
            return None

        # Rule 1: Owner count vs team size
        if constraints.team_size is not None:
            skip_labels = {"tbd", "unassigned", "n/a", "various", ""}
            unique_owners = {
                t.owner.strip().lower()
                for t in tasks_data.tasks
                if t.owner and t.owner.strip().lower() not in skip_labels
            }
            if len(unique_owners) > constraints.team_size:
                names = ", ".join(sorted(unique_owners))
                return Contradiction(
                    description=(
                        f"You mentioned a team of {constraints.team_size} in Stage 2, "
                        f"but I'm now seeing {len(unique_owners)} distinct task owners: {names}."
                    ),
                    clarification_question=(
                        "Should I update the team size, or are some of these the same "
                        "person referenced by different names?"
                    ),
                )

        # Rule 2: Total sequential duration vs deadline (heuristic — flags > 400 days)
        total_days = sum(
            t.duration_days for t in tasks_data.tasks if t.duration_days is not None
        )
        if total_days > 400:
            deadline_str = f" against your deadline of '{constraints.deadline}'" if constraints.deadline else ""
            return Contradiction(
                description=(
                    f"The sum of all task durations is approximately {total_days} days{deadline_str}. "
                    "That seems longer than a typical project timeline."
                ),
                clarification_question=(
                    "Are these tasks meant to run in parallel, or should we revisit some "
                    "of the duration estimates?"
                ),
            )

        return None
