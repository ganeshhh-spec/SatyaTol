import csv
import io
from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from app.models.certificate import Certificate
from app.models.application import Application
from app.models.instrument import Instrument
from app.models.inspection import Inspection
from app.models.user import User
from app.models.standards import Standard, EnforcementCase, RepairRecord


def generate_certificate_pdf(certificate: Certificate) -> bytes:
    """Generate a PDF for a single certificate."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=20*mm, bottomMargin=20*mm)
    styles = getSampleStyleSheet()
    story = []

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle', parent=styles['Title'],
        fontSize=18, spaceAfter=6, alignment=TA_CENTER,
        textColor=colors.HexColor('#1e3a5f')
    )
    subtitle_style = ParagraphStyle(
        'CustomSubtitle', parent=styles['Normal'],
        fontSize=12, spaceAfter=4, alignment=TA_CENTER,
        textColor=colors.HexColor('#374151')
    )
    header_style = ParagraphStyle(
        'TableHeader', parent=styles['Normal'],
        fontSize=10, textColor=colors.white, alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    cell_style = ParagraphStyle(
        'TableCell', parent=styles['Normal'],
        fontSize=9, textColor=colors.black, alignment=TA_LEFT
    )
    cell_style_center = ParagraphStyle(
        'TableCellCenter', parent=cell_style,
        alignment=TA_CENTER
    )

    # Title
    story.append(Paragraph("GOVERNMENT OF INDIA", title_style))
    story.append(Paragraph("MINISTRY OF CONSUMER AFFAIRS", subtitle_style))
    story.append(Paragraph("LEGAL METROLOGY DEPARTMENT", subtitle_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph("VERIFICATION CERTIFICATE", title_style))
    story.append(Spacer(1, 12))

    # Certificate details table
    data = [
        [Paragraph("Field", header_style), Paragraph("Details", header_style)],
        [Paragraph("Certificate Number:", cell_style), Paragraph(certificate.certificate_number, cell_style)],
        [Paragraph("Verification Token:", cell_style), Paragraph(certificate.verification_token[:16] + "...", cell_style)],
        [Paragraph("Issue Date:", cell_style), Paragraph(certificate.issue_date.strftime("%d-%m-%Y"), cell_style)],
        [Paragraph("Valid From:", cell_style), Paragraph(certificate.valid_from.strftime("%d-%m-%Y"), cell_style)],
        [Paragraph("Valid Until:", cell_style), Paragraph(certificate.valid_until.strftime("%d-%m-%Y"), cell_style)],
        [Paragraph("Status:", cell_style), Paragraph(certificate.status.value.upper(), cell_style)],
    ]

    # Instrument details
    if certificate.instrument:
        data.extend([
            [Paragraph("Instrument Category:", cell_style), Paragraph(certificate.instrument.category.value.replace('_', ' ').title() if certificate.instrument.category else "N/A", cell_style)],
            [Paragraph("Manufacturer:", cell_style), Paragraph(certificate.instrument.manufacturer or "N/A", cell_style)],
            [Paragraph("Model:", cell_style), Paragraph(certificate.instrument.model or "N/A", cell_style)],
            [Paragraph("Serial Number:", cell_style), Paragraph(certificate.instrument.serial_number or "N/A", cell_style)],
            [Paragraph("Capacity/Range:", cell_style), Paragraph(f"{certificate.instrument.capacity or ''} {certificate.instrument.unit or ''}".strip(), cell_style)],
        ])

    # Issuer details
    if certificate.issuer:
        data.extend([
            [Paragraph("Issued By:", cell_style), Paragraph(certificate.issuer.full_name or "N/A", cell_style)],
            [Paragraph("Issuing Office:", cell_style), Paragraph(certificate.issuer.organization or "N/A", cell_style)],
        ])

    table = Table(data, colWidths=[60*mm, 110*mm])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a5f')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fafc')),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f1f5f9')]),
    ]))
    story.append(table)

    story.append(Spacer(1, 20))

    # QR Code placeholder and disclaimer
    disclaimer_style = ParagraphStyle(
        'Disclaimer', parent=styles['Normal'],
        fontSize=8, textColor=colors.HexColor('#6b7280'), alignment=TA_CENTER
    )
    story.append(Paragraph("SCAN QR CODE TO VERIFY ONLINE", disclaimer_style))
    story.append(Spacer(1, 4))
    story.append(Paragraph(f"https://verify.satya-tol.gov.in/{certificate.verification_token}", disclaimer_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph("This is a system-generated certificate. No signature required.", disclaimer_style))
    story.append(Paragraph(f"Generated on {datetime.utcnow().strftime('%d-%m-%Y %H:%M:%S')} UTC", disclaimer_style))

    # Prototype disclaimer
    story.append(Spacer(1, 20))
    prototype_style = ParagraphStyle(
        'Prototype', parent=styles['Normal'],
        fontSize=9, textColor=colors.HexColor('#f59e0b'), alignment=TA_CENTER,
        backColor=colors.HexColor('#fffbeb'), borderWidth=1, borderColor=colors.HexColor('#f59e0b'),
        borderPadding=6, borderRadius=4
    )
    story.append(Paragraph("⚠ PROTOTYPE SYSTEM — NOT AN OFFICIAL LEGAL METROLOGY CERTIFICATE", prototype_style))
    story.append(Paragraph("PS-26036 / SIH26036 Demonstration System — No Legal Validity", prototype_style))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()


def generate_certificate_csv(certificates: List[Certificate]) -> str:
    """Generate CSV export for certificates."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Certificate Number', 'Verification Token', 'Issue Date', 'Valid From', 
        'Valid Until', 'Status', 'Instrument Category', 'Manufacturer', 'Model', 
        'Serial Number', 'Capacity', 'Unit', 'Issuer Name', 'Issuer Organization',
        'Application ID', 'Instrument ID'
    ])
    
    for cert in certificates:
        writer.writerow([
            cert.certificate_number,
            cert.verification_token,
            cert.issue_date.strftime("%Y-%m-%d"),
            cert.valid_from.strftime("%Y-%m-%d"),
            cert.valid_until.strftime("%Y-%m-%d"),
            cert.status.value,
            cert.instrument.category.value if cert.instrument and cert.instrument.category else "N/A",
            cert.instrument.manufacturer if cert.instrument else "N/A",
            cert.instrument.model if cert.instrument else "N/A",
            cert.instrument.serial_number if cert.instrument else "N/A",
            cert.instrument.capacity if cert.instrument else "N/A",
            cert.instrument.unit if cert.instrument else "N/A",
            cert.issuer.full_name if cert.issuer else "N/A",
            cert.issuer.organization if cert.issuer else "N/A",
            cert.application_id,
            cert.instrument_id,
        ])
    
    return output.getvalue()


