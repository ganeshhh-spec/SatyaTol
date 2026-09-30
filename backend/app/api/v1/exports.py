from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional, List
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.export import (
    generate_certificate_pdf, generate_certificate_csv,
    generate_applications_csv, generate_inspections_csv,
    generate_instruments_csv, generate_standards_csv,
    generate_enforcement_cases_csv, generate_repair_records_csv,
)
from app.models.certificate import Certificate
from app.models.application import Application
from app.models.inspection import Inspection
from app.models.instrument import Instrument
from app.models.standards import Standard, EnforcementCase, RepairRecord
from app.models.user import User
from app.core.errors import NotFoundError, ForbiddenError
from app.core.permissions import has_permission, Permission

router = APIRouter(tags=["exports"])


def get_certificates_for_export(db: Session, user: User, certificate_ids: Optional[List[int]] = None) -> List[Certificate]:
    query = db.query(Certificate).join(Certificate.application).join(Certificate.instrument).join(Certificate.issuer)
    
    if user.role == UserRole.OWNER:
        query = query.filter(Application.applicant_id == user.id)
    elif user.role == UserRole.LMO:
        if user.jurisdiction:
            query = query.filter(Application.jurisdiction == user.jurisdiction)
    elif user.role == UserRole.GATC:
        query = query.filter(Application.assigned_centre_id == user.id)
    # Admin/Regulator see all
    
    if certificate_ids:
        query = query.filter(Certificate.id.in_(certificate_ids))
    
    return query.all()


def get_applications_for_export(db: Session, user: User, application_ids: Optional[List[int]] = None) -> List[Application]:
    query = db.query(Application).join(Application.instrument).join(Application.applicant)
    
    if user.role == UserRole.OWNER:
        query = query.filter(Application.applicant_id == user.id)
    elif user.role == UserRole.LMO:
        if user.jurisdiction:
            query = query.filter(Application.jurisdiction == user.jurisdiction)
    elif user.role == UserRole.GATC:
        query = query.filter(Application.assigned_centre_id == user.id)
    
    if application_ids:
        query = query.filter(Application.id.in_(application_ids))
    
    return query.all()


def get_inspections_for_export(db: Session, user: User, inspection_ids: Optional[List[int]] = None) -> List[Inspection]:
    query = db.query(Inspection).join(Inspection.inspector).join(Inspection.application).join(Inspection.application.instrument)
    
    if user.role == UserRole.LMO:
        query = query.filter(Inspection.inspector_id == user.id)
        if user.jurisdiction:
            query = query.filter(Inspection.application.has(jurisdiction=user.jurisdiction))
    elif user.role == UserRole.GATC:
        query = query.filter(Inspection.inspector_id == user.id)
    
    if inspection_ids:
        query = query.filter(Inspection.id.in_(inspection_ids))
    
    return query.all()


def get_instruments_for_export(db: Session, user: User, instrument_ids: Optional[List[int]] = None) -> List[Instrument]:
    query = db.query(Instrument).join(Instrument.owner)
    
    if user.role == UserRole.OWNER:
        query = query.filter(Instrument.owner_id == user.id)
    
    if instrument_ids:
        query = query.filter(Instrument.id.in_(instrument_ids))
    
    return query.all()


def get_standards_for_export(db: Session, user: User, standard_ids: Optional[List[int]] = None):
    from app.models.standards import Standard
    query = db.query(Standard)
    
    if user.role not in [UserRole.ADMIN, UserRole.REGULATOR]:
        query = query.filter(
            or_(Standard.owner_id == user.id, Standard.custodian_id == user.id)
        )
    
    if standard_ids:
        query = query.filter(Standard.id.in_(standard_ids))
    
    return query.all()


def get_enforcement_cases_for_export(db: Session, user: User, case_ids: Optional[List[int]] = None):
    from app.models.standards import EnforcementCase
    query = db.query(EnforcementCase)
    
    if user.role == UserRole.OWNER:
        query = query.filter(
            or_(EnforcementCase.complainant_id == user.id, EnforcementCase.respondent_id == user.id)
        )
    elif user.role == UserRole.LMO:
        query = query.filter(EnforcementCase.assigned_officer_id == user.id)
    
    if case_ids:
        query = query.filter(EnforcementCase.id.in_(case_ids))
    
    return query.all()


