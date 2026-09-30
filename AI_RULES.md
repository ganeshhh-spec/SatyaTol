# AI Agent Build Rules — PS-26036 Prototype

These rules are binding instructions for any AI coding agent building this repository. Read `PRD.md`, `ARCHITECTURE.md`, `DESIGN.md`, and `USER_FLOWS.md` before writing code.

## 1. Source of truth and scope
1. Treat these five specification files as the source of truth for the prototype.
2. Implement the smallest complete end-to-end workflow first. Prioritize a reliable, persistent, demonstrable web app over a large set of superficial screens.
3. If requirements conflict, use this priority: (1) security/authorization rules here, (2) PRD workflow and role rules, (3) architecture and data model, (4) visual/design preferences.
4. Do not silently invent legal rules, statutory validity periods, fees, required documents, or authority powers. Use clearly labelled configurable demo values and record unresolved decisions in `OPEN_QUESTIONS.md`.
5. Default certificate issue/revoke authority is an explicitly authorized LMO. Do not grant certificate powers to GATC, regulator, or admin by assumption.
6. Clearly label mocked/simulated payment, email/SMS, external integration, offline sync, and analytics. Never claim they work if they do not.

## 2. Build workflow
1. Inspect the existing repository before changing files. Preserve working code and established conventions.
2. First create/verify project structure, database models, migrations/schema, seed demo accounts, authentication, authorization, and API error handling.
3. Implement one vertical slice: login → owner instrument registration → application submission → LMO review → scheduling → inspection → authorized decision/certificate → public QR verification.
4. Then implement dashboards, reminders, search, reports, responsive polish, and remaining acceptance criteria.
5. Keep code modular but do not introduce microservices or complex infrastructure for this prototype.
6. After each milestone, run the app and relevant tests. Fix errors before moving forward.
7. Maintain `README.md` with setup, environment variables, migrations/seed instructions, demo credentials, run/test commands, implemented vs simulated vs planned feature status.

## 3. Mandatory security rules
- Enforce authentication, role permissions, jurisdiction/assignment rules, and record ownership in backend endpoints/services. Hiding buttons in the frontend is not security.
- Never trust `user_id`, `role`, `owner_id`, `issuer_id`, or jurisdiction supplied by the client. Derive identity and privileges from the authenticated server-side session/token and database.
- Do not allow self-service role escalation. Privileged roles require admin assignment/seeded demo provisioning.
- Hash passwords using a suitable password-hashing library if local password auth is implemented. Never store plaintext passwords.
- Keep secrets in environment variables; provide `.env.example` without real secrets. Do not commit tokens, private keys, real personal data, or production credentials.
- Validate all inputs and uploaded files server-side. Restrict upload size and allowed MIME/extensions; use generated storage names; prevent path traversal. Do not expose private file paths or attachments through public certificate pages.
- Use parameterized SQL/ORM. Avoid unsafe HTML rendering and open redirects.
- Public certificate verification is read-only and exposes only explicitly approved fields.
- Audit events are created server-side for sensitive transitions. Users must not be able to edit/delete them through normal APIs.
- Return generic authentication errors and safe validation messages; never expose stack traces, SQL, secrets, or internal file paths to clients.

## 4. Workflow invariants
- Application state changes must follow allowed transitions, enforced server-side.
- Correction requests and rejections require a reason.
- Inspection result is distinct from application status.
- A failed or incomplete inspection must not generate a valid certificate.
- Certificate issue requires passing inspection and authorized approval.
- Certificate revoke/supersede requires an authorized actor and a reason.
- Certificate status is evaluated server-side at lookup time. Revoked/superseded status takes precedence over date-derived validity; otherwise valid-until determines expired vs valid.
- QR contains a verification URL/token, not a self-contained claim that cannot be checked against current server state.
- Prevent conflicting appointment slots for the same assigned officer/centre according to the prototype's defined time-slot rule.
- Every important status/assignment/inspection/certificate transition produces an audit event.
- An owner may only access their own instruments, applications, appointments, attachments, and certificates unless an explicitly authorized staff role has access.

## 5. UX rules
- Use the same navigation, terminology, status labels, date formats, form patterns, and visual tokens across roles.
- Include loading, empty, success, validation, server-error, and access-denied states.
- Never leave buttons inert. If a feature is not implemented, disable it with an explanatory label or mark it as planned.
- Use realistic synthetic demo data, never real personal data. Clearly mark demo data where appropriate.
- Ensure responsive desktop/mobile layouts, accessible labels, keyboard focus, and readable contrast.
- Do not use fake dashboard metrics that disagree with database records unless explicitly labelled as static demo illustrations.

## 6. Engineering rules
- Use React + Tailwind CSS frontend, Python + FastAPI backend, PostgreSQL database, JWT/session authentication with RBAC, and server-side QR verification.
- Prefer a modular monolith with clear modules for auth, users, instruments, applications, scheduling, inspections, certificates, notifications, reporting, and audit.
- Keep API contracts and data types consistent between frontend/backend. Avoid duplicating business rules in the UI.
- Use migrations/schema versioning and deterministic seed data.
- Write automated tests for role permissions, ownership, status transitions, certificate rules, QR status, and appointment conflicts.
- Use UTC internally for timestamps and render user-facing dates consistently; document timezone assumptions for appointments.
- Avoid adding Redis, MongoDB, blockchain, Kubernetes, native mobile app, AI scoring, payment gateway, or third-party services unless the user explicitly asks and the core workflow is stable.

## 7. Definition of done
A feature is done only when it works end-to-end, persists expected data, enforces permissions on the backend, handles error/empty states, is responsive where applicable, has tests for critical logic, and is documented as implemented. Never mark planned or mocked behavior as complete.
