# Product Requirements Document (PRD)
## Online Verification System for Weighing and Measuring Instruments
**Problem statement:** SIH26036 / PS-26036 — Development of an Online Verification System for Weighing and Measuring Instruments  
**Document status:** Prototype specification; not an approved government deployment specification.

## 1. Product purpose
Build a demonstrable, secure web prototype for managing the digital lifecycle of weighing and measuring instruments: registration, verification/re-verification applications, document uploads, review, scheduling, inspection recording, authorized decision and certificate issuance, QR-based public status checking, expiry reminders, and role-based monitoring.

The system supports official work; it does not replace physical inspection, statutory judgment, stamping, or decisions by legally authorized personnel.

## 2. Evidence and assumptions
The SIH problem statement calls for stakeholder registration, online applications, scheduling/allocation, digital certificates with QR codes, digital inspection records, validity tracking, reminders, dashboards, search/retrieval, document/photo uploads, export/printing, role-based login, and mobile support for field officers. See the problem statement reference: https://sih2026.vuce.in/ps/SIH26036

Pain points such as delays, fragmented records, status uncertainty, and difficulty checking certificates are treated as problem context/hypotheses, not measured claims about every jurisdiction. Rules, fees, required documents, validity periods, and decision authority may vary by instrument category and jurisdiction and must be configurable/confirmed before real deployment.

## 3. Goals
- Demonstrate one complete end-to-end workflow with persistent data.
- Make application status and next steps visible to instrument owners.
- Keep each instrument's applications, inspections, certificates, and status history linked.
- Enforce permissions by role and ownership.
- Allow public QR/certificate-ID checking without exposing private documents or personal data.
- Provide dashboards for businesses, LMOs, GATCs, and administrators/regulators.
- Clearly distinguish implemented, simulated, and planned capabilities.

## 4. Out of scope for the prototype
- Actual legal approval, official certificate validity rules, or real stamping decisions.
- Production integration with government databases, payment gateways, SMS/email providers, Aadhaar, e-sign, or departmental identity systems unless credentials and approval are provided.
- Blockchain, microservices, advanced AI risk scoring, and a separate native mobile app as mandatory requirements.
- Claiming measured reduction in cost or processing time without pilot evidence.

## 5. User roles and permissions
### Business / Instrument Owner
Register and manage own instruments; create verification/re-verification applications; upload supporting documents/photos; view own applications and appointments; respond to correction requests; download issued certificates; receive reminders.

### Legal Metrology Officer (LMO)
View cases within assigned jurisdiction/queue; review applications; request corrections or reject with reasons; conduct/record inspection; record observations and results; issue/revoke certificates only when the account has explicit authorized permission; view instrument history and audit events relevant to their duties.

### Government Approved Test Centre (GATC)
View cases assigned to the centre; manage centre availability/slots; coordinate appointments; record centre-side test observations/results where permitted. GATC must not issue/revoke official certificates unless an explicitly configured legal authority allows it. Default prototype authority is LMO-only issuance/revocation.

### Regulator / Supervisor
View jurisdiction-level dashboards, pendency, completed cases, workload, validity/expiry summaries, and audit reports. No certificate issuance unless separately granted.

### Platform Administrator
Manage accounts, roles, jurisdiction/configuration, instrument categories, and system settings. Administrative access alone must not automatically confer authority to approve an inspection or issue a certificate.

### Public / Consumer
Search by certificate ID or scan QR to see only the minimum public certificate fields and live status (valid, expired, revoked, superseded, not found/invalid).

## 6. Core data entities
- User: id, name, email/phone, role, active status, jurisdiction/organization, timestamps.
- Instrument: id, owner_id, instrument type/category, manufacturer, model, serial number, capacity/range, unit, location, use/context, registration date, current lifecycle status.
- Application: id, instrument_id, applicant_id, verification type (initial/re-verification), submitted date, status, assigned officer/centre, jurisdiction, requested appointment, fee/payment status (prototype may be simulated), remarks.
- Attachment: id, application_id, filename, media type, storage key, uploader, timestamp; never expose private files through public endpoints.
- Appointment: id, application_id, date/time, location/mode, assigned officer/centre, status.
- Inspection: id, application_id, inspector_id, date/time, observations, result (pass/fail/needs-follow-up), instrument condition notes, photo references, checklist fields, signature/confirmation metadata where implemented.
- Certificate: id, application_id, instrument_id, certificate number, issue date, valid-from, valid-until, status, issuer_id, public verification token/URL, revocation/supersession reason.
- AuditEvent: id, actor_id, action, entity type/id, timestamp, previous/new status where applicable, reason, request metadata.
- Notification: id, recipient_id, type, message, created_at, read_at, delivery status.

## 7. Application lifecycle and status rules
Recommended application states: `draft → submitted → under_review → correction_requested → resubmitted → approved_for_scheduling → scheduled → inspection_in_progress → inspection_recorded → decision_pending → completed`.
Alternative terminal outcomes: `rejected`, `withdrawn`, `cancelled`.
Inspection result is separate from application status: `pass`, `fail`, `needs_follow_up`.
Certificate status: `valid`, `expired` (derived from dates), `revoked`, `superseded`, `not_found/invalid` (verification response, not a stored certificate status).

Only valid transitions should be accepted by the backend. A failed inspection must not produce a valid certificate. A certificate may be issued only after an authorized decision and a passing recorded inspection, unless a jurisdiction-specific workflow is later formally defined. Corrections and rejections require a reason. Every important transition creates an audit event.

