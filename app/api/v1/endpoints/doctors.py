from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.doctor import DoctorCreate, DoctorRead
from app.services import doctor_service
from app.services.doctor_service import DoctorAlreadyExistsError

router = APIRouter()


@router.post("", response_model=DoctorRead, status_code=status.HTTP_201_CREATED)
def create_doctor(doctor_in: DoctorCreate, db: Session = Depends(get_db)) -> DoctorRead:
    try:
        return doctor_service.create_doctor(db, doctor_in)
    except DoctorAlreadyExistsError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
