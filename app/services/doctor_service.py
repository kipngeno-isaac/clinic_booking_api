from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.repositories import doctor_repository
from app.schemas.doctor import DoctorCreate


class DoctorAlreadyExistsError(Exception):
    pass


def create_doctor(db: Session, doctor_in: DoctorCreate) -> Doctor:
    try:
        return doctor_repository.create(db, doctor_in)
    except IntegrityError as exc:
        db.rollback()
        raise DoctorAlreadyExistsError(
            f"A doctor named '{doctor_in.name}' already exists"
        ) from exc
