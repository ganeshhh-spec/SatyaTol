import pytest
from datetime import datetime
from app.models.application import Application, ApplicationStatus
from app.models.inspection import Inspection, InspectionResult
from app.services.inspection import create_inspection, finalize_inspection
from app.core.errors import ValidationError, ForbiddenError


class TestInspectionExecutionAndRules:
    @pytest.fixture
    def scheduled_application(self, db, test_application):
        test_application.status = ApplicationStatus.SCHEDULED
        db.commit()
        db.refresh(test_application)
        return test_application

    def test_unassigned_inspector_cannot_create_inspection(
        self, db, gatc_user, scheduled_application
    ):
        with pytest.raises(ForbiddenError):
            create_inspection(
                db,
                inspector=gatc_user,
                application_id=scheduled_application.id,
                appointment_id=None,
                result=InspectionResult.PASS,
                is_finalized=False,
            )

    def test_create_draft_inspection(self, db, lmo_user, scheduled_application):
        insp = create_inspection(
            db,
            inspector=lmo_user,
            application_id=scheduled_application.id,
            appointment_id=None,
            result=InspectionResult.PASS,
            observations="Preliminary visual check OK",
            is_finalized=False,
        )
        assert insp.id is not None
        assert insp.is_finalized is False
        assert insp.observations == "Preliminary visual check OK"

    def test_finalizing_requires_observations(self, db, lmo_user, scheduled_application):
        with pytest.raises(ValidationError) as exc:
            create_inspection(
                db,
                inspector=lmo_user,
                application_id=scheduled_application.id,
                appointment_id=None,
                result=InspectionResult.PASS,
                observations="",
                is_finalized=True,
            )
        assert "observations" in str(exc.value).lower()

    def test_finalizing_fail_requires_condition_notes(self, db, lmo_user, scheduled_application):
        with pytest.raises(ValidationError) as exc:
            create_inspection(
                db,
                inspector=lmo_user,
                application_id=scheduled_application.id,
                appointment_id=None,
                result=InspectionResult.FAIL,
                observations="Max permissible error exceeded",
                condition_notes="",
                is_finalized=True,
            )
        assert "condition notes" in str(exc.value).lower()

    def test_finalizing_pass_updates_application_status(self, db, lmo_user, scheduled_application):
        insp = create_inspection(
            db,
            inspector=lmo_user,
            application_id=scheduled_application.id,
            appointment_id=None,
            result=InspectionResult.PASS,
            observations="Load test and eccentricity test passed within MPE limits",
            is_finalized=True,
        )
        assert insp.is_finalized is True
        db.refresh(scheduled_application)
        assert scheduled_application.status == ApplicationStatus.INSPECTION_RECORDED
