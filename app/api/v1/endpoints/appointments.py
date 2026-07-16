from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentRead, AppointmentStatusUpdate
from app.services import appointment_service
from app.services.appointment_service import (
    AppointmentNotFoundError,
    DoctorNotFoundError,
    InvalidSlotError,
    InvalidStatusTransitionError,
    PatientNotFoundError,
    SlotUnavailableError,
)

router = APIRouter()


@router.post("", response_model=AppointmentRead, status_code=status.HTTP_201_CREATED)
def book_appointment(
    appointment_in: AppointmentCreate, db: Session = Depends(get_db)
) -> AppointmentRead:
    try:
        return appointment_service.book_appointment(db, appointment_in)
    except (DoctorNotFoundError, PatientNotFoundError) as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidSlotError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc
    except SlotUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{appointment_id}/approve", response_model=AppointmentRead)
def approve_appointment(appointment_id: int, db: Session = Depends(get_db)) -> AppointmentRead:
    try:
        return appointment_service.approve_appointment(db, appointment_id)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{appointment_id}/reject", response_model=AppointmentRead)
def reject_appointment(
    appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db)
) -> AppointmentRead:
    try:
        return appointment_service.reject_appointment(db, appointment_id, payload.reason)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc


@router.patch("/{appointment_id}/cancel", response_model=AppointmentRead)
def cancel_appointment(
    appointment_id: int, payload: AppointmentStatusUpdate, db: Session = Depends(get_db)
) -> AppointmentRead:
    try:
        return appointment_service.cancel_appointment(db, appointment_id, payload.reason)
    except AppointmentNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except InvalidStatusTransitionError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
