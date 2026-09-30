# System Architecture — PS-26036 Prototype

## 1. Architecture decision
Use a simple modular monolith: React + Tailwind web client, FastAPI REST API, PostgreSQL, controlled document storage, JWT-based authentication/RBAC, and server-side QR verification. This is a prototype architecture, not a final government production architecture.

## 2. Context diagram
```text
Business / Instrument Owner ─┐
LMO / Inspector ──────────────┤
GATC staff ──────────────────┼── React + Tailwind Web UI
Regulator / Supervisor ──────┤              │ HTTPS / JSON REST
Platform Admin ──────────────┘              ▼
                                      FastAPI Application
                         ┌──────────────┼────────────────┐
                         ▼              ▼                ▼
                     Auth/RBAC     Workflow modules   Public QR API
                         │              │                │
                         └──────────────┼────────────────┘
                                        ▼
                                   PostgreSQL
                                        │
                            Private attachment storage
                                        │
                       In-app notifications + audit events
```

## 3. Suggested repository structure
```text
root/
  frontend/
    src/
      app/                 # routes, layouts, providers
      components/          # shared UI components
      features/
        auth/ users/ instruments/ applications/ scheduling/
        inspections/ certificates/ dashboards/ notifications/ reports/
      lib/                 # API client, validation, formatting
      styles/
  backend/
    app/
      main.py
      core/                # config, security, permissions, errors
      db/                  # session, base, migrations/seed helpers
      models/
      schemas/
      api/v1/              # routers
      services/            # business rules and state transitions
      repositories/        # data access if needed
      tests/
    requirements.txt or pyproject.toml
  docs/
  .env.example
  docker-compose.yml       # optional local convenience
  README.md
  PRD.md
  AI_RULES.md
  ARCHITECTURE.md
  DESIGN.md
  USER_FLOWS.md
```

## 4. Backend modules
- `auth`: login, logout/token handling, current user.
- `users`: profiles, active state, role assignment by authorized admin.
- `instruments`: owner-scoped instrument CRUD and lifecycle history.
- `applications`: create, submit, review, correction, resubmission, rejection, withdrawal.
- `scheduling`: assignee/centre availability, appointment assignment, conflict detection.
- `inspections`: assigned inspection record, observations, result, attachment references.
- `certificates`: issue/revoke/supersede, certificate rendering data, status calculation.
- `public_verification`: lookup by unguessable token or certificate ID, minimal public output.
- `notifications`: in-app notifications and expiry reminders.
- `reports`: role-scoped aggregate counts, search and export.
- `audit`: append-only application-level audit events.

Keep business rules in service functions and call them from API routes. Routes should authenticate, validate input, invoke services, and return typed schemas. Do not put critical authorization only in React.

## 5. Data model and relationships
```text
User 1 ── * Instrument
Instrument 1 ── * Application
Application 1 ── * Attachment
Application 1 ── 0..* Appointment (prototype may enforce one active appointment)
Application 1 ── 0..* Inspection
Application 1 ── 0..* Certificate (renewal/supersession history)
User 1 ── * AuditEvent (actor)
User 1 ── * Notification
```

Recommended constraints/indexes:
- Unique user email/username.
- Unique certificate number and public verification token.
- Index instruments by owner, serial number, category, and status.
- Index applications by status, instrument, applicant, jurisdiction, assigned officer/centre, and submitted date.
- Index appointments by assignee and start/end time.
- Index certificates by instrument, status, valid-until, and token.
- Foreign keys for ownership and lifecycle links; use transactions for multi-step state changes.
- Prevent duplicate active applications for an instrument where the prototype policy says only one can be active.

## 6. Authentication and authorization
- Use short-lived access tokens and appropriate refresh/session strategy for the prototype. Store signing secret in environment variables.
- Resolve the current user from a verified token; never accept role/identity as a trusted request field.
- Use a centralized permission layer with checks for role + ownership + jurisdiction/assignment.
- Example policy: owner sees own records; LMO sees cases in assigned jurisdiction/queue; GATC sees cases assigned to their centre; regulator sees permitted aggregates/records; admin manages accounts/configuration but cannot issue certificates solely by being admin; public can only call certificate verification.
- Seeded demo accounts are allowed for demonstrations and must be documented as demo-only.

