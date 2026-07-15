from sqlalchemy.orm import Session

from app.models.doctor import Doctor
from app.schemas.doctor import DoctorCreate


def create(db: Session, doctor_in: DoctorCreate) -> Doctor:
    doctor = Doctor(
        name=doctor_in.name,
        work_start=doctor_in.work_start,
        work_end=doctor_in.work_end,
    )
    db.add(doctor)
    db.commit()
    db.refresh(doctor)
    return doctor
