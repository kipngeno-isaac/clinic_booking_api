from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.doctor import AvailabilitySlot, DoctorCreate, DoctorRead
from app.services import availability_service, doctor_service
from app.services.appointment_service import DoctorNotFoundError
from app.services.doctor_service import DoctorAlreadyExistsError

router = APIRouter()


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor_in: DoctorCreate, db: Session = Depends(get_db)) -> DoctorRead:
    try:
        return doctor_service.create_doctor(db, doctor_in)
    except DoctorAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.get("/{doctor_id}/availability", response_model=list[AvailabilitySlot])
def get_doctor_availability(
    doctor_id: int, on: date, db: Session = Depends(get_db)
) -> list[AvailabilitySlot]:
    try:
        return availability_service.get_availability(db, doctor_id, on)
    except DoctorNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
