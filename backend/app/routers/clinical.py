from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas.api_responses import ClinicalSnapshot, TimelineResponse
from app.services.clinical_service import get_snapshot, get_timeline

router = APIRouter()


@router.get("/patients/{patient_id}/snapshot", response_model=ClinicalSnapshot)
def get_patient_snapshot(patient_id: str, db: Session = Depends(get_db)):
    snapshot = get_snapshot(db, patient_id)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Patient not found")
    return snapshot


@router.get("/patients/{patient_id}/timeline", response_model=TimelineResponse)
def get_patient_timeline(
    patient_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    return get_timeline(db, patient_id, page=page, page_size=page_size)
