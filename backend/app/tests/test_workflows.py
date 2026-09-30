import pytest
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, VerificationType, ApplicationStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.models.attachment import Attachment
from app.core.security import get_password_hash
from app.services.application import (
    create_application,
    submit_application,
    review_application,
    schedule_application,
    transition_application_status,
)
from app.services.inspection import create_inspection, finalize_inspection
from app.services.certificate import issue_certificate, revoke_certificate
from app.services.instrument import create_instrument, get_instrument_history
from app.core.errors import ValidationError, ForbiddenError, NotFoundError, ConflictError


@pytest.fixture
def test_owner(db: Session) -> User:
    user = User(
        email="test_owner@test.com",
        hashed_password=get_password_hash("test1234"),
        full_name="Test Owner",
        role=UserRole.OWNER,
        organization="Test Org",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_lmo(db: Session) -> User:
    user = User(
        email="test_lmo@test.com",
        hashed_password=get_password_hash("test1234"),
        full_name="Test LMO",
        role=UserRole.LMO,
        jurisdiction="Test Zone",
        organization="Legal Metrology Dept - Test",
        can_issue_certificate=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_gatc(db: Session) -> User:
    user = User(
        email="test_gatc@test.com",
        hashed_password=get_password_hash("test1234"),
        full_name="Test GATC",
        role=UserRole.GATC,
        organization="GATC - Test Centre",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@pytest.fixture
def test_instrument(db: Session, test_owner: User) -> Instrument:
    instrument = Instrument(
        owner_id=test_owner.id,
        category=InstrumentCategory.WEIGHING_NON_AUTOMATIC,
        instrument_type="Platform Scale",
        manufacturer="Test Mfg",
        model="Test Model",
        serial_number="TEST-001",
        capacity="100",
        unit="kg",
        location="Test Location",
    )
    db.add(instrument)
    db.commit()
    db.refresh(instrument)
    return instrument


@pytest.fixture
def test_application(db: Session, test_owner: User, test_instrument: Instrument, test_lmo: User) -> Application:
    app = Application(
        instrument_id=test_instrument.id,
        applicant_id=test_owner.id,
        verification_type=VerificationType.INITIAL,
        jurisdiction="Test Zone",
        status=ApplicationStatus.DRAFT,
        assigned_officer_id=test_lmo.id,
    )
    db.add(app)
    db.commit()
    db.refresh(app)
    return app


class TestApplicationWorkflow:
    def test_owner_can_create_application(self, db: Session, test_owner: User, test_instrument: Instrument):
        app = create_application(db, test_owner, test_instrument.id, VerificationType.INITIAL, "Test Zone")
        assert app.id is not None
        assert app.status == ApplicationStatus.DRAFT
        assert app.instrument_id == test_instrument.id

    def test_owner_cannot_create_application_for_other_owner(self, db: Session, test_owner: User, test_lmo: User):
        instrument = Instrument(
            owner_id=test_lmo.id,
            category=InstrumentCategory.WEIGHING_NON_AUTOMATIC,
            instrument_type="Test",
            manufacturer="Test",
            model="Test",
            serial_number="TEST-002",
        )
        db.add(instrument)
        db.commit()
        db.refresh(instrument)

        with pytest.raises(ForbiddenError):
            create_application(db, test_owner, instrument.id, VerificationType.INITIAL)

    def test_duplicate_active_application_prevented(self, db: Session, test_owner: User, test_instrument: Instrument, test_lmo: User):
        # Create and submit first application to make it active
        app1 = create_application(db, test_owner, test_instrument.id, VerificationType.INITIAL, "Test Zone")
        
        # Add attachment
        attachment = Attachment(
            application_id=app1.id,
            filename="test.pdf",
            media_type="application/pdf",
            storage_key="test.pdf",
            uploader_id=test_owner.id,
        )
        db.add(attachment)
        db.commit()
        
        # Submit first application
        submit_application(db, app1.id, test_owner)
        
        # Try to create second application for same instrument
        with pytest.raises(ConflictError):
            create_application(db, test_owner, test_instrument.id, VerificationType.INITIAL, "Test Zone")

    def test_application_submit_requires_attachment(self, db: Session, test_owner: User, test_application: Application):
        # Submit without attachment should fail
        with pytest.raises(ValidationError, match="attachment"):
            submit_application(db, test_application.id, test_owner)
        
        # Add attachment
        attachment = Attachment(
            application_id=test_application.id,
            filename="test.pdf",
            media_type="application/pdf",
            storage_key="test.pdf",
            uploader_id=test_owner.id,
        )
        db.add(attachment)
        db.commit()
        
        # Now submit should work
        submitted = submit_application(db, test_application.id, test_owner)
        assert submitted.status == ApplicationStatus.SUBMITTED

    def test_status_transitions_valid(self, db: Session, test_owner: User, test_application: Application):
        # DRAFT -> SUBMITTED
        transition_application_status(db, test_application, ApplicationStatus.SUBMITTED, test_owner)
        assert test_application.status == ApplicationStatus.SUBMITTED

        # SUBMITTED -> UNDER_REVIEW
        transition_application_status(db, test_application, ApplicationStatus.UNDER_REVIEW, test_owner)
        assert test_application.status == ApplicationStatus.UNDER_REVIEW

    def test_invalid_status_transition_rejected(self, db: Session, test_owner: User, test_application: Application):
        # Cannot go from DRAFT directly to COMPLETED
        with pytest.raises(ValidationError):
            transition_application_status(db, test_application, ApplicationStatus.COMPLETED, test_owner)


class TestInspectionWorkflow:
    def test_create_draft_inspection(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.SCHEDULED
        db.commit()

        inspection = create_inspection(
            db, test_lmo, test_application.id, None,
            InspectionResult.PASS, "Test observations", is_finalized=False
        )
        assert inspection.is_finalized is False
        assert test_application.status == ApplicationStatus.SCHEDULED

    def test_finalize_inspection_requires_observations(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.SCHEDULED
        db.commit()

        inspection = create_inspection(
            db, test_lmo, test_application.id, None,
            InspectionResult.PASS, "", is_finalized=False
        )

        with pytest.raises(ValidationError, match="Observations are required"):
            finalize_inspection(db, inspection.id, test_lmo)

    def test_finalize_fail_requires_condition_notes(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.SCHEDULED
        db.commit()

        inspection = create_inspection(
            db, test_lmo, test_application.id, None,
            InspectionResult.FAIL, "Failed test", is_finalized=False
        )

        with pytest.raises(ValidationError, match="Condition notes"):
            finalize_inspection(db, inspection.id, test_lmo)

    def test_finalize_pass_sets_application_to_inspection_recorded(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.SCHEDULED
        db.commit()

        inspection = create_inspection(
            db, test_lmo, test_application.id, None,
            InspectionResult.PASS, "Passed all tests", "All good", is_finalized=False
        )

        finalized = finalize_inspection(db, inspection.id, test_lmo)
        assert finalized.is_finalized is True
        assert finalized.result == InspectionResult.PASS
        db.refresh(test_application)
        assert test_application.status == ApplicationStatus.INSPECTION_RECORDED

    def test_unassigned_inspector_cannot_create_inspection(self, db: Session, test_gatc: User, test_application: Application):
        test_application.status = ApplicationStatus.SCHEDULED
        test_application.assigned_officer_id = None
        db.commit()

        with pytest.raises(ForbiddenError):
            create_inspection(db, test_gatc, test_application.id, None, InspectionResult.PASS, "Test")


class TestCertificateIssuance:
    def test_certificate_issuance_requires_finalized_pass_inspection(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        with pytest.raises(ValidationError, match="finalized passing inspection"):
            issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))

    def test_certificate_issuance_rejected_for_fail_inspection(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.FAIL,
            observations="Failed",
            condition_notes="Failed",
            is_finalized=True,
        )
        db.add(inspection)
        db.commit()

        with pytest.raises(ValidationError, match="inspection result is fail"):
            issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))

    def test_certificate_issuance_rejected_for_needs_followup(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.NEEDS_FOLLOW_UP,
            observations="Needs followup",
            condition_notes="Needs followup",
            is_finalized=True,
        )
        db.add(inspection)
        db.commit()

        with pytest.raises(ValidationError, match="inspection result is needs_follow_up"):
            issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))

    def test_certificate_issuance_rejected_for_draft_inspection(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Passed",
            is_finalized=False,
        )
        db.add(inspection)
        db.commit()

        with pytest.raises(ValidationError, match="finalized passing inspection"):
            issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))

    def test_successful_certificate_issuance(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="All tests passed",
            condition_notes="Good condition",
            is_finalized=True,
        )
        db.add(inspection)
        db.commit()

        cert = issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))
        assert cert.status == CertificateStatus.VALID
        assert cert.issuer_id == test_lmo.id
        db.refresh(test_application)
        assert test_application.status == ApplicationStatus.COMPLETED

    def test_duplicate_certificate_issuance_prevented(self, db: Session, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Passed",
            condition_notes="Good",
            is_finalized=True,
        )
        db.add(inspection)
        db.commit()

        # Issue first certificate
        issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))
        
        # Reset application status to DECISION_PENDING for second attempt
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        with pytest.raises(ValidationError, match="certificate already exists"):
            issue_certificate(db, test_lmo, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))

    def test_unauthorized_user_cannot_issue_certificate(self, db: Session, test_owner: User, test_lmo: User, test_application: Application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        inspection = Inspection(
            application_id=test_application.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Passed",
            condition_notes="Good",
            is_finalized=True,
        )
        db.add(inspection)
        db.commit()

        with pytest.raises(ForbiddenError, match="authorized LMOs"):
            issue_certificate(db, test_owner, test_application.id, datetime.utcnow(), datetime.utcnow() + timedelta(days=365))


class TestAuthorization:
    def test_owner_cannot_access_other_owner_application(self, db: Session, test_owner: User, test_lmo: User, test_instrument: Instrument):
        other_instrument = Instrument(
            owner_id=test_lmo.id,
            category=InstrumentCategory.WEIGHING_NON_AUTOMATIC,
            instrument_type="Test",
            manufacturer="Test",
            model="Test",
            serial_number="TEST-003",
        )
        db.add(other_instrument)
        db.commit()
        db.refresh(other_instrument)

        app = Application(
            instrument_id=other_instrument.id,
            applicant_id=test_lmo.id,
            verification_type=VerificationType.INITIAL,
            status=ApplicationStatus.SUBMITTED,
        )
        db.add(app)
        db.commit()
        db.refresh(app)

        from app.services.application import get_application
        with pytest.raises(ForbiddenError):
            get_application(db, app.id, test_owner)

    def test_lmo_cannot_access_unassigned_application(self, db: Session, test_lmo: User, test_application: Application):
        test_application.assigned_officer_id = None
        db.commit()

        from app.services.application import get_application
        with pytest.raises(ForbiddenError):
            get_application(db, test_application.id, test_lmo)


class TestInstrumentHistory:
    def test_instrument_history_includes_all_events(self, db: Session, test_owner: User, test_instrument: Instrument, test_lmo: User):
        # Create application
        app = Application(
            instrument_id=test_instrument.id,
            applicant_id=test_owner.id,
            verification_type=VerificationType.INITIAL,
            status=ApplicationStatus.COMPLETED,
            assigned_officer_id=test_lmo.id,
        )
        db.add(app)
        db.commit()

        # Create inspection
        insp = Inspection(
            application_id=app.id,
            inspector_id=test_lmo.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Test",
            is_finalized=True,
        )
        db.add(insp)
        db.commit()

        # Create certificate
        cert = Certificate(
            application_id=app.id,
            instrument_id=test_instrument.id,
            certificate_number="LM-TEST-001",
            verification_token="test-token",
            issue_date=datetime.utcnow(),
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=365),
            status=CertificateStatus.VALID,
            issuer_id=test_lmo.id,
        )
        db.add(cert)
        db.commit()

        history = get_instrument_history(db, test_instrument.id, test_owner)
        assert history["instrument"].id == test_instrument.id
        assert len(history["applications"]) == 1
        assert len(history["inspections"]) == 1
        assert len(history["certificates"]) == 1
        assert len(history["timeline"]) > 0