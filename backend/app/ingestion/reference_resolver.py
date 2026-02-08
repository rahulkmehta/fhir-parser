from typing import Optional

from app.schemas.fhir_resources import FhirReference


def extract_patient_id(reference: Optional[FhirReference]) -> Optional[str]:
    """Extract patient UUID from 'Patient/UUID' reference string."""
    if not reference or not reference.reference:
        return None
    ref = reference.reference
    if ref.startswith("Patient/"):
        return ref[len("Patient/"):]
    return None


def extract_encounter_id(reference: Optional[FhirReference]) -> Optional[str]:
    """Extract encounter UUID from 'Encounter/UUID' reference string."""
    if not reference or not reference.reference:
        return None
    ref = reference.reference
    if ref.startswith("Encounter/"):
        return ref[len("Encounter/"):]
    return None


def extract_npi_from_reference(ref_string: str) -> Optional[str]:
    """Extract NPI from 'Practitioner?identifier=http://hl7.org/fhir/sid/us-npi|NPI' pattern."""
    if "us-npi|" in ref_string:
        return ref_string.split("us-npi|")[1]
    return None
