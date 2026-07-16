# Clinic Booking API

[![CI/CD](https://github.com/kipngeno-isaac/clinic_booking_api/actions/workflows/ci.yml/badge.svg)](https://github.com/kipngeno-isaac/clinic_booking_api/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kipngeno-isaac/clinic_booking_api/branch/main/graph/badge.svg)](https://codecov.io/gh/kipngeno-isaac/clinic_booking_api)

The system is a clinic appointment booking API that allows patients to view doctor availability, book appointments, and cancel existing appointments.

**Live API docs:** [clinic-booking-api.unirouteglobal.org/docs](https://clinic-booking-api.unirouteglobal.org/docs)

## Core Functionality

The service implements four primary operations: checking a doctor's available slots, booking a slot, a doctor approving or rejecting a pending appointment, and cancelling an appointment.

## Tech Stack

- **API framework:** Python + FastAPI
- **Database:** PostgreSQL
- **Containerization:** The API is dockerized; PostgreSQL runs via Docker Compose for local development, so a contributor only needs Docker to get a working environment. The same compose setup doubles as the basis for deployment automation.

## System Design

### Overview

The initial system supports a small clinic with 5 doctors, where each doctor has predefined working hours and appointments are divided into 30-minute slots.

### Requirements

**Functional**

- Patients can view a doctor's available 30-minute slots for a given day.
- Patients can book an open slot; once booked, it must not be available to others.
- Doctors can approve or reject a pending appointment.
- Patients can cancel an existing appointment by providing a reason.

**API Endpoints**

- `POST /appointments` — Book a slot. Validates that it falls within the doctor's working hours, is not in the past, and is not already taken. Creates the appointment in `pending` status.
- `GET /doctors/{id}/availability` — Return all available 30-minute slots for a doctor on a given date.
- `PATCH /appointments/{id}/approve` — Doctor approves a pending appointment.
- `PATCH /appointments/{id}/reject` — Doctor rejects a pending appointment with a reason. The slot becomes bookable again.
- `PATCH /appointments/{id}/cancel` — Cancel an appointment with a reason. The slot becomes bookable again. Returns an error if already cancelled or rejected.
- `PATCH /appointments/{id}/reschedule` — Move an appointment to a new slot. The original slot becomes bookable again and the new slot is validated exactly like a fresh booking (working hours, lead time, alignment, not already taken). Returns an error if the appointment is `cancelled` or `rejected`.
- `GET /patients/{id}/appointments` *(stretch)* — Upcoming appointments sorted by date.

**Non-functional**

- Validation failures return meaningful error messages with correct HTTP status codes.
- Code is structured sensibly across modules rather than a single file.
- Booking logic has at least basic automated test coverage.
- Bookings within 1 hour of the current time are prevented *(stretch)*.
- The system starts small (5 doctors) but should be designed to grow.

### Models & Components

- **Doctor** — `id`, `name`, `working_hours` (start/end per day). Defines the grid of bookable slots.
- **Patient** — `id`, `name`, contact info. Referenced by appointments; no dedicated patient-management endpoints are required for the initial scope.
- **Appointment** — `id`, `doctor_id`, `patient_id`, `slot_start`, `status` (`pending` / `approved` / `rejected` / `cancelled`), `reason` (used for rejection or cancellation). `slot_end` is derived (`slot_start + 30 min`) rather than stored.

### Key Design Decisions & Trade-offs

- **Slots are computed, not pre-generated.** Availability for `GET /doctors/{id}/availability` is derived at request time from the doctor's working hours minus existing `pending`/`approved` appointments, rather than materializing a row per slot per day. Simpler to reason about and avoids a background job to pre-populate future slots; the trade-off is a bit more computation per availability request, which is acceptable at this scale.
- **Concurrency safety via a DB constraint, not just an application check.** A "check then insert" pattern is a race condition under concurrent requests for the same slot. The plan is a unique constraint on `(doctor_id, slot_start)` (or `SELECT ... FOR UPDATE` inside a transaction) so the database — not application logic — is the source of truth for "slot taken."
- **Booking creates a pending appointment, not an immediately confirmed one.** A slot is held (excluded from availability) as soon as it's booked, but requires doctor approval to become confirmed. This models real clinic behavior — the doctor has final say over their schedule — while still preventing double-booking of the same slot during the pending window.
- **Status changes are flags, not deletes.** Cancelled/rejected appointments stay in the table rather than being removed, preserving history and freeing the slot without losing the audit trail.
- **Rescheduling is disallowed for `rejected`, not just `cancelled`.** The spec only calls out returning an error for a cancelled appointment; `rejected` is treated the same way since it's an equally terminal state — a doctor already declined the slot, so moving it to a new time doesn't reflect their decision. This is noted as an ambiguity resolution rather than a spec requirement. Rescheduling reuses the exact same slot validation as a fresh booking (working hours, lead time, alignment, uniqueness) and keeps the appointment's existing status (`pending` or `approved`) rather than resetting it.
- **All times stored in UTC; clinic timezone is Africa/Nairobi (EAT, UTC+3).** The clinic operates in a single timezone; storing UTC avoids ambiguity and keeps slot-matching logic timezone-agnostic, while doctor working hours and availability are interpreted in Africa/Nairobi and only converted to/from UTC at the API boundary.
- **Growth beyond 5 doctors requires no schema change** — `doctor_id` is just an indexed foreign key, so the design isn't hardcoded to a fixed doctor count.
- **Dockerized API + Compose-managed database.** Running Postgres via Docker Compose removes "works on my machine" setup friction and keeps local dev close to how the service would run in a container-based deployment. The trade-off is a Docker dependency for local development, which is acceptable given the deployment target is also container-based.
- **FastAPI over Django REST Framework.** FastAPI is fast and ships with built-in interactive API docs (Swagger UI / ReDoc), which makes it easy to exercise the deployed endpoints post-deployment without needing separate API-testing tooling.

### Assumptions

- **Authentication and authorization are out of scope.** User management (patient/doctor identity, login, permissions) is assumed to already be handled elsewhere. The API focuses solely on the specified booking endpoints, and `patient_id` / `doctor_id` are trusted as given rather than derived from an authenticated session.
- **Doctors work Monday–Friday.** Working hours apply to weekdays only; weekends have no available slots. This can be revisited if the clinic later needs weekend or per-doctor variable schedules.
- **"Upcoming" for `GET /patients/{id}/appointments` means future *and* still active.** It returns `pending`/`approved` appointments with `slot_start` in the future, sorted ascending — a patient looking at what's coming up doesn't want appointments they already cancelled or that were rejected cluttering the list.

### Testing & Edge Cases to Consider

- Booking a slot outside the doctor's working hours.
- Booking a slot that falls in the past.
- Booking a slot that's already `pending` or `approved` for that doctor.
- Two concurrent booking requests for the same `(doctor_id, slot_start)` — only one should succeed.
- Booking a slot that doesn't align to the 30-minute grid (e.g. `10:15` instead of `10:00`/`10:30`).
- Booking within 1 hour of the current time (stretch rule).
- Approving or rejecting an appointment that's already `approved`, `rejected`, or `cancelled`.
- Cancelling an appointment that's already `cancelled` or `rejected`.
- Rescheduling to a slot that's outside working hours, in the past, misaligned, or already taken — same validation as a fresh booking.
- Rescheduling an appointment that's already `cancelled` or `rejected`.
- Rescheduling frees the original slot, so it must become bookable by someone else immediately.
- Requesting availability for a weekend date — should return an empty slot list, not an error.
- Requesting availability or booking against a non-existent `doctor_id`.
- Booking near a UTC day boundary that falls on a different local (Africa/Nairobi) day, or vice versa.
- Rejecting/cancelling with a missing or empty reason.

## Implementation

### Project Structure

```
app/
  main.py                     # FastAPI app instance, mounts the v1 router
  core/
    config.py                  # Settings (DB connection) via pydantic-settings, reads .env
    constants.py                # Shared clinic-schedule constants (timezone, slot size, lead time)
  db/
    session.py                   # SQLAlchemy engine + SessionLocal
    base.py                       # Declarative Base
  models/                       # SQLAlchemy ORM models: Doctor, Patient, Appointment
  schemas/                      # Pydantic request/response schemas
  repositories/                 # Data-access layer (DB queries only, no business logic)
  services/                     # Business logic: validation, status transitions
  api/
    deps.py                       # get_db dependency
    v1/router.py                   # aggregates versioned routers
    v1/endpoints/                   # doctors, patients, appointments, health
alembic/                       # DB migrations
tests/                        # pytest suite (helpers.py has shared fixtures/date utilities)
```

Each request flows `api` → `services` → `repositories` → `db`, so HTTP concerns, business rules, and persistence stay separated. `services` raise plain Python exceptions (e.g. `DoctorNotFoundError`, `InvalidStatusTransitionError`); the `api` layer is the only place that translates those into HTTP status codes.

### Running Locally

Prerequisites: Python 3.10+, Docker.

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env          # defaults work as-is for local dev
docker compose up -d db       # starts Postgres on localhost:5432
alembic upgrade head          # creates the schema

uvicorn app.main:app --reload
```

Verify with `curl http://127.0.0.1:8000/health` — expect `{"app": "ok", "db": "ok"}`. Interactive API docs (Swagger UI) are at `http://127.0.0.1:8000/docs`.

### Database Migrations

Alembic is wired to `Settings.database_url` (so `.env` stays the single source of truth) and `Base.metadata` (so new models are autodetected). Workflow for a schema change:

```bash
# after adding/editing a model, and importing it in alembic/env.py
alembic revision --autogenerate -m "description of the change"
# review the generated file, then:
alembic upgrade head
```

### CI/CD

`.github/workflows/ci.yml` runs on every pull request and on pushes to `main`/`dev`:

1. **`test`** — spins up a `postgres:16-alpine` service container, installs `requirements-dev.txt`, runs the full pytest suite with coverage, uploads the coverage report to [Codecov](https://codecov.io).
2. **`build`** — `needs: test`, so it only runs if every test passes. Builds the Docker image to validate it builds cleanly. On a push to `main` specifically (i.e. a PR just got merged), it additionally logs into **Docker Hub** and pushes the image (`docker.io/kipngenoisaac/clinic-booking-api`) tagged both `latest` and `<commit-sha>`.
3. **`deploy`** — `needs: build`, same "push to `main`" condition. SSHes into the deployment VM (via [`appleboy/ssh-action`](https://github.com/appleboy/ssh-action)) and runs `docker compose -f docker-compose.prod.yml pull && up -d`.

The two README badges above reflect this: the CI/CD badge is this workflow's overall status (test + build + deploy all in one workflow, so it's also the de facto "tests passing" badge), and the codecov badge tracks line coverage over time.

**Required GitHub Actions secrets** (Settings → Secrets and variables → Actions):

| Secret | Purpose |
|---|---|
| `CODECOV_TOKEN` | Codecov upload token (codecov.io → repo settings) — optional for public repos but avoids upload rate-limiting |
| `DOCKERHUB_USERNAME` | Docker Hub username (`kipngenoisaac`) |
| `DOCKERHUB_TOKEN` | Docker Hub access token (Account Settings → Security → Access Tokens — not your account password) |
| `VM_HOST` | VM's public IP or hostname |
| `VM_USER` | SSH user on the VM |
| `VM_SSH_KEY` | Private key for that user (public key must be in the VM's `~/.ssh/authorized_keys`) |
| `VM_APP_DIR` | Absolute path on the VM containing `docker-compose.prod.yml` and `.env` |

**VM-side setup — done:** Docker + Docker Compose confirmed installed and running, `docker-compose.prod.yml` and a production `.env` (freshly generated random Postgres password, not the dev defaults) are in place at the deploy directory.

**Deployment manually verified end-to-end on this VM:** pulled `kipngenoisaac/clinic-booking-api:latest` from Docker Hub, brought up `db` + `api` via `docker-compose.prod.yml`, Alembic ran all migrations automatically against the fresh database, and `/health` plus a real request (create doctor → check availability) both worked correctly — confirmed both from the VM itself and externally at [clinic-booking-api.unirouteglobal.org](https://clinic-booking-api.unirouteglobal.org/docs).

**Still outstanding:**
- Add the 7 secrets above in GitHub, so the `deploy` job can reach this VM automatically instead of the pull/up steps being run by hand (as done above).
- Sign up at codecov.io with your GitHub account and add the repo (needed for the coverage badge to render — it'll otherwise show "unknown").

**Note:** an earlier VM was tried first but had to be abandoned — its cloud firewall was intermittently blocking inbound SSH (both from GitHub Actions and direct connections), unrelated to anything in this repo. It was replaced with the current VM above.

`docker-compose.prod.yml` differs from the dev `docker-compose.yml`: it pulls the prebuilt Docker Hub image instead of building locally, drops the `--reload` flag and the source bind-mount, and — since this is a publicly reachable VM — does **not** expose Postgres's port to the host, only to `api` over the internal Docker network. The `api` service itself is published as `127.0.0.1:8000:8000` rather than `8000:8000`, so it's reachable only from the VM's own nginx, not directly from the public internet; nginx terminates TLS and reverse-proxies the public hostname to it.

**Not yet verified end-to-end:** the `test` and `build` jobs (image build, tagging) have been validated locally against equivalent configuration. The actual SSH deploy and Docker Hub push are unverified until the secrets above are added and a real PR merges to `main`.

### API Reference

Endpoints from the original spec:

| Method & Path | Status |
|---|---|
| `POST /appointments` | ✅ implemented |
| `GET /doctors/{id}/availability` | ✅ implemented |
| `PATCH /appointments/{id}/cancel` | ✅ implemented |
| `PATCH /appointments/{id}/reschedule` | ✅ implemented |
| `GET /patients/{id}/appointments` *(stretch)* | ✅ implemented |

Added beyond the original spec, since auth/user-management is out of scope (see Assumptions) and there was otherwise no way to seed data or model a doctor declining a booking:

- `POST /doctors` — create a doctor. Enforces a unique `name` (`409` on duplicate) so retries can't silently create duplicate doctors.
- `POST /patients` — create a patient. No uniqueness constraint — unlike doctors, two real patients can legitimately share a name.
- `PATCH /appointments/{id}/approve` — doctor approves a pending appointment.
- `PATCH /appointments/{id}/reject` — doctor rejects a pending appointment with a reason; the slot becomes bookable again.
- `GET /health` — reports both app and DB status (`{"app": "ok", "db": "ok"}`), `503` if the DB is unreachable.

### Sample Requests

**Health check**

```bash
curl http://127.0.0.1:8000/health
```
```json
{"app": "ok", "db": "ok"}
```

**Create a doctor**

```bash
curl -X POST http://127.0.0.1:8000/doctors \
  -H "Content-Type: application/json" \
  -d '{"name": "Dr. Jane Wanjiru", "work_start": "09:00:00", "work_end": "17:00:00"}'
```
```json
{"id": 1, "name": "Dr. Jane Wanjiru", "work_start": "09:00:00", "work_end": "17:00:00"}
```
A repeat call with the same `name` returns `409 {"detail": "A doctor named 'Dr. Jane Wanjiru' already exists"}`.

**Create a patient**

```bash
curl -X POST http://127.0.0.1:8000/patients \
  -H "Content-Type: application/json" \
  -d '{"name": "John Kamau", "email": "john@example.com"}'
```
```json
{"id": 1, "name": "John Kamau", "email": "john@example.com"}
```
`email` is optional.

**Check a doctor's availability**

```bash
curl "http://127.0.0.1:8000/doctors/1/availability?on=2026-07-16"
```
```json
[
  {"start": "2026-07-16T06:00:00Z", "end": "2026-07-16T06:30:00Z"},
  {"start": "2026-07-16T06:30:00Z", "end": "2026-07-16T07:00:00Z"}
]
```
Times are in UTC (09:00 Africa/Nairobi = 06:00 UTC). A weekend date returns `[]`; an unknown `doctor_id` returns `404`.

**Book an appointment**

```bash
curl -X POST http://127.0.0.1:8000/appointments \
  -H "Content-Type: application/json" \
  -d '{"doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-16T06:00:00Z"}'
```
```json
{
  "id": 1,
  "doctor_id": 1,
  "patient_id": 1,
  "slot_start": "2026-07-16T06:00:00Z",
  "status": "pending",
  "reason": null,
  "created_at": "2026-07-15T11:36:13.558993Z"
}
```
`slot_start` must be ≥60 minutes from now, within the doctor's working hours, aligned to the 30-minute grid, and not already taken — each violation returns `422`; an already-booked slot returns `409`.

**Approve an appointment**

```bash
curl -X PATCH http://127.0.0.1:8000/appointments/1/approve
```
```json
{"id": 1, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-16T06:00:00Z", "status": "approved", "reason": null, "created_at": "..."}
```
Only valid from `pending`; otherwise `409`.

**Reject an appointment**

```bash
curl -X PATCH http://127.0.0.1:8000/appointments/1/reject \
  -H "Content-Type: application/json" \
  -d '{"reason": "Doctor unavailable"}'
```
```json
{"id": 1, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-16T06:00:00Z", "status": "rejected", "reason": "Doctor unavailable", "created_at": "..."}
```
Only valid from `pending`; `reason` is required and can't be blank.

**Cancel an appointment**

```bash
curl -X PATCH http://127.0.0.1:8000/appointments/1/cancel \
  -H "Content-Type: application/json" \
  -d '{"reason": "Patient requested cancellation"}'
```
```json
{"id": 1, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-16T06:00:00Z", "status": "cancelled", "reason": "Patient requested cancellation", "created_at": "..."}
```
Valid from `pending` or `approved`; returns `409` if already `cancelled` or `rejected`.

**Reschedule an appointment**

```bash
curl -X PATCH http://127.0.0.1:8000/appointments/1/reschedule \
  -H "Content-Type: application/json" \
  -d '{"slot_start": "2026-07-16T07:00:00Z"}'
```
```json
{"id": 1, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-16T07:00:00Z", "status": "pending", "reason": null, "created_at": "..."}
```
The original slot (`06:00:00Z`) becomes bookable again; the new `slot_start` is validated exactly like a fresh booking. Status is unchanged. Returns `422` on an invalid new slot, `409` if the new slot is taken or the appointment is `cancelled`/`rejected`, `404` for an unknown `id`.

**List a patient's upcoming appointments**

```bash
curl "http://127.0.0.1:8000/patients/1/appointments"
```
```json
[
  {"id": 2, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-17T06:00:00Z", "status": "pending", "reason": null, "created_at": "..."},
  {"id": 1, "doctor_id": 1, "patient_id": 1, "slot_start": "2026-07-20T10:00:00Z", "status": "approved", "reason": null, "created_at": "..."}
]
```
Only future `pending`/`approved` appointments, sorted by `slot_start` ascending; `cancelled`/`rejected` ones are excluded (see Assumptions). Unknown `patient_id` returns `404`.

### Testing

Tests run against a dedicated `clinic_booking_test` database on the same Postgres instance (created automatically if missing), not the dev database — this is deliberate, since the concurrency guard is a Postgres-specific partial unique index that a SQLite in-memory DB can't replicate faithfully.

```bash
pip install -r requirements-dev.txt
docker compose up -d db     # tests need a live Postgres instance
pytest
```

46 tests in `tests/`, covering the full booking lifecycle and the edge cases listed above: creation (doctors/patients, including duplicate-name handling), availability (weekday grid, weekend empty list, unknown doctor, booked-slot exclusion), booking/approve/reject/cancel/reschedule (happy paths, every invalid-status-transition case, lead-time/working-hours/grid-alignment/weekend validation, the double-booking race condition via the DB constraint, rescheduling freeing the original slot, and every `404` on an unknown ID), the `/health` DB-unreachable branch (mocked `OperationalError`), and the `get_db` dependency itself (session yielded and closed).

**Coverage:**

```bash
pytest --cov=app --cov-report=term-missing
```

Currently 100% line coverage (435/435 statements).

### AI Reflection

See [AI_REFLECTION.md](./AI_REFLECTION.md).

