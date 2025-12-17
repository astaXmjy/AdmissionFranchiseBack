from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import csv
import io
from ..database import get_db
from ..auth import get_current_franchise
from ..models import User, Student
from ..schemas import StudentCreate, StudentResponse, StudentListResponse, StudentStats
from sqlalchemy import func

router = APIRouter()

@router.post("/students", response_model=StudentResponse)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    # Create student record
    student = Student(
        student_name=student_data.student_name,
        father_name=student_data.father_name,
        mother_name=student_data.mother_name,
        previous_class=student_data.previous_class,
        course_applied=student_data.course_applied,
        branch_specialization=student_data.branch_specialization,
        affiliating_university=student_data.affiliating_university,
        street_locality=student_data.street_locality,
        city=student_data.city,
        state=student_data.state,
        pincode=student_data.pincode,
        contact_number=student_data.contact_number,
        aadhar_number=student_data.aadhar_number,
        franchise_id=current_franchise.id
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    # Return response with franchise name
    return StudentResponse(
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
        franchise_name=current_franchise.full_name,
        status=student.status.value,
        created_at=student.created_at,
        updated_at=student.updated_at
    )

@router.get("/students", response_model=StudentListResponse)
def get_my_students(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    query = db.query(Student).filter(Student.franchise_id == current_franchise.id)

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
            franchise_name=current_franchise.full_name,
            status=student.status.value,
            created_at=student.created_at,
            updated_at=student.updated_at
        ))

    return StudentListResponse(students=student_responses, total=len(student_responses))

@router.get("/statistics", response_model=StudentStats)
def get_my_statistics(
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    from ..models import AdmissionStatus

    # Get total students for this franchise
    total = db.query(func.count(Student.id)).filter(Student.franchise_id == current_franchise.id).scalar()

    # Get counts by status
    pending = db.query(func.count(Student.id)).filter(
        Student.franchise_id == current_franchise.id,
        Student.status == AdmissionStatus.PENDING
    ).scalar()

    confirmed = db.query(func.count(Student.id)).filter(
        Student.franchise_id == current_franchise.id,
        Student.status == AdmissionStatus.CONFIRMED
    ).scalar()

    rejected = db.query(func.count(Student.id)).filter(
        Student.franchise_id == current_franchise.id,
        Student.status == AdmissionStatus.REJECTED
    ).scalar()

    return StudentStats(
        total=total,
        pending=pending,
        confirmed=confirmed,
        rejected=rejected
    )

@router.get("/students/csv")
def export_students_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    query = db.query(Student).filter(Student.franchise_id == current_franchise.id)

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
        'Franchise', 'Status', 'Created At', 'Updated At'
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
            current_franchise.full_name,
            student.status.value,
            student.created_at.isoformat(),
            student.updated_at.isoformat()
        ])

    output.seek(0)

    # Return CSV response
    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )
