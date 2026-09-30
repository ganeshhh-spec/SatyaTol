# Open Questions — PS-26036 Prototype

This document records unresolved decisions and prototype-specific simplifications that must be confirmed before real deployment.

## Legal & Regulatory Questions

### 1. Certificate Validity Periods
**Question:** What are the legally mandated validity periods for each instrument category?
**Prototype Setting:** 365 days (configurable via `DEMO_CERTIFICATE_VALIDITY_DAYS`)
**Decision Needed:** Confirm per-category validity periods with legal metrology department.

### 2. Required Documents per Application Type
**Question:** What supporting documents are mandatory for initial vs re-verification applications per instrument category?
**Prototype Setting:** At least one attachment required (PDF/JPG/PNG), no category-specific rules.
**Decision Needed:** Define document checklists per category and verification type.

### 3. Fee Structure
**Question:** What are the official fees for verification/re-verification per instrument category and capacity?
**Prototype Setting:** Fee amount field exists, simulated as paid/unpaid boolean.
**Decision Needed:** Official fee schedule from department.

### 4. Certificate Issuance Authority
**Question:** Can GATC officers issue certificates under any circumstances, or only LMOs?
**Prototype Setting:** Only LMOs with `can_issue_certificate=true` can issue/revoke.
**Decision Needed:** Legal confirmation of authority delegation rules.

### 5. Digital Signature Requirements
**Question:** Are digital signatures (DSC/e-sign) required for certificate issuance or inspection records?
**Prototype Setting:** Signature metadata field exists but not enforced.
**Decision Needed:** DSC requirements for legal validity.

### 6. Inspection Checklist Standards
**Question:** What are the standardized inspection checklists per instrument category?
**Prototype Setting:** Free-text checklist field.
**Decision Needed:** Official checklist templates from department.

### 7. Revocation/Supersession Public Disclosure
**Question:** What revocation/supersession reasons can be shown publicly vs kept internal?
**Prototype Setting:** Reason shown on public verification page.
**Decision Needed:** Policy on public disclosure of revocation reasons.

### 8. Jurisdiction Boundaries
**Question:** How are jurisdiction boundaries defined and enforced for LMO assignments?
**Prototype Setting:** Simple string field "North Zone"/"South Zone".
**Decision Needed:** Official jurisdiction mapping and LMO assignment rules.

### 9. Re-verification Triggers
**Question:** What triggers mandatory re-verification (time-based, repair, modification, etc.)?
**Prototype Setting:** Owner manually selects "re-verification" type.
**Decision Needed:** Automated re-verification scheduling rules.

### 10. Data Retention & Archival
**Question:** What are the data retention periods for applications, inspections, certificates?
**Prototype Setting:** No retention policy implemented.
**Decision Needed:** Compliance with state records retention laws.

## Technical & Operational Questions

### 11. Payment Gateway Integration
**Question:** Which payment gateway(s) are approved for fee collection?
**Prototype Setting:** Simulated (fee_paid boolean).
**Decision Needed:** Integration with Bharat BillPay, UPI, or state treasury.

### 12. SMS/Email Gateway
**Question:** Which SMS/email provider for notifications (NIC, MeitY, or commercial)?
**Prototype Setting:** In-app notifications only.
**Decision Needed:** Approved communication channels and templates.

### 13. Aadhaar/e-KYC Integration
**Question:** Is Aadhaar-based identity verification required for owner registration?
**Prototype Setting:** Email/password only.
**Decision Needed:** KYC requirements for stakeholder registration.

### 14. Official Logo & Branding
**Question:** Can the system use official department logos and branding?
**Prototype Setting:** Generic "Legal Metrology" branding.
**Decision Needed:** Branding guidelines and logo usage approval.

### 15. Hosting & Security Compliance
**Question:** What are the hosting requirements (MeitY cloud, NIC, state data center) and security certifications needed?
**Prototype Setting:** Docker Compose for local development.
**Decision Needed:** Production hosting approval and security audit requirements.

### 16. Multi-language Support
**Question:** Which languages must be supported (Hindi, English, regional)?
**Prototype Setting:** English only.
**Decision Needed:** Localization requirements.

### 17. API Integration with State Systems
**Question:** Are there existing state systems (e.g., e-District, state portal) for integration?
**Prototype Setting:** Standalone prototype.
**Decision Needed:** Integration points and API specifications.

### 18. Backup & Disaster Recovery
**Question:** What are the RPO/RTO requirements and backup procedures?
**Prototype Setting:** Not implemented.
**Decision Needed:** DR plan for production deployment.

## Prototype-Specific Simplifications (Documented)

| Simplification | Location | Note |
|----------------|----------|------|
| Universal 365-day validity | `DEMO_CERTIFICATE_VALIDITY_DAYS` | Must be per-category configurable |
| Free-text checklists | Inspection model | Should use structured checklist templates |
| Single attachment required | Application submission | Should be category-specific document list |
| String-based jurisdiction | User model | Should reference jurisdiction master table |
| Simulated fee payment | `fee_paid` boolean | Needs payment gateway integration |
| In-app notifications only | Notification service | Needs SMS/email for production |
| No digital signature enforcement | `signature_metadata` field | Needs DSC integration |
| English-only UI | Frontend | Needs Hindi/regional language support |
| No data retention policy | All models | Needs compliance with state laws |

## Priority for Resolution

1. **High** (Blocks legal validity): Certificate validity periods, issuance authority, fee structure, required documents
2. **Medium** (Blocks production deployment): Payment gateway, SMS/email, hosting, security audit, data retention
3. **Low** (Enhancement): Multi-language, digital signatures, advanced checklists, API integrations

---

*Last updated: Prototype development phase*
*Review before: Production deployment approval*