import enum

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.base import Base


class AppointmentStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    doctor_id = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False)
    slot_start = Column(DateTime(timezone=True), nullable=False)
    status = Column(
        Enum(
            AppointmentStatus,
            name="appointment_status",
            values_callable=lambda enum_cls: [member.value for member in enum_cls],
        ),
        nullable=False,
        default=AppointmentStatus.PENDING,
    )
    reason = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    doctor = relationship("Doctor", back_populates="appointments")
    patient = relationship("Patient", back_populates="appointments")

    __table_args__ = (
        # Only one active (pending/approved) appointment per doctor per slot.
        # A slot freed by rejection/cancellation can be rebooked without
        # violating this index, since old rows keep their terminal status.
        Index(
            "uq_active_appointment_slot",
            "doctor_id",
            "slot_start",
            unique=True,
            postgresql_where=status.in_([AppointmentStatus.PENDING, AppointmentStatus.APPROVED]),
        ),
    )
