import pytest
from app.agent.plan_compiler import PlanCompiler
from app.models.session import Session, PlanningStage
from app.models.stage_data import (
    OutcomeData, ConstraintsData, PhasesData, MilestoneDefinition,
    TasksData, TaskDefinition, SubTaskDefinition,
    RiskGovernanceData, RiskDefinition, KPIDefinition,
)


def build_complete_session(project_type: str = "general") -> Session:
    session = Session()
    session.is_complete = True

    session.stage_data[PlanningStage.DEFINE_OUTCOME.value] = OutcomeData(
        project_name="Test Project",
        project_type=project_type,
        success_definition="Launch a working product",
        measurable_result="1000 users by Q4",
        key_stakeholders=["CEO", "CTO"],
    ).model_dump()

    session.stage_data[PlanningStage.STRATEGIC_CONSTRAINTS.value] = ConstraintsData(
        deadline="Q4 2026",
        budget="$500,000",
        team_size=5,
        methodology="Agile",
    ).model_dump()

    session.stage_data[PlanningStage.PHASES_AND_MILESTONES.value] = PhasesData(
        phases=["Discovery", "Development"],
        milestones=[
            MilestoneDefinition(
                name="Discovery",
                deliverable="Requirements doc",
                timeline="Month 1",
                owner="PM",
            ),
            MilestoneDefinition(
                name="Development",
                deliverable="Working MVP",
                timeline="Month 4",
                owner="Tech Lead",
            ),
        ],
    ).model_dump()

    session.stage_data[PlanningStage.TASKS_AND_SUBTASKS.value] = TasksData(
        tasks=[
            TaskDefinition(
                name="Stakeholder interviews",
                phase="Discovery",
                owner="PM",
                duration_days=5,
                subtasks=[
                    SubTaskDefinition(
                        name="Schedule interviews",
                        owner="PM",
                        duration_days=1,
                        deliverable="Calendar invites sent",
                    )
                ],
            ),
            TaskDefinition(
                name="Build API",
                phase="Development",
                owner="Backend Dev",
                duration_days=20,
            ),
        ]
    ).model_dump()

    session.stage_data[PlanningStage.RISK_AND_GOVERNANCE.value] = RiskGovernanceData(
        risks=[
            RiskDefinition(
                description="Key engineer leaves",
                severity="high",
                mitigation="Cross-train team members",
            )
        ],
        stakeholders=["CEO", "CTO", "PM"],
        kpis=[KPIDefinition(metric="User signups", target="1000")],
        external_vendors=["Stripe"],
        review_cadence="Weekly standup, bi-weekly steering",
    ).model_dump()

    return session


def test_compile_general_project():
    session = build_complete_session("general")
    plan = PlanCompiler().compile(session)

    assert plan.project_name == "Test Project"
    assert plan.project_type == "general"
    assert plan.deadline == "Q4 2026"
    assert plan.team_size == 5
    assert len(plan.milestones) == 2
    assert plan.milestones[0].name == "Discovery"
    assert len(plan.milestones[0].tasks) == 1
    assert plan.milestones[0].tasks[0].name == "Stakeholder interviews"
    assert len(plan.milestones[0].tasks[0].subtasks) == 1
    assert plan.governance is not None
    assert len(plan.governance.risks) == 1
    assert plan.governance.risks[0].severity == "high"


def test_compile_program_project():
    session = build_complete_session("program")

    # Override milestone names with pillar prefix pattern
    from app.models.stage_data import PhasesData, MilestoneDefinition
    session.stage_data[PlanningStage.PHASES_AND_MILESTONES.value] = PhasesData(
        phases=["Technology", "People"],
        milestones=[
            MilestoneDefinition(
                name="Technology - MVP",
                deliverable="Deployed product",
                timeline="Q3",
            ),
            MilestoneDefinition(
                name="People - Onboarding",
                deliverable="Team onboarded",
                timeline="Q2",
            ),
        ],
    ).model_dump()

    plan = PlanCompiler().compile(session)

    assert plan.project_type == "program"
    assert len(plan.pillars) == 2
    pillar_names = {p.name for p in plan.pillars}
    assert "Technology" in pillar_names
    assert "People" in pillar_names
