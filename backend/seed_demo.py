#!/usr/bin/env python3
"""
Demo data seeding script for PS-26036 Legal Metrology Prototype.
Run with: python seed_demo.py
"""
import os
import sys
from datetime import datetime, timedelta
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.session import Base
from app.models.user import User, UserRole
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, VerificationType, ApplicationStatus
from app.models.attachment import Attachment
from app.models.appointment import Appointment, AppointmentStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.models.audit import AuditEvent
from app.models.notification import Notification, NotificationType
from app.models.requirement import VerificationRequirement, ChecklistTemplate, ChecklistItem, RequirementSourceType


def create_demo_requirements(db):
    requirements_data = [
        {
            "instrument_category": "weighing_non_automatic",
            "requirement_code": "WNA-01",
            "title": "Maximum Permissible Error (MPE) Verification",
            "description": "Verify that the instrument's indication error does not exceed the maximum permissible error for its accuracy class.",
            "source_type": RequirementSourceType.GENERAL_RULES,
            "source_reference": "Legal Metrology (General) Rules, 2011",
            "source_section": "Rule 15, Schedule II",
            "jurisdiction": "All India",
            "is_mandatory": True,
            "is_verified": True,
        },
        {
            "instrument_category": "weighing_non_automatic",
            "requirement_code": "WNA-02",
            "title": "Zero Setting Test",
            "description": "Verify that the zero indication is within the permissible limits when the load receptor is empty.",
            "source_type": RequirementSourceType.GENERAL_RULES,
            "source_reference": "Legal Metrology (General) Rules, 2011",
            "source_section": "Rule 15, Schedule II",
            "jurisdiction": "All India",
            "is_mandatory": True,
            "is_verified": True,
        },
        {
            "instrument_category": "weighing_automatic",
            "requirement_code": "WA-01",
            "title": "Weighbridge Span Test",
            "description": "Verify weighbridge accuracy across the full weighing range using certified test weights.",
            "source_type": RequirementSourceType.GENERAL_RULES,
            "source_reference": "Legal Metrology (General) Rules, 2011",
            "source_section": "Rule 16, Schedule III",
            "jurisdiction": "All India",
            "is_mandatory": True,
            "is_verified": True,
        },
        {
            "instrument_category": "measuring_length",
            "requirement_code": "ML-01",
            "title": "Length Standard Verification",
            "description": "Verify measuring tape/steel rule against a calibrated reference standard.",
            "source_type": RequirementSourceType.GENERAL_RULES,
            "source_reference": "Legal Metrology (General) Rules, 2011",
            "source_section": "Rule 17, Schedule IV",
            "jurisdiction": "All India",
            "is_mandatory": True,
            "is_verified": True,
        },
        {
            "instrument_category": "measuring_volume",
            "requirement_code": "MV-01",
            "title": "Fuel Dispenser Volume Test",
            "description": "Verify fuel dispenser delivers correct volume at various flow rates using calibrated measures.",
            "source_type": RequirementSourceType.GENERAL_RULES,
            "source_reference": "Legal Metrology (General) Rules, 2011",
            "source_section": "Rule 18, Schedule V",
            "jurisdiction": "All India",
            "is_mandatory": True,
            "is_verified": True,
        },
    ]

    for data in requirements_data:
        existing = db.query(VerificationRequirement).filter(
            VerificationRequirement.instrument_category == data["instrument_category"],
            VerificationRequirement.requirement_code == data["requirement_code"]
        ).first()
        if not existing:
            req = VerificationRequirement(**data)
            db.add(req)
    db.commit()


def create_demo_checklist_templates(db):
    # Get requirement IDs for referencing
    reqs = db.query(VerificationRequirement).all()
    req_map = {f"{r.instrument_category}-{r.requirement_code}": r.id for r in reqs}

    templates_data = [
        {
            "instrument_category": "weighing_non_automatic",
            "name": "Non-Automatic Weighing Instrument Checklist",
            "description": "Standard checklist for verifying non-automatic weighing instruments (platform scales, bench scales, etc.)",
            "version": "1.0",
            "source_requirement_ids": ",".join(str(req_map.get(k, 0)) for k in [
                "weighing_non_automatic-WNA-01",
                "weighing_non_automatic-WNA-02",
            ]),
            "is_active": True,
            "items": [
                {"item_code": "WNA-CK-01", "title": "Visual Inspection", "description": "Check for damage, corrosion, level indicator, display readability", "is_mandatory": True, "sort_order": 1},
                {"item_code": "WNA-CK-02", "title": "Zero Setting Test", "description": "Verify zero indication with empty load receptor", "expected_result": "Zero within ±0.25e", "is_mandatory": True, "sort_order": 2},
                {"item_code": "WNA-CK-03", "title": "Eccentricity Test", "description": "Apply test load at different positions on load receptor", "expected_result": "Error within MPE", "is_mandatory": True, "sort_order": 3},
                {"item_code": "WNA-CK-04", "title": "Repeatability Test", "description": "Apply same load multiple times", "expected_result": "Difference ≤ 1e", "is_mandatory": True, "sort_order": 4},
                {"item_code": "WNA-CK-05", "title": "MPE Verification", "description": "Verify indication error at multiple load points", "expected_result": "Error within MPE for accuracy class", "is_mandatory": True, "sort_order": 5},
            ]
        },
        {
            "instrument_category": "weighing_automatic",
            "name": "Weighbridge Verification Checklist",
            "description": "Checklist for weighbridge (automatic weighing instrument) verification",
            "version": "1.0",
            "source_requirement_ids": ",".join(str(req_map.get(k, 0)) for k in [
                "weighing_automatic-WA-01",
            ]),
            "is_active": True,
            "items": [
                {"item_code": "WA-CK-01", "title": "Visual Inspection", "description": "Check platform, joints, drainage, display", "is_mandatory": True, "sort_order": 1},
                {"item_code": "WA-CK-02", "title": "Zero Test", "description": "Verify zero with empty platform", "expected_result": "Zero within limits", "is_mandatory": True, "sort_order": 2},
                {"item_code": "WA-CK-03", "title": "Span Test (Multiple Loads)", "description": "Apply certified weights at multiple points", "expected_result": "Error within MPE", "is_mandatory": True, "sort_order": 3},
                {"item_code": "WA-CK-04", "title": "Corner/Section Test", "description": "Test each section/corner independently", "expected_result": "Error within MPE", "is_mandatory": True, "sort_order": 4},
            ]
        },
        {
            "instrument_category": "measuring_length",
            "name": "Measuring Length Instrument Checklist",
            "description": "Checklist for steel tapes, rules, and other length measuring instruments",
            "version": "1.0",
            "source_requirement_ids": ",".join(str(req_map.get(k, 0)) for k in [
                "measuring_length-ML-01",
            ]),
            "is_active": True,
            "items": [
                {"item_code": "ML-CK-01", "title": "Visual Inspection", "description": "Check for damage, markings, graduation clarity", "is_mandatory": True, "sort_order": 1},
                {"item_code": "ML-CK-02", "title": "Length Verification", "description": "Compare against calibrated reference standard", "expected_result": "Error within tolerance class", "is_mandatory": True, "sort_order": 2},
                {"item_code": "ML-CK-03", "title": "Temperature Compensation Check", "description": "Verify markings include reference temperature", "expected_result": "Marked at 20°C", "is_mandatory": True, "sort_order": 3},
            ]
        },
        {
            "instrument_category": "measuring_volume",
            "name": "Fuel Dispenser Verification Checklist",
            "description": "Checklist for fuel dispenser (volume measuring instrument) verification",
            "version": "1.0",
            "source_requirement_ids": ",".join(str(req_map.get(k, 0)) for k in [
                "measuring_volume-MV-01",
            ]),
            "is_active": True,
            "items": [
                {"item_code": "MV-CK-01", "title": "Visual Inspection", "description": "Check display, hose, nozzle, seals, calibration marks", "is_mandatory": True, "sort_order": 1},
                {"item_code": "MV-CK-02", "title": "Volume Test (Low Flow)", "description": "Deliver at minimum flow rate into calibrated measure", "expected_result": "Error within ±0.5%", "is_mandatory": True, "sort_order": 2},
                {"item_code": "MV-CK-03", "title": "Volume Test (Normal Flow)", "description": "Deliver at normal flow rate", "expected_result": "Error within ±0.3%", "is_mandatory": True, "sort_order": 3},
                {"item_code": "MV-CK-04", "title": "Volume Test (High Flow)", "description": "Deliver at maximum flow rate", "expected_result": "Error within ±0.3%", "is_mandatory": True, "sort_order": 4},
                {"item_code": "MV-CK-05", "title": "Interlock/ Safety Tests", "description": "Verify safety interlocks and automatic cut-off", "is_mandatory": True, "sort_order": 5},
            ]
        },
    ]

    for tmpl_data in templates_data:
        items = tmpl_data.pop("items")
        existing = db.query(ChecklistTemplate).filter(
            ChecklistTemplate.instrument_category == tmpl_data["instrument_category"],
            ChecklistTemplate.name == tmpl_data["name"]
        ).first()
        if not existing:
            tmpl = ChecklistTemplate(**tmpl_data)
            db.add(tmpl)
            db.flush()
            for item_data in items:
                item = ChecklistItem(template_id=tmpl.id, **item_data)
                db.add(item)
    db.commit()


