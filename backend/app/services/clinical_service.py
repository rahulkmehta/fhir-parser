import json
import re
from sqlalchemy.orm import Session
from sqlalchemy import desc

_SNOMED_TAG_RE = re.compile(r"\s*\((disorder|procedure)\)\s*$")


def _clean_display(display: str | None) -> str:
    """Strip SNOMED semantic tags like (disorder) and (procedure) from display text."""
    if not display:
        return "Unknown"
    return _SNOMED_TAG_RE.sub("", display).strip() or display

from app.models.db_models import Condition, Observation, Procedure
from app.schemas.api_responses import (
    ClinicalSnapshot, ConditionSummary, ObservationSummary,
    ProcedureSummary, TimelineEntry, TimelineResponse,
)
from app.services.patient_service import get_patient
from app.utils.code_systems import (
    LOINC_BMI, LOINC_BP_PANEL, LOINC_BP_SYSTOLIC, LOINC_BP_DIASTOLIC,
    LOINC_BODY_WEIGHT, LOINC_BODY_HEIGHT,
)


def _format_obs_value(obs: Observation) -> str | None:
    if obs.value_quantity is not None:
        unit = obs.value_unit or ""
        return f"{obs.value_quantity} {unit}".strip()
    if obs.value_display:
        return obs.value_display
    return None


def _obs_to_summary(obs: Observation) -> ObservationSummary:
    return ObservationSummary(
        id=obs.id,
        code=obs.code,
        display=_clean_display(obs.display),
        value=_format_obs_value(obs),
        value_numeric=obs.value_quantity,
        date=obs.effective_date_time,
        category=obs.category,
    )


def _get_latest_obs(db: Session, patient_id: str, loinc_code: str) -> Observation | None:
    return (
        db.query(Observation)
        .filter(Observation.patient_id == patient_id, Observation.code == loinc_code)
        .order_by(desc(Observation.effective_date_time))
        .first()
    )


def _get_bp_components(obs: Observation) -> tuple[ObservationSummary | None, ObservationSummary | None]:
    """Extract systolic and diastolic from a BP panel's component_json."""
    if not obs or not obs.component_json:
        return None, None

    components = json.loads(obs.component_json)
    systolic = None
    diastolic = None

    for comp in components:
        code_info = comp.get("code", {})
        codings = code_info.get("coding", [])
        if not codings:
            continue
        comp_code = codings[0].get("code")
        vq = comp.get("valueQuantity", {})
        value = vq.get("value")
        unit = vq.get("unit", "")

        if comp_code == LOINC_BP_SYSTOLIC and value is not None:
            systolic = ObservationSummary(
                id=obs.id,
                code=LOINC_BP_SYSTOLIC,
                display="Systolic Blood Pressure",
                value=f"{value} {unit}".strip(),
                value_numeric=value,
                date=obs.effective_date_time,
                category=obs.category,
            )
        elif comp_code == LOINC_BP_DIASTOLIC and value is not None:
            diastolic = ObservationSummary(
                id=obs.id,
                code=LOINC_BP_DIASTOLIC,
                display="Diastolic Blood Pressure",
                value=f"{value} {unit}".strip(),
                value_numeric=value,
                date=obs.effective_date_time,
                category=obs.category,
            )

    return systolic, diastolic


def get_snapshot(db: Session, patient_id: str) -> ClinicalSnapshot | None:
    patient = get_patient(db, patient_id)
    if not patient:
        return None

    # Active conditions — exclude non-clinical SNOMED semantic tags
    _EXCLUDED_TAGS = ("(finding)", "(person)", "(situation)")
    active_conditions = [
        c
        for c in db.query(Condition)
        .filter(Condition.patient_id == patient_id, Condition.clinical_status == "active")
        .order_by(desc(Condition.onset_date_time))
        .all()
        if not (c.display and any(c.display.endswith(tag) for tag in _EXCLUDED_TAGS))
    ]

    # Recent procedures (last 10)
    recent_procedures = (
        db.query(Procedure)
        .filter(Procedure.patient_id == patient_id)
        .order_by(desc(Procedure.performed_start))
        .limit(10)
        .all()
    )

    # Key observations
    missing_data = []

    bmi_obs = _get_latest_obs(db, patient_id, LOINC_BMI)
    bmi = _obs_to_summary(bmi_obs) if bmi_obs else None
    if not bmi:
        missing_data.append("No BMI observation recorded")

    bp_obs = _get_latest_obs(db, patient_id, LOINC_BP_PANEL)
    systolic, diastolic = _get_bp_components(bp_obs)
    if not systolic:
        missing_data.append("No blood pressure data available")

    weight_obs = _get_latest_obs(db, patient_id, LOINC_BODY_WEIGHT)
    weight = _obs_to_summary(weight_obs) if weight_obs else None
    if not weight:
        missing_data.append("No body weight recorded")

    height_obs = _get_latest_obs(db, patient_id, LOINC_BODY_HEIGHT)
    height = _obs_to_summary(height_obs) if height_obs else None
    if not height:
        missing_data.append("No body height recorded")

    return ClinicalSnapshot(
        patient=patient,
        active_conditions=[
            ConditionSummary(
                id=c.id,
                code=c.code,
                display=_clean_display(c.display),
                clinical_status=c.clinical_status,
                onset_date=c.onset_date_time,
            )
            for c in active_conditions
        ],
        recent_procedures=[
            ProcedureSummary(
                id=p.id,
                code=p.code,
                display=_clean_display(p.display),
                status=p.status,
                performed_date=p.performed_start,
            )
            for p in recent_procedures
        ],
        key_observations={
            "bmi": bmi,
            "systolic_bp": systolic,
            "diastolic_bp": diastolic,
            "weight": weight,
            "height": height,
        },
        missing_data=missing_data,
    )


def get_timeline(
    db: Session, patient_id: str, page: int = 1, page_size: int = 50
) -> TimelineResponse:
    # Get observations
    obs_query = (
        db.query(Observation)
        .filter(Observation.patient_id == patient_id)
        .order_by(desc(Observation.effective_date_time))
    )
    obs_count = obs_query.count()

    # Get procedures
    proc_query = (
        db.query(Procedure)
        .filter(Procedure.patient_id == patient_id)
        .order_by(desc(Procedure.performed_start))
    )
    proc_count = proc_query.count()

    total = obs_count + proc_count

    # Merge and sort: fetch all, combine, sort, paginate in Python
    # For 1000 patients this is fine; for larger datasets we'd use UNION in SQL
    all_entries = []

    for obs in obs_query.all():
        all_entries.append(TimelineEntry(
            resource_type="Observation",
            resource_id=obs.id,
            display_name=_clean_display(obs.display),
            date=obs.effective_date_time,
            detail=_format_obs_value(obs),
        ))

    for proc in proc_query.all():
        all_entries.append(TimelineEntry(
            resource_type="Procedure",
            resource_id=proc.id,
            display_name=_clean_display(proc.display),
            date=proc.performed_start,
            detail=proc.status,
        ))

    # Sort by date descending (None dates go to end)
    all_entries.sort(key=lambda e: e.date or "", reverse=True)

    # Paginate
    start = (page - 1) * page_size
    end = start + page_size
    page_entries = all_entries[start:end]

    return TimelineResponse(entries=page_entries, total=total)
