from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_, desc
from datetime import datetime, timedelta, date
from app.models.user import User, UserRole
from app.models.instrument import Instrument, InstrumentStatus
from app.models.application import Application, ApplicationStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.models.standards import Standard, EnforcementCase, RepairRecord
from app.services.certificate import calculate_certificate_status
from app.services.notification import check_and_create_expiry_reminders
from app.schemas.dashboard import (
    OwnerDashboardStats,
    LMODashboardStats,
    GATCDashboardStats,
    RegulatorDashboardStats,
    AdminDashboardStats,
    DashboardResponse,
    TrendDataPoint,
    WorkloadDistribution,
)
from app.models.user import User, UserRole
from app.models.instrument import Instrument, InstrumentStatus
from app.models.application import Application, ApplicationStatus
from app.models.appointment import Appointment, AppointmentStatus
from app.models.inspection import Inspection, InspectionResult
from app.models.certificate import Certificate, CertificateStatus
from app.models.standards import Standard, EnforcementCase, RepairRecord
from app.services.certificate import calculate_certificate_status
from app.services.notification import check_and_create_expiry_reminders
from app.schemas.dashboard import (
    OwnerDashboardStats,
    LMODashboardStats,
    GATCDashboardStats,
    RegulatorDashboardStats,
    AdminDashboardStats,
    DashboardResponse,
    TrendDataPoint,
    WorkloadDistribution,
)


def get_owner_dashboard(db: Session, user: User) -> OwnerDashboardStats:
    check_and_create_expiry_reminders(db)

    total_instruments = db.query(Instrument).filter(Instrument.owner_id == user.id).count()
    
    # Instruments by status
    instruments_by_status = {}
    for status in InstrumentStatus:
        count = db.query(Instrument).filter(
            Instrument.owner_id == user.id,
            Instrument.status == status
        ).count()
        if count > 0:
            instruments_by_status[status.value] = count

    active_applications = db.query(Application).filter(
        Application.applicant_id == user.id,
        Application.status.in_([
            ApplicationStatus.SUBMITTED,
            ApplicationStatus.UNDER_REVIEW,
            ApplicationStatus.CORRECTION_REQUESTED,
            ApplicationStatus.RESUBMITTED,
            ApplicationStatus.APPROVED_FOR_SCHEDULING,
            ApplicationStatus.SCHEDULED,
            ApplicationStatus.INSPECTION_IN_PROGRESS,
            ApplicationStatus.INSPECTION_RECORDED,
            ApplicationStatus.DECISION_PENDING,
        ]),
    ).count()
    
    # Applications by status
    applications_by_status = {}
    for status in ApplicationStatus:
        count = db.query(Application).filter(
            Application.applicant_id == user.id,
            Application.status == status
        ).count()
        if count > 0:
            applications_by_status[status.value] = count

    upcoming_appointments = db.query(Appointment).join(Application).filter(
        Application.applicant_id == user.id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.IN_PROGRESS]),
    ).count()

    certs = db.query(Certificate).join(Application).filter(Application.applicant_id == user.id).all()
    active_certificates = 0
    expiring_soon = 0
    expiring_7_days = 0
    expired_certificates = 0
    now = datetime.utcnow()
    for cert in certs:
        status = calculate_certificate_status(cert)
        if status == CertificateStatus.VALID:
            active_certificates += 1
            days_until_expiry = (cert.valid_until - now).days
            if days_until_expiry <= 7:
                expiring_7_days += 1
            elif days_until_expiry <= 30:
                expiring_soon += 1
        elif status == CertificateStatus.EXPIRED:
            expired_certificates += 1

    # Monthly application trend (last 6 months)
    application_trend = []
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = db.query(Application).filter(
            Application.applicant_id == user.id,
            Application.created_at >= month_start,
            Application.created_at <= month_end
        ).count()
        application_trend.append(TrendDataPoint(
            label=month_start.strftime("%b %Y"),
            value=count,
            date=month_start
        ))

    return OwnerDashboardStats(
        total_instruments=total_instruments,
        instruments_by_status=instruments_by_status,
        active_applications=active_applications,
        applications_by_status=applications_by_status,
        upcoming_appointments=upcoming_appointments,
        active_certificates=active_certificates,
        expiring_soon=expiring_soon,
        expiring_7_days=expiring_7_days,
        expired_certificates=expired_certificates,
        application_trend=application_trend,
    )


