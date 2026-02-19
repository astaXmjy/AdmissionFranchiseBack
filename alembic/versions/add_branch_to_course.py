"""add branch to course

Revision ID: b7c8d9e0f1a2
Revises: fcd052229707
Create Date: 2026-02-19

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = 'b7c8d9e0f1a2'
down_revision = 'fcd052229707'
branch_labels = None
depends_on = None


def _column_exists(table, column):
    conn = op.get_bind()
    insp = inspect(conn)
    return column in [c['name'] for c in insp.get_columns(table)]

def _table_exists(table):
    conn = op.get_bind()
    insp = inspect(conn)
    return table in insp.get_table_names()

def _index_exists(table, index_name):
    conn = op.get_bind()
    insp = inspect(conn)
    return any(i['name'] == index_name for i in insp.get_indexes(table))

def _constraint_exists(table, constraint_name):
    conn = op.get_bind()
    insp = inspect(conn)
    uqs = insp.get_unique_constraints(table)
    return any(c['name'] == constraint_name for c in uqs)


def upgrade():
    # 1. Create branch table (skip if already exists)
    if not _table_exists('branch'):
        op.create_table(
            'branch',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('course_id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(255), nullable=False),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['course_id'], ['course.id'], ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('course_id', 'name', name='uq_branch_course_name'),
        )
        op.create_index(op.f('ix_branch_id'), 'branch', ['id'], unique=False)
        op.create_index(op.f('ix_branch_course_id'), 'branch', ['course_id'], unique=False)
        op.create_index(op.f('ix_branch_is_active'), 'branch', ['is_active'], unique=False)

    # 2. Add branch_id to course_variant (nullable, for branch-level variants)
    if not _column_exists('course_variant', 'branch_id'):
        op.add_column('course_variant', sa.Column('branch_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_course_variant_branch_id',
            'course_variant', 'branch',
            ['branch_id'], ['id'],
            ondelete='CASCADE'
        )
        op.create_index(op.f('ix_course_variant_branch_id'), 'course_variant', ['branch_id'], unique=False)

    # 3. Drop old unique constraint on (course_id, course_type) if it still exists
    if _constraint_exists('course_variant', 'uq_course_variant_type'):
        op.drop_constraint('uq_course_variant_type', 'course_variant', type_='unique')

    # 4. Add new partial unique indexes (skip if already exist)
    if not _index_exists('course_variant', 'uq_course_variant_no_branch'):
        op.create_index(
            'uq_course_variant_no_branch',
            'course_variant',
            ['course_id', 'course_type'],
            unique=True,
            postgresql_where=sa.text('branch_id IS NULL')
        )
    if not _index_exists('course_variant', 'uq_branch_variant_type'):
        op.create_index(
            'uq_branch_variant_type',
            'course_variant',
            ['branch_id', 'course_type'],
            unique=True,
            postgresql_where=sa.text('branch_id IS NOT NULL')
        )

    # 5. Add branch_id to student table
    if not _column_exists('student', 'branch_id'):
        op.add_column('student', sa.Column('branch_id', sa.Integer(), nullable=True))
        op.create_foreign_key(
            'fk_student_branch_id',
            'student', 'branch',
            ['branch_id'], ['id'],
            ondelete='SET NULL'
        )
        op.create_index(op.f('ix_student_branch_id'), 'student', ['branch_id'], unique=False)


def downgrade():
    # Reverse the steps
    op.drop_index(op.f('ix_student_branch_id'), table_name='student')
    op.drop_constraint('fk_student_branch_id', 'student', type_='foreignkey')
    op.drop_column('student', 'branch_id')

    op.drop_index('uq_branch_variant_type', table_name='course_variant')
    op.drop_index('uq_course_variant_no_branch', table_name='course_variant')
    op.drop_index(op.f('ix_course_variant_branch_id'), table_name='course_variant')
    op.drop_constraint('fk_course_variant_branch_id', 'course_variant', type_='foreignkey')
    op.drop_column('course_variant', 'branch_id')

    # Restore old unique constraint
    op.create_unique_constraint('uq_course_variant_type', 'course_variant', ['course_id', 'course_type'])

    op.drop_index(op.f('ix_branch_is_active'), table_name='branch')
    op.drop_index(op.f('ix_branch_course_id'), table_name='branch')
    op.drop_index(op.f('ix_branch_id'), table_name='branch')
    op.drop_table('branch')
