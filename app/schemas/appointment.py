from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from app.models.appointment import AppointmentStatus


class AppointmentCreate(BaseModel):
    doctor_id: int
    patient_id: int
    slot_start: datetime


class AppointmentStatusUpdate(BaseModel):
    reason: str

    @field_validator("reason")
    @classmethod
    def reason_not_blank(cls, reason: str) -> str:
        if not reason.strip():
            raise ValueError("reason must not be empty")
        return reason


class AppointmentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    doctor_id: int
    patient_id: int
    slot_start: datetime
    status: AppointmentStatus
    reason: str | None = None
    created_at: datetime
