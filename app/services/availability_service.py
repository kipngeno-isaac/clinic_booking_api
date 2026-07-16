from datetime import date as date_, datetime, timedelta, timezone

from sqlalchemy.orm import Session

from app.core.constants import CLINIC_TZ, SATURDAY, SLOT_MINUTES
from app.models.appointment import AppointmentStatus
from app.repositories import appointment_repository, doctor_repository
from app.schemas.doctor import AvailabilitySlot
from app.services.appointment_service import DoctorNotFoundError


def get_availability(db: Session, doctor_id: int, on: date_) -> list[AvailabilitySlot]:
    doctor = doctor_repository.get(db, doctor_id)
    if doctor is None:
        raise DoctorNotFoundError(f"Doctor {doctor_id} not found")

    # Doctors work Mon-Fri only; see README "Assumptions".
    if on.weekday() >= SATURDAY:
        return []

    booked_starts = {
        appt.slot_start
        for appt in appointment_repository.list_for_doctor_on_date(
            db, doctor_id=doctor_id, on=on, tz=CLINIC_TZ
        )
        if appt.status in (AppointmentStatus.PENDING, AppointmentStatus.APPROVED)
    }

    step = timedelta(minutes=SLOT_MINUTES)
    cursor = datetime.combine(on, doctor.work_start, tzinfo=CLINIC_TZ)
    local_end = datetime.combine(on, doctor.work_end, tzinfo=CLINIC_TZ)

    slots: list[AvailabilitySlot] = []
    while cursor + step <= local_end:
        slot_start_utc = cursor.astimezone(timezone.utc)
        if slot_start_utc not in booked_starts:
            slots.append(
                AvailabilitySlot(
                    start=slot_start_utc,
                    end=(cursor + step).astimezone(timezone.utc),
                )
            )
        cursor += step

    return slots
