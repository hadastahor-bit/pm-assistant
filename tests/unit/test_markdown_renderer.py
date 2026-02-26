from app.utils.markdown_renderer import MarkdownRenderer
from app.models.plan import (
    ProjectPlan, Milestone, Task, SubTask, GovernanceInfo, Risk, KPI
)


def make_plan(project_type: str = "general") -> ProjectPlan:
    return ProjectPlan(
        project_name="Launch App",
        project_type=project_type,
        success_definition="1000 active users",
        deadline="Q4 2026",
        team_size=4,
        milestones=[
            Milestone(
                name="MVP",
                deliverable="Working app",
                timeline="Month 3",
                owner="Tech Lead",
                tasks=[
                    Task(
                        name="Build backend",
                        owner="Dev",
                        duration_days=20,
                        subtasks=[
                            SubTask(name="Design DB schema", owner="Dev", timeline="3d")
                        ],
                    )
                ],
            )
        ],
        governance=GovernanceInfo(
            stakeholders=["CEO"],
            kpis=[KPI(metric="DAU", target="1000")],
            risks=[Risk(description="Scope creep", severity="medium", mitigation="Strict backlog")],
        ),
    )


def test_renders_project_name():
    renderer = MarkdownRenderer()
    md = renderer.render(make_plan())
    assert "# Launch App" in md


def test_renders_milestone():
    renderer = MarkdownRenderer()
    md = renderer.render(make_plan())
    assert "## MVP" in md
    assert "_Deliverable: Working app_" in md


def test_renders_task():
    renderer = MarkdownRenderer()
    md = renderer.render(make_plan())
    assert "**Build backend**" in md
    assert "Owner: Dev" in md
    assert "Duration: 20d" in md


def test_renders_subtask():
    renderer = MarkdownRenderer()
    md = renderer.render(make_plan())
    assert "Design DB schema" in md
    assert "Timeline: 3d" in md


def test_renders_governance():
    renderer = MarkdownRenderer()
    md = renderer.render(make_plan())
    assert "## Governance & Risk" in md
    assert "CEO" in md
    assert "**DAU**" in md
    assert "[MEDIUM] Scope creep" in md
    assert "Strict backlog" in md