def generate_applications_csv(applications: List[Application]) -> str:
    """Generate CSV export for applications."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Application ID', 'Verification Type', 'Status', 'Instrument Category',
        'Manufacturer', 'Model', 'Serial Number', 'Applicant Name', 'Applicant Email',
        'Jurisdiction', 'Assigned Officer', 'Assigned Centre', 'Submitted At',
        'Fee Amount', 'Fee Paid'
    ])
    
    for app in applications:
        writer.writerow([
            app.id,
            app.verification_type.value if app.verification_type else "N/A",
            app.status.value if app.status else "N/A",
            app.instrument.category.value if app.instrument and app.instrument.category else "N/A",
            app.instrument.manufacturer if app.instrument else "N/A",
            app.instrument.model if app.instrument else "N/A",
            app.instrument.serial_number if app.instrument else "N/A",
            app.applicant.full_name if app.applicant else "N/A",
            app.applicant.email if app.applicant else "N/A",
            app.jurisdiction or "N/A",
            app.assigned_officer.full_name if app.assigned_officer else "N/A",
            app.assigned_centre.full_name if app.assigned_centre else "N/A",
            app.submitted_at.strftime("%Y-%m-%d %H:%M") if app.submitted_at else "N/A",
            app.fee_amount or 0,
            "Yes" if app.fee_paid else "No",
        ])
    
    return output.getvalue()


def generate_inspections_csv(inspections: List[Inspection]) -> str:
    """Generate CSV export for inspections."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Inspection ID', 'Application ID', 'Inspector Name', 'Inspector Email',
        'Inspection Date', 'Result', 'Observations', 'Checklist', 'Condition Notes',
        'Is Finalized', 'Appointment ID'
    ])
    
    for insp in inspections:
        writer.writerow([
            insp.id,
            insp.application_id,
            insp.inspector.full_name if insp.inspector else "N/A",
            insp.inspector.email if insp.inspector else "N/A",
            insp.inspection_date.strftime("%Y-%m-%d %H:%M") if insp.inspection_date else "N/A",
            insp.result.value if insp.result else "N/A",
            insp.observations or "N/A",
            insp.checklist or "N/A",
            insp.condition_notes or "N/A",
            "Yes" if insp.is_finalized else "No",
            insp.appointment_id or "N/A",
        ])
    
    return output.getvalue()


