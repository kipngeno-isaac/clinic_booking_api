from datetime import date, datetime, timedelta, timezone

from app.core.constants import CLINIC_TZ


def next_weekday_date(days_ahead: int = 2) -> date:
    """A future Mon-Fri calendar date in the clinic's timezone. `days_ahead`
    defaults to 2 so tests comfortably clear the 60-minute booking lead time."""
    candidate = (datetime.now(CLINIC_TZ) + timedelta(days=days_ahead)).date()
    while candidate.weekday() >= 5:  # Saturday=5, Sunday=6
        candidate += timedelta(days=1)
    return candidate


def next_weekday_at(local_hour: int, local_minute: int = 0, days_ahead: int = 2) -> datetime:
    """A future UTC datetime that falls on a Mon-Fri day at the given local
    (Africa/Nairobi) time."""
    on_date = next_weekday_date(days_ahead=days_ahead)
    local_dt = datetime.combine(on_date, datetime.min.time(), tzinfo=CLINIC_TZ).replace(
        hour=local_hour, minute=local_minute
    )
    return local_dt.astimezone(timezone.utc)


def next_weekend_date(days_ahead: int = 2) -> date:
    candidate = (datetime.now(CLINIC_TZ) + timedelta(days=days_ahead)).date()
    while candidate.weekday() < 5:
        candidate += timedelta(days=1)
    return candidate


def create_doctor(client, name="Dr. Test", work_start="09:00:00", work_end="17:00:00") -> int:
    resp = client.post(
        "/doctors", json={"name": name, "work_start": work_start, "work_end": work_end}
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


def create_patient(client, name="Test Patient", email=None) -> int:
    resp = client.post("/patients", json={"name": name, "email": email})
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]