def create_demo_users(db):
    users_data = [
        {
            "email": "owner1@demo.com",
            "password": "demo1234",
            "full_name": "Rajesh Kumar",
            "role": UserRole.OWNER,
            "organization": "Kumar Weighing Solutions",
            "phone": "+91 98765 43210",
        },
        {
            "email": "owner2@demo.com",
            "password": "demo1234",
            "full_name": "Priya Sharma",
            "role": UserRole.OWNER,
            "organization": "Sharma Industries",
            "phone": "+91 98765 43211",
        },
        {
            "email": "lmo1@demo.com",
            "password": "demo1234",
            "full_name": "Inspector Arjun Singh",
            "role": UserRole.LMO,
            "jurisdiction": "North Zone",
            "organization": "Legal Metrology Dept - North",
            "can_issue_certificate": True,
        },
        {
            "email": "lmo2@demo.com",
            "password": "demo1234",
            "full_name": "Inspector Meera Patel",
            "role": UserRole.LMO,
            "jurisdiction": "South Zone",
            "organization": "Legal Metrology Dept - South",
            "can_issue_certificate": True,
        },
        {
            "email": "gatc1@demo.com",
            "password": "demo1234",
            "full_name": "GATC Central Lab",
            "role": UserRole.GATC,
            "organization": "Government Approved Test Centre - Central",
        },
        {
            "email": "regulator1@demo.com",
            "password": "demo1234",
            "full_name": "Regional Controller",
            "role": UserRole.REGULATOR,
            "organization": "Regulatory Authority",
        },
        {
            "email": "admin@demo.com",
            "password": "demo1234",
            "full_name": "Platform Administrator",
            "role": UserRole.ADMIN,
            "organization": "Platform Administration",
        },
    ]

    created_users = []
    all_users = {}
    for data in users_data:
        existing = db.query(User).filter(User.email == data["email"]).first()
        if not existing:
            user = User(
                email=data["email"],
                hashed_password=get_password_hash(data["password"]),
                full_name=data["full_name"],
                role=data["role"],
                jurisdiction=data.get("jurisdiction"),
                organization=data.get("organization"),
                phone=data.get("phone"),
                can_issue_certificate=data.get("can_issue_certificate", False),
            )
            db.add(user)
            created_users.append(user)
        else:
            all_users[existing.email] = existing
    db.commit()
    for u in created_users:
        db.refresh(u)
        all_users[u.email] = u
    return all_users


def create_demo_instruments(db, users):
    instruments_data = [
        {
            "owner": users["owner1@demo.com"],
            "category": InstrumentCategory.WEIGHING_NON_AUTOMATIC,
            "instrument_type": "Platform Scale",
            "manufacturer": "Avery Weigh-Tronix",
            "model": "ZM510",
            "serial_number": "AWT-ZM510-2024-001",
            "capacity": "500",
            "unit": "kg",
            "location": "Warehouse A, Industrial Area, Delhi",
            "use_context": "Weighing incoming raw materials",
        },
        {
            "owner": users["owner1@demo.com"],
            "category": InstrumentCategory.WEIGHING_AUTOMATIC,
            "instrument_type": "Weighbridge",
            "manufacturer": "Essae",
            "model": "WB-60T",
            "serial_number": "ESS-WB60-2024-002",
            "capacity": "60000",
            "unit": "kg",
            "location": "Main Gate, Factory Complex, Gurgaon",
            "use_context": "Weighing trucks for dispatch",
        },
        {
            "owner": users["owner2@demo.com"],
            "category": InstrumentCategory.MEASURING_LENGTH,
            "instrument_type": "Steel Tape Measure",
            "manufacturer": "Freemans",
            "model": "ProLine 5m",
            "serial_number": "FRE-PL5-2024-003",
            "capacity": "5",
            "unit": "m",
            "location": "Site Office, Construction Project, Mumbai",
            "use_context": "Measuring construction dimensions",
        },
        {
            "owner": users["owner2@demo.com"],
            "category": InstrumentCategory.MEASURING_VOLUME,
            "instrument_type": "Fuel Dispenser",
            "manufacturer": "Tokheim",
            "model": "Quantium 510",
            "serial_number": "TOK-Q510-2024-004",
            "capacity": "100",
            "unit": "litre",
            "location": "Petrol Pump, NH-48, Jaipur",
            "use_context": "Dispensing petrol/diesel to vehicles",
        },
    ]

    created_instruments = []
    all_instruments = []
    for data in instruments_data:
        owner = data.pop("owner")
        existing = db.query(Instrument).filter(
            Instrument.owner_id == owner.id,
            Instrument.serial_number == data["serial_number"]
        ).first()
        if not existing:
            inst = Instrument(owner_id=owner.id, **data)
            db.add(inst)
            created_instruments.append(inst)
        else:
            all_instruments.append(existing)
    db.commit()
    for i in created_instruments:
        db.refresh(i)
        all_instruments.append(i)
    return all_instruments


