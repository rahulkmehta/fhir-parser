import base64
import glob
import json
import logging
import os
import re
import time
from collections import defaultdict

from sqlalchemy import create_engine, insert
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.ingestion.ndjson_reader import stream_ndjson
from app.ingestion.reference_resolver import extract_patient_id, extract_encounter_id
from app.models.db_models import (
    Patient, Condition, Observation, Procedure, Encounter,
    MedicationRequest, DocumentReference, AllergyIntolerance,
    Device, Immunization, Location, Practitioner, Organization,
)
from app.schemas.fhir_resources import (
    FhirPatient, FhirCondition, FhirObservation, FhirProcedure,
    FhirEncounter, FhirMedicationRequest, FhirDocumentReference,
    FhirAllergyIntolerance, FhirDevice, FhirImmunization,
    FhirLocation, FhirPractitioner, FhirOrganization,
)

logger = logging.getLogger(__name__)

BATCH_SIZE = 5000


def _strip_synthea_digits(name: str | None) -> str | None:
    """Strip trailing digits that Synthea appends to each part of synthetic names."""
    if not name:
        return name
    parts = [re.sub(r"\d+$", "", part).strip() for part in name.split()]
    return " ".join(p for p in parts if p) or name


def discover_ndjson_files(data_dir: str) -> dict[str, list[str]]:
    """Scan data directory and group NDJSON files by resource type."""
    files_by_type = defaultdict(list)
    for path in sorted(glob.glob(os.path.join(data_dir, "*.ndjson"))):
        fname = os.path.basename(path)
        if fname == "log.ndjson":
            continue
        resource_type = fname.split(".")[0]
        files_by_type[resource_type].append(path)
    return dict(files_by_type)


def _extract_extension_text(extensions, url_fragment: str) -> str | None:
    """Extract the text value from a FHIR extension matching the URL fragment."""
    for ext in extensions:
        if ext.url and url_fragment in ext.url:
            for sub in ext.extension:
                if sub.url == "text" and sub.valueString:
                    return sub.valueString
    return None


def _get_first_coding(codeable_concept):
    """Get the first coding (code, system, display) from a CodeableConcept."""
    if not codeable_concept or not codeable_concept.coding:
        return None, None, None
    c = codeable_concept.coding[0]
    return c.code, c.system, c.display


def _get_clinical_status(status_concept) -> str | None:
    if not status_concept or not status_concept.coding:
        return None
    return status_concept.coding[0].code


def _get_category(categories) -> str | None:
    if not categories:
        return None
    code, _, _ = _get_first_coding(categories[0])
    return code


