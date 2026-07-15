from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.appointment import AppointmentCreate, AppointmentRead
from app.services import appointment_service
from app.services.appointment_service import (
    DoctorNotFoundError,
    InvalidSlotError,
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
