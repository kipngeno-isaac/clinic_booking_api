from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.repositories import patient_repository
from app.schemas.patient import PatientCreate


def create_patient(db: Session, patient_in: PatientCreate) -> Patient:
    return patient_repository.create(db, patient_in)
