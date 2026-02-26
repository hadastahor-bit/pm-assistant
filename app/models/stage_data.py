from typing import Optional, List
from pydantic import BaseModel


class OutcomeData(BaseModel):
    project_name: str
    project_type: str  # "general" or "program"
    success_definition: str
    measurable_result: str
    key_stakeholders: List[str] = []


class ConstraintsData(BaseModel):
    deadline: Optional[str] = None
    budget: Optional[str] = None
    team_size: Optional[int] = None
    methodology: Optional[str] = None
    key_constraints: List[str] = []
    assumptions: List[str] = []


class MilestoneDefinition(BaseModel):
    name: str
    deliverable: str
    timeline: Optional[str] = None
    owner: Optional[str] = None


class PhasesData(BaseModel):
    phases: List[str]
    milestones: List[MilestoneDefinition]


class SubTaskDefinition(BaseModel):
    name: str
    owner: Optional[str] = None
    duration_days: Optional[int] = None
    dependencies: List[str] = []
    deliverable: Optional[str] = None


class TaskDefinition(BaseModel):
    name: str
    phase: str
    owner: Optional[str] = None
    duration_days: Optional[int] = None
    dependencies: List[str] = []
    subtasks: List[SubTaskDefinition] = []


class TasksData(BaseModel):
    tasks: List[TaskDefinition]


class RiskDefinition(BaseModel):
    description: str
    severity: str  # "high", "medium", "low"
    mitigation: Optional[str] = None


class KPIDefinition(BaseModel):
    metric: str
    target: Optional[str] = None


class RiskGovernanceData(BaseModel):
    risks: List[RiskDefinition]
    stakeholders: List[str]
    kpis: List[KPIDefinition]
    external_vendors: List[str] = []
    review_cadence: Optional[str] = None
