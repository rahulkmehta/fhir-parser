from sqlalchemy import Column, String, Float, Text, ForeignKey, Index
from sqlalchemy.orm import relationship

from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(String, primary_key=True)
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    prefix = Column(String, nullable=True)
    gender = Column(String, nullable=True)
    birth_date = Column(String, nullable=True)
    deceased_date_time = Column(String, nullable=True)
    race = Column(String, nullable=True)
    ethnicity = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    marital_status = Column(String, nullable=True)
    raw_json = Column(Text, nullable=True)

    conditions = relationship("Condition", back_populates="patient", lazy="selectin")
    observations = relationship("Observation", back_populates="patient", lazy="selectin")
    procedures = relationship("Procedure", back_populates="patient", lazy="selectin")
    encounters = relationship("Encounter", back_populates="patient", lazy="selectin")
    medication_requests = relationship("MedicationRequest", back_populates="patient", lazy="selectin")
    document_references = relationship("DocumentReference", back_populates="patient", lazy="selectin")
    allergy_intolerances = relationship("AllergyIntolerance", back_populates="patient", lazy="selectin")
    devices = relationship("Device", back_populates="patient", lazy="selectin")
    immunizations = relationship("Immunization", back_populates="patient", lazy="selectin")



class Condition(Base):
    __tablename__ = "conditions"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    clinical_status = Column(String, nullable=True)
    verification_status = Column(String, nullable=True)
    code_system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display = Column(String, nullable=True)
    onset_date_time = Column(String, nullable=True)
    abatement_date_time = Column(String, nullable=True)
    recorded_date = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="conditions")

    __table_args__ = (
        Index("ix_conditions_patient_code", "patient_id", "code"),
        Index("ix_conditions_patient_status", "patient_id", "clinical_status"),
    )


class Observation(Base):
    __tablename__ = "observations"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    status = Column(String, nullable=True)
    category = Column(String, nullable=True)
    code_system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display = Column(String, nullable=True)
    effective_date_time = Column(String, nullable=True, index=True)
    value_quantity = Column(Float, nullable=True)
    value_unit = Column(String, nullable=True)
    value_code = Column(String, nullable=True)
    value_display = Column(String, nullable=True)
    component_json = Column(Text, nullable=True)

    patient = relationship("Patient", back_populates="observations")

    __table_args__ = (
        Index("ix_observations_patient_code", "patient_id", "code"),
        Index("ix_observations_patient_date", "patient_id", "effective_date_time"),
        Index("ix_observations_patient_code_date", "patient_id", "code", "effective_date_time"),
    )


class Procedure(Base):
    __tablename__ = "procedures"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    status = Column(String, nullable=True)
    code_system = Column(String, nullable=True)
    code = Column(String, nullable=True, index=True)
    display = Column(String, nullable=True)
    performed_start = Column(String, nullable=True)
    performed_end = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    reason_display = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="procedures")

    __table_args__ = (
        Index("ix_procedures_patient_code", "patient_id", "code"),
        Index("ix_procedures_patient_date", "patient_id", "performed_start"),
    )


class Encounter(Base):
    __tablename__ = "encounters"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    status = Column(String, nullable=True)
    encounter_class = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    period_start = Column(String, nullable=True)
    period_end = Column(String, nullable=True)
    practitioner_display = Column(String, nullable=True)
    location_display = Column(String, nullable=True)
    organization_display = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="encounters")


class MedicationRequest(Base):
    __tablename__ = "medication_requests"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    status = Column(String, nullable=True)
    intent = Column(String, nullable=True)
    medication_code = Column(String, nullable=True)
    medication_display = Column(String, nullable=True)
    authored_on = Column(String, nullable=True)
    reason_code = Column(String, nullable=True)
    reason_display = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="medication_requests")


class DocumentReference(Base):
    __tablename__ = "document_references"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    status = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    date = Column(String, nullable=True)
    content_text = Column(Text, nullable=True)
    author_display = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="document_references")


class AllergyIntolerance(Base):
    __tablename__ = "allergy_intolerances"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    clinical_status = Column(String, nullable=True)
    verification_status = Column(String, nullable=True)
    allergy_type = Column(String, nullable=True)
    category = Column(String, nullable=True)
    criticality = Column(String, nullable=True)
    code = Column(String, nullable=True)
    display = Column(String, nullable=True)
    recorded_date = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="allergy_intolerances")


class Device(Base):
    __tablename__ = "devices"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    status = Column(String, nullable=True)
    device_name = Column(String, nullable=True)
    type_code = Column(String, nullable=True)
    type_display = Column(String, nullable=True)
    manufacture_date = Column(String, nullable=True)
    expiration_date = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="devices")


class Immunization(Base):
    __tablename__ = "immunizations"

    id = Column(String, primary_key=True)
    patient_id = Column(String, ForeignKey("patients.id"), nullable=False, index=True)
    encounter_id = Column(String, nullable=True)
    status = Column(String, nullable=True)
    vaccine_code = Column(String, nullable=True)
    vaccine_display = Column(String, nullable=True)
    occurrence_date_time = Column(String, nullable=True)
    location_display = Column(String, nullable=True)

    patient = relationship("Patient", back_populates="immunizations")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True)
    identifier_value = Column(String, nullable=True, index=True)
    status = Column(String, nullable=True)
    name = Column(String, nullable=True)
    address_city = Column(String, nullable=True)
    address_state = Column(String, nullable=True)
    phone = Column(String, nullable=True)
    managing_org_display = Column(String, nullable=True)


class Practitioner(Base):
    __tablename__ = "practitioners"

    id = Column(String, primary_key=True)
    npi = Column(String, nullable=True, index=True, unique=True)
    family_name = Column(String, nullable=True)
    given_name = Column(String, nullable=True)
    prefix = Column(String, nullable=True)


class Organization(Base):
    __tablename__ = "organizations"

    id = Column(String, primary_key=True)
    identifier_value = Column(String, nullable=True, index=True)
    name = Column(String, nullable=True)


