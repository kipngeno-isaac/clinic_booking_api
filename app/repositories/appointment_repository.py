from datetime import date, datetime, time, timedelta, tzinfo

from sqlalchemy.orm import Session

from app.models.appointment import Appointment


def create(db: Session, appointment: Appointment) -> Appointment:
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    return appointment


def list_for_doctor_on_date(
    db: Session, doctor_id: int, on: date, tz: tzinfo
) -> list[Appointment]:
    local_day_start = datetime.combine(on, time.min, tzinfo=tz)
    local_day_end = local_day_start + timedelta(days=1)
    return (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            Appointment.slot_start >= local_day_start,
            Appointment.slot_start < local_day_end,
        )
        .all()
    )
