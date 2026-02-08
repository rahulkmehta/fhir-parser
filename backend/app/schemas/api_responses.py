from pydantic import BaseModel
from typing import Optional, List


class PatientSummary(BaseModel):
    id: str
    full_name: str
    gender: Optional[str]
    birth_date: Optional[str]
    age: Optional[int]
    city: Optional[str]
    state: Optional[str]
    is_deceased: bool


class PatientListResponse(BaseModel):
    patients: List[PatientSummary]
    total: int
    page: int
    page_size: int


class ConditionSummary(BaseModel):
    id: str
    code: Optional[str]
    display: Optional[str]
    clinical_status: Optional[str]
    onset_date: Optional[str]


class ObservationSummary(BaseModel):
    id: str
    code: Optional[str]
    display: Optional[str]
    value: Optional[str]  # formatted: "29.98 kg/m2" or "Positive"
    value_numeric: Optional[float]
    date: Optional[str]
    category: Optional[str]


class ProcedureSummary(BaseModel):
    id: str
    code: Optional[str]
    display: Optional[str]
    status: Optional[str]
    performed_date: Optional[str]


class ClinicalSnapshot(BaseModel):
    patient: PatientSummary
    active_conditions: List[ConditionSummary]
    recent_procedures: List[ProcedureSummary]
    key_observations: dict  # {"bmi": ObservationSummary|None, "systolic_bp": ..., etc.}
    missing_data: List[str]


class TimelineEntry(BaseModel):
    resource_type: str  # "Observation" or "Procedure"
    resource_id: str
    display_name: str
    date: Optional[str]
    detail: Optional[str]  # value for observations, status for procedures


class TimelineResponse(BaseModel):
    entries: List[TimelineEntry]
    total: int
