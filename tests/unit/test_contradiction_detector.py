import pytest
from app.agent.contradiction_detector import ContradictionDetector
from app.models.session import PlanningStage
from app.models.stage_data import (
    ConstraintsData, TasksData, TaskDefinition
)


def make_tasks_data(owners: list, durations: list = None) -> TasksData:
    if durations is None:
        durations = [None] * len(owners)
    tasks = [
        TaskDefinition(name=f"Task {i}", phase="Phase 1", owner=o, duration_days=d)
        for i, (o, d) in enumerate(zip(owners, durations))
    ]
    return TasksData(tasks=tasks)


def make_stage_data(team_size: int = None, deadline: str = None) -> dict:
    constraints = ConstraintsData(team_size=team_size, deadline=deadline)
    return {
        PlanningStage.STRATEGIC_CONSTRAINTS.value: constraints.model_dump()
    }


def test_no_contradiction_when_owners_within_team_size():
    detector = ContradictionDetector()
    tasks = make_tasks_data(["Alice", "Bob"])
    existing = make_stage_data(team_size=3)
    result = detector.check(PlanningStage.TASKS_AND_SUBTASKS, tasks, existing)
    assert result is None


def test_contradiction_when_owners_exceed_team_size():
    detector = ContradictionDetector()
    tasks = make_tasks_data(["Alice", "Bob", "Carol", "Dave"])
    existing = make_stage_data(team_size=2)
    result = detector.check(PlanningStage.TASKS_AND_SUBTASKS, tasks, existing)
    assert result is not None
    assert "4" in result.description or "2" in result.description


def test_no_contradiction_when_no_team_size_set():
    detector = ContradictionDetector()
    tasks = make_tasks_data(["Alice", "Bob", "Carol", "Dave", "Eve"])
    existing = make_stage_data(team_size=None)
    result = detector.check(PlanningStage.TASKS_AND_SUBTASKS, tasks, existing)
    assert result is None


def test_contradiction_when_total_duration_very_high():
    detector = ContradictionDetector()
    # 401 days total sequential — triggers the heuristic
    tasks = make_tasks_data(
        owners=["Alice"] * 5,
        durations=[81, 80, 80, 80, 80],
    )
    existing = make_stage_data(deadline="Q2 2025")
    result = detector.check(PlanningStage.TASKS_AND_SUBTASKS, tasks, existing)
    assert result is not None
    assert "401" in result.description


def test_no_contradiction_for_other_stages():
    detector = ContradictionDetector()
    # Contradiction check is only implemented for TASKS_AND_SUBTASKS
    from app.models.stage_data import OutcomeData
    outcome = OutcomeData(
        project_name="X", project_type="general",
        success_definition="Y", measurable_result="Z"
    )
    result = detector.check(PlanningStage.DEFINE_OUTCOME, outcome, {})
    assert result is None


def test_tbd_owners_are_excluded_from_count():
    detector = ContradictionDetector()
    tasks = make_tasks_data(["Alice", "TBD", "unassigned", "Bob"])
    existing = make_stage_data(team_size=2)
    # Only Alice and Bob count — should NOT trigger (2 == 2)
    result = detector.check(PlanningStage.TASKS_AND_SUBTASKS, tasks, existing)
    assert result is None
