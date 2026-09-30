# UX / UI Design Specification — PS-26036

## 1. Product experience
Design a clear, trustworthy public-service workflow. The user should always understand: what record they are viewing, its current status, the next action, who can take that action, and what information is missing. Use plain English and avoid claiming that a prototype certificate is an official government certificate.

## 2. Visual direction
- Style: clean civic-tech service portal, restrained and professional.
- Layout: desktop-first dashboard with responsive mobile support; left sidebar on desktop, compact top bar/menu on small screens.
- Color: neutral light background, dark readable text, one primary blue/teal accent, restrained success/warning/error colors. Do not rely on color alone to communicate status.
- Typography: legible sans-serif; clear hierarchy between page title, section title, field label, helper text, and table metadata.
- Components: consistent cards, tables, filters, form controls, badges, alerts, breadcrumbs, dialogs, pagination, empty states, and confirmation prompts.
- Use icons only with text labels where meaning might be unclear.

## 3. Global navigation
### Public
- Home / Overview
- Verify Certificate
- Sign In
- Help / Process Overview (prototype guidance)

### Owner
- Dashboard
- My Instruments
- Applications
- Appointments
- Certificates
- Notifications
- Profile

### LMO / Inspector
- Dashboard / Work Queue
- Applications to Review
- Appointments
- Inspections
- Certificates (only if authorized)
- Instrument Search

### GATC
- Dashboard
- Assigned Applications
- Centre Calendar / Slots
- Inspection / Test Records
- Instrument Search

### Regulator / Supervisor
- Overview Dashboard
- Pendency & Workload
- Expiry / Validity Monitoring
- Reports / Exports
- Audit Activity (permission-scoped)

### Platform Administrator
- Users & Roles
- Jurisdictions / Centres / Configuration
- Instrument Categories / Prototype Settings
- System Activity

Navigation must be role-specific; unauthorized pages should not appear, and direct URL/API access must also be denied.

## 4. Required screens
1. Public landing page explaining the service and linking to certificate verification and sign-in.
2. Sign-in page with validation and demo account guidance where applicable.
3. Role dashboard with database-backed summary cards, recent activity, pending tasks, and quick actions.
4. Instrument list with search, filters, status, and add instrument action.
5. Register/edit instrument form with required fields and inline validation.
6. Instrument detail page showing specifications, owner-visible status, linked applications, inspection history, certificates, and lifecycle timeline.
7. Application creation wizard: select instrument → choose verification type → enter request details → attach files → review and submit.
8. Application detail/status timeline with reference number, current status, assigned office/centre if permitted, appointment, attachments, and action history.
9. LMO review page with application details, document list, request-correction/reject/approve actions and mandatory reason fields where applicable.
10. Scheduling page with date/time, location/mode, officer/centre assignment, available-slot indication, and conflict errors.
11. Field inspection page with instrument/app details, checklist/observations, pass/fail/follow-up result, notes, optional photo upload, save/submit confirmation.
12. Decision/certificate issue page restricted to authorized LMO, displaying inspection result and confirmation step.
13. Certificate detail/print view with certificate ID, instrument details, issue/validity dates, status, issuing office/authorized issuer, QR code, and demo/prototype label where applicable.
14. Public certificate verification page with clear status banner and limited approved details; distinct states for valid, expired, revoked, superseded, invalid/unknown.
15. Notifications list and reminder details.
16. Search/report page with filters and export/print affordances if implemented.
17. User/role administration page restricted to administrator.
18. Access-denied, not-found, loading, empty, validation-error, and server-error states.

## 5. Status presentation
Use consistent text labels and badge styles:
- Application: Draft, Submitted, Under Review, Correction Required, Resubmitted, Approved for Scheduling, Scheduled, Inspection in Progress, Inspection Recorded, Decision Pending, Completed, Rejected, Withdrawn, Cancelled.
- Inspection: Pass, Fail, Needs Follow-up.
- Certificate: Valid, Expired, Revoked, Superseded, Invalid / Not Found.

Show a short explanation and next action near each status. Do not use “approved” to mean “inspection passed” unless the workflow stage is explicit.

## 6. Forms and validation
- Mark required fields visibly and use inline error messages near fields.
- Preserve entered values after validation failures where safe.
- Show allowed file types and size limit before upload.
- Ask for a reason for correction requests, rejection, revocation, and supersession.
- Confirm irreversible/high-impact actions before submission.
- Show a success screen with application/certificate reference after successful action.
- Avoid one giant form; group instrument identity, application details, appointment details, and inspection result.

## 7. Dashboard design
Cards should reflect API/database counts, with links to filtered lists. Owner cards: instruments, active applications, upcoming appointments, active certificates, expiring soon. LMO cards: pending reviews, scheduled inspections, decision pending, recently completed. GATC cards: assigned applications, upcoming slots, pending test records. Regulator cards: pending by stage, workload by office/centre, expiry summaries. Admin cards: active users, role/centre configuration. If data is seeded/static, label the display “Demo data”.

## 8. Public verification page
- Display a prominent status banner and status text, not just a green tick.
- Display verification timestamp (“Status checked at …”) if feasible.
- Show only approved certificate fields; never show owner contact details, private attachments, or precise private addresses.
- If revoked/superseded/expired, explain that the status differs and display only an authorized reason if configured for public disclosure.
- Unknown certificate: state “Certificate not found” without exposing database details.
- Include a note that the prototype's demo certificate is not an official certificate.

## 9. Responsive and accessibility requirements
- Support narrow mobile screens without horizontal overflow for primary flows.
- Use semantic headings, labelled inputs, keyboard navigation, visible focus, descriptive button labels, accessible validation feedback, and sufficient contrast.
- Tables may transform to stacked cards on mobile; preserve labels and actions.
- Touch targets should be comfortable for field use. Inspection form should be usable one-handed where practical.

## 10. Interaction requirements
- Every visible action must work, or be explicitly disabled/labelled “Planned”.
- Use loading indicators for requests and prevent duplicate submits while requests are pending.
- Use confirmation dialogs for issue/revoke/supersede and destructive administrative actions.
- Use toast/inline feedback for success and failure; important workflow outcomes must also be visible in page content.
- Keep filters and pagination predictable; provide “Clear filters”.

## 11. Demo presentation
Use synthetic names, organizations, instruments, dates, and certificate IDs. Do not use real citizen/business data or official logos unless permission exists. Any generated sample certificate must visibly state “Prototype / Demo — Not an official legal metrology certificate”.
