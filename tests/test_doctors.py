def test_create_doctor(client):
    response = client.post(
        "/doctors",
        json={"name": "Dr. Jane Wanjiru", "work_start": "09:00:00", "work_end": "17:00:00"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Dr. Jane Wanjiru"
    assert body["work_start"] == "09:00:00"
    assert body["work_end"] == "17:00:00"
    assert isinstance(body["id"], int)


def test_create_doctor_duplicate_name_returns_409(client):
    payload = {"name": "Dr. Duplicate", "work_start": "09:00:00", "work_end": "17:00:00"}
    first = client.post("/doctors", json=payload)
    assert first.status_code == 201

    second = client.post("/doctors", json=payload)

    assert second.status_code == 409


def test_create_doctor_work_end_before_work_start_returns_422(client):
    response = client.post(
        "/doctors",
        json={"name": "Dr. Bad Hours", "work_start": "17:00:00", "work_end": "09:00:00"},
    )

    assert response.status_code == 422
