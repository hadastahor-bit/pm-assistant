from ..models.plan import ProjectPlan, Milestone


class MarkdownRenderer:
    """
    Converts a ProjectPlan into human-readable Markdown.

    General project:
        ## Milestone Name
        _Deliverable: ..._
        - **Task** | Owner: X | Duration: Y days
          - Sub-task | Owner: Z | Timeline: W

    Program:
        ## Pillar: Pillar Name
        ### Milestone: Milestone Name
        - **Task** | Owner: X | Duration: Y days
          - Sub-task | Owner: Z | Timeline: W
    """

    def render(self, plan: ProjectPlan) -> str:
        lines = []

        lines.append(f"# {plan.project_name}")
        lines.append(f"**Type:** {plan.project_type.capitalize()}")
        lines.append(f"**Success Definition:** {plan.success_definition}")
        if plan.deadline:
            lines.append(f"**Deadline:** {plan.deadline}")
        if plan.budget:
            lines.append(f"**Budget:** {plan.budget}")
        if plan.team_size:
            lines.append(f"**Team Size:** {plan.team_size}")
        if plan.methodology:
            lines.append(f"**Methodology:** {plan.methodology}")
        lines.append("")
        lines.append("---")

        if plan.project_type == "program" and plan.pillars:
            lines.append("## Program Structure")
            for pillar in plan.pillars:
                lines.append(f"\n## Pillar: {pillar.name}")
                for milestone in pillar.milestones:
                    lines += self._render_milestone(milestone, level=3)
        else:
            lines.append("## Project Plan")
            for milestone in plan.milestones:
                lines += self._render_milestone(milestone, level=2)

        if plan.governance:
            gov = plan.governance
            lines.append("\n---")
            lines.append("## Governance & Risk")

            if gov.stakeholders:
                lines.append("\n### Stakeholders")
                for s in gov.stakeholders:
                    lines.append(f"- {s}")

            if gov.kpis:
                lines.append("\n### KPIs")
                for kpi in gov.kpis:
                    target_str = f" — Target: {kpi.target}" if kpi.target else ""
                    lines.append(f"- **{kpi.metric}**{target_str}")

            if gov.risks:
                lines.append("\n### Risks")
                for risk in gov.risks:
                    badge = f"[{risk.severity.upper()}]"
                    lines.append(f"- {badge} {risk.description}")
                    if risk.mitigation:
                        lines.append(f"  - _Mitigation: {risk.mitigation}_")

            if gov.external_vendors:
                lines.append("\n### External Vendors / Dependencies")
                for v in gov.external_vendors:
                    lines.append(f"- {v}")

            if gov.review_cadence:
                lines.append(f"\n### Review Cadence\n{gov.review_cadence}")

        return "\n".join(lines)

    def _render_milestone(self, milestone: Milestone, level: int) -> list:
        hashes = "#" * level
        lines = []
        lines.append(f"\n{hashes} {milestone.name}")
        if milestone.deliverable:
            lines.append(f"_Deliverable: {milestone.deliverable}_")
        if milestone.timeline:
            lines.append(f"_Timeline: {milestone.timeline}_")
        if milestone.owner:
            lines.append(f"_Owner: {milestone.owner}_")

        for task in milestone.tasks:
            parts = [f"**{task.name}**"]
            if task.owner:
                parts.append(f"Owner: {task.owner}")
            if task.duration_days:
                parts.append(f"Duration: {task.duration_days}d")
            lines.append("\n- " + " | ".join(parts))

            if task.dependencies:
                lines.append(f"  - _Dependencies: {', '.join(task.dependencies)}_")

            for st in task.subtasks:
                st_parts = [st.name]
                if st.owner:
                    st_parts.append(f"Owner: {st.owner}")
                if st.timeline:
                    st_parts.append(f"Timeline: {st.timeline}")
                lines.append("  - " + " | ".join(st_parts))
                if st.deliverable:
                    lines.append(f"    - _Deliverable: {st.deliverable}_")

        return lines
