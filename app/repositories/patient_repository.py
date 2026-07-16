from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate


def get(db: Session, patient_id: int) -> Patient | None:
    return db.get(Patient, patient_id)


def create(db: Session, patient_in: PatientCreate) -> Patient:
    patient = Patient(name=patient_in.name, email=patient_in.email)
    db.add(patient)
    db.commit()
    db.refresh(patient)
    return patient