def create_demo_applications(db, users, instruments):
    apps_data = [
        {
            "instrument": instruments[0],
            "applicant": users["owner1@demo.com"],
            "verification_type": VerificationType.INITIAL,
            "jurisdiction": "North Zone",
            "status": ApplicationStatus.COMPLETED,
            "submitted_at": datetime.utcnow() - timedelta(days=30),
            "assigned_officer": users["lmo1@demo.com"],
            "fee_amount": 2000,
            "fee_paid": True,
        },
        {
            "instrument": instruments[1],
            "applicant": users["owner1@demo.com"],
            "verification_type": VerificationType.REVERIFICATION,
            "jurisdiction": "North Zone",
            "status": ApplicationStatus.DECISION_PENDING,
            "submitted_at": datetime.utcnow() - timedelta(days=10),
            "assigned_officer": users["lmo1@demo.com"],
            "fee_amount": 1500,
            "fee_paid": True,
        },
        {
            "instrument": instruments[2],
            "applicant": users["owner2@demo.com"],
            "verification_type": VerificationType.INITIAL,
            "jurisdiction": "South Zone",
            "status": ApplicationStatus.SUBMITTED,
            "submitted_at": datetime.utcnow() - timedelta(days=2),
            "fee_amount": 1000,
            "fee_paid": False,
        },
        {
            "instrument": instruments[3],
            "applicant": users["owner2@demo.com"],
            "verification_type": VerificationType.REVERIFICATION,
            "jurisdiction": "South Zone",
            "status": ApplicationStatus.UNDER_REVIEW,
            "submitted_at": datetime.utcnow() - timedelta(days=5),
            "assigned_officer": users["lmo2@demo.com"],
            "fee_amount": 1500,
            "fee_paid": True,
        },
    ]

    created_apps = []
    all_apps = []
    for data in apps_data:
        instrument = data.pop("instrument")
        applicant = data.pop("applicant")
        assigned_officer = data.pop("assigned_officer", None)

        existing = db.query(Application).filter(
            Application.instrument_id == instrument.id,
            Application.applicant_id == applicant.id,
        ).first()
        if not existing:
            app = Application(
                instrument_id=instrument.id,
                applicant_id=applicant.id,
                assigned_officer_id=assigned_officer.id if assigned_officer else None,
                **data,
            )
            db.add(app)
            created_apps.append(app)
        else:
            all_apps.append(existing)
    db.commit()
    for a in created_apps:
        db.refresh(a)
        all_apps.append(a)
    return all_apps


def create_demo_attachments(db, apps, users):
    for app in apps:
        if not app.attachments:
            att = Attachment(
                application_id=app.id,
                filename=f"doc_application_{app.id}.pdf",
                media_type="application/pdf",
                storage_key=f"demo/app_{app.id}_doc.pdf",
                uploader_id=app.applicant_id,
            )
            db.add(att)
    db.commit()


