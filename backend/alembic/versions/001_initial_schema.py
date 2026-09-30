"""initial_schema

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=False),
        sa.Column('role', sa.Enum('owner', 'lmo', 'gatc', 'regulator', 'admin', name='userrole'), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('jurisdiction', sa.String(length=255), nullable=True),
        sa.Column('organization', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('can_issue_certificate', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_role', 'users', ['role'])

    # Create instruments table
    op.create_table(
        'instruments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.Enum('weighing_non_automatic', 'weighing_automatic', 'measuring_length', 'measuring_volume', 'measuring_flow', 'other', name='instrumentcategory'), nullable=False),
        sa.Column('instrument_type', sa.String(length=100), nullable=False),
        sa.Column('manufacturer', sa.String(length=255), nullable=False),
        sa.Column('model', sa.String(length=100), nullable=False),
        sa.Column('serial_number', sa.String(length=100), nullable=False),
        sa.Column('capacity', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=50), nullable=True),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('use_context', sa.Text(), nullable=True),
        sa.Column('registration_date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('status', sa.Enum('registered', 'under_verification', 'verified', 'expired', 'rejected', name='instrumentstatus'), nullable=False, default='registered'),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('owner_id', 'serial_number', name='ix_instrument_owner_serial'),
    )
    op.create_index('ix_instruments_owner_id', 'instruments', ['owner_id'])
    op.create_index('ix_instruments_serial_number', 'instruments', ['serial_number'])
    op.create_index('ix_instruments_category', 'instruments', ['category'])
    op.create_index('ix_instruments_status', 'instruments', ['status'])

    # Create applications table
    op.create_table(
        'applications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('applicant_id', sa.Integer(), nullable=False),
        sa.Column('verification_type', sa.Enum('initial', 'reverification', name='verificationtype'), nullable=False),
        sa.Column('status', sa.Enum('draft', 'submitted', 'under_review', 'correction_requested', 'resubmitted', 'approved_for_scheduling', 'scheduled', 'inspection_in_progress', 'inspection_recorded', 'decision_pending', 'completed', 'rejected', 'withdrawn', 'cancelled', name='applicationstatus'), nullable=False, default='draft'),
        sa.Column('jurisdiction', sa.String(length=255), nullable=True),
        sa.Column('assigned_officer_id', sa.Integer(), nullable=True),
        sa.Column('assigned_centre_id', sa.Integer(), nullable=True),
        sa.Column('requested_appointment', sa.DateTime(), nullable=True),
        sa.Column('fee_amount', sa.Integer(), nullable=True),
        sa.Column('fee_paid', sa.Boolean(), nullable=False, default=False),
        sa.Column('remarks', sa.Text(), nullable=True),
        sa.Column('submitted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['applicant_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_officer_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_centre_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_applications_instrument_id', 'applications', ['instrument_id'])
    op.create_index('ix_applications_applicant_id', 'applications', ['applicant_id'])
    op.create_index('ix_applications_assigned_officer_id', 'applications', ['assigned_officer_id'])
    op.create_index('ix_applications_assigned_centre_id', 'applications', ['assigned_centre_id'])
    op.create_index('ix_applications_status', 'applications', ['status'])
    op.create_index('ix_applications_instrument_status', 'applications', ['instrument_id', 'status'])

    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('media_type', sa.String(length=100), nullable=False),
        sa.Column('storage_key', sa.String(length=255), nullable=False),
        sa.Column('uploader_id', sa.Integer(), nullable=False),
        sa.Column('uploaded_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploader_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_attachments_application_id', 'attachments', ['application_id'])
    op.create_index('ix_attachments_uploader_id', 'attachments', ['uploader_id'])

    # Create appointments table
    op.create_table(
        'appointments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('assigned_officer_id', sa.Integer(), nullable=True),
        sa.Column('assigned_centre_id', sa.Integer(), nullable=True),
        sa.Column('scheduled_start', sa.DateTime(), nullable=False),
        sa.Column('scheduled_end', sa.DateTime(), nullable=False),
        sa.Column('location', sa.Text(), nullable=True),
        sa.Column('mode', sa.String(length=50), nullable=True),
        sa.Column('status', sa.Enum('scheduled', 'in_progress', 'completed', 'cancelled', 'no_show', name='appointmentstatus'), nullable=False, default='scheduled'),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['assigned_officer_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['assigned_centre_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_appointments_application_id', 'appointments', ['application_id'])
    op.create_index('ix_appointments_assigned_officer_id', 'appointments', ['assigned_officer_id'])
    op.create_index('ix_appointments_assigned_centre_id', 'appointments', ['assigned_centre_id'])
    op.create_index('ix_appointments_scheduled_start', 'appointments', ['scheduled_start'])
    op.create_index('ix_appointment_officer_time', 'appointments', ['assigned_officer_id', 'scheduled_start', 'scheduled_end'])
    op.create_index('ix_appointment_centre_time', 'appointments', ['assigned_centre_id', 'scheduled_start', 'scheduled_end'])

    # Create inspections table
    op.create_table(
        'inspections',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('inspector_id', sa.Integer(), nullable=False),
        sa.Column('appointment_id', sa.Integer(), nullable=True),
        sa.Column('inspection_date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('observations', sa.Text(), nullable=True),
        sa.Column('checklist', sa.Text(), nullable=True),
        sa.Column('condition_notes', sa.Text(), nullable=True),
        sa.Column('result', sa.Enum('pass', 'fail', 'needs_follow_up', name='inspectionresult'), nullable=False),
        sa.Column('photos', sa.Text(), nullable=True),
        sa.Column('signature_metadata', sa.Text(), nullable=True),
        sa.Column('is_finalized', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['inspector_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_inspections_application_id', 'inspections', ['application_id'])
    op.create_index('ix_inspections_inspector_id', 'inspections', ['inspector_id'])
    op.create_index('ix_inspections_appointment_id', 'inspections', ['appointment_id'])
    op.create_index('ix_inspections_result', 'inspections', ['result'])
    op.create_index('ix_inspection_application_result', 'inspections', ['application_id', 'result'])

    # Create certificates table
    op.create_table(
        'certificates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('application_id', sa.Integer(), nullable=False),
        sa.Column('instrument_id', sa.Integer(), nullable=False),
        sa.Column('certificate_number', sa.String(length=100), nullable=False),
        sa.Column('verification_token', sa.String(length=64), nullable=False),
        sa.Column('issue_date', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('valid_from', sa.DateTime(), nullable=False),
        sa.Column('valid_until', sa.DateTime(), nullable=False),
        sa.Column('status', sa.Enum('valid', 'expired', 'revoked', 'superseded', name='certificatestatus'), nullable=False, default='valid'),
        sa.Column('issuer_id', sa.Integer(), nullable=False),
        sa.Column('revocation_reason', sa.Text(), nullable=True),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.Column('superseded_by_id', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['issuer_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['superseded_by_id'], ['certificates.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('certificate_number'),
        sa.UniqueConstraint('verification_token'),
    )
    op.create_index('ix_certificates_application_id', 'certificates', ['application_id'])
    op.create_index('ix_certificates_instrument_id', 'certificates', ['instrument_id'])
    op.create_index('ix_certificates_issuer_id', 'certificates', ['issuer_id'])
    op.create_index('ix_certificates_certificate_number', 'certificates', ['certificate_number'], unique=True)
    op.create_index('ix_certificates_verification_token', 'certificates', ['verification_token'], unique=True)
    op.create_index('ix_certificates_status', 'certificates', ['status'])
    op.create_index('ix_certificates_valid_until', 'certificates', ['valid_until'])
    op.create_index('ix_certificate_instrument_status', 'certificates', ['instrument_id', 'status'])

    # Create audit_events table
    op.create_table(
        'audit_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('actor_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('entity_type', sa.String(length=100), nullable=False),
        sa.Column('entity_id', sa.Integer(), nullable=False),
        sa.Column('previous_status', sa.String(length=100), nullable=True),
        sa.Column('new_status', sa.String(length=100), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('request_metadata', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.ForeignKeyConstraint(['actor_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_audit_events_actor_id', 'audit_events', ['actor_id'])
    op.create_index('ix_audit_events_entity', 'audit_events', ['entity_type', 'entity_id'])
    op.create_index('ix_audit_events_timestamp', 'audit_events', ['timestamp'])
    op.create_index('ix_audit_actor_time', 'audit_events', ['actor_id', 'timestamp'])

    # Create notifications table
    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('application_submitted', 'application_under_review', 'correction_requested', 'application_rejected', 'application_approved_scheduling', 'appointment_scheduled', 'appointment_cancelled', 'inspection_recorded', 'certificate_issued', 'certificate_revoked', 'certificate_superseded', 'certificate_expiring_soon', 'certificate_expired', 'general', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('reference_type', sa.String(length=100), nullable=True),
        sa.Column('reference_id', sa.Integer(), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=sa.func.now()),
        sa.Column('read_at', sa.DateTime(), nullable=True),
        sa.Column('delivery_status', sa.String(length=50), nullable=False, default='pending'),
        sa.ForeignKeyConstraint(['recipient_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_notifications_recipient_id', 'notifications', ['recipient_id'])
    op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
    op.create_index('ix_notifications_recipient_unread', 'notifications', ['recipient_id', 'is_read'])
    op.create_index('ix_notifications_reference', 'notifications', ['reference_type', 'reference_id'])


def downgrade() -> None:
    op.drop_table('notifications')
    op.drop_table('audit_events')
    op.drop_table('certificates')
    op.drop_table('inspections')
    op.drop_table('appointments')
    op.drop_table('attachments')
    op.drop_table('applications')
    op.drop_table('instruments')
    op.drop_table('users')