def get_lmo_dashboard(db: Session, user: User) -> LMODashboardStats:
    base_query = db.query(Application).filter(Application.assigned_officer_id == user.id)
    if user.jurisdiction:
        base_query = base_query.filter(Application.jurisdiction == user.jurisdiction)

    pending_reviews = base_query.filter(
        Application.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.RESUBMITTED]),
    ).count()
    
    appointment_query = db.query(Appointment).filter(Appointment.assigned_officer_id == user.id)
    if user.jurisdiction:
        appointment_query = appointment_query.join(Application).filter(Application.jurisdiction == user.jurisdiction)
    scheduled_inspections = appointment_query.filter(
        Appointment.status == AppointmentStatus.SCHEDULED,
    ).count()
    in_progress_inspections = appointment_query.filter(
        Appointment.status == AppointmentStatus.IN_PROGRESS,
    ).count()
    
    decision_pending = base_query.filter(
        Application.status == ApplicationStatus.DECISION_PENDING,
    ).count()
    recently_completed = base_query.filter(
        Application.status == ApplicationStatus.COMPLETED,
    ).count()

    # Applications by status
    applications_by_status = {}
    for status in ApplicationStatus:
        count = base_query.filter(Application.status == status).count()
        if count > 0:
            applications_by_status[status.value] = count

    # Monthly inspection completion trend (last 6 months)
    inspection_trend = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = db.query(Inspection).join(Application).filter(
            Application.assigned_officer_id == user.id,
            Inspection.inspection_date >= month_start,
            Inspection.inspection_date <= month_end,
            Inspection.is_finalized == True
        ).count()
        inspection_trend.append(TrendDataPoint(
            label=month_start.strftime("%b %Y"),
            value=count,
            date=month_start
        ))

    # Inspection results distribution
    inspection_results = {}
    for result in InspectionResult:
        count = db.query(Inspection).join(Application).filter(
            Application.assigned_officer_id == user.id,
            Inspection.result == result,
            Inspection.is_finalized == True
        ).count()
        if count > 0:
            inspection_results[result.value] = count

    return LMODashboardStats(
        pending_reviews=pending_reviews,
        scheduled_inspections=scheduled_inspections,
        in_progress_inspections=in_progress_inspections,
        decision_pending=decision_pending,
        recently_completed=recently_completed,
        applications_by_status=applications_by_status,
        inspection_trend=inspection_trend,
        inspection_results=inspection_results,
    )


