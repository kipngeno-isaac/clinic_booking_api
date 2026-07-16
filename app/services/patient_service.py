from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.patient import Patient
from app.repositories import appointment_repository, patient_repository
from app.schemas.patient import PatientCreate
from app.services.appointment_service import PatientNotFoundError


def create_patient(db: Session, patient_in: PatientCreate) -> Patient:
    return patient_repository.create(db, patient_in)


def get_upcoming_appointments(db: Session, patient_id: int) -> list[Appointment]:
    patient = patient_repository.get(db, patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {patient_id} not found")

    now = datetime.now(timezone.utc)
    return appointment_repository.list_upcoming_for_patient(db, patient_id, now)
