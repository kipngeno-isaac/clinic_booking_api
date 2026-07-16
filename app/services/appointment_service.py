from datetime import datetime, timedelta, timezone

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.constants import CLINIC_TZ, MIN_BOOKING_LEAD_MINUTES, SATURDAY, SLOT_MINUTES
from app.models.appointment import Appointment, AppointmentStatus
from app.models.doctor import Doctor
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


class AppointmentNotFoundError(Exception):
    pass


class InvalidStatusTransitionError(Exception):
    pass


def _validate_slot(doctor: Doctor, slot_start: datetime) -> datetime:
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

    return slot_start_utc


def book_appointment(db: Session, appointment_in: AppointmentCreate) -> Appointment:
    doctor = doctor_repository.get(db, appointment_in.doctor_id)
    if doctor is None:
        raise DoctorNotFoundError(f"Doctor {appointment_in.doctor_id} not found")

    patient = patient_repository.get(db, appointment_in.patient_id)
    if patient is None:
        raise PatientNotFoundError(f"Patient {appointment_in.patient_id} not found")

    slot_start_utc = _validate_slot(doctor, appointment_in.slot_start)

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


def _get_or_raise(db: Session, appointment_id: int) -> Appointment:
    appointment = appointment_repository.get(db, appointment_id)
    if appointment is None:
        raise AppointmentNotFoundError(f"Appointment {appointment_id} not found")
    return appointment


def approve_appointment(db: Session, appointment_id: int) -> Appointment:
    appointment = _get_or_raise(db, appointment_id)
    if appointment.status != AppointmentStatus.PENDING:
        raise InvalidStatusTransitionError(
            f"Cannot approve an appointment with status '{appointment.status.value}'"
        )
    appointment.status = AppointmentStatus.APPROVED
    db.commit()
    db.refresh(appointment)
    return appointment


def reject_appointment(db: Session, appointment_id: int, reason: str) -> Appointment:
    appointment = _get_or_raise(db, appointment_id)
    if appointment.status != AppointmentStatus.PENDING:
        raise InvalidStatusTransitionError(
            f"Cannot reject an appointment with status '{appointment.status.value}'"
        )
    appointment.status = AppointmentStatus.REJECTED
    appointment.reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment


def cancel_appointment(db: Session, appointment_id: int, reason: str) -> Appointment:
    appointment = _get_or_raise(db, appointment_id)
    if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED):
        raise InvalidStatusTransitionError(
            f"Cannot cancel an appointment with status '{appointment.status.value}'"
        )
    appointment.status = AppointmentStatus.CANCELLED
    appointment.reason = reason
    db.commit()
    db.refresh(appointment)
    return appointment


def reschedule_appointment(db: Session, appointment_id: int, new_slot_start: datetime) -> Appointment:
    appointment = _get_or_raise(db, appointment_id)
    # Terminal states can't be moved; only pending/approved are "active".
    if appointment.status in (AppointmentStatus.CANCELLED, AppointmentStatus.REJECTED):
        raise InvalidStatusTransitionError(
            f"Cannot reschedule an appointment with status '{appointment.status.value}'"
        )

    doctor = doctor_repository.get(db, appointment.doctor_id)
    slot_start_utc = _validate_slot(doctor, new_slot_start)

    appointment.slot_start = slot_start_utc
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise SlotUnavailableError("This slot is already booked") from exc
    db.refresh(appointment)
    return appointment
