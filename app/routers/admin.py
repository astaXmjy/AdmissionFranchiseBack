from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import csv
import io
from ..database import get_db
from ..auth import get_current_admin, get_password_hash
from ..models import User, Student
from ..schemas import (
    UserCreate, UserResponse, StudentListResponse, StudentResponse,
    StudentFilter, StatusUpdate, StudentStats, FranchiseStats
)

router = APIRouter()

@router.post("/franchises", response_model=UserResponse)
def create_franchise(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    # Create franchise user
    hashed_password = get_password_hash(user_data.password)
    franchise = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        full_name=user_data.full_name
    )
    db.add(franchise)
    db.commit()
    db.refresh(franchise)
    return franchise

@router.get("/franchises", response_model=List[UserResponse])
def get_franchises(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    franchises = db.query(User).filter(User.role == "franchise").all()
    return franchises

@router.get("/students", response_model=StudentListResponse)
def get_all_students(
    franchise_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from sqlalchemy.orm import selectinload

    query = db.query(Student).options(selectinload(Student.franchise))

    if franchise_id:
        query = query.filter(Student.franchise_id == franchise_id)
    if start_date:
        query = query.filter(Student.created_at >= start_date)
    if end_date:
        query = query.filter(Student.created_at <= end_date)

    students = query.all()

    # Convert to response format
    student_responses = []
    for student in students:
        student_responses.append(StudentResponse(
            id=student.id,
            student_name=student.student_name,
            father_name=student.father_name,
            mother_name=student.mother_name,
            previous_class=student.previous_class,
            course_applied=student.course_applied,
            branch_specialization=student.branch_specialization,
            affiliating_university=student.affiliating_university,
            street_locality=student.street_locality,
            city=student.city,
            state=student.state,
            pincode=student.pincode,
            contact_number=student.contact_number,
            aadhar_number=student.aadhar_number,
            franchise_id=student.franchise_id,
            franchise_name=student.franchise.full_name,
            status=student.status.value,
            created_at=student.created_at,
            updated_at=student.updated_at
        ))

    return StudentListResponse(students=student_responses, total=len(student_responses))

@router.patch("/students/{student_id}/status")
def update_student_status(
    student_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Get student
    student = db.query(Student).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    # Update status
    student.status = status_update.status
    student.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(student)

    return {"message": "Status updated successfully", "status": student.status.value}

@router.get("/statistics", response_model=StudentStats)
def get_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from ..models import AdmissionStatus

    # Get total students
    total = db.query(func.count(Student.id)).scalar()

    # Get counts by status
    pending = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.PENDING).scalar()

    confirmed = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.CONFIRMED).scalar()

    rejected = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.REJECTED).scalar()

    return StudentStats(
        total=total,
        pending=pending,
        confirmed=confirmed,
        rejected=rejected
    )

@router.get("/franchises/statistics", response_model=List[FranchiseStats])
def get_franchise_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from ..models import AdmissionStatus

    # Get all franchises
    franchises = db.query(User).filter(User.role == "franchise").all()

    franchise_stats = []
    for franchise in franchises:
        # Get student counts for this franchise
        total = db.query(func.count(Student.id)).filter(Student.franchise_id == franchise.id).scalar()

        pending = db.query(func.count(Student.id)).filter(
            Student.franchise_id == franchise.id,
            Student.status == AdmissionStatus.PENDING
        ).scalar()

        confirmed = db.query(func.count(Student.id)).filter(
            Student.franchise_id == franchise.id,
            Student.status == AdmissionStatus.CONFIRMED
        ).scalar()

        rejected = db.query(func.count(Student.id)).filter(
            Student.franchise_id == franchise.id,
            Student.status == AdmissionStatus.REJECTED
        ).scalar()

        franchise_stats.append(FranchiseStats(
            id=franchise.id,
            username=franchise.username,
            full_name=franchise.full_name,
            total_students=total,
            pending=pending,
            confirmed=confirmed,
            rejected=rejected,
            created_at=franchise.created_at,
            is_active=franchise.is_active
        ))

    return franchise_stats

@router.get("/students/csv")
def export_all_students_csv(
    franchise_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from sqlalchemy.orm import selectinload

    query = db.query(Student).options(selectinload(Student.franchise))

    if franchise_id:
        query = query.filter(Student.franchise_id == franchise_id)
    if start_date:
        query = query.filter(Student.created_at >= start_date)
    if end_date:
        query = query.filter(Student.created_at <= end_date)

    students = query.all()

    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow([
        'ID', 'Student Name', 'Father Name', 'Mother Name', 'Previous Class',
        'Course Applied', 'Branch/Specialization', 'Affiliating University',
        'Street/Locality', 'City', 'State', 'Pincode', 'Contact Number', 'Aadhar Number',
        'Franchise ID', 'Franchise Name', 'Status', 'Created At', 'Updated At'
    ])

    # Write data
    for student in students:
        writer.writerow([
            student.id,
            student.student_name,
            student.father_name,
            student.mother_name,
            student.previous_class,
            student.course_applied,
            student.branch_specialization or '',
            student.affiliating_university or '',
            student.street_locality,
            student.city,
            student.state,
            student.pincode,
            student.contact_number,
            student.aadhar_number,
            student.franchise_id,
            student.franchise.full_name,
            student.status.value,
            student.created_at.isoformat(),
            student.updated_at.isoformat()
        ])

    output.seek(0)

    # Return CSV response
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_students.csv"}
    )