def get_repair_records_for_export(db: Session, user: User, repair_ids: Optional[List[int]] = None):
    from app.models.standards import RepairRecord
    from app.models.instrument import Instrument
    query = db.query(RepairRecord).join(Instrument)
    
    if user.role == UserRole.OWNER:
        query = query.filter(Instrument.owner_id == user.id)
    elif user.role == UserRole.LMO:
        if user.jurisdiction:
            query = query.filter(Instrument.jurisdiction == user.jurisdiction)
    
    if repair_ids:
        query = query.filter(RepairRecord.id.in_(repair_ids))
    
    return query.all()


@router.get("/certificates/pdf")
def export_certificate_pdf(
    certificate_id: int = Query(..., description="Certificate ID to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export a single certificate as PDF."""
    try:
        certificates = get_certificates_for_export(db, current_user, [certificate_id])
        if not certificates:
            raise HTTPException(status_code=404, detail="Certificate not found or access denied")
        
        pdf_bytes = generate_certificate_pdf(certificates[0])
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="certificate_{certificates[0].certificate_number}.pdf"'}
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF generation failed: {str(e)}")


@router.get("/certificates/csv")
def export_certificates_csv(
    certificate_ids: Optional[List[int]] = Query(None, description="Certificate IDs to export (optional, exports all accessible if not provided)"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export certificates as CSV."""
    try:
        certificates = get_certificates_for_export(db, current_user, certificate_ids)
        csv_data = generate_certificate_csv(certificates)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="certificates_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/applications/csv")
def export_applications_csv(
    application_ids: Optional[List[int]] = Query(None, description="Application IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export applications as CSV."""
    try:
        applications = get_applications_for_export(db, current_user, application_ids)
        csv_data = generate_applications_csv(applications)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="applications_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/inspections/csv")
def export_inspections_csv(
    inspection_ids: Optional[List[int]] = Query(None, description="Inspection IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export inspections as CSV."""
    try:
        inspections = get_inspections_for_export(db, current_user, inspection_ids)
        csv_data = generate_inspections_csv(inspections)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="inspections_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/instruments/csv")
def export_instruments_csv(
    instrument_ids: Optional[List[int]] = Query(None, description="Instrument IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export instruments as CSV."""
    try:
        instruments = get_instruments_for_export(db, current_user, instrument_ids)
        csv_data = generate_instruments_csv(instruments)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="instruments_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/standards/csv")
def export_standards_csv(
    standard_ids: Optional[List[int]] = Query(None, description="Standard IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export standards as CSV."""
    try:
        standards = get_standards_for_export(db, current_user, standard_ids)
        csv_data = generate_standards_csv(standards)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="standards_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/enforcement/cases/csv")
def export_enforcement_cases_csv(
    case_ids: Optional[List[int]] = Query(None, description="Case IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export enforcement cases as CSV."""
    try:
        cases = get_enforcement_cases_for_export(db, current_user, case_ids)
        csv_data = generate_enforcement_cases_csv(cases)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="enforcement_cases_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


@router.get("/repairs/csv")
def export_repair_records_csv(
    repair_ids: Optional[List[int]] = Query(None, description="Repair record IDs to export"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Export repair records as CSV."""
    try:
        repairs = get_repair_records_for_export(db, current_user, repair_ids)
        csv_data = generate_repair_records_csv(repairs)
        
        return StreamingResponse(
            io.StringIO(csv_data),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="repair_records_{datetime.utcnow().strftime("%Y%m%d")}.csv"'}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"CSV generation failed: {str(e)}")


import io
from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, Query
from app.models.user import User, UserRole
from app.models.certificate import Certificate
from app.models.application import Application
from app.models.inspection import Inspection
from app.models.instrument import Instrument
from app.models.standards import Standard, EnforcementCase, RepairRecord
from sqlalchemy import or_