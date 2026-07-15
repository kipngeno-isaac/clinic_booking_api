from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    name: str
    email: str | None = None


class PatientRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: str | None = None