def get_gatc_dashboard(db: Session, user: User) -> GATCDashboardStats:
    assigned_applications = db.query(Application).filter(
        Application.assigned_centre_id == user.id,
    ).count()
    upcoming_slots = db.query(Appointment).filter(
        Appointment.assigned_centre_id == user.id,
        Appointment.status.in_([AppointmentStatus.SCHEDULED, AppointmentStatus.IN_PROGRESS]),
    ).count()
    pending_test_records = db.query(Inspection).join(Application).filter(
        Application.assigned_centre_id == user.id,
        Inspection.is_finalized == False,
    ).count()

    # Applications by status
    applications_by_status = {}
    for status in ApplicationStatus:
        count = db.query(Application).filter(
            Application.assigned_centre_id == user.id,
            Application.status == status
        ).count()
        if count > 0:
            applications_by_status[status.value] = count

    # Slots by status
    slots_by_status = {}
    for status in AppointmentStatus:
        count = db.query(Appointment).filter(
            Appointment.assigned_centre_id == user.id,
            Appointment.status == status
        ).count()
        if count > 0:
            slots_by_status[status.value] = count

    # Monthly bench test completion trend
    test_trend = []
    now = datetime.utcnow()
    for i in range(5, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = db.query(Inspection).join(Application).filter(
            Application.assigned_centre_id == user.id,
            Inspection.inspection_date >= month_start,
            Inspection.inspection_date <= month_end,
            Inspection.is_finalized == True
        ).count()
        test_trend.append(TrendDataPoint(
            label=month_start.strftime("%b %Y"),
            value=count,
            date=month_start
        ))

    # Test results distribution
    test_results = {}
    for result in InspectionResult:
        count = db.query(Inspection).join(Application).filter(
            Application.assigned_centre_id == user.id,
            Inspection.result == result,
            Inspection.is_finalized == True
        ).count()
        if count > 0:
            test_results[result.value] = count

    return GATCDashboardStats(
        assigned_applications=assigned_applications,
        upcoming_slots=upcoming_slots,
        pending_test_records=pending_test_records,
        applications_by_status=applications_by_status,
        slots_by_status=slots_by_status,
        test_trend=test_trend,
        test_results=test_results,
    )


def get_regulator_dashboard(db: Session, user: User) -> RegulatorDashboardStats:
    pending_by_stage = {}
    for status in ApplicationStatus:
        count = db.query(Application).filter(Application.status == status).count()
        if count > 0:
            pending_by_stage[status.value] = count

    workload_by_office = {}
    lmos = db.query(User).filter(User.role == UserRole.LMO, User.is_active == True).all()
    for lmo in lmos:
        count = db.query(Application).filter(
            Application.assigned_officer_id == lmo.id,
            Application.status.in_([
                ApplicationStatus.SUBMITTED,
                ApplicationStatus.UNDER_REVIEW,
                ApplicationStatus.SCHEDULED,
                ApplicationStatus.INSPECTION_IN_PROGRESS,
                ApplicationStatus.DECISION_PENDING,
            ]),
        ).count()
        if count > 0:
            workload_by_office[lmo.full_name] = count

    # Workload distribution for charting
    workload_distribution = [
        WorkloadDistribution(officer=name, count=count)
        for name, count in workload_by_office.items()
    ]

    from datetime import datetime
    now = datetime.utcnow()
    expiry_summaries = {
        "expired": 0,
        "expiring_30_days": 0,
        "expiring_7_days": 0,
        "valid": 0,
    }
    certs = db.query(Certificate).filter(
        Certificate.status.in_([CertificateStatus.VALID, CertificateStatus.EXPIRED])
    ).all()
    for cert in certs:
        status = calculate_certificate_status(cert)
        if status == CertificateStatus.EXPIRED:
            expiry_summaries["expired"] += 1
        elif status == CertificateStatus.VALID:
            expiry_summaries["valid"] += 1
            if cert.valid_until - now <= timedelta(days=7):
                expiry_summaries["expiring_7_days"] += 1
            elif cert.valid_until - now <= timedelta(days=30):
                expiry_summaries["expiring_30_days"] += 1

    # Certificate status distribution
    cert_status_distribution = {}
    for status in CertificateStatus:
        count = db.query(Certificate).filter(Certificate.status == status).count()
        if count > 0:
            cert_status_distribution[status.value] = count

    # Monthly application trend (all)
    application_trend = []
    now = datetime.utcnow()
    for i in range(11, -1, -1):
        month_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        count = db.query(Application).filter(
            Application.created_at >= month_start,
            Application.created_at <= month_end
        ).count()
        application_trend.append(TrendDataPoint(
            label=month_start.strftime("%b %Y"),
            value=count,
            date=month_start
        ))

    # Enforcement cases summary
    enforcement_summary = {
        "open": db.query(EnforcementCase).filter(EnforcementCase.status == EnforcementCaseStatus.OPEN).count(),
        "under_investigation": db.query(EnforcementCase).filter(EnforcementCase.status == EnforcementCaseStatus.UNDER_INVESTIGATION).count(),
        "decided": db.query(EnforcementCase).filter(EnforcementCase.status == EnforcementCaseStatus.DECIDED).count(),
        "closed": db.query(EnforcementCase).filter(EnforcementCase.status == EnforcementCaseStatus.CLOSED).count(),
    }

    # Standards calibration status
    standards_calibration = {
        "active": db.query(Standard).filter(Standard.calibration_status == StandardStatus.ACTIVE).count(),
        "expiring_30": db.query(Standard).filter(
            Standard.calibration_due_date <= date.today() + timedelta(days=30),
            Standard.calibration_due_date >= date.today(),
            Standard.calibration_status == StandardStatus.ACTIVE
        ).count(),
        "expired": db.query(Standard).filter(Standard.calibration_status == StandardStatus.EXPIRED).count(),
    }

    return RegulatorDashboardStats(
        pending_by_stage=pending_by_stage,
        workload_by_office=workload_by_office,
        workload_distribution=workload_distribution,
        expiry_summaries=expiry_summaries,
        cert_status_distribution=cert_status_distribution,
        application_trend=application_trend,
        enforcement_summary=enforcement_summary,
        standards_calibration=standards_calibration,
    )


def get_admin_dashboard(db: Session, user: User) -> AdminDashboardStats:
    active_users = db.query(User).filter(User.is_active == True).count()
    total_users = db.query(User).count()
    inactive_users = total_users - active_users

    role_distribution = {}
    for role in UserRole:
        count = db.query(User).filter(User.role == role).count()
        if count > 0:
            role_distribution[role.value] = count

    centre_configuration = db.query(User).filter(User.role == UserRole.GATC).count()

    # System health metrics
    total_instruments = db.query(Instrument).count()
    total_applications = db.query(Application).count()
    total_certificates = db.query(Certificate).count()
    total_inspections = db.query(Inspection).count()
    total_standards = db.query(Standard).count()
    total_enforcement_cases = db.query(EnforcementCase).count()
    total_repair_records = db.query(RepairRecord).count()

    # Audit events (last 24 hours)
    from datetime import datetime, timedelta
    yesterday = datetime.utcnow() - timedelta(days=1)
    recent_audit_events = db.query(AuditEvent).filter(AuditEvent.timestamp >= yesterday).count()

    # Pending actions
    pending_reviews = db.query(Application).filter(
        Application.status.in_([ApplicationStatus.SUBMITTED, ApplicationStatus.RESUBMITTED])
    ).count()
    pending_inspections = db.query(Inspection).filter(Inspection.is_finalized == False).count()
    overdue_standards = db.query(Standard).filter(
        Standard.calibration_due_date < date.today(),
        Standard.calibration_status.in_([StandardStatus.ACTIVE, StandardStatus.EXPIRED])
    ).count()

    return AdminDashboardStats(
        active_users=active_users,
        inactive_users=inactive_users,
        total_users=total_users,
        role_distribution=role_distribution,
        centre_configuration=centre_configuration,
        total_instruments=total_instruments,
        total_applications=total_applications,
        total_certificates=total_certificates,
        total_inspections=total_inspections,
        total_standards=total_standards,
        total_enforcement_cases=total_enforcement_cases,
        total_repair_records=total_repair_records,
        recent_audit_events=recent_audit_events,
        pending_reviews=pending_reviews,
        pending_inspections=pending_inspections,
        overdue_standards=overdue_standards,
    )


def get_dashboard(db: Session, user: User) -> DashboardResponse:
    response = DashboardResponse()

    if user.role == UserRole.OWNER:
        response.owner = get_owner_dashboard(db, user)
    elif user.role == UserRole.LMO:
        response.lmo = get_lmo_dashboard(db, user)
    elif user.role == UserRole.GATC:
        response.gatc = get_gatc_dashboard(db, user)
    elif user.role == UserRole.REGULATOR:
        response.regulator = get_regulator_dashboard(db, user)
    elif user.role == UserRole.ADMIN:
        response.admin = get_admin_dashboard(db, user)

    return response