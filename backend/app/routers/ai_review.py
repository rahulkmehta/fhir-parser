from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.schemas.api_responses import AIReviewResponse
from app.services.ai_review_service import generate_ai_review

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/patients/{patient_id}/ai-review", response_model=AIReviewResponse)
def ai_review(patient_id: str, db: Session = Depends(get_db)):
    result = generate_ai_review(db, patient_id)
    if result.error and result.error == "Patient not found.":
        raise HTTPException(status_code=404, detail="Patient not found")
    return result
