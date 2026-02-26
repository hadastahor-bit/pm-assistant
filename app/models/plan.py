from typing import Optional, List
from pydantic import BaseModel


class SubTask(BaseModel):
    name: str
    owner: Optional[str] = None
    timeline: Optional[str] = None
    deliverable: Optional[str] = None
    dependencies: List[str] = []


class Task(BaseModel):
    name: str
    owner: Optional[str] = None
    timeline: Optional[str] = None
    duration_days: Optional[int] = None
    dependencies: List[str] = []
    subtasks: List[SubTask] = []


class Milestone(BaseModel):
    name: str
    deliverable: Optional[str] = None
    timeline: Optional[str] = None
    owner: Optional[str] = None
    tasks: List[Task] = []


class Pillar(BaseModel):
    name: str
    milestones: List[Milestone] = []


class Risk(BaseModel):
    description: str
    severity: str
    mitigation: Optional[str] = None


class KPI(BaseModel):
    metric: str
    target: Optional[str] = None
    measurement_method: Optional[str] = None


class GovernanceInfo(BaseModel):
    stakeholders: List[str] = []
    kpis: List[KPI] = []
    risks: List[Risk] = []
    external_vendors: List[str] = []
    review_cadence: Optional[str] = None


class ProjectPlan(BaseModel):
    project_name: str
    project_type: str
    success_definition: str
    deadline: Optional[str] = None
    budget: Optional[str] = None
    team_size: Optional[int] = None
    methodology: Optional[str] = None

    milestones: List[Milestone] = []
    pillars: List[Pillar] = []

    governance: Optional[GovernanceInfo] = None
    generated_at: Optional[str] = None
