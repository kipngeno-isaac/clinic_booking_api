from sqlalchemy import Column, Integer, String, Time
from sqlalchemy.orm import relationship

from app.db.base import Base


class Doctor(Base):
    __tablename__ = "doctors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False, unique=True)

    # Working hours apply Mon-Fri; see README "Assumptions".
    work_start = Column(Time, nullable=False)
    work_end = Column(Time, nullable=False)

    appointments = relationship("Appointment", back_populates="doctor")
