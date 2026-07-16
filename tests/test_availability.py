from tests.helpers import create_doctor, create_patient, next_weekday_at, next_weekday_date, next_weekend_date


def test_availability_returns_full_grid_for_weekday(client):
    doctor_id = create_doctor(client, work_start="09:00:00", work_end="11:00:00")
    on_date = next_weekday_date()

    response = client.get(f"/doctors/{doctor_id}/availability", params={"on": on_date.isoformat()})

    assert response.status_code == 200
    slots = response.json()
    assert len(slots) == 4  # 09:00-11:00 in 30-min slots


def test_availability_weekend_returns_empty_list(client):
    doctor_id = create_doctor(client)
    weekend_date = next_weekend_date()

    response = client.get(
        f"/doctors/{doctor_id}/availability", params={"on": weekend_date.isoformat()}
    )

    assert response.status_code == 200
    assert response.json() == []


def test_availability_unknown_doctor_returns_404(client):
    on_date = next_weekday_date()

    response = client.get("/doctors/999999/availability", params={"on": on_date.isoformat()})

    assert response.status_code == 404


def test_availability_excludes_booked_slot(client):
    doctor_id = create_doctor(client, work_start="09:00:00", work_end="11:00:00")
    patient_id = create_patient(client)
    on_date = next_weekday_date()
    slot_start = next_weekday_at(9)

    book = client.post(
        "/appointments",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "slot_start": slot_start.isoformat(),
        },
    )
    assert book.status_code == 201

    response = client.get(f"/doctors/{doctor_id}/availability", params={"on": on_date.isoformat()})

    assert response.status_code == 200
    starts = [slot["start"] for slot in response.json()]
    assert slot_start.isoformat().replace("+00:00", "Z") not in starts
    assert len(starts) == 3  # one of the 4 slots is now booked
