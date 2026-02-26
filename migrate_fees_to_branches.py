#!/usr/bin/env python3
"""
Migration script: clone course-level fees into branch-level fees.

For every fee that is linked to a course-level CourseVariant (branch_id = NULL),
this script will:
  1. Find all active branches of that course.
  2. For each branch, find (or create) a variant with the same course_type.
  3. Create a fee for that branch variant with identical amounts.
  4. (Optionally) delete the original course-level fee.

Run from the backend/ directory:
    python migrate_fees_to_branches.py
    python migrate_fees_to_branches.py --delete-originals
"""

import sys
from datetime import datetime
from app.database import SessionLocal
from app.models import Fee, CourseVariant, Branch, Course


def migrate(delete_originals: bool = False):
    db = SessionLocal()
    try:
        # Load all fees whose variant has no branch
        course_level_fees = (
            db.query(Fee)
            .join(CourseVariant, Fee.course_variant_id == CourseVariant.id)
            .filter(CourseVariant.branch_id == None)
            .all()
        )

        if not course_level_fees:
            print("No course-level fees found. Nothing to migrate.")
            return

        print(f"Found {len(course_level_fees)} course-level fee(s) to process.\n")

        created_total = 0
        skipped_total = 0

        for fee in course_level_fees:
            variant = db.query(CourseVariant).filter(CourseVariant.id == fee.course_variant_id).first()
            course = db.query(Course).filter(Course.id == variant.course_id).first()
            branches = db.query(Branch).filter(Branch.course_id == course.id, Branch.is_active == True).all()

            if not branches:
                print(f"  [SKIP] Fee ID {fee.id} | Course: {course.name} | No active branches found.")
                skipped_total += 1
                continue

            print(f"  Fee ID {fee.id} | Course: {course.name} | Variant: {variant.course_type} | {len(branches)} branch(es)")

            for branch in branches:
                # Find or create the branch-level variant
                branch_variant = (
                    db.query(CourseVariant)
                    .filter(
                        CourseVariant.course_id == course.id,
                        CourseVariant.branch_id == branch.id,
                        CourseVariant.course_type == variant.course_type,
                    )
                    .first()
                )

                if not branch_variant:
                    branch_variant = CourseVariant(
                        course_id=course.id,
                        branch_id=branch.id,
                        course_type=variant.course_type,
                        is_active=True,
                    )
                    db.add(branch_variant)
                    db.flush()
                    print(f"    Created variant for branch '{branch.name}' ({variant.course_type})")

                # Skip if a fee already exists for this branch variant
                existing = db.query(Fee).filter(Fee.course_variant_id == branch_variant.id).first()
                if existing:
                    print(f"    [SKIP] Branch '{branch.name}' already has a fee (ID {existing.id})")
                    skipped_total += 1
                    continue

                # Create fee for this branch variant
                new_fee = Fee(
                    course_variant_id=branch_variant.id,
                    tuition_fee=fee.tuition_fee,
                    registration_fee=fee.registration_fee,
                    exam_fee_yearly=fee.exam_fee_yearly,
                    other_fees=fee.other_fees,
                    currency=fee.currency,
                    academic_year=fee.academic_year,
                    effective_from=fee.effective_from,
                    is_active=fee.is_active,
                    created_at=datetime.utcnow(),
                    updated_at=datetime.utcnow(),
                )
                db.add(new_fee)
                print(f"    Created fee for branch '{branch.name}'")
                created_total += 1

            if delete_originals:
                db.delete(fee)
                print(f"    Deleted original course-level fee ID {fee.id}")

        db.commit()
        print(f"\nDone. Created: {created_total}  |  Skipped: {skipped_total}")
        if not delete_originals:
            print("Original course-level fees were kept. Run with --delete-originals to remove them.")

    except Exception as e:
        db.rollback()
        print(f"Error: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    delete_originals = "--delete-originals" in sys.argv
    migrate(delete_originals=delete_originals)
