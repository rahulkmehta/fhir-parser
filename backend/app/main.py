from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import patients, clinical, eligibility, ai_review

app = FastAPI(title="FHIR Prior Auth Review Tool")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients.router, prefix="/api")
app.include_router(clinical.router, prefix="/api")
app.include_router(eligibility.router, prefix="/api")
app.include_router(ai_review.router, prefix="/api")
