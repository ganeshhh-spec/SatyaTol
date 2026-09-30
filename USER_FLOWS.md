# User Flows — PS-26036 Prototype

## 1. Flow map
```text
Public landing ──> Certificate lookup/QR verification
       │
       └──> Sign in ──> Role-based dashboard
                          ├── Owner: Register instrument → Apply → Track → Appointment → Certificate
                          ├── LMO: Review → Request correction / Reject / Approve for scheduling
                          │             └── Schedule → Inspect/record result → Authorized decision → Issue/revoke
                          ├── GATC: View assigned work → Manage available slots → Record permitted test result
                          ├── Regulator: Monitor pendency/workload/expiry → Reports
                          └── Admin: Manage users/roles/configuration
```

## 2. Owner: registration and application
**Precondition:** Owner is authenticated.
1. Open “My Instruments”.
2. Select “Register Instrument”.
3. Enter instrument category/type, manufacturer, model, serial number, capacity/range, unit, location/use details, and any configured required fields.
4. Submit. Backend validates required fields and checks duplicate serial policy.
5. Open instrument detail; confirm instrument record is saved and linked to owner.
6. Select “Apply for Verification” or “Apply for Re-verification”.
7. Complete application details and upload permitted supporting documents/photos.
8. Review summary and submit.
9. System generates application reference and sets status to `submitted`; audit event and owner notification are created.
10. Owner sees current status and next-step guidance on dashboard/application detail.
**Failure states:** missing required fields, duplicate instrument, unsupported/oversized attachment, network/server error, existing active application disallowed by policy.

## 3. LMO: review and correction loop
**Precondition:** LMO is authenticated and authorized for the case/jurisdiction.
1. Open work queue and filter by `submitted`/`resubmitted`.
2. Open application and review instrument details and attachments.
3. Choose one permitted action:
   - Request correction: enter mandatory explanation; status becomes `correction_requested`; notify owner.
   - Reject: enter mandatory reason; status becomes `rejected`; notify owner.
   - Approve for scheduling: confirm required information; status becomes `approved_for_scheduling`; proceed to scheduling.
4. Record audit event with actor, action, timestamp, entity, and reason/status transition.
**Security:** an LMO cannot review cases outside authorized assignment/jurisdiction. A user cannot change the application ID in a URL/API call to bypass this.

## 4. Owner: correction and resubmission
**Precondition:** Application status is `correction_requested` and owner owns the record.
1. Open application and read correction reasons.
2. Edit permitted fields and/or upload replacement documents.
3. Submit response.
4. Backend validates and changes status to `resubmitted`; preserve previous history and create audit event.
5. Application returns to authorized review queue.
**Failure states:** owner attempts to modify a record not theirs; application is not awaiting correction; invalid upload.

## 5. Scheduling and allocation
**Precondition:** Application is `approved_for_scheduling`; scheduler has permission.
1. Open scheduling screen.
2. Select permitted LMO or GATC, date/time, location or approved mode.
3. Backend validates jurisdiction/assignment and checks assignee/centre availability for conflicts.
4. If conflict exists, reject with a clear message and preserve unsaved details where possible.
5. If valid, create appointment and set application status to `scheduled`.
6. Notify owner and assignee; add audit event.
7. Owner sees appointment details; staff see it in calendar/work queue.
**Note:** If actual availability calendars are not implemented, present slots as prototype demo scheduling and do not imply real departmental availability.

## 6. Field inspection / test record
**Precondition:** Authenticated inspector is assigned to the appointment/application.
1. Open “My Appointments” or assigned case.
2. Confirm instrument identity and application details.
3. Record inspection date/time, observations, checklist fields, condition notes, and optional photographs.
4. Select result: `pass`, `fail`, or `needs_follow_up`.
5. Review and submit inspection record.
6. Backend checks assignment and allowed status; persists inspection and audit event.
7. Application moves to `inspection_recorded` then `decision_pending` according to implementation.
8. Owner sees the allowed status summary; private internal notes may be restricted by role/policy.
**Failure states:** unassigned inspector, wrong workflow state, missing required observations, upload rejected, duplicate submit.

