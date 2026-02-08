from pydantic import BaseModel, Field
from typing import Optional, List, Any


class FhirCoding(BaseModel):
    system: Optional[str] = None
    code: Optional[str] = None
    display: Optional[str] = None


class FhirCodeableConcept(BaseModel):
    coding: List[FhirCoding] = []
    text: Optional[str] = None


class FhirReference(BaseModel):
    reference: Optional[str] = None
    display: Optional[str] = None


class FhirPeriod(BaseModel):
    start: Optional[str] = None
    end: Optional[str] = None


class FhirQuantity(BaseModel):
    value: Optional[float] = None
    unit: Optional[str] = None
    system: Optional[str] = None
    code: Optional[str] = None


class FhirHumanName(BaseModel):
    use: Optional[str] = None
    family: Optional[str] = None
    given: List[str] = []
    prefix: List[str] = []


class FhirAddress(BaseModel):
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class FhirAttachment(BaseModel):
    contentType: Optional[str] = None
    data: Optional[str] = None


class FhirContent(BaseModel):
    attachment: Optional[FhirAttachment] = None


class FhirExtension(BaseModel):
    url: Optional[str] = None
    valueString: Optional[str] = None
    valueCode: Optional[str] = None
    valueDecimal: Optional[float] = None
    valueCoding: Optional[FhirCoding] = None
    extension: List["FhirExtension"] = []


class FhirIdentifier(BaseModel):
    system: Optional[str] = None
    value: Optional[str] = None


class FhirComponent(BaseModel):
    code: Optional[FhirCodeableConcept] = None
    valueQuantity: Optional[FhirQuantity] = None


# ---- Top-level resource models ----


class FhirPatient(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    name: List[FhirHumanName] = []
    gender: Optional[str] = None
    birthDate: Optional[str] = None
    deceasedDateTime: Optional[str] = None
    address: List[FhirAddress] = []
    maritalStatus: Optional[FhirCodeableConcept] = None
    extension: List[FhirExtension] = []
    identifier: List[FhirIdentifier] = []


class FhirCondition(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    clinicalStatus: Optional[FhirCodeableConcept] = None
    verificationStatus: Optional[FhirCodeableConcept] = None
    category: List[FhirCodeableConcept] = []
    code: Optional[FhirCodeableConcept] = None
    subject: Optional[FhirReference] = None
    encounter: Optional[FhirReference] = None
    onsetDateTime: Optional[str] = None
    abatementDateTime: Optional[str] = None
    recordedDate: Optional[str] = None


class FhirObservation(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    category: List[FhirCodeableConcept] = []
    code: Optional[FhirCodeableConcept] = None
    subject: Optional[FhirReference] = None
    encounter: Optional[FhirReference] = None
    effectiveDateTime: Optional[str] = None
    issued: Optional[str] = None
    valueQuantity: Optional[FhirQuantity] = None
    valueCodeableConcept: Optional[FhirCodeableConcept] = None
    component: List[FhirComponent] = []


class FhirProcedure(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    code: Optional[FhirCodeableConcept] = None
    subject: Optional[FhirReference] = None
    encounter: Optional[FhirReference] = None
    performedPeriod: Optional[FhirPeriod] = None
    performedDateTime: Optional[str] = None
    reasonCode: List[FhirCodeableConcept] = []
    reasonReference: List[FhirReference] = []


class FhirEncounter(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    resourceType: str
    id: str
    status: Optional[str] = None
    class_field: Optional[FhirCoding] = Field(None, alias="class")
    type: List[FhirCodeableConcept] = []
    subject: Optional[FhirReference] = None
    period: Optional[FhirPeriod] = None
    participant: List[Any] = []
    location: List[Any] = []
    serviceProvider: Optional[FhirReference] = None


class FhirMedicationRequest(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    intent: Optional[str] = None
    medicationCodeableConcept: Optional[FhirCodeableConcept] = None
    subject: Optional[FhirReference] = None
    encounter: Optional[FhirReference] = None
    authoredOn: Optional[str] = None
    requester: Optional[FhirReference] = None
    reasonCode: List[FhirCodeableConcept] = []


class FhirDocumentReference(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    type: Optional[FhirCodeableConcept] = None
    category: List[FhirCodeableConcept] = []
    subject: Optional[FhirReference] = None
    date: Optional[str] = None
    author: List[FhirReference] = []
    content: List[FhirContent] = []


class FhirAllergyIntolerance(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    clinicalStatus: Optional[FhirCodeableConcept] = None
    verificationStatus: Optional[FhirCodeableConcept] = None
    type: Optional[str] = None
    category: List[str] = []
    criticality: Optional[str] = None
    code: Optional[FhirCodeableConcept] = None
    patient: Optional[FhirReference] = None  # Note: uses 'patient' not 'subject'
    recordedDate: Optional[str] = None


class FhirDeviceName(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None


class FhirDevice(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    deviceName: List[FhirDeviceName] = []
    type: Optional[FhirCodeableConcept] = None
    patient: Optional[FhirReference] = None
    manufactureDate: Optional[str] = None
    expirationDate: Optional[str] = None


class FhirImmunization(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    status: Optional[str] = None
    vaccineCode: Optional[FhirCodeableConcept] = None
    patient: Optional[FhirReference] = None
    encounter: Optional[FhirReference] = None
    occurrenceDateTime: Optional[str] = None
    location: Optional[FhirReference] = None


class FhirLocation(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    identifier: List[FhirIdentifier] = []
    status: Optional[str] = None
    name: Optional[str] = None
    address: Optional[FhirAddress] = None
    telecom: List[Any] = []
    managingOrganization: Optional[FhirReference] = None


class FhirPractitioner(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    identifier: List[FhirIdentifier] = []
    name: List[FhirHumanName] = []
    active: Optional[bool] = None


class FhirOrganization(BaseModel):
    model_config = {"extra": "allow"}

    resourceType: str
    id: str
    identifier: List[FhirIdentifier] = []
    name: Optional[str] = None


RESOURCE_MODEL_MAP = {
    "Patient": FhirPatient,
    "Condition": FhirCondition,
    "Observation": FhirObservation,
    "Procedure": FhirProcedure,
    "Encounter": FhirEncounter,
    "MedicationRequest": FhirMedicationRequest,
    "DocumentReference": FhirDocumentReference,
    "AllergyIntolerance": FhirAllergyIntolerance,
    "Device": FhirDevice,
    "Immunization": FhirImmunization,
    "Location": FhirLocation,
    "Practitioner": FhirPractitioner,
    "Organization": FhirOrganization,
}