def generate_instruments_csv(instruments: List[Instrument]) -> str:
    """Generate CSV export for instruments."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Instrument ID', 'Owner Name', 'Owner Email', 'Category', 'Type',
        'Manufacturer', 'Model', 'Serial Number', 'Capacity', 'Unit',
        'Location', 'Use Context', 'Registration Date', 'Status'
    ])
    
    for inst in instruments:
        writer.writerow([
            inst.id,
            inst.owner.full_name if inst.owner else "N/A",
            inst.owner.email if inst.owner else "N/A",
            inst.category.value if inst.category else "N/A",
            inst.instrument_type or "N/A",
            inst.manufacturer or "N/A",
            inst.model or "N/A",
            inst.serial_number or "N/A",
            inst.capacity or "N/A",
            inst.unit or "N/A",
            inst.location or "N/A",
            inst.use_context or "N/A",
            inst.registration_date.strftime("%Y-%m-%d") if inst.registration_date else "N/A",
            inst.status.value if inst.status else "N/A",
        ])
    
    return output.getvalue()


def generate_standards_csv(standards: List['Standard']) -> str:
    """Generate CSV export for standards."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Standard ID', 'Standard Code', 'Name', 'Type', 'Nominal Value', 'Unit',
        'Accuracy Class', 'Manufacturer', 'Serial Number', 'Calibration Date',
        'Calibration Due Date', 'Calibration Status', 'Owner', 'Custodian',
        'Location', 'Status'
    ])
    
    for std in standards:
        writer.writerow([
            std.id,
            std.standard_code,
            std.name,
            std.standard_type.value if std.standard_type else "N/A",
            std.nominal_value,
            std.unit,
            std.accuracy_class or "N/A",
            std.manufacturer or "N/A",
            std.serial_number or "N/A",
            std.calibration_date.strftime("%Y-%m-%d") if std.calibration_date else "N/A",
            std.calibration_due_date.strftime("%Y-%m-%d") if std.calibration_due_date else "N/A",
            std.calibration_status.value if std.calibration_status else "N/A",
            std.owner.full_name if std.owner else "N/A",
            std.custodian.full_name if std.custodian else "N/A",
            std.location or "N/A",
            std.status.value if std.status else "N/A",
        ])
    
    return output.getvalue()


def generate_enforcement_cases_csv(cases: List['EnforcementCase']) -> str:
    """Generate CSV export for enforcement cases."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Case ID', 'Case Number', 'Case Type', 'Title', 'Status',
        'Complainant', 'Respondent', 'Instrument', 'Jurisdiction',
        'Assigned Officer', 'Opened At', 'Closed At', 'Target Resolution',
        'Outcome', 'Penalty Amount', 'Penalty Paid'
    ])
    
    for case in cases:
        writer.writerow([
            case.id,
            case.case_number,
            case.case_type.value if case.case_type else "N/A",
            case.title,
            case.status.value if case.status else "N/A",
            case.complainant.full_name if case.complainant else "N/A",
            case.respondent.full_name if case.respondent else "N/A",
            f"{case.instrument.manufacturer} {case.instrument.model} ({case.instrument.serial_number})" if case.instrument else "N/A",
            case.jurisdiction or "N/A",
            case.assigned_officer.full_name if case.assigned_officer else "N/A",
            case.opened_at.strftime("%Y-%m-%d %H:%M") if case.opened_at else "N/A",
            case.closed_at.strftime("%Y-%m-%d %H:%M") if case.closed_at else "N/A",
            case.target_resolution_date.strftime("%Y-%m-%d") if case.target_resolution_date else "N/A",
            case.outcome or "N/A",
            case.penalty_amount or 0,
            "Yes" if case.penalty_paid else "No",
        ])
    
    return output.getvalue()


def generate_repair_records_csv(repairs: List['RepairRecord']) -> str:
    """Generate CSV export for repair records."""
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Repair ID', 'Instrument', 'Repair Type', 'Description', 'Performed By',
        'Repairer License', 'Repair Date', 'Next Due Date', 'Old Seal', 'New Seal',
        'Seal Broken Reason', 'Requires Re-verification', 'Re-verification App ID',
        'Cost', 'Approved By', 'Work Order', 'Invoice', 'Status'
    ])
    
    for repair in repairs:
        writer.writerow([
            repair.id,
            f"{repair.instrument.manufacturer} {repair.instrument.model} ({repair.instrument.serial_number})" if repair.instrument else "N/A",
            repair.repair_type,
            repair.description,
            repair.performed_by or "N/A",
            repair.repairer_license or "N/A",
            repair.repair_date.strftime("%Y-%m-%d") if repair.repair_date else "N/A",
            repair.next_due_date.strftime("%Y-%m-%d") if repair.next_due_date else "N/A",
            repair.old_seal_number or "N/A",
            repair.new_seal_number or "N/A",
            repair.seal_broken_reason or "N/A",
            "Yes" if repair.requires_reverification else "No",
            repair.re_verification_application_id or "N/A",
            repair.cost or 0,
            repair.approver.full_name if repair.approver else "N/A",
            repair.work_order_number or "N/A",
            repair.invoice_number or "N/A",
            repair.status,
        ])
    
    return output.getvalue()