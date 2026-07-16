from datetime import timedelta

from tests.helpers import create_doctor, create_patient, next_weekday_at, next_weekend_date


def _book(client, doctor_id, patient_id, slot_start):
    return client.post(
        "/appointments",
        json={
            "doctor_id": doctor_id,
            "patient_id": patient_id,
            "slot_start": slot_start.isoformat(),
        },
    )


def test_book_appointment_success(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    slot_start = next_weekday_at(9)

    response = _book(client, doctor_id, patient_id, slot_start)

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "pending"
    assert body["doctor_id"] == doctor_id
    assert body["patient_id"] == patient_id


def test_book_duplicate_slot_returns_409(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    slot_start = next_weekday_at(9)

    first = _book(client, doctor_id, patient_id, slot_start)
    second = _book(client, doctor_id, patient_id, slot_start)

    assert first.status_code == 201
    assert second.status_code == 409


def test_book_unknown_doctor_returns_404(client):
    patient_id = create_patient(client)

    response = _book(client, 999999, patient_id, next_weekday_at(9))

    assert response.status_code == 404


def test_book_unknown_patient_returns_404(client):
    doctor_id = create_doctor(client)

    response = _book(client, doctor_id, 999999, next_weekday_at(9))

    assert response.status_code == 404


def test_book_less_than_min_lead_time_returns_422(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    from datetime import datetime, timezone

    too_soon = datetime.now(timezone.utc) + timedelta(minutes=10)

    response = _book(client, doctor_id, patient_id, too_soon)

    assert response.status_code == 422


def test_book_outside_working_hours_returns_422(client):
    doctor_id = create_doctor(client, work_start="09:00:00", work_end="17:00:00")
    patient_id = create_patient(client)
    before_hours = next_weekday_at(7)  # 07:00 local, doctor starts at 09:00

    response = _book(client, doctor_id, patient_id, before_hours)

    assert response.status_code == 422


def test_book_misaligned_slot_returns_422(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    misaligned = next_weekday_at(9, local_minute=15)

    response = _book(client, doctor_id, patient_id, misaligned)

    assert response.status_code == 422


def test_book_on_weekend_returns_422(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    from datetime import datetime, time, timezone

    from app.core.constants import CLINIC_TZ

    weekend_date = next_weekend_date()
    slot_start = datetime.combine(weekend_date, time(9, 0), tzinfo=CLINIC_TZ).astimezone(
        timezone.utc
    )

    response = _book(client, doctor_id, patient_id, slot_start)

    assert response.status_code == 422


def test_approve_pending_appointment(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]

    response = client.patch(f"/appointments/{appt_id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"


def test_approve_already_approved_returns_409(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/approve")

    response = client.patch(f"/appointments/{appt_id}/approve")

    assert response.status_code == 409


def test_approve_unknown_appointment_returns_404(client):
    response = client.patch("/appointments/999999/approve")

    assert response.status_code == 404


def test_reject_pending_appointment(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]

    response = client.patch(
        f"/appointments/{appt_id}/reject", json={"reason": "Doctor unavailable"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "rejected"
    assert body["reason"] == "Doctor unavailable"


def test_reject_blank_reason_returns_422(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]

    response = client.patch(f"/appointments/{appt_id}/reject", json={"reason": "   "})

    assert response.status_code == 422


def test_reject_missing_reason_returns_422(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]

    response = client.patch(f"/appointments/{appt_id}/reject", json={})

    assert response.status_code == 422


def test_reject_already_rejected_returns_409(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/reject", json={"reason": "first rejection"})

    response = client.patch(f"/appointments/{appt_id}/reject", json={"reason": "again"})

    assert response.status_code == 409


def test_rejected_slot_becomes_bookable_again(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    other_patient_id = create_patient(client, name="Second Patient")
    slot_start = next_weekday_at(9)
    appt_id = _book(client, doctor_id, patient_id, slot_start).json()["id"]
    client.patch(f"/appointments/{appt_id}/reject", json={"reason": "freeing the slot"})

    response = _book(client, doctor_id, other_patient_id, slot_start)

    assert response.status_code == 201


def test_cancel_pending_appointment(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]

    response = client.patch(
        f"/appointments/{appt_id}/cancel", json={"reason": "Patient requested cancellation"}
    )

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_approved_appointment(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/approve")

    response = client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "no longer needed"})

    assert response.status_code == 200
    assert response.json()["status"] == "cancelled"


def test_cancel_already_cancelled_returns_409(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "first cancel"})

    response = client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "again"})

    assert response.status_code == 409


def test_cancel_rejected_appointment_returns_409(client):
    doctor_id = create_doctor(client)
    patient_id = create_patient(client)
    appt_id = _book(client, doctor_id, patient_id, next_weekday_at(9)).json()["id"]
    client.patch(f"/appointments/{appt_id}/reject", json={"reason": "rejected first"})

    response = client.patch(f"/appointments/{appt_id}/cancel", json={"reason": "try cancel"})

    assert response.status_code == 409


def test_cancel_unknown_appointment_returns_404(client):
    response = client.patch("/appointments/999999/cancel", json={"reason": "test"})

    assert response.status_code == 404
