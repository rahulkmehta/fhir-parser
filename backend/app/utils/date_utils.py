from datetime import datetime, date
from typing import Optional


def parse_fhir_date(date_str: Optional[str]) -> Optional[date]:
    """Parse a FHIR date string (YYYY-MM-DD) into a Python date."""
    if not date_str:
        return None
    try:
        return datetime.fromisoformat(date_str[:10]).date()
    except (ValueError, TypeError):
        return None


def parse_fhir_datetime(dt_str: Optional[str]) -> Optional[datetime]:
    """Parse a FHIR datetime string (ISO 8601 with timezone) into a Python datetime."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError):
        return None


def compute_age(birth_date_str: Optional[str], as_of: Optional[date] = None) -> Optional[int]:
    """Compute age in years from a FHIR birth date string."""
    birth = parse_fhir_date(birth_date_str)
    if not birth:
        return None
    ref = as_of or date.today()
    age = ref.year - birth.year
    if (ref.month, ref.day) < (birth.month, birth.day):
        age -= 1
    return age
