from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.api_responses import PatientListResponse, PatientSummary
from app.services.patient_service import list_patients, get_patient

router = APIRouter()


@router.get("/patients", response_model=PatientListResponse)
def get_patients(
    q: str = Query("", description="Search by name or ID"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    return list_patients(db, q=q, page=page, page_size=page_size)


@router.get("/patients/{patient_id}", response_model=PatientSummary)
def get_patient_by_id(patient_id: str, db: Session = Depends(get_db)):
    patient = get_patient(db, patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return patient