def create_demo_appointments(db, apps, users):
    now = datetime.utcnow()
    appointments_data = [
        {
            "application": apps[0],
            "assigned_officer": users["lmo1@demo.com"],
            "assigned_centre": users["gatc1@demo.com"],
            "scheduled_start": now - timedelta(days=20),
            "scheduled_end": now - timedelta(days=20, hours=-2),
            "location": "Warehouse A, Industrial Area, Delhi",
            "status": AppointmentStatus.COMPLETED,
        },
        {
            "application": apps[1],
            "assigned_officer": users["lmo1@demo.com"],
            "assigned_centre": users["gatc1@demo.com"],
            "scheduled_start": now + timedelta(days=2),
            "scheduled_end": now + timedelta(days=2, hours=2),
            "location": "Factory Complex, Gurgaon",
            "status": AppointmentStatus.SCHEDULED,
        },
        {
            "application": apps[3],
            "assigned_officer": users["lmo2@demo.com"],
            "assigned_centre": users["gatc1@demo.com"],
            "scheduled_start": now + timedelta(days=3),
            "scheduled_end": now + timedelta(days=3, hours=2),
            "location": "Petrol Pump, NH-48, Jaipur",
            "status": AppointmentStatus.SCHEDULED,
        },
    ]

    for data in appointments_data:
        app = data.pop("application")
        officer = data.pop("assigned_officer")
        centre = data.pop("assigned_centre", None)
        existing = db.query(Appointment).filter(Appointment.application_id == app.id).first()
        if not existing:
            appt = Appointment(
                application_id=app.id,
                assigned_officer_id=officer.id,
                assigned_centre_id=centre.id if centre else None,
                **data,
            )
            db.add(appt)
    db.commit()


def create_demo_inspections(db, apps, users):
    inspections_data = [
        {
            "application": apps[0],
            "inspector": users["lmo1@demo.com"],
            "inspection_date": datetime.utcnow() - timedelta(days=20),
            "result": InspectionResult.PASS,
            "observations": "Platform scale verified within permissible limits. All test weights passed. Zero setting stable. Repeatability test passed.",
            "checklist": "Zero test: PASS\nLoad test (100kg, 200kg, 500kg): PASS\nRepeatability: PASS\nEccentricity test: PASS",
            "condition_notes": "Instrument in good condition. No visible damage. Display clear.",
            "is_finalized": True,
        },
        {
            "application": apps[1],
            "inspector": users["lmo1@demo.com"],
            "inspection_date": datetime.utcnow() + timedelta(days=2),
            "result": InspectionResult.PASS,
            "observations": "Weighbridge inspection scheduled. Pending physical verification.",
            "checklist": "To be completed after inspection",
            "condition_notes": "Pending inspection",
            "is_finalized": False,
        },
    ]

    for data in inspections_data:
        app = data.pop("application")
        inspector = data.pop("inspector")
        existing = db.query(Inspection).filter(Inspection.application_id == app.id).first()
        if not existing:
            insp = Inspection(
                application_id=app.id,
                inspector_id=inspector.id,
                **data,
            )
            db.add(insp)
    db.commit()


def create_demo_certificates(db, apps, users):
    certs_data = [
        {
            "application": apps[0],
            "valid_from": datetime.utcnow() - timedelta(days=25),
            "valid_until": datetime.utcnow() + timedelta(days=340),
            "issuer": users["lmo1@demo.com"],
        },
        {
            "application": apps[1],
            "valid_from": datetime.utcnow(),
            "valid_until": datetime.utcnow() + timedelta(days=365),
            "issuer": users["lmo1@demo.com"],
        },
    ]

    for data in certs_data:
        app = data.pop("application")
        issuer = data.pop("issuer")
        existing = db.query(Certificate).filter(Certificate.application_id == app.id).first()
        if not existing:
            cert = Certificate(
                application_id=app.id,
                instrument_id=app.instrument_id,
                certificate_number=f"LM-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}",
                verification_token=uuid.uuid4().hex,
                issue_date=datetime.utcnow(),
                status=CertificateStatus.VALID,
                issuer_id=issuer.id,
                **data,
            )
            db.add(cert)
    db.commit()

    # Create an expired certificate for demo
    expired_app = apps[0]
    expired_cert = db.query(Certificate).filter(Certificate.application_id == expired_app.id).first()
    if expired_cert:
        expired_cert.valid_until = datetime.utcnow() - timedelta(days=10)
        expired_cert.status = CertificateStatus.EXPIRED
        db.commit()

    # Create a revoked certificate for demo
    revoked_cert = Certificate(
        application_id=apps[0].id,
        instrument_id=apps[0].instrument_id,
        certificate_number=f"LM-REVOKED-{uuid.uuid4().hex[:8].upper()}",
        verification_token=uuid.uuid4().hex,
        issue_date=datetime.utcnow() - timedelta(days=100),
        valid_from=datetime.utcnow() - timedelta(days=100),
        valid_until=datetime.utcnow() + timedelta(days=200),
        status=CertificateStatus.REVOKED,
        issuer_id=users["lmo1@demo.com"].id,
        revocation_reason="Instrument found non-compliant during surprise inspection",
        revoked_at=datetime.utcnow() - timedelta(days=30),
    )
    db.add(revoked_cert)

    # Create a superseded certificate for demo
    superseded_cert = Certificate(
        application_id=apps[0].id,
        instrument_id=apps[0].instrument_id,
        certificate_number=f"LM-SUPERSEDED-{uuid.uuid4().hex[:8].upper()}",
        verification_token=uuid.uuid4().hex,
        issue_date=datetime.utcnow() - timedelta(days=400),
        valid_from=datetime.utcnow() - timedelta(days=400),
        valid_until=datetime.utcnow() - timedelta(days=35),
        status=CertificateStatus.SUPERSEDED,
        issuer_id=users["lmo1@demo.com"].id,
    )
    db.add(superseded_cert)
    db.commit()

    # Link superseded
    new_cert = db.query(Certificate).filter(Certificate.application_id == apps[0].id, Certificate.status == CertificateStatus.VALID).first()
    if new_cert and superseded_cert:
        superseded_cert.superseded_by_id = new_cert.id
        db.commit()


