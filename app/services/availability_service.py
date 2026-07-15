from datetime import date as date_, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from sqlalchemy.orm import Session

from app.repositories import doctor_repository
from app.schemas.doctor import AvailabilitySlot

CLINIC_TZ = ZoneInfo("Africa/Nairobi")
SLOT_MINUTES = 30
SATURDAY = 5


class DoctorNotFoundError(Exception):
    pass


def get_availability(db: Session, doctor_id: int, on: date_) -> list[AvailabilitySlot]:
    doctor = doctor_repository.get(db, doctor_id)
    if doctor is None:
        raise DoctorNotFoundError(f"Doctor {doctor_id} not found")

    # Doctors work Mon-Fri only; see README "Assumptions".
    if on.weekday() >= SATURDAY:
        return []

    step = timedelta(minutes=SLOT_MINUTES)
    cursor = datetime.combine(on, doctor.work_start, tzinfo=CLINIC_TZ)
    local_end = datetime.combine(on, doctor.work_end, tzinfo=CLINIC_TZ)

    slots: list[AvailabilitySlot] = []
    while cursor + step <= local_end:
        slots.append(
            AvailabilitySlot(
                start=cursor.astimezone(timezone.utc),
                end=(cursor + step).astimezone(timezone.utc),
            )
        )
        cursor += step

    # TODO: exclude slots with a pending/approved Appointment once that
    # model exists (see README "Key Design Decisions & Trade-offs").
    return slots