## 7. Authorized decision and certificate issuance
**Precondition:** Inspection is recorded; result is `pass`; actor is an explicitly authorized LMO; all configured required fields are present.
1. LMO opens decision-pending case and reviews inspection record.
2. LMO confirms issue action and configured validity dates/category-specific demo setting.
3. Backend re-checks permission and passing inspection; generates unique certificate number and verification token.
4. Certificate is stored and linked to instrument, application, inspection, and issuer.
5. Application becomes `completed`; audit event and owner notification are created.
6. Certificate detail/print view shows prototype label, dates, instrument details, QR code, and public verification URL.
**Must not happen:** GATC/admin/regulator can issue solely because of role name; failed inspection issues valid certificate; frontend-only permission checks; hardcoded universal validity period.

## 8. Certificate revocation or supersession
**Precondition:** Actor has explicit certificate management authority.
1. Open certificate detail.
2. Select revoke or supersede.
3. Enter mandatory reason and confirm.
4. Backend updates status/history and writes audit event; owner notification may be created.
5. Public QR lookup immediately reflects the changed status from the server.
6. Revoked/superseded certificate must never display as valid due only to its date range.

## 9. Public certificate lookup / QR scan
1. User scans QR or opens public “Verify Certificate” page.
2. If scanning, the QR opens the server-side verification URL/token. Manual lookup accepts certificate ID.
3. Backend looks up the certificate and calculates current status from database and dates.
4. Public page displays one of:
   - Valid: certificate record found and currently valid.
   - Expired: validity date has passed.
   - Revoked: certificate has been revoked.
   - Superseded: a newer/replacement certificate has superseded it.
   - Not found/invalid: no matching record/token; no internal details exposed.
5. Show only approved public fields and status-check time if implemented.
6. Display prototype disclaimer for demo certificates.

## 10. Expiry reminders
1. System identifies certificates approaching configured expiry window and expired certificates.
2. It creates in-app notifications without duplicate reminders for the same rule/window.
3. Owner dashboard shows expiring soon/expired instruments and links to instrument/application detail.
4. External email/SMS is shown as simulated/planned unless credentials and delivery tests exist.
5. Expiry date is based on certificate data and configurable prototype settings, not an assumed universal statutory period.

## 11. Role dashboards and reports
1. After login, route user to the dashboard appropriate to their server-side role.
2. Fetch role-scoped summary counts and recent records from API.
3. Clicking a card opens a filtered list.
4. Search/filter supports permitted instrument/application/certificate IDs, status, category, and jurisdiction.
5. Regulator sees permitted aggregate monitoring data; owner never sees other owners' records; public sees no dashboard.
6. Exports/print must use the same permission scope as the screen.

## 12. Administrator: users and configuration
1. Admin opens user management.
2. Admin creates/activates/deactivates user and assigns an approved role/jurisdiction/organization.
3. Backend verifies admin permission and prevents accidental self-escalation where appropriate.
4. Changes are audited. Admin account does not automatically receive LMO certificate-issuance permission.
5. Prototype settings may include instrument categories, demo validity duration, reminder windows, and permitted attachment types. Display a clear “Prototype configuration — verify before real use” note.

## 13. End-to-end demo script
1. Sign in as demo owner.
2. Register a synthetic weighing instrument.
3. Submit a verification application and attach a sample image/document.
4. Sign in as authorized demo LMO; review and approve for scheduling.
5. Schedule an appointment.
6. Record a passing inspection.
7. Issue a demo certificate as authorized LMO.
8. Open public QR verification and show valid status.
9. Demonstrate a separate seeded expired/revoked/invalid certificate lookup.
10. Show owner dashboard, LMO queue, audit history, and one unauthorized-action test.
11. Explicitly disclose which integrations or functions are simulated/planned.

## 14. Minimum test scenarios
- Owner A cannot access Owner B's instrument/application/attachments by changing IDs.
- Owner cannot issue/revoke certificate.
- GATC cannot issue/revoke by default.
- Admin cannot issue solely because they are admin.
- Unassigned officer cannot submit inspection.
- Failed inspection cannot issue valid certificate.
- Appointment conflict is blocked.
- Correction/rejection requires reason.
- QR status changes after revocation/supersession.
- Expired, revoked, superseded, valid, unknown IDs show distinct statuses.
- Public page never exposes private attachment URLs/contact data.
- Dashboard numbers reflect database records or are explicitly labelled demo/static.
