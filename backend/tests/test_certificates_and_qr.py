import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.models.application import Application, ApplicationStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.services.certificate import (
    issue_certificate,
    revoke_certificate,
    supersede_certificate,
    calculate_certificate_status,
)
from app.core.errors import ValidationError, ForbiddenError


class TestCertificateIssuanceRules:
    @pytest.fixture
    def app_with_pass_inspection(self, db, test_application, lmo_user):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        insp = Inspection(
            application_id=test_application.id,
            inspector_id=lmo_user.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Complete pass across all test points",
            is_finalized=True,
        )
        db.add(insp)
        db.commit()
        return test_application

    @pytest.fixture
    def app_with_fail_inspection(self, db, test_application, lmo_user):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        insp = Inspection(
            application_id=test_application.id,
            inspector_id=lmo_user.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.FAIL,
            observations="MPE exceeded by 0.5%",
            condition_notes="Load cell damaged",
            is_finalized=True,
        )
        db.add(insp)
        db.commit()
        return test_application

    def test_successful_issuance(self, db, lmo_user, app_with_pass_inspection):
        valid_from = datetime.utcnow()
        valid_until = datetime.utcnow() + timedelta(days=365)

        cert = issue_certificate(
            db,
            issuer=lmo_user,
            application_id=app_with_pass_inspection.id,
            valid_from=valid_from,
            valid_until=valid_until,
        )
        assert cert.id is not None
        assert cert.status == CertificateStatus.VALID
        assert cert.verification_token is not None
        assert cert.certificate_number is not None

    def test_block_issuance_for_fail_inspection(self, db, lmo_user, app_with_fail_inspection):
        with pytest.raises(ValidationError) as exc:
            issue_certificate(
                db,
                issuer=lmo_user,
                application_id=app_with_fail_inspection.id,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=365),
            )
        assert "fail" in str(exc.value).lower()

    def test_block_duplicate_issuance(self, db, lmo_user, app_with_pass_inspection):
        valid_from = datetime.utcnow()
        valid_until = datetime.utcnow() + timedelta(days=365)

        issue_certificate(
            db,
            issuer=lmo_user,
            application_id=app_with_pass_inspection.id,
            valid_from=valid_from,
            valid_until=valid_until,
        )

        # Attempting second issuance must fail
        with pytest.raises(ValidationError):
            issue_certificate(
                db,
                issuer=lmo_user,
                application_id=app_with_pass_inspection.id,
                valid_from=valid_from,
                valid_until=valid_until,
            )

    def test_block_unauthorized_user_issuance(self, db, owner1_user, app_with_pass_inspection):
        with pytest.raises(ForbiddenError):
            issue_certificate(
                db,
                issuer=owner1_user,
                application_id=app_with_pass_inspection.id,
                valid_from=datetime.utcnow(),
                valid_until=datetime.utcnow() + timedelta(days=365),
            )


class TestPublicVerificationAndRevocation:
    @pytest.fixture
    def issued_certificate(self, db, lmo_user, test_application):
        test_application.status = ApplicationStatus.DECISION_PENDING
        db.commit()

        insp = Inspection(
            application_id=test_application.id,
            inspector_id=lmo_user.id,
            inspection_date=datetime.utcnow(),
            result=InspectionResult.PASS,
            observations="Pass",
            is_finalized=True,
        )
        db.add(insp)
        db.commit()

        cert = issue_certificate(
            db,
            issuer=lmo_user,
            application_id=test_application.id,
            valid_from=datetime.utcnow(),
            valid_until=datetime.utcnow() + timedelta(days=365),
        )
        return cert

    def test_public_qr_verification_valid_certificate(self, client, issued_certificate):
        response = client.get(
            f"/api/v1/certificates/public/verify/{issued_certificate.verification_token}"
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["certificate_number"] == issued_certificate.certificate_number
        assert data["status"] == "valid"

    def test_revocation_lifecycle(self, client, db, lmo_headers, lmo_user, issued_certificate):
        # Revoke via API
        response = client.post(
            f"/api/v1/certificates/{issued_certificate.id}/revoke",
            headers=lmo_headers,
            json={"reason": "Seal broken during random field check"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "revoked"
        assert data["revocation_reason"] == "Seal broken during random field check"

        # Public verification must immediately reflect REVOKED status
        public_resp = client.get(
            f"/api/v1/certificates/public/verify/{issued_certificate.verification_token}"
        )
        assert public_resp.status_code == status.HTTP_200_OK
        pub_data = public_resp.json()
        assert pub_data["status"] == "revoked"

    def test_expired_certificate_status_calculation(self, issued_certificate):
        issued_certificate.valid_until = datetime.utcnow() - timedelta(days=1)
        status_calc = calculate_certificate_status(issued_certificate)
        assert status_calc == CertificateStatus.EXPIRED
