import pytest
from datetime import date, datetime, timedelta
from app.models.standards import (
    Standard, StandardType, StandardStatus,
    EnforcementCase, EnforcementCaseType, EnforcementCaseStatus,
    RepairRecord,
)
from app.services.standards import (
    create_standard,
    get_overdue_standards,
    create_repair_record,
    create_enforcement_case,
    add_enforcement_action,
)
from app.core.errors import ForbiddenError, ConflictError


class TestStandardsRegistry:
    def test_create_standard_by_admin(self, db, admin_user):
        std = create_standard(
            db,
            actor=admin_user,
            standard_code="STD-WT-001",
            name="10 kg F1 Stainless Steel Weight",
            standard_type=StandardType.REFERENCE_WEIGHT,
            nominal_value="10",
            unit="kg",
            accuracy_class="Class F1",
            calibration_date=date.today() - timedelta(days=60),
            calibration_due_date=date.today() + timedelta(days=305),
        )
        assert std.id is not None
        assert std.standard_code == "STD-WT-001"
        assert std.status == StandardStatus.ACTIVE

    def test_duplicate_standard_code_rejected(self, db, admin_user):
        create_standard(
            db,
            actor=admin_user,
            standard_code="STD-DUP-01",
            name="Standard 1",
            standard_type=StandardType.REFERENCE_WEIGHT,
            nominal_value="5",
            unit="kg",
        )
        with pytest.raises(ConflictError):
            create_standard(
                db,
                actor=admin_user,
                standard_code="STD-DUP-01",
                name="Standard 2",
                standard_type=StandardType.REFERENCE_WEIGHT,
                nominal_value="5",
                unit="kg",
            )

    def test_overdue_standards_tracking(self, db, admin_user):
        # Create an expiring standard (due in 5 days)
        create_standard(
            db,
            actor=admin_user,
            standard_code="STD-EXP-01",
            name="Expiring Test Standard",
            standard_type=StandardType.REFERENCE_WEIGHT,
            nominal_value="1",
            unit="kg",
            calibration_due_date=date.today() + timedelta(days=5),
        )
        overdue_list = get_overdue_standards(db)
        assert any(s.standard_code == "STD-EXP-01" for s in overdue_list)


class TestRepairAndEnforcement:
    def test_repair_with_seal_break_flags_reverification(self, db, lmo_user, test_instrument):
        repair = create_repair_record(
            db,
            actor=lmo_user,
            instrument_id=test_instrument.id,
            repair_type="load_cell_replacement",
            description="Replaced faulty strain gauge sensor and reset physical seals",
            old_seal_number="SEAL-OLD-110",
            new_seal_number="SEAL-NEW-220",
            seal_broken_reason="Maintenance after error spike",
            requires_reverification=True,
        )
        assert repair.id is not None
        assert repair.requires_reverification is True
        db.refresh(test_instrument)
        # Instrument status must be flagged as under_verification
        assert test_instrument.status == "under_verification"

    def test_create_enforcement_case_and_action(self, db, lmo_user, test_instrument):
        case = create_enforcement_case(
            db,
            actor=lmo_user,
            case_type=EnforcementCaseType.CONSUMER_COMPLAINT,
            title="Short measure reported by consumer at petrol pump",
            description="Consumer complaint filed regarding Dispenser No 3 dispensing 950ml per 1L",
            instrument_id=test_instrument.id,
            assigned_officer_id=lmo_user.id,
        )
        assert case.id is not None
        assert case.case_type == EnforcementCaseType.CONSUMER_COMPLAINT
        assert case.status == EnforcementCaseStatus.OPEN

        action = add_enforcement_action(
            db,
            actor=lmo_user,
            case_id=case.id,
            action_type="notice_issued",
            title="Show Cause Notice under Section 30",
            description="Notice issued to dealer to present dispenser for mandatory re-check",
        )
        assert action.id is not None
        assert action.case_id == case.id
