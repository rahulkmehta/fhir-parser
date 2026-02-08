from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.db_models import Patient
from app.schemas.api_responses import EligibilityResult, CohortReport
from app.services.eligibility_engine import determine_eligibility, generate_cohort_report

router = APIRouter()


@router.get("/patients/{patient_id}/eligibility", response_model=EligibilityResult)
def get_patient_eligibility(patient_id: str, db: Session = Depends(get_db)):
    patient = db.query(Patient).get(patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return determine_eligibility(db, patient_id)


@router.get("/cohort", response_model=CohortReport)
def get_cohort_report(db: Session = Depends(get_db)):
    return generate_cohort_report(db)
