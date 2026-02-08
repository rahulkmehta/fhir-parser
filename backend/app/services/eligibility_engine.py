from collections import Counter

from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.models.db_models import Patient, Condition, Observation, Procedure
from app.schemas.api_responses import (
    EvidenceItem, EligibilityCriterion, EligibilityResult,
    CohortReport, CohortReportCategory, UnknownReason,
)
from app.utils.code_systems import (
    LOINC_BMI,
    SNOMED_ALL_COMORBIDITY_CODES,
    SNOMED_WEIGHT_LOSS_CODES, SNOMED_PSYCH_EVAL_CODES,
)


def _get_latest_bmi(db: Session, patient_id: str) -> Observation | None:
    return (
        db.query(Observation)
        .filter(Observation.patient_id == patient_id, Observation.code == LOINC_BMI)
        .order_by(desc(Observation.effective_date_time))
        .first()
    )


def _get_comorbidities(db: Session, patient_id: str) -> list[Condition]:
    return (
        db.query(Condition)
        .filter(
            Condition.patient_id == patient_id,
            Condition.clinical_status == "active",
            Condition.code.in_(SNOMED_ALL_COMORBIDITY_CODES),
        )
        .all()
    )


def _get_weight_loss_evidence(db: Session, patient_id: str) -> list[Procedure]:
    return (
        db.query(Procedure)
        .filter(
            Procedure.patient_id == patient_id,
            Procedure.code.in_(SNOMED_WEIGHT_LOSS_CODES),
        )
        .all()
    )


def _get_psych_eval_evidence(db: Session, patient_id: str) -> list[Procedure]:
    return (
        db.query(Procedure)
        .filter(
            Procedure.patient_id == patient_id,
            Procedure.code.in_(SNOMED_PSYCH_EVAL_CODES),
        )
        .all()
    )


def _to_evidence(resource_type: str, obj) -> EvidenceItem:
    date = None
    if resource_type == "Observation":
        date = obj.effective_date_time
    elif resource_type == "Condition":
        date = obj.onset_date_time
    elif resource_type == "Procedure":
        date = obj.performed_start

    return EvidenceItem(
        resource_type=resource_type,
        resource_id=obj.id,
        display=obj.display,
        code=obj.code,
        date=date,
    )


