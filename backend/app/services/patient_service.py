from sqlalchemy.orm import Session
from sqlalchemy import func, or_

from app.models.db_models import Patient
from app.schemas.api_responses import PatientSummary, PatientListResponse
from app.utils.date_utils import compute_age


def _to_summary(p: Patient) -> PatientSummary:
    given = p.given_name or ""
    family = p.family_name or ""
    prefix = f"{p.prefix} " if p.prefix else ""
    full_name = f"{prefix}{given} {family}".strip() or "Unknown"

    return PatientSummary(
        id=p.id,
        full_name=full_name,
        gender=p.gender,
        birth_date=p.birth_date,
        age=compute_age(p.birth_date),
        city=p.address_city,
        state=p.address_state,
        is_deceased=p.deceased_date_time is not None,
    )


def list_patients(db: Session, q: str = "", page: int = 1, page_size: int = 20) -> PatientListResponse:
    query = db.query(Patient)

    if q:
        search = f"%{q}%"
        query = query.filter(
            or_(
                Patient.given_name.ilike(search),
                Patient.family_name.ilike(search),
                Patient.id.ilike(search),
            )
        )

    total = query.count()
    patients = (
        query
        .order_by(Patient.family_name, Patient.given_name)
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return PatientListResponse(
        patients=[_to_summary(p) for p in patients],
        total=total,
        page=page,
        page_size=page_size,
    )


def get_patient(db: Session, patient_id: str) -> PatientSummary | None:
    p = db.query(Patient).get(patient_id)
    if not p:
        return None
    return _to_summary(p)