## 8. Functional requirements
### FR-01 Authentication and profile
Users can sign in/out. The prototype may provide seeded demo accounts. Passwords must be hashed if local credentials are implemented. Never hardcode production secrets. Users can see their role and profile. Disabled accounts cannot sign in.

### FR-02 Stakeholder registration
Support stakeholder account/profile registration or admin-created accounts. If self-selection of privileged roles is exposed in demo, prevent it from granting privileges: privileged roles must be approved/assigned by an administrator. A user must not elevate their own role.

### FR-03 Instrument registration
Owner creates instrument record with required fields and supporting details. Serial number duplication should be detected at least within a defined scope. Owner can only view/edit their own instrument records, except authorized staff.

### FR-04 Applications and attachments
Owner submits initial verification or re-verification request for an instrument. Validate required fields and file type/size. Show submission reference and status. Prevent duplicate active applications for the same instrument and verification purpose unless explicitly allowed by a documented rule.

### FR-05 Review and correction
Authorized LMO reviews applications in their jurisdiction/assignment. Actions: request correction, reject with reason, approve for scheduling. Applicants can respond/resubmit when correction is requested. Each action is auditable.

### FR-06 Scheduling and allocation
Authorized staff assign an LMO or GATC and schedule a date/time/location or approved mode. Prevent overlapping appointments for the same assigned officer/centre within the same time slot. Show upcoming appointments and status. If slot availability is only simulated, label it as such.

### FR-07 Inspection recording
Assigned inspector records date/time, observations, checklist/result, notes, and optional photos. Enforce assignment/jurisdiction permission. Inspection data is editable only under a controlled correction process; changes are audited. Mobile-responsive layout is required. Offline sync is future scope unless explicitly implemented and tested.

### FR-08 Decision and certificate
Only explicitly authorized LMO account can issue/revoke a certificate by default. Issue requires recorded passing inspection and completed required fields. Generate a unique certificate ID and QR code pointing to a server-side public verification route. Revoke/supersede actions require reason and audit record. Certificate dates/validity configuration must be labelled prototype configuration, not universal legal rule.

### FR-09 Public certificate verification
QR and manual certificate ID lookup return current server-side status. Public view contains only approved fields, e.g., certificate ID, instrument category, manufacturer/model, masked/limited serial identifier if policy permits, issue date, valid-until, issuing authority/office, status. No owner contact, private documents, or sensitive location details. QR must not embed mutable certificate claims as the sole source of truth.

### FR-10 Lifecycle and reminders
Show upcoming expiry and overdue instruments based on configured dates. In-app notifications are sufficient for the prototype. Email/SMS integration is optional and must not be represented as active unless configured and tested. Expired status is computed from valid-until date and current date; revocation overrides date-based validity.

### FR-11 Dashboards, search, reports
Owner dashboard: instruments, active applications, appointments, certificates, reminders. LMO/GATC dashboard: assigned cases, pending review, appointments, inspections due. Regulator dashboard: aggregate counts, pendency by status, workload, expiry summaries. Admin dashboard: user/configuration overview. Search/filter by instrument ID, application ID, certificate ID, status, category, and jurisdiction according to role. Export/print reports and certificates where implemented.

### FR-12 Audit and traceability
Log submission, assignment, review decision, correction request, scheduling, inspection changes, certificate issue/revocation, and role/config changes. Audit events should be append-only through the application UI. Do not allow ordinary users to edit/delete audit records.

### FR-13 Responsive/mobile field use
Core screens must work on desktop and mobile widths. Field inspection forms must have readable labels, large touch targets, save/validation feedback, and clear connectivity/error messages. A native app or offline synchronization is not required for the initial web prototype.

## 9. Non-functional requirements
- Secure-by-default role and ownership checks on the backend, not only in the UI.
- Validate all inputs server-side; parameterized database access/ORM; upload allowlist and size limits.
- Public verification must reveal only approved fields.
- Clear loading, empty, error, success, and permission-denied states.
- Keyboard-accessible forms, labels, visible focus, sufficient contrast, responsive layout.
- Use environment variables for secrets; never commit credentials.
- Keep API errors understandable but do not leak stack traces or internal data.
- Include seed/demo data and setup instructions.
- Use one maintainable modular backend before considering microservices.

## 10. Acceptance criteria
1. Owner can register an instrument and submit an application with an attachment.
2. Another owner cannot access or modify that instrument/application by changing IDs in URLs/API calls.
3. LMO can review only permitted cases and request corrections/reject/approve for scheduling with reasons as applicable.
4. Authorized staff can assign and schedule an inspection without creating a conflicting slot for the same assignee.
5. Assigned inspector can record a pass/fail/follow-up result.
6. Failed inspection cannot generate a valid certificate.
7. Unauthorized roles cannot issue or revoke certificates even by direct API call.
8. Authorized issuance creates a certificate and QR route; public route reflects current server-side status.
9. Expired, revoked, superseded, invalid, and unknown certificate IDs display distinct outcomes.
10. Important state changes create audit events.
11. Dashboards/search reflect stored data rather than unrelated hardcoded counters, except clearly labelled demo summaries.
12. Main workflows are usable on desktop and mobile viewport sizes.

## 11. Prototype success measurement
Report only measured test results: completed workflow tests, authorization tests passed/failed, QR status cases passed/failed, and responsive checks. Processing-time or cost improvements are hypotheses until measured in a pilot.

## 12. Open decisions before real deployment
Confirm jurisdiction-specific application requirements, instrument categories, fees, validity periods, officer/centre authority, digital signature requirements, records retention, hosting/security approvals, official integrations, and legal acceptance of digital certificates. Do not invent these rules in code; make prototype settings configurable.
