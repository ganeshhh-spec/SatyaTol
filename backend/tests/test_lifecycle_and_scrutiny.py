import pytest
from datetime import datetime, timedelta
from fastapi import status
from app.models.user import User
from app.models.instrument import Instrument, InstrumentCategory, InstrumentStatus
from app.models.application import Application, VerificationType, ApplicationStatus
from app.models.attachment import Attachment
from app.models.appointment import Appointment, AppointmentStatus
from app.services.application import (
    create_application,
    submit_application,
    review_application,
    schedule_application,
)
from app.core.errors import ValidationError, ForbiddenError, ConflictError


class TestInstrumentAndApplicationLifecycle:
    def test_instrument_registration(self, client, owner1_headers):
        response = client.post(
            "/api/v1/instruments",
            headers=owner1_headers,
            json={
                "serial_number": "SCALE-REG-001",
                "category": "weighing_non_automatic",
                "instrument_type": "Electronic Balance",
                "model": "Precision Model X",
                "manufacturer": "Standard Scales Co.",
                "capacity": "150.0",
                "unit": "kg",
            },
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["serial_number"] == "SCALE-REG-001"
        assert data["status"] == "registered"

    def test_duplicate_active_application_prevented(self, db, owner1_user, test_instrument, test_application):
        # test_application already exists in active SUBMITTED status
        with pytest.raises(ConflictError):
            create_application(
                db,
                applicant=owner1_user,
                instrument_id=test_instrument.id,
                verification_type=VerificationType.INITIAL,
            )

    def test_submit_requires_attachment(self, db, owner1_user, test_instrument):
        # Create a fresh draft application with no attachments
        draft_app = Application(
            instrument_id=test_instrument.id,
            applicant_id=owner1_user.id,
            verification_type=VerificationType.INITIAL,
            status=ApplicationStatus.DRAFT,
        )
        db.add(draft_app)
        db.commit()
        db.refresh(draft_app)

        with pytest.raises(ValidationError) as exc:
            submit_application(db, draft_app.id, owner1_user)
        assert "attachment" in str(exc.value).lower()


class TestScrutinyAndScheduling:
    def test_scrutiny_request_correction(self, client, db, lmo_headers, test_application):
        test_application.status = ApplicationStatus.UNDER_REVIEW
        db.commit()

        response = client.post(
            f"/api/v1/applications/{test_application.id}/review",
            headers=lmo_headers,
            json={"action": "request_correction", "reason": "Invoice copy is unreadable"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "correction_requested"

    def test_scrutiny_rejection_requires_reason(self, client, db, lmo_headers, test_application):
        test_application.status = ApplicationStatus.UNDER_REVIEW
        db.commit()

        response = client.post(
            f"/api/v1/applications/{test_application.id}/review",
            headers=lmo_headers,
            json={"action": "reject", "reason": ""},
        )
        # Empty reason must be rejected with 422
        assert response.status_code in [status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST]

    def test_scrutiny_approval_flow(self, client, db, lmo_headers, test_application):
        test_application.status = ApplicationStatus.UNDER_REVIEW
        db.commit()

        response = client.post(
            f"/api/v1/applications/{test_application.id}/review",
            headers=lmo_headers,
            json={"action": "approve", "reason": "Documents verified and complete"},
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "approved_for_scheduling"

    def test_scheduling_flow(self, client, db, lmo_headers, lmo_user, test_application):
        # Move to approved_for_scheduling first
        test_application.status = ApplicationStatus.APPROVED_FOR_SCHEDULING
        db.commit()

        start = (datetime.utcnow() + timedelta(days=2)).isoformat()
        end = (datetime.utcnow() + timedelta(days=2, hours=2)).isoformat()

        response = client.post(
            f"/api/v1/applications/{test_application.id}/schedule",
            headers=lmo_headers,
            json={
                "assigned_officer_id": lmo_user.id,
                "assigned_centre_id": None,
                "scheduled_start": start,
                "scheduled_end": end,
                "location": "Central Market Stall 45",
                "mode": "field",
            },
        )
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "scheduled"
