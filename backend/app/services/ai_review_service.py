import json
import logging

from openai import OpenAI
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.models.db_models import Patient, Condition, Observation, Procedure, MedicationRequest
from app.services.eligibility_engine import determine_eligibility
from app.schemas.api_responses import (
    AIReviewResponse, AIChecklistItem, EvidenceItem,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """\
You are a clinical prior authorization reviewer for bariatric surgery eligibility.

You will receive structured patient data from a FHIR-based system including demographics, \
active conditions, recent observations, procedures, medications, and a deterministic \
eligibility assessment.

Your task is to produce a structured JSON review that helps a clinician understand the \
patient's bariatric surgery eligibility. You must follow these rules strictly:

HARD RULES:
1. GROUNDING: Every clinical claim you make MUST reference specific FHIR resource IDs from \
the provided data. If you cannot ground a claim in provided evidence, explicitly state \
"No supporting evidence in record" — never infer or assume.
2. DETERMINISM BOUNDARY: The "deterministic_status" field is computed by a rule-based engine \
and is FINAL. You must NOT override, contradict, or reinterpret this status. Your role is to \
EXPLAIN it, not change it.
3. NO SILENT INFERENCE: Do not use phrases like "likely", "probably", or "suggests" without \
citing a specific FHIR resource. If evidence is ambiguous or missing, say so explicitly.
4. FAILURE TRANSPARENCY: If you lack sufficient data to assess a criterion, mark it as \
"unknown" with a clear explanation of what's missing.

OUTPUT FORMAT (strict JSON):
{
  "clinical_summary": "2-4 sentence summary of the patient's clinical picture relevant to bariatric surgery, referencing FHIR resource IDs",
  "eligibility_assessment": "1-2 sentence explanation of WHY the deterministic status was reached, grounded in evidence",
  "checklist": [
    {
      "criterion": "Name of criterion (e.g., BMI ≥ 40)",
      "status": "met" | "not_met" | "unknown",
      "evidence": [
        {
          "resource_type": "Observation|Condition|Procedure",
          "resource_id": "the FHIR resource ID",
          "display": "human-readable description",
          "code": "SNOMED/LOINC code",
          "date": "ISO date or null"
        }
      ],
      "explanation": "Why this criterion is met/not_met/unknown, referencing resource IDs"
    }
  ],
  "recommended_next_steps": ["Actionable next step 1", "Actionable next step 2"]
}

Return ONLY valid JSON. No markdown fences, no commentary outside the JSON object.\
"""


def _build_patient_context(db: Session, patient_id: str) -> str | None:
    """Build a structured text block of patient data for the AI prompt."""
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return None

    lines = []

    # Demographics
    given = patient.given_name or ""
    family = patient.family_name or ""
    lines.append(f"PATIENT: {given} {family} (ID: {patient.id})")
    lines.append(f"Gender: {patient.gender or 'Unknown'}")
    lines.append(f"DOB: {patient.birth_date or 'Unknown'}")
    if patient.deceased_date_time:
        lines.append(f"Deceased: {patient.deceased_date_time}")
    lines.append("")

    # Active conditions
    conditions = (
        db.query(Condition)
        .filter(Condition.patient_id == patient_id, Condition.clinical_status == "active")
        .all()
    )
    lines.append(f"ACTIVE CONDITIONS ({len(conditions)}):")
    for c in conditions:
        lines.append(
            f"  - {c.display} | Code: {c.code} | Onset: {c.onset_date_time or 'Unknown'} | FHIR ID: {c.id}"
        )
    lines.append("")

    # Recent observations (last 30 by date)
    observations = (
        db.query(Observation)
        .filter(Observation.patient_id == patient_id)
        .order_by(desc(Observation.effective_date_time))
        .limit(30)
        .all()
    )
    lines.append(f"RECENT OBSERVATIONS ({len(observations)}):")
    for o in observations:
        value = ""
        if o.value_quantity is not None:
            value = f"{o.value_quantity} {o.value_unit or ''}".strip()
        elif o.value_display:
            value = o.value_display
        lines.append(
            f"  - {o.display} | Value: {value} | Code: {o.code} | "
            f"Date: {o.effective_date_time or 'Unknown'} | FHIR ID: {o.id}"
        )
    lines.append("")

    # Recent procedures (last 20 by date)
    procedures = (
        db.query(Procedure)
        .filter(Procedure.patient_id == patient_id)
        .order_by(desc(Procedure.performed_start))
        .limit(20)
        .all()
    )
    lines.append(f"RECENT PROCEDURES ({len(procedures)}):")
    for p in procedures:
        lines.append(
            f"  - {p.display} | Code: {p.code} | Status: {p.status} | "
            f"Date: {p.performed_start or 'Unknown'} | FHIR ID: {p.id}"
        )
    lines.append("")

    # Medications
    medications = (
        db.query(MedicationRequest)
        .filter(MedicationRequest.patient_id == patient_id)
        .order_by(desc(MedicationRequest.authored_on))
        .limit(15)
        .all()
    )
    if medications:
        lines.append(f"MEDICATIONS ({len(medications)}):")
        for m in medications:
            lines.append(
                f"  - {m.medication_display} | Status: {m.status} | "
                f"Date: {m.authored_on or 'Unknown'} | FHIR ID: {m.id}"
            )
        lines.append("")

    return "\n".join(lines)


def _parse_ai_response(raw: str, patient_id: str, deterministic_status: str) -> AIReviewResponse:
    """Parse the AI's JSON response into our schema. Raises on invalid structure."""
    data = json.loads(raw)

    checklist = []
    for item in data.get("checklist", []):
        evidence = []
        for e in item.get("evidence", []):
            evidence.append(EvidenceItem(
                resource_type=e.get("resource_type", "Unknown"),
                resource_id=e.get("resource_id", "unknown"),
                display=e.get("display"),
                code=e.get("code"),
                date=e.get("date"),
            ))
        checklist.append(AIChecklistItem(
            criterion=item.get("criterion", "Unknown criterion"),
            status=item.get("status", "unknown"),
            evidence=evidence,
            explanation=item.get("explanation", "No explanation provided"),
        ))

    return AIReviewResponse(
        patient_id=patient_id,
        deterministic_status=deterministic_status,
        clinical_summary=data.get("clinical_summary", "No clinical summary generated."),
        eligibility_assessment=data.get("eligibility_assessment", "No assessment generated."),
        checklist=checklist,
        recommended_next_steps=data.get("recommended_next_steps", []),
        error=None,
    )


def generate_ai_review(db: Session, patient_id: str) -> AIReviewResponse:
    """Generate an AI-assisted review for a patient's bariatric surgery eligibility."""

    # Step 1: Get deterministic eligibility (Part C) — this is the source of truth
    eligibility = determine_eligibility(db, patient_id)
    deterministic_status = eligibility.status

    # Step 2: Build patient context
    context = _build_patient_context(db, patient_id)
    if context is None:
        return AIReviewResponse(
            patient_id=patient_id,
            deterministic_status=deterministic_status,
            clinical_summary="",
            eligibility_assessment="",
            checklist=[],
            recommended_next_steps=[],
            error="Patient not found.",
        )

    # Step 3: Build the user message with deterministic status + patient data
    user_message = (
        f"DETERMINISTIC ELIGIBILITY STATUS: {deterministic_status}\n"
        f"DETERMINISTIC REASONS: {'; '.join(eligibility.reasons)}\n"
        f"BMI VALUE: {eligibility.bmi_value if eligibility.bmi_value is not None else 'Not recorded'}\n\n"
        f"{context}"
    )

    # Step 4: Call OpenAI
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message},
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=2000,
        )

        content = response.choices[0].message.content
        if not content or not content.strip():
            return AIReviewResponse(
                patient_id=patient_id,
                deterministic_status=deterministic_status,
                clinical_summary="",
                eligibility_assessment="",
                checklist=[],
                recommended_next_steps=[],
                error="AI model returned an empty response.",
            )

        return _parse_ai_response(content, patient_id, deterministic_status)

    except json.JSONDecodeError as e:
        logger.error(f"AI review JSON parse error for patient {patient_id}: {e}")
        return AIReviewResponse(
            patient_id=patient_id,
            deterministic_status=deterministic_status,
            clinical_summary="",
            eligibility_assessment="",
            checklist=[],
            recommended_next_steps=[],
            error=f"AI response was not valid JSON: {str(e)}",
        )
    except Exception as e:
        logger.error(f"AI review error for patient {patient_id}: {e}")
        return AIReviewResponse(
            patient_id=patient_id,
            deterministic_status=deterministic_status,
            clinical_summary="",
            eligibility_assessment="",
            checklist=[],
            recommended_next_steps=[],
            error=f"AI review failed: {str(e)}",
        )
