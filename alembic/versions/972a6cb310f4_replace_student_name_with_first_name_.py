"""replace student_name with first_name middle_name last_name, add dob and email

Revision ID: 972a6cb310f4
Revises:
Create Date: 2026-02-10 00:36:05.324776

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '972a6cb310f4'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Step 1: Add new columns as nullable first
    op.add_column('student', sa.Column('first_name', sa.String(), nullable=True))
    op.add_column('student', sa.Column('middle_name', sa.String(), nullable=True))
    op.add_column('student', sa.Column('last_name', sa.String(), nullable=True))
    op.add_column('student', sa.Column('dob', sa.Date(), nullable=True))
    op.add_column('student', sa.Column('email', sa.String(), nullable=True))

    # Step 2: Migrate existing data - copy student_name to first_name
    op.execute("UPDATE student SET first_name = student_name, last_name = '' WHERE first_name IS NULL")
    op.execute("UPDATE student SET dob = '2000-01-01' WHERE dob IS NULL")

    # Step 3: Make required columns non-nullable
    op.alter_column('student', 'first_name', nullable=False)
    op.alter_column('student', 'last_name', nullable=False)
    op.alter_column('student', 'dob', nullable=False)

    # Step 4: Drop old column
    op.drop_column('student', 'student_name')


def downgrade() -> None:
    """Downgrade schema."""
    # Step 1: Re-add student_name as nullable
    op.add_column('student', sa.Column('student_name', sa.VARCHAR(), nullable=True))

    # Step 2: Migrate data back
    op.execute("UPDATE student SET student_name = first_name || COALESCE(' ' || middle_name, '') || ' ' || last_name")

    # Step 3: Make student_name non-nullable
    op.alter_column('student', 'student_name', nullable=False)

    # Step 4: Drop new columns
    op.drop_column('student', 'email')
    op.drop_column('student', 'dob')
    op.drop_column('student', 'last_name')
    op.drop_column('student', 'middle_name')
    op.drop_column('student', 'first_name')
