"""add course_variant table and eligible_education

Revision ID: a1b2c3d4e5f6
Revises: 35cf1078d536
Create Date: 2026-02-12

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '35cf1078d536'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add eligible_education to course table
    op.add_column('course', sa.Column('eligible_education', sa.String(length=50), nullable=True))

    # 2. Create course_variant table
    op.create_table(
        'course_variant',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=False),
        sa.Column('course_type', sa.String(length=50), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('course_id', 'course_type', name='uq_course_variant_type')
    )
    op.create_index(op.f('ix_course_variant_id'), 'course_variant', ['id'], unique=False)
    op.create_index(op.f('ix_course_variant_course_id'), 'course_variant', ['course_id'], unique=False)

    # 3. Add course_variant_id to fee table
    op.add_column('fee', sa.Column('course_variant_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_fee_course_variant_id', 'fee', 'course_variant', ['course_variant_id'], ['id'], ondelete='CASCADE')
    op.create_index(op.f('ix_fee_course_variant_id'), 'fee', ['course_variant_id'], unique=True)

    # 4. Add course_variant_id to student table
    op.add_column('student', sa.Column('course_variant_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_student_course_variant_id', 'student', 'course_variant', ['course_variant_id'], ['id'], ondelete='SET NULL')
    op.create_index(op.f('ix_student_course_variant_id'), 'student', ['course_variant_id'], unique=False)

    # 5. Remove old course_id unique constraint and column from fee
    # First drop the old foreign key and unique constraint on fee.course_id
    op.execute('ALTER TABLE fee DROP CONSTRAINT IF EXISTS fee_course_id_key')
    op.execute('ALTER TABLE fee DROP CONSTRAINT IF EXISTS fee_course_id_fkey')
    op.drop_column('fee', 'course_id')


def downgrade() -> None:
    # Re-add course_id to fee
    op.add_column('fee', sa.Column('course_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fee_course_id_fkey', 'fee', 'course', ['course_id'], ['id'], ondelete='CASCADE')
    op.create_unique_constraint('fee_course_id_key', 'fee', ['course_id'])

    # Remove course_variant_id from student
    op.drop_index(op.f('ix_student_course_variant_id'), table_name='student')
    op.drop_constraint('fk_student_course_variant_id', 'student', type_='foreignkey')
    op.drop_column('student', 'course_variant_id')

    # Remove course_variant_id from fee
    op.drop_index(op.f('ix_fee_course_variant_id'), table_name='fee')
    op.drop_constraint('fk_fee_course_variant_id', 'fee', type_='foreignkey')
    op.drop_column('fee', 'course_variant_id')

    # Drop course_variant table
    op.drop_index(op.f('ix_course_variant_course_id'), table_name='course_variant')
    op.drop_index(op.f('ix_course_variant_id'), table_name='course_variant')
    op.drop_table('course_variant')

    # Remove eligible_education from course
    op.drop_column('course', 'eligible_education')
