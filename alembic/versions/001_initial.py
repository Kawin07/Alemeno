"""initial

Revision ID: 001
Revises: 
Create Date: 2024-07-15 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table('jobs',
    sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('filename', sa.String(length=255), nullable=False),
    sa.Column('file_content', sa.LargeBinary(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=False),
    sa.Column('row_count_raw', sa.Integer(), nullable=True),
    sa.Column('row_count_clean', sa.Integer(), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('completed_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('job_summaries',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('total_spend_inr', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('total_spend_usd', sa.Numeric(precision=14, scale=2), nullable=True),
    sa.Column('top_merchants', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('anomaly_count', sa.Integer(), nullable=True),
    sa.Column('narrative', sa.Text(), nullable=True),
    sa.Column('risk_level', sa.String(length=10), nullable=True),
    sa.Column('llm_raw_response', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('job_id')
    )
    op.create_index(op.f('ix_job_summaries_id'), 'job_summaries', ['id'], unique=False)
    op.create_table('transactions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('txn_id', sa.String(length=50), nullable=True),
    sa.Column('date', sa.Date(), nullable=False),
    sa.Column('merchant', sa.String(length=100), nullable=False),
    sa.Column('amount', sa.Numeric(precision=12, scale=2), nullable=False),
    sa.Column('currency', sa.String(length=3), nullable=False),
    sa.Column('status', sa.String(length=10), nullable=False),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('account_id', sa.String(length=20), nullable=False),
    sa.Column('notes', sa.Text(), nullable=True),
    sa.Column('is_anomaly', sa.Boolean(), nullable=False),
    sa.Column('anomaly_reasons', postgresql.JSON(astext_type=sa.Text()), nullable=True),
    sa.Column('llm_category', sa.String(length=50), nullable=True),
    sa.Column('llm_raw_response', sa.Text(), nullable=True),
    sa.Column('llm_failed', sa.Boolean(), nullable=False),
    sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_transactions_id'), 'transactions', ['id'], unique=False)



def downgrade() -> None:

    op.drop_index(op.f('ix_transactions_id'), table_name='transactions')
    op.drop_table('transactions')
    op.drop_index(op.f('ix_job_summaries_id'), table_name='job_summaries')
    op.drop_table('job_summaries')
    op.drop_table('jobs')

