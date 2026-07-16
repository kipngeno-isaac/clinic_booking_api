from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.appointment import AppointmentRead
from app.schemas.patient import PatientCreate, PatientRead
from app.services import patient_service
from app.services.appointment_service import PatientNotFoundError

router = APIRouter()


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    return patient_service.create_patient(db, patient_in)


@router.get("/{patient_id}/appointments", response_model=list[AppointmentRead])
def get_patient_appointments(
    patient_id: int, db: Session = Depends(get_db)
) -> list[AppointmentRead]:
    try:
        return patient_service.get_upcoming_appointments(db, patient_id)
    except PatientNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