def determine_eligibility(db: Session, patient_id: str) -> EligibilityResult:
    criteria: list[EligibilityCriterion] = []
    reasons: list[str] = []

    bmi_obs = _get_latest_bmi(db, patient_id)
    bmi_value = bmi_obs.value_quantity if bmi_obs else None

    if bmi_obs is None or bmi_value is None:
        criteria.append(EligibilityCriterion(
            criterion="BMI observation recorded",
            met=False,
            evidence=[],
            reason="No BMI observation found in patient record",
        ))
        return EligibilityResult(
            patient_id=patient_id,
            status="unknown",
            reasons=["No BMI observation recorded"],
            criteria=criteria,
            bmi_value=None,
        )

    bmi_evidence = [_to_evidence("Observation", bmi_obs)]

    bmi_gte_40 = bmi_value >= 40
    bmi_gte_35 = bmi_value >= 35

    if not bmi_gte_35:
        criteria.append(EligibilityCriterion(
            criterion="BMI ≥ 35",
            met=False,
            evidence=bmi_evidence,
            reason=f"BMI is {bmi_value:.1f}, below threshold of 35",
        ))
        return EligibilityResult(
            patient_id=patient_id,
            status="not_eligible",
            reasons=[f"BMI {bmi_value:.1f} is below 35"],
            criteria=criteria,
            bmi_value=bmi_value,
        )

    if bmi_gte_40:
        criteria.append(EligibilityCriterion(
            criterion="BMI ≥ 40",
            met=True,
            evidence=bmi_evidence,
            reason=None,
        ))
    else:
        criteria.append(EligibilityCriterion(
            criterion="BMI ≥ 35",
            met=True,
            evidence=bmi_evidence,
            reason=None,
        ))

        comorbidities = _get_comorbidities(db, patient_id)
        if not comorbidities:
            criteria.append(EligibilityCriterion(
                criterion="Comorbidity present (e.g., hypertension, type 2 diabetes, sleep apnea, hyperlipidemia)",
                met=False,
                evidence=[],
                reason="No qualifying active comorbidity found",
            ))
            return EligibilityResult(
                patient_id=patient_id,
                status="not_eligible",
                reasons=[f"BMI {bmi_value:.1f} (35-39.9) with no qualifying comorbidity"],
                criteria=criteria,
                bmi_value=bmi_value,
            )

        criteria.append(EligibilityCriterion(
            criterion="Comorbidity present (e.g., hypertension, type 2 diabetes, sleep apnea, hyperlipidemia)",
            met=True,
            evidence=[_to_evidence("Condition", c) for c in comorbidities],
            reason=None,
        ))

    wl_evidence = _get_weight_loss_evidence(db, patient_id)
    if not wl_evidence:
        criteria.append(EligibilityCriterion(
            criterion="Evidence of prior weight-loss attempts",
            met=False,
            evidence=[],
            reason="No weight-loss attempt documentation found (e.g., CBT, counseling, exercise program)",
        ))
        return EligibilityResult(
            patient_id=patient_id,
            status="unknown",
            reasons=["No evidence of prior weight-loss attempts"],
            criteria=criteria,
            bmi_value=bmi_value,
        )

    criteria.append(EligibilityCriterion(
        criterion="Evidence of prior weight-loss attempts",
        met=True,
        evidence=[_to_evidence("Procedure", p) for p in wl_evidence],
        reason=None,
    ))

    psych_evidence = _get_psych_eval_evidence(db, patient_id)
    if not psych_evidence:
        criteria.append(EligibilityCriterion(
            criterion="Psychological evaluation",
            met=False,
            evidence=[],
            reason="No psychological evaluation found (e.g., mental health screening, psychosocial care)",
        ))
        return EligibilityResult(
            patient_id=patient_id,
            status="unknown",
            reasons=["No psychological evaluation found"],
            criteria=criteria,
            bmi_value=bmi_value,
        )

    criteria.append(EligibilityCriterion(
        criterion="Psychological evaluation",
        met=True,
        evidence=[_to_evidence("Procedure", p) for p in psych_evidence],
        reason=None,
    ))

    return EligibilityResult(
        patient_id=patient_id,
        status="eligible",
        reasons=["All eligibility criteria met"],
        criteria=criteria,
        bmi_value=bmi_value,
    )


def generate_cohort_report(db: Session) -> CohortReport:
    patient_ids = [pid for (pid,) in db.query(Patient.id).all()]
    total = len(patient_ids)

    buckets: dict[str, list[str]] = {"eligible": [], "not_eligible": [], "unknown": []}
    unknown_reasons: list[str] = []

    for pid in patient_ids:
        result = determine_eligibility(db, pid)
        buckets[result.status].append(pid)
        if result.status == "unknown":
            unknown_reasons.extend(result.reasons)

    def _make_category(ids: list[str]) -> CohortReportCategory:
        return CohortReportCategory(
            count=len(ids),
            percentage=round(len(ids) / total * 100, 1) if total else 0,
            patient_ids=ids,
        )

    reason_counts = Counter(unknown_reasons)
    unknown_total = len(buckets["unknown"])
    top_reasons = [
        UnknownReason(
            reason=reason,
            count=count,
            percentage=round(count / unknown_total * 100, 1) if unknown_total else 0,
        )
        for reason, count in reason_counts.most_common()
    ]

    return CohortReport(
        total_patients=total,
        eligible=_make_category(buckets["eligible"]),
        not_eligible=_make_category(buckets["not_eligible"]),
        unknown=_make_category(buckets["unknown"]),
        top_unknown_reasons=top_reasons,
    )
