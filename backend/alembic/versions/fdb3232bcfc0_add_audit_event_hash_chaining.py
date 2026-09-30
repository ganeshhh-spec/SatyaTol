"""Add audit event hash chaining

Revision ID: fdb3232bcfc0
Revises: c967248701ba
Create Date: 2026-09-30 00:40:21.842153

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fdb3232bcfc0'
down_revision = 'c967248701ba'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add hash chaining columns to audit_events table
    op.add_column('audit_events', sa.Column('event_hash', sa.String(length=64), nullable=True))
    op.add_column('audit_events', sa.Column('previous_hash', sa.String(length=64), nullable=True))


def downgrade() -> None:
    op.drop_column('audit_events', 'event_hash')
    op.drop_column('audit_events', 'previous_hash')