def create_demo_audit_events(db, users):
    events = [
        {"actor": users["owner1@demo.com"], "action": "create_instrument", "entity_type": "instrument", "entity_id": 1},
        {"actor": users["owner1@demo.com"], "action": "submit_application", "entity_type": "application", "entity_id": 1},
        {"actor": users["lmo1@demo.com"], "action": "review_application", "entity_type": "application", "entity_id": 1, "new_status": "approved_for_scheduling"},
        {"actor": users["lmo1@demo.com"], "action": "schedule_appointment", "entity_type": "appointment", "entity_id": 1},
        {"actor": users["lmo1@demo.com"], "action": "create_inspection", "entity_type": "inspection", "entity_id": 1, "new_status": "pass"},
        {"actor": users["lmo1@demo.com"], "action": "issue_certificate", "entity_type": "certificate", "entity_id": 1, "new_status": "valid"},
    ]
    for evt in events:
        actor = evt.pop("actor")
        audit = AuditEvent(actor_id=actor.id, **evt)
        db.add(audit)
    db.commit()


def create_demo_notifications(db, users):
    notifications = [
        {"recipient": users["owner1@demo.com"], "type": NotificationType.CERTIFICATE_ISSUED, "title": "Certificate Issued", "message": "Certificate LM-20241015-ABC12345 has been issued for your platform scale.", "reference_type": "certificate", "reference_id": 1},
        {"recipient": users["owner2@demo.com"], "type": NotificationType.APPLICATION_SUBMITTED, "title": "Application Submitted", "message": "Your re-verification application for fuel dispenser has been submitted.", "reference_type": "application", "reference_id": 4},
        {"recipient": users["lmo1@demo.com"], "type": NotificationType.APPLICATION_SUBMITTED, "title": "New Application for Review", "message": "Application #2 assigned to you for review.", "reference_type": "application", "reference_id": 2},
    ]
    for notif in notifications:
        recipient = notif.pop("recipient")
        n = Notification(recipient_id=recipient.id, **notif)
        db.add(n)
    db.commit()


def main():
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        print("Seeding demo users...")
        users = create_demo_users(db)

        print("Seeding demo instruments...")
        instruments = create_demo_instruments(db, users)

        print("Seeding demo requirements...")
        create_demo_requirements(db)

        print("Seeding demo checklist templates...")
        create_demo_checklist_templates(db)

        print("Seeding demo applications...")
        apps = create_demo_applications(db, users, instruments)

        print("Seeding demo attachments...")
        create_demo_attachments(db, apps, users)

        print("Seeding demo appointments...")
        create_demo_appointments(db, apps, users)

        print("Seeding demo inspections...")
        create_demo_inspections(db, apps, users)

        print("Seeding demo certificates...")
        create_demo_certificates(db, apps, users)

        print("Seeding demo audit events...")
        create_demo_audit_events(db, users)

        print("Seeding demo notifications...")
        create_demo_notifications(db, users)

        print("\n[SUCCESS] Demo data seeded successfully!")
        print("\nDemo Accounts (password: demo1234):")
        for email, user in users.items():
            print(f"  {email} ({user.role.value})")

    except Exception as e:
        print(f"[ERROR] Error seeding data: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()