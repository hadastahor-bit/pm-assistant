from datetime import datetime, timezone

from ..models.plan import (
    ProjectPlan, Milestone, Task, SubTask, Pillar,
    GovernanceInfo, Risk, KPI,
)
from ..models.session import Session, PlanningStage
from ..models.stage_data import (
    OutcomeData, ConstraintsData, PhasesData, TasksData, RiskGovernanceData,
)


class PlanCompiler:
    """
    Assembles a typed ProjectPlan from all five committed stage_data entries.
    Only call this when session.is_complete is True.
    """

    def compile(self, session: Session) -> ProjectPlan:
        sd = session.stage_data

        outcome = OutcomeData(**sd[PlanningStage.DEFINE_OUTCOME.value])
        constraints = ConstraintsData(**sd[PlanningStage.STRATEGIC_CONSTRAINTS.value])
        phases_data = PhasesData(**sd[PlanningStage.PHASES_AND_MILESTONES.value])
        tasks_data = TasksData(**sd[PlanningStage.TASKS_AND_SUBTASKS.value])
        risk_data = RiskGovernanceData(**sd[PlanningStage.RISK_AND_GOVERNANCE.value])

        plan = ProjectPlan(
            project_name=outcome.project_name,
            project_type=outcome.project_type,
            success_definition=outcome.success_definition,
            deadline=constraints.deadline,
            budget=constraints.budget,
            team_size=constraints.team_size,
            methodology=constraints.methodology,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

        # Group tasks by phase name for lookup
        tasks_by_phase: dict[str, list] = {}
        for task_def in tasks_data.tasks:
            tasks_by_phase.setdefault(task_def.phase, []).append(task_def)

        if outcome.project_type == "program":
            self._build_program_structure(plan, phases_data, tasks_by_phase)
        else:
            self._build_general_structure(plan, phases_data, tasks_by_phase)

        plan.governance = GovernanceInfo(
            stakeholders=risk_data.stakeholders,
            kpis=[
                KPI(metric=k.metric, target=k.target)
                for k in risk_data.kpis
            ],
            risks=[
                Risk(
                    description=r.description,
                    severity=r.severity,
                    mitigation=r.mitigation,
                )
                for r in risk_data.risks
            ],
            external_vendors=risk_data.external_vendors,
            review_cadence=risk_data.review_cadence,
        )

        return plan

    def _build_general_structure(self, plan, phases_data, tasks_by_phase) -> None:
        """General project: Milestone → Task → SubTask"""
        for ms_def in phases_data.milestones:
            milestone = Milestone(
                name=ms_def.name,
                deliverable=ms_def.deliverable,
                timeline=ms_def.timeline,
                owner=ms_def.owner,
                tasks=self._build_tasks(tasks_by_phase.get(ms_def.name, [])),
            )
            plan.milestones.append(milestone)

    def _build_program_structure(self, plan, phases_data, tasks_by_phase) -> None:
        """Program: Pillar → Milestone → Task → SubTask.
        Pillar name is inferred from the first token before ' - ' in milestone names,
        or milestones are grouped under phases if pillar prefixes are absent.
        """
        pillars: dict[str, Pillar] = {}

        for ms_def in phases_data.milestones:
            # Attempt to split "Pillar Name - Milestone Name"
            if " - " in ms_def.name:
                pillar_name, milestone_label = ms_def.name.split(" - ", 1)
            else:
                # Fall back: use the phase as the pillar name
                pillar_name = phases_data.phases[0] if phases_data.phases else "Program"
                milestone_label = ms_def.name

            milestone = Milestone(
                name=milestone_label,
                deliverable=ms_def.deliverable,
                timeline=ms_def.timeline,
                owner=ms_def.owner,
                tasks=self._build_tasks(tasks_by_phase.get(ms_def.name, [])),
            )

            if pillar_name not in pillars:
                pillars[pillar_name] = Pillar(name=pillar_name)
            pillars[pillar_name].milestones.append(milestone)

        plan.pillars = list(pillars.values())

    def _build_tasks(self, task_defs: list) -> list[Task]:
        return [
            Task(
                name=t.name,
                owner=t.owner,
                duration_days=t.duration_days,
                dependencies=t.dependencies,
                subtasks=[
                    SubTask(
                        name=st.name,
                        owner=st.owner,
                        deliverable=st.deliverable,
                        timeline=f"{st.duration_days}d" if st.duration_days else None,
                        dependencies=st.dependencies,
                    )
                    for st in t.subtasks
                ],
            )
            for t in task_defs
        ]
