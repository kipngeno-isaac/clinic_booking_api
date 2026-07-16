from tests.helpers import create_doctor, create_patient, next_weekday_at


def test_create_patient_with_email(client):
    response = client.post("/patients", json={"name": "John Kamau", "email": "john@example.com"})

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "John Kamau"
    assert body["email"] == "john@example.com"


def test_create_patient_without_email(client):
    response = client.post("/patients", json={"name": "Jane Wambui"})

    assert response.status_code == 201
    assert response.json()["email"] is None


def test_create_patient_duplicate_name_is_allowed(client):
    payload = {"name": "John Kamau"}
    first = client.post("/patients", json=payload)
    second = client.post("/patients", json=payload)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["id"] != second.json()["id"]


def test_upcoming_appointments_empty_when_none_booked(client):
    patient_id = create_patient(client)

    response = client.get(f"/patients/{patient_id}/appointments")

    assert response.status_code == 200
    assert response.json() == []


def test_upcoming_appointments_unknown_patient_returns_404(client):
    response = client.get("/patients/999999/appointments")

    assert response.status_code == 404


def test_upcoming_appointments_sorted_by_date_and_excludes_terminal_statuses(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)

    later = _book(client, doctor_id, patient_id, next_weekday_at(9, days_ahead=6))
    sooner = _book(client, doctor_id, patient_id, next_weekday_at(9, days_ahead=2))
    cancelled = _book(client, doctor_id, patient_id, next_weekday_at(11, days_ahead=2))

    later_id = later.json()["id"]
    sooner_id = sooner.json()["id"]
    cancelled_id = cancelled.json()["id"]

    client.patch(f"/appointments/{later_id}/approve")
    client.patch(f"/appointments/{cancelled_id}/cancel", json={"reason": "not needed"})

    response = client.get(f"/patients/{patient_id}/appointments")

    assert response.status_code == 200
    body = response.json()
    ids = [a["id"] for a in body]
    assert ids == [sooner_id, later_id]  # sorted by slot_start, cancelled one excluded


def _book(client, doctor_id, patient_id, slot_start):
    return client.post(
        "/appointments",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "slot_start": slot_start.isoformat(),
        },
    )
