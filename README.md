# Clinic Booking API

The system is a clinic appointment booking API that allows patients to view doctor availability, book appointments, and cancel existing appointments.

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
- **All times stored in UTC; clinic timezone is Africa/Nairobi (EAT, UTC+3).** The clinic operates in a single timezone; storing UTC avoids ambiguity and keeps slot-matching logic timezone-agnostic, while doctor working hours and availability are interpreted in Africa/Nairobi and only converted to/from UTC at the API boundary.
- **Growth beyond 5 doctors requires no schema change** — `doctor_id` is just an indexed foreign key, so the design isn't hardcoded to a fixed doctor count.
- **Dockerized API + Compose-managed database.** Running Postgres via Docker Compose removes "works on my machine" setup friction and keeps local dev close to how the service would run in a container-based deployment. The trade-off is a Docker dependency for local development, which is acceptable given the deployment target is also container-based.
- **FastAPI over Django REST Framework.** FastAPI is fast and ships with built-in interactive API docs (Swagger UI / ReDoc), which makes it easy to exercise the deployed endpoints post-deployment without needing separate API-testing tooling.

### Assumptions

- **Authentication and authorization are out of scope.** User management (patient/doctor identity, login, permissions) is assumed to already be handled elsewhere. The API focuses solely on the specified booking endpoints, and `patient_id` / `doctor_id` are trusted as given rather than derived from an authenticated session.
- **Doctors work Monday–Friday.** Working hours apply to weekdays only; weekends have no available slots. This can be revisited if the clinic later needs weekend or per-doctor variable schedules.

### Testing & Edge Cases to Consider

- Booking a slot outside the doctor's working hours.
- Booking a slot that falls in the past.
- Booking a slot that's already `pending` or `approved` for that doctor.
- Two concurrent booking requests for the same `(doctor_id, slot_start)` — only one should succeed.
- Booking a slot that doesn't align to the 30-minute grid (e.g. `10:15` instead of `10:00`/`10:30`).
- Booking within 1 hour of the current time (stretch rule).
- Approving or rejecting an appointment that's already `approved`, `rejected`, or `cancelled`.
- Cancelling an appointment that's already `cancelled` or `rejected`.
- Requesting availability for a weekend date — should return an empty slot list, not an error.
- Requesting availability or booking against a non-existent `doctor_id`.
- Booking near a UTC day boundary that falls on a different local (Africa/Nairobi) day, or vice versa.
- Rejecting/cancelling with a missing or empty reason.