## 7. Workflow/state machine
Application transitions should be defined centrally and tested. Initial allowed transitions:
```text
draft -> submitted
submitted -> under_review
under_review -> correction_requested | rejected | approved_for_scheduling
correction_requested -> resubmitted
resubmitted -> under_review
approved_for_scheduling -> scheduled
scheduled -> inspection_in_progress | cancelled
inspection_in_progress -> inspection_recorded
inspection_recorded -> decision_pending
 decision_pending -> completed | correction_requested | rejected
```
Some transitions may be simplified for the demo, but must not permit skipping required inspection/decision steps. `completed` is only reached after a final outcome is recorded. A passing inspection plus authorized decision can lead to certificate issuance. A failed result cannot create a valid certificate. Document any prototype-specific simplification.

## 8. Certificate status logic
1. If revoked, status is `revoked`.
2. Else if superseded, status is `superseded`.
3. Else if current date is later than `valid_until`, status is `expired`.
4. Else status is `valid` only if the certificate was issued by an authorized actor and is linked to a passing inspection/application.
5. Unknown ID/token returns `not_found`; malformed/invalid token returns a safe invalid/not-found response without leaking internal details.

Validity duration must be configurable per prototype instrument category and visibly labelled as demo configuration. Never assume a universal 12-month legal validity.

## 9. API route outline
Use `/api/v1` prefix and consistent typed request/response schemas. Example endpoints (names may be refined but behavior must match):
- `POST /auth/login`, `GET /auth/me`
- `GET/POST /instruments`, `GET/PATCH /instruments/{id}`
- `GET/POST /applications`, `GET /applications/{id}`, `POST /applications/{id}/submit`
- `POST /applications/{id}/review`, `POST /applications/{id}/request-correction`, `POST /applications/{id}/schedule`
- `POST /applications/{id}/inspections`, `GET /applications/{id}/inspections`
- `POST /applications/{id}/certificates/issue`, `POST /certificates/{id}/revoke`, `POST /certificates/{id}/supersede`
- `GET /certificates/{id}`, `GET /public/verify/{token}`, `GET /public/verify?certificate_id=...`
- `GET /dashboards/owner`, `/dashboards/lmo`, `/dashboards/gatc`, `/dashboards/regulator`, `/dashboards/admin`
- `GET /notifications`, `POST /notifications/{id}/read`
- `GET /reports/...`, `GET /audit-events` (strictly role-scoped)

## 10. File handling
Store uploads outside public web root or in a private object-storage bucket. Save metadata in PostgreSQL. Serve files through an authenticated endpoint after checking record permissions. For public certificates, show only generated certificate fields/PDF approved for public access; do not expose application attachments.

## 11. QR implementation
Generate QR code containing a stable HTTPS verification URL with an unguessable token. QR route queries the database at scan time, computes current certificate status, and displays the public verification page. Do not treat a QR image or client-provided fields as proof of validity. In local development, document how the URL base is configured.

## 12. Reminders and scheduled tasks
For a small prototype, reminders may be generated when dashboards load or through a simple scheduled command, as long as behavior is documented. Avoid adding a separate queue/Redis unless needed. Use configurable reminder windows (e.g. 30/7 days as demo settings, not statutory requirements). Record notification generation to avoid repeated duplicates.

## 13. Testing strategy
- Unit tests for state transitions, certificate status calculation, appointment conflicts, and permission policies.
- API integration tests for owner isolation, role access, issue/revoke controls, file access, and public QR behavior.
- End-to-end test for owner submission → review → schedule → inspection → certificate → public verification.
- Seed synthetic records for valid, expired, revoked, superseded, failed-inspection, and invalid-ID scenarios.

## 14. Deployment and configuration
Local setup should work using documented commands. Environment variables should include database URL, JWT secret, allowed frontend origin, file storage directory, and public base URL. Include `.env.example`, migrations, seed script, health endpoint, and Docker Compose if useful. Production hosting, departmental integration, legal compliance, security review, backup, retention, and digital-signature acceptance remain future approvals.

## 15. Explicitly deferred
Blockchain, microservices, Kubernetes, Redis, MongoDB, native mobile app, offline sync, payment gateway, external government APIs, SMS/email vendor integration, advanced analytics/AI, and digital signatures are deferred unless already implemented and demonstrable. The first goal is a secure working vertical slice.
