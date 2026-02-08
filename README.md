# FHIR Prior Authorization Review Tool

A clinician-facing tool for reviewing bariatric surgery prior authorization eligibility. Parses FHIR bulk export data (NDJSON), runs deterministic eligibility logic against NIH/CMS bariatric surgery guidelines, and provides an optional AI-assisted review layer via OpenAI GPT-4o.

Built with FastAPI + SQLAlchemy/SQLite on the backend, Next.js + shadcn/ui + Tailwind on the frontend.

## Project Structure

```
backend/
  app/
    main.py                        FastAPI app, CORS, router mounting
    config.py                      Settings (DB path, data dir, OpenAI key)
    database.py                    SQLAlchemy engine + session
    models/db_models.py            ORM models (Patient, Condition, Observation, etc.)
    schemas/
      fhir_resources.py            Pydantic models for parsing FHIR NDJSON
      api_responses.py             Pydantic response models for all endpoints
    ingestion/
      pipeline.py                  Ingestion orchestrator — parses NDJSON into SQLite
      ndjson_reader.py             Streaming NDJSON parser with validation
      reference_resolver.py        Extracts patient/encounter IDs from FHIR references
    routers/
      patients.py                  GET /api/patients, /api/patients/{id}
      clinical.py                  GET /api/patients/{id}/snapshot, /timeline
      eligibility.py               GET /api/patients/{id}/eligibility, /api/cohort
      ai_review.py                 POST /api/patients/{id}/ai-review
    services/
      patient_service.py           Patient listing, search, summary
      clinical_service.py          Clinical snapshot + timeline construction
      eligibility_engine.py        Deterministic bariatric eligibility logic
      ai_review_service.py         OpenAI GPT integration for AI-assisted review
    utils/
      code_systems.py              SNOMED/LOINC code constants
      date_utils.py                ISO 8601 date helpers
  scripts/
    ingest.py                      CLI entry point for data ingestion

frontend/
  src/
    app/
      page.tsx                     Main layout — sidebar + detail + cohort view
      layout.tsx                   Root layout
    components/
      PatientSidebar.tsx           Searchable patient list with pagination
      PatientDetail.tsx            Patient header + segmented tab control
      ClinicalOverview.tsx         Key observations, active conditions, procedures
      TimelineView.tsx             Paginated chronological view of all FHIR events
      EligibilityView.tsx          Eligibility status, criteria checklist, AI review button
      CohortReport.tsx             Cohort-wide eligibility distribution
    lib/api.ts                     Typed fetch wrapper for all backend endpoints
    types/index.ts                 TypeScript interfaces matching API responses
```

## Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- FHIR bulk export data in NDJSON format (tested with Synthea 1000-patient dataset)

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in the `backend/` directory:

```
OPENAI_API_KEY=sk-your-key-here
```

The `DATABASE_URL` and `DATA_DIR` are configured in `config.py` with defaults. Override them in `.env` if your paths differ.

### Data Ingestion

Place your FHIR NDJSON files in the data directory (defaults to `backend/raw_data/sample-bulk-fhir-datasets-1000-patients/`), then run:

```bash
cd backend
python -m scripts.ingest
```

This drops and recreates all tables, then loads all resource types: Patient, Condition, Observation, Procedure, Encounter, MedicationRequest, DocumentReference, AllergyIntolerance, Device, Immunization, Practitioner, Organization, Location.

Observations use bulk inserts for performance (~5000 per batch). Synthea-specific name digits are stripped at ingestion time.

### Start the Backend

```bash
cd backend
uvicorn app.main:app --reload
```

Runs on `http://localhost:8000`.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Runs on `http://localhost:3000`.

## API Endpoints

| Method | Route | Description |
|--------|-------|-------------|
| GET | `/api/patients?q=&page=&page_size=` | List/search patients by name or ID |
| GET | `/api/patients/{id}` | Single patient summary |
| GET | `/api/patients/{id}/snapshot` | Clinical snapshot (demographics, conditions, observations, procedures) |
| GET | `/api/patients/{id}/timeline?page=&page_size=` | Chronological observations + procedures |
| GET | `/api/patients/{id}/eligibility` | Per-patient eligibility with evidence chain |
| GET | `/api/cohort` | Cohort-wide eligibility report |
| POST | `/api/patients/{id}/ai-review` | AI-assisted review (calls OpenAI) |

## Eligibility Logic

Deterministic bariatric surgery eligibility based on NIH/CMS guidelines:

1. **BMI check** — must have a recorded BMI observation (LOINC `39156-5`)
2. **BMI threshold** — BMI must be >= 35
3. **BMI >= 40** qualifies directly; **BMI 35-39.9** requires an active qualifying comorbidity (hypertension, type 2 diabetes, sleep apnea, hyperlipidemia, metabolic syndrome, osteoarthritis, GERD, NAFLD, etc.)
4. **Weight-loss documentation** — evidence of prior weight-loss attempts (counseling, CBT, exercise programs, dietary management, weight management referrals)
5. **Psychological evaluation** — mental health screening, psychiatric interview, depression/anxiety assessment

Each criterion is evaluated with specific SNOMED/LOINC codes. Every eligibility result includes the full evidence chain with FHIR resource IDs.

Possible statuses: `eligible`, `not_eligible`, `unknown` (missing data prevents classification).

## AI-Assisted Review

The AI review layer sits on top of the deterministic eligibility engine. It calls OpenAI GPT-4o with the patient's clinical data and the deterministic eligibility result, and returns structured JSON:

- **Clinical summary** — 2-4 sentence overview referencing FHIR resource IDs
- **Eligibility assessment** — explains the deterministic status (never overrides it)
- **Criteria checklist** — each criterion with status, evidence, and explanation
- **Recommended next steps** — actionable items for the clinician

Hard constraints enforced by the system prompt:
- Every claim must reference a FHIR resource ID or state "No supporting evidence in record"
- The deterministic status from the eligibility engine is final — the AI explains but cannot override
- No silent inference (no "likely" or "probably" without cited evidence)
- Graceful failure handling for API errors, empty responses, and invalid JSON

The frontend displays FHIR resource IDs as footnotes — superscript numbers in the text body with a sources list at the bottom.

## Design Decisions

- **Hybrid schema**: normalized patient-centric tables with denormalized `code` + `display` on each row to avoid joins on read-heavy paths
- **ISO 8601 strings for dates**: preserves timezone offsets that SQLite would otherwise strip
- **Condition filtering**: excludes SNOMED semantic tags `(finding)`, `(person)`, `(situation)` from the active conditions display, and strips `(disorder)` and `(procedure)` tags from all display text
- **Synthea normalization**: trailing digits stripped from name parts at ingestion, prefix (Mr./Mrs.) excluded from display
- **Observation bulk inserts**: bypasses ORM overhead for the highest-volume resource type
- **Footnoted FHIR references**: AI review modal replaces inline FHIR IDs with superscript numbers, collected in a sources section at the bottom
