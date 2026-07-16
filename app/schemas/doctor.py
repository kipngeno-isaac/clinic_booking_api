from datetime import datetime, time

from pydantic import BaseModel, ConfigDict, field_validator


class DoctorCreate(BaseModel):
    name: str
    work_start: time
    work_end: time

    @field_validator("work_end")
    @classmethod
    def work_end_after_start(cls, work_end: time, info) -> time:
        work_start = info.data.get("work_start")
        if work_start is not None and work_end <= work_start:
            raise ValueError("work_end must be after work_start")
        return work_end


class DoctorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    work_start: time
    work_end: time


class AvailabilitySlot(BaseModel):
    start: datetime
    end: datetime
