from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.patient import PatientCreate, PatientRead
from app.services import patient_service

router = APIRouter()


@router.post("", response_model=PatientRead, status_code=status.HTTP_201_CREATED)
def create_patient(patient_in: PatientCreate, db: Session = Depends(get_db)) -> PatientRead:
    return patient_service.create_patient(db, patient_in)