def load_practitioners(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirPractitioner):
            npi = None
            for ident in parsed.identifier:
                if ident.system and "us-npi" in ident.system:
                    npi = ident.value
                    break
            name = parsed.name[0] if parsed.name else None
            session.add(Practitioner(
                id=parsed.id,
                npi=npi,
                family_name=name.family if name else None,
                given_name=name.given[0] if name and name.given else None,
                prefix=name.prefix[0] if name and name.prefix else None,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} practitioners")


def load_organizations(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirOrganization):
            ident_value = None
            for ident in parsed.identifier:
                if ident.system and "synthea" in ident.system:
                    ident_value = ident.value
                    break
            session.add(Organization(
                id=parsed.id,
                identifier_value=ident_value,
                name=parsed.name,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} organizations")


def load_locations(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirLocation):
            ident_value = None
            for ident in parsed.identifier:
                if ident.system and "synthea" in ident.system:
                    ident_value = ident.value
                    break
            addr = parsed.address
            phone = None
            for t in parsed.telecom:
                if isinstance(t, dict) and t.get("system") == "phone":
                    phone = t.get("value")
                    break
            session.add(Location(
                id=parsed.id,
                identifier_value=ident_value,
                status=parsed.status,
                name=parsed.name,
                address_city=addr.city if addr else None,
                address_state=addr.state if addr else None,
                phone=phone,
                managing_org_display=(
                    parsed.managingOrganization.display
                    if parsed.managingOrganization else None
                ),
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} locations")


def load_patients(session, files: list[str]):
    count = 0
    for path in files:
        for raw_json, parsed in stream_ndjson(path, FhirPatient):
            name = parsed.name[0] if parsed.name else None
            race = _extract_extension_text(parsed.extension, "us-core-race")
            ethnicity = _extract_extension_text(parsed.extension, "us-core-ethnicity")
            addr = parsed.address[0] if parsed.address else None
            session.add(Patient(
                id=parsed.id,
                family_name=_strip_synthea_digits(name.family) if name else None,
                given_name=_strip_synthea_digits(" ".join(name.given)) if name and name.given else None,
                prefix=name.prefix[0] if name and name.prefix else None,
                gender=parsed.gender,
                birth_date=parsed.birthDate,
                deceased_date_time=parsed.deceasedDateTime,
                race=race,
                ethnicity=ethnicity,
                address_city=addr.city if addr else None,
                address_state=addr.state if addr else None,
                marital_status=(
                    parsed.maritalStatus.text if parsed.maritalStatus else None
                ),
                raw_json=raw_json,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} patients")


def load_conditions(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirCondition):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue
            code, code_system, display = _get_first_coding(parsed.code)
            session.add(Condition(
                id=parsed.id,
                patient_id=patient_id,
                encounter_id=extract_encounter_id(parsed.encounter),
                clinical_status=_get_clinical_status(parsed.clinicalStatus),
                verification_status=_get_clinical_status(parsed.verificationStatus),
                code_system=code_system,
                code=code,
                display=display or (parsed.code.text if parsed.code else None),
                onset_date_time=parsed.onsetDateTime,
                abatement_date_time=parsed.abatementDateTime,
                recorded_date=parsed.recordedDate,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} conditions")


def load_observations(session, files: list[str]):
    count = 0
    batch = []
    for path in files:
        for _, parsed in stream_ndjson(path, FhirObservation):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue
            code, code_system, display = _get_first_coding(parsed.code)

            value_quantity = None
            value_unit = None
            value_code = None
            value_display = None
            if parsed.valueQuantity and parsed.valueQuantity.value is not None:
                value_quantity = parsed.valueQuantity.value
                value_unit = parsed.valueQuantity.unit
            elif parsed.valueCodeableConcept:
                vc, _, vd = _get_first_coding(parsed.valueCodeableConcept)
                value_code = vc
                value_display = vd or (
                    parsed.valueCodeableConcept.text
                    if parsed.valueCodeableConcept else None
                )

            component_json = None
            if parsed.component:
                component_json = json.dumps(
                    [c.model_dump(exclude_none=True) for c in parsed.component]
                )

            batch.append({
                "id": parsed.id,
                "patient_id": patient_id,
                "encounter_id": extract_encounter_id(parsed.encounter),
                "status": parsed.status,
                "category": _get_category(parsed.category),
                "code_system": code_system,
                "code": code,
                "display": display or (parsed.code.text if parsed.code else None),
                "effective_date_time": parsed.effectiveDateTime,
                "value_quantity": value_quantity,
                "value_unit": value_unit,
                "value_code": value_code,
                "value_display": value_display,
                "component_json": component_json,
            })
            count += 1
            if len(batch) >= BATCH_SIZE:
                session.execute(insert(Observation), batch)
                batch = []
    if batch:
        session.execute(insert(Observation), batch)
    session.commit()
    logger.info(f"Loaded {count} observations")


def load_procedures(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirProcedure):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue
            code, code_system, display = _get_first_coding(parsed.code)

            reason_code = None
            reason_display = None
            if parsed.reasonCode:
                reason_code, _, reason_display = _get_first_coding(parsed.reasonCode[0])
            elif parsed.reasonReference:
                reason_display = parsed.reasonReference[0].display

            performed_start = None
            performed_end = None
            if parsed.performedPeriod:
                performed_start = parsed.performedPeriod.start
                performed_end = parsed.performedPeriod.end
            elif parsed.performedDateTime:
                performed_start = parsed.performedDateTime

            session.add(Procedure(
                id=parsed.id,
                patient_id=patient_id,
                encounter_id=extract_encounter_id(parsed.encounter),
                status=parsed.status,
                code_system=code_system,
                code=code,
                display=display or (parsed.code.text if parsed.code else None),
                performed_start=performed_start,
                performed_end=performed_end,
                reason_code=reason_code,
                reason_display=reason_display,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} procedures")


def load_encounters(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirEncounter):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue

            type_code = None
            type_display = None
            if parsed.type:
                type_code, _, type_display = _get_first_coding(parsed.type[0])

            practitioner_display = None
            for p in parsed.participant:
                if isinstance(p, dict):
                    indiv = p.get("individual", {})
                    if isinstance(indiv, dict) and indiv.get("display"):
                        practitioner_display = indiv["display"]
                        break

            location_display = None
            for loc in parsed.location:
                if isinstance(loc, dict):
                    loc_ref = loc.get("location", {})
                    if isinstance(loc_ref, dict) and loc_ref.get("display"):
                        location_display = loc_ref["display"]
                        break

            organization_display = (
                parsed.serviceProvider.display if parsed.serviceProvider else None
            )

            session.add(Encounter(
                id=parsed.id,
                patient_id=patient_id,
                status=parsed.status,
                encounter_class=(
                    parsed.class_field.code if parsed.class_field else None
                ),
                type_code=type_code,
                type_display=type_display,
                period_start=parsed.period.start if parsed.period else None,
                period_end=parsed.period.end if parsed.period else None,
                practitioner_display=practitioner_display,
                location_display=location_display,
                organization_display=organization_display,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} encounters")


def load_medication_requests(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirMedicationRequest):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue
            med_code, _, med_display = _get_first_coding(
                parsed.medicationCodeableConcept
            )
            reason_code = None
            reason_display = None
            if parsed.reasonCode:
                reason_code, _, reason_display = _get_first_coding(
                    parsed.reasonCode[0]
                )
            session.add(MedicationRequest(
                id=parsed.id,
                patient_id=patient_id,
                encounter_id=extract_encounter_id(parsed.encounter),
                status=parsed.status,
                intent=parsed.intent,
                medication_code=med_code,
                medication_display=med_display,
                authored_on=parsed.authoredOn,
                reason_code=reason_code,
                reason_display=reason_display,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} medication requests")


def load_document_references(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirDocumentReference):
            patient_id = extract_patient_id(parsed.subject)
            if not patient_id:
                continue

            type_code, _, type_display = _get_first_coding(parsed.type)

            content_text = None
            if parsed.content:
                attachment = parsed.content[0].attachment
                if attachment and attachment.data:
                    try:
                        content_text = base64.b64decode(attachment.data).decode(
                            "utf-8", errors="replace"
                        )
                    except Exception:
                        pass

            author_display = None
            if parsed.author:
                author_display = parsed.author[0].display

            session.add(DocumentReference(
                id=parsed.id,
                patient_id=patient_id,
                status=parsed.status,
                type_code=type_code,
                type_display=type_display,
                date=parsed.date,
                content_text=content_text,
                author_display=author_display,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} document references")


def load_allergy_intolerances(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirAllergyIntolerance):
            patient_id = extract_patient_id(parsed.patient)
            if not patient_id:
                continue
            code, _, display = _get_first_coding(parsed.code)
            session.add(AllergyIntolerance(
                id=parsed.id,
                patient_id=patient_id,
                clinical_status=_get_clinical_status(parsed.clinicalStatus),
                verification_status=_get_clinical_status(parsed.verificationStatus),
                allergy_type=parsed.type,
                category=parsed.category[0] if parsed.category else None,
                criticality=parsed.criticality,
                code=code,
                display=display or (parsed.code.text if parsed.code else None),
                recorded_date=parsed.recordedDate,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} allergy intolerances")


def load_devices(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirDevice):
            patient_id = extract_patient_id(parsed.patient)
            if not patient_id:
                continue
            type_code, _, type_display = _get_first_coding(parsed.type)
            device_name = None
            if parsed.deviceName:
                device_name = parsed.deviceName[0].name
            session.add(Device(
                id=parsed.id,
                patient_id=patient_id,
                status=parsed.status,
                device_name=device_name or type_display,
                type_code=type_code,
                type_display=type_display,
                manufacture_date=parsed.manufactureDate,
                expiration_date=parsed.expirationDate,
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} devices")


def load_immunizations(session, files: list[str]):
    count = 0
    for path in files:
        for _, parsed in stream_ndjson(path, FhirImmunization):
            patient_id = extract_patient_id(parsed.patient)
            if not patient_id:
                continue
            vaccine_code, _, vaccine_display = _get_first_coding(parsed.vaccineCode)
            session.add(Immunization(
                id=parsed.id,
                patient_id=patient_id,
                encounter_id=extract_encounter_id(parsed.encounter),
                status=parsed.status,
                vaccine_code=vaccine_code,
                vaccine_display=vaccine_display,
                occurrence_date_time=parsed.occurrenceDateTime,
                location_display=(
                    parsed.location.display if parsed.location else None
                ),
            ))
            count += 1
            if count % BATCH_SIZE == 0:
                session.flush()
    session.commit()
    logger.info(f"Loaded {count} immunizations")


def run_ingestion(data_dir: str, db_url: str):
    """Parse all FHIR NDJSON files and load into SQLite."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    engine = create_engine(db_url, connect_args={"check_same_thread": False})
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()

    files = discover_ndjson_files(data_dir)
    logger.info(f"Discovered resource types: {list(files.keys())}")

    start = time.time()

    load_practitioners(session, files.get("Practitioner", []))
    load_organizations(session, files.get("Organization", []))
    load_locations(session, files.get("Location", []))
    load_patients(session, files.get("Patient", []))
    load_conditions(session, files.get("Condition", []))
    load_observations(session, files.get("Observation", []))
    load_procedures(session, files.get("Procedure", []))
    load_encounters(session, files.get("Encounter", []))
    load_medication_requests(session, files.get("MedicationRequest", []))
    load_document_references(session, files.get("DocumentReference", []))
    load_allergy_intolerances(session, files.get("AllergyIntolerance", []))
    load_devices(session, files.get("Device", []))
    load_immunizations(session, files.get("Immunization", []))

    elapsed = time.time() - start
    logger.info(f"Ingestion complete in {elapsed:.1f}s")

    session.close()
    engine.dispose()
