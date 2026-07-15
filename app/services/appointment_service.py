from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import CLINIC_TZ, MIN_BOOKING_LEAD_MINUTES, SATURDAY, SLOT_MINUTES
from app.models.appointment import Appointment, AppointmentStatus
from app.repositories import appointment_repository, doctor_repository, patient_repository
from app.schemas.appointment import AppointmentCreate


class DoctorNotFoundError(Exception):
    pass


class PatientNotFoundError(Exception):
    pass


class InvalidSlotError(Exception):
    pass


class SlotUnavailableError(Exception):
    pass


def book_appointment(db: Session, appointment_in: AppointmentCreate) -> Appointment:
    doctor = doctor_repository.get(db, appointment_in.doctor_id)
    if doctor is None:
        raise DoctorNotFoundError(f"Doctor {appointment_in.doctor_id} not found")

    patient = patient_repository.get(db, appointment_in.patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {appointment_in.patient_id} not found")

    slot_start = appointment_in.slot_start
    slot_start_utc = (
        slot_start.replace(tzinfo=timezone.utc)
        if slot_start.tzinfo is None
        else slot_start.astimezone(timezone.utc)
    )

    now = datetime.now(timezone.utc)
    if slot_start_utc < now + timedelta(minutes=MIN_BOOKING_LEAD_MINUTES):
        raise InvalidSlotError(
            f"slot_start must be at least {MIN_BOOKING_LEAD_MINUTES} minutes from now"
        )

    local_slot = slot_start_utc.astimezone(CLINIC_TZ)

    # Doctors work Mon-Fri only; see README "Assumptions".
    if local_slot.weekday() >= SATURDAY:
        raise InvalidSlotError("doctor does not work on weekends")

    local_work_start = datetime.combine(local_slot.date(), doctor.work_start, tzinfo=CLINIC_TZ)
    local_work_end = datetime.combine(local_slot.date(), doctor.work_end, tzinfo=CLINIC_TZ)

    if local_slot < local_work_start or local_slot + timedelta(minutes=SLOT_MINUTES) > local_work_end:
        raise InvalidSlotError("slot_start is outside the doctor's working hours")

    offset_minutes = (local_slot - local_work_start).total_seconds() / 60
    if offset_minutes % SLOT_MINUTES != 0:
        raise InvalidSlotError("slot_start does not align to a 30-minute slot boundary")

    appointment = Appointment(
        doctor_id=doctor.id,
        patient_id=patient.id,
        slot_start=slot_start_utc,
        status=AppointmentStatus.PENDING,
    )
    try:
        return appointment_repository.create(db, appointment)
    except IntegrityError as exc:
        db.rollback()
        raise SlotUnavailableError("This slot is already booked") from exc
