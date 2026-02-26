"""Add document upload columns to student

Revision ID: a3f8b2e1c4d9
Revises: fcd052229707
Create Date: 2026-02-25 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a3f8b2e1c4d9'
down_revision: Union[str, Sequence[str], None] = 'b7c8d9e0f1a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('student', sa.Column('passport_photo', sa.String(), nullable=True))
    op.add_column('student', sa.Column('aadhar_card_doc', sa.String(), nullable=True))
    op.add_column('student', sa.Column('eligible_document', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column('student', 'eligible_document')
    op.drop_column('student', 'aadhar_card_doc')
    op.drop_column('student', 'passport_photo')
