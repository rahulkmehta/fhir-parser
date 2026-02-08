# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A clinician-facing **prior authorization review tool** that ingests raw FHIR bulk data, presents a clear patient view, and uses AI-assisted reasoning to determine whether a procedure (bariatric surgery) meets coverage requirements.

## Problem Domain

**FHIR** (Fast Healthcare Interoperability Resources) is an HL7 standard for structured clinical data. Resources are composable units (Patient, Condition, Observation, Procedure) with standardized medical codes (ICD, CPT, LOINC, SNOMED), timestamps, and cross-references. The input data uses Bulk FHIR Export format: NDJSON files (one JSON object per line), split by resource type.

## Four-Part Architecture

### Part A: Data Ingestion (Backend)
- Parse and normalize FHIR NDJSON resources into internal models
- Resolve inter-resource references (e.g., `Condition.subject` → `Patient`)
- Group all resources by patient
- Handle missing/partial fields safely
- **Mandatory**: implement one measurable performance optimization with before/after benchmarks

### Part B: Frontend (React or Next.js)
- **Patient Selector**: search by name or ID, switching updates all views
- **Clinical Snapshot**: age, sex, active conditions, recent procedures, key observations (BMI, BP)
- **Timeline View**: chronological list of Observations and Procedures with display name, date, source FHIR resource ID
- UX: information hierarchy over visual polish; missing data must be explicit

### Part C: Eligibility Logic (Deterministic)
Per-patient bariatric surgery eligibility classification — exactly one of: `eligible`, `not eligible`, `unknown`.

**Criteria:**
- BMI >= 40, OR BMI >= 35 AND at least one comorbidity (hypertension, type 2 diabetes)
- Required documentation: prior weight-loss attempts, psychological evaluation
- `unknown` must explain why (missing BMI, missing comorbidity evidence, missing documentation)

**Cohort report:** total patients, count/percentage per category, top reasons for `unknown` status.

### Part D: AI-Assisted Review
- Structured JSON output grounded in FHIR resource IDs (clinicalSummary, eligibilityAssessment, checklist with evidence references, recommendedNextSteps)
- **Hard constraints**: every claim references FHIR resource IDs or is marked unknown; eligibility status comes from Part C (AI explains but doesn't override); must handle model failure, empty/partial responses, conflicting evidence; no silent inference ("likely"/"probably" without evidence is disallowed)

## Data

Sample dataset in `backend/raw_data/sample-bulk-fhir-datasets-1000-patients/` (~1.6GB, 1000 synthetic Synthea patients). Not checked into git. FHIR resource types: AllergyIntolerance, Condition, Device, DiagnosticReport, DocumentReference, Encounter, Immunization, Location, MedicationRequest, Observation, Organization, Patient, Practitioner, PractitionerRole, Procedure.

## Project Structure

- **`backend/`** — Python backend (data ingestion, eligibility logic, AI review)
  - `app/main.py` — Application entry point
  - `requirements.txt` — Python dependencies (conda environment)
  - `raw_data/` — FHIR NDJSON sample data (not in git)
- **`frontend/`** — React/Next.js frontend
