"""Add 8th class fields and split eligible_document into 4 doc columns

Revision ID: d4e5f6a7b8c9
Revises: a3f8b2e1c4d9
Create Date: 2026-02-26 00:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, Sequence[str], None] = 'a3f8b2e1c4d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 8th class detail fields
    op.add_column('student', sa.Column('eighth_board', sa.String(length=50), nullable=True))
    op.add_column('student', sa.Column('eighth_board_other', sa.String(length=100), nullable=True))
    op.add_column('student', sa.Column('eighth_school', sa.String(length=255), nullable=True))
    op.add_column('student', sa.Column('eighth_passing_year', sa.String(length=4), nullable=True))
    op.add_column('student', sa.Column('eighth_percentage', sa.String(length=10), nullable=True))
    # Split eligible_document into 4 specific doc columns
    op.add_column('student', sa.Column('doc_eighth', sa.String(), nullable=True))
    op.add_column('student', sa.Column('doc_tenth', sa.String(), nullable=True))
    op.add_column('student', sa.Column('doc_twelfth', sa.String(), nullable=True))
    op.add_column('student', sa.Column('doc_graduation', sa.String(), nullable=True))
    op.drop_column('student', 'eligible_document')


def downgrade() -> None:
    op.add_column('student', sa.Column('eligible_document', sa.String(), nullable=True))
    op.drop_column('student', 'doc_graduation')
    op.drop_column('student', 'doc_twelfth')
    op.drop_column('student', 'doc_tenth')
    op.drop_column('student', 'doc_eighth')
    op.drop_column('student', 'eighth_percentage')
    op.drop_column('student', 'eighth_passing_year')
    op.drop_column('student', 'eighth_school')
    op.drop_column('student', 'eighth_board_other')
    op.drop_column('student', 'eighth_board')
