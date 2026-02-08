# FHIR Prior Authorization Review Tool

Clinician-facing prior authorization review tool for bariatric surgery eligibility.

## Prerequisites

- Python 3.11+
- Node.js 18+
- FHIR bulk export data in NDJSON format

## Setup

### Backend

```bash
cd backend
pip install -r requirements.txt
```

Create a `.env` file in `backend/`:

```
OPENAI_API_KEY=sk-your-key-here
```

### Data Ingestion

Place FHIR NDJSON files in the data directory (defaults to `backend/raw_data/sample-bulk-fhir-datasets-1000-patients/`), then:

```bash
cd backend
python -m scripts.ingest
```

### Run

```bash
# Backend (http://localhost:8000)
cd backend
uvicorn app.main:app --reload

# Frontend (http://localhost:3000)
cd frontend
npm install
npm run dev
```
