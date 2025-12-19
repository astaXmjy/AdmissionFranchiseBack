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
from ..models import User, Student, University, Course, Fee
from ..schemas import (
    UserCreate, UserResponse, StudentListResponse, StudentResponse,
    StudentFilter, StatusUpdate, StudentStats, FranchiseStats,
    UniversityCreate, UniversityUpdate, UniversityResponse, UniversitySelectResponse,
    CourseCreate, CourseUpdate, CourseResponse, CourseSelectResponse, CourseWithFeeResponse,
    FeeCreate, FeeUpdate, FeeResponse
)

router = APIRouter()

# ===== FRANCHISE MANAGEMENT =====

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

# ===== UNIVERSITY MANAGEMENT =====

@router.post("/universities", response_model=UniversityResponse)
def create_university(
    university_data: UniversityCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if university name already exists
    existing = db.query(University).filter(University.name == university_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="University with this name already exists")

    # Check if code already exists (if provided)
    if university_data.code:
        existing_code = db.query(University).filter(University.code == university_data.code).first()
        if existing_code:
            raise HTTPException(status_code=400, detail="University with this code already exists")

    university = University(**university_data.dict())
    db.add(university)
    db.commit()
    db.refresh(university)
    return university

@router.get("/universities", response_model=List[UniversityResponse])
def get_universities(
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(University)
    if is_active is not None:
        query = query.filter(University.is_active == is_active)
    universities = query.all()
    return universities

@router.get("/universities/select", response_model=List[UniversitySelectResponse])
def get_universities_for_select(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get active universities for dropdown selection"""
    universities = db.query(University).filter(University.is_active == True).all()
    return universities

@router.get("/universities/{university_id}", response_model=UniversityResponse)
def get_university(
    university_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")
    return university

@router.patch("/universities/{university_id}", response_model=UniversityResponse)
def update_university(
    university_id: int,
    university_data: UniversityUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Update only provided fields
    for field, value in university_data.dict(exclude_unset=True).items():
        setattr(university, field, value)

    university.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(university)
    return university

@router.delete("/universities/{university_id}")
def delete_university(
    university_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    university = db.query(University).filter(University.id == university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Check if university has courses
    courses_count = db.query(func.count(Course.id)).filter(Course.university_id == university_id).scalar()
    if courses_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete university with {courses_count} associated courses. Delete courses first or deactivate the university."
        )

    db.delete(university)
    db.commit()
    return {"message": "University deleted successfully"}

# ===== COURSE MANAGEMENT =====

@router.post("/courses", response_model=CourseResponse)
def create_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if university exists
    university = db.query(University).filter(University.id == course_data.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Check if course code already exists for this university (if provided)
    if course_data.code:
        existing = db.query(Course).filter(
            Course.university_id == course_data.university_id,
            Course.code == course_data.code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Course with this code already exists for this university")

    course = Course(**course_data.dict())
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

@router.get("/courses", response_model=List[CourseWithFeeResponse])
def get_courses(
    university_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from sqlalchemy.orm import selectinload

    query = db.query(Course).options(
        selectinload(Course.university),
        selectinload(Course.fee)
    )

    if university_id:
        query = query.filter(Course.university_id == university_id)
    if is_active is not None:
        query = query.filter(Course.is_active == is_active)

    courses = query.all()
    return courses

@router.get("/courses/select/{university_id}", response_model=List[CourseSelectResponse])
def get_courses_for_select(
    university_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get active courses for dropdown selection by university"""
    courses = db.query(Course).filter(
        Course.university_id == university_id,
        Course.is_active == True
    ).all()
    return courses

@router.get("/courses/{course_id}", response_model=CourseWithFeeResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from sqlalchemy.orm import selectinload

    course = db.query(Course).options(
        selectinload(Course.university),
        selectinload(Course.fee)
    ).filter(Course.id == course_id).first()

    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

@router.patch("/courses/{course_id}", response_model=CourseResponse)
def update_course(
    course_id: int,
    course_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Update only provided fields
    for field, value in course_data.dict(exclude_unset=True).items():
        setattr(course, field, value)

    course.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(course)
    return course

@router.delete("/courses/{course_id}")
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if course has students
    students_count = db.query(func.count(Student.id)).filter(Student.course_id == course_id).scalar()
    if students_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete course with {students_count} enrolled students. Deactivate the course instead."
        )

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

# ===== FEE MANAGEMENT =====

@router.post("/fees", response_model=FeeResponse)
def create_fee(
    fee_data: FeeCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if course exists
    course = db.query(Course).filter(Course.id == fee_data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Check if fee already exists for this course
    existing_fee = db.query(Fee).filter(Fee.course_id == fee_data.course_id).first()
    if existing_fee:
        raise HTTPException(status_code=400, detail="Fee structure already exists for this course. Use update instead.")

    fee = Fee(**fee_data.dict())
    db.add(fee)
    db.commit()
    db.refresh(fee)
    return fee

@router.get("/fees", response_model=List[FeeResponse])
def get_fees(
    course_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(Fee)

    if course_id:
        query = query.filter(Fee.course_id == course_id)
    if is_active is not None:
        query = query.filter(Fee.is_active == is_active)

    fees = query.all()
    return fees

@router.get("/fees/{fee_id}", response_model=FeeResponse)
def get_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
    return fee

@router.get("/fees/by-course/{course_id}", response_model=FeeResponse)
def get_fee_by_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    fee = db.query(Fee).filter(Fee.course_id == course_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee structure not found for this course")
    return fee

@router.patch("/fees/{fee_id}", response_model=FeeResponse)
def update_fee(
    fee_id: int,
    fee_data: FeeUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")

    # Update only provided fields
    for field, value in fee_data.dict(exclude_unset=True).items():
        setattr(fee, field, value)

    fee.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(fee)
    return fee

@router.delete("/fees/{fee_id}")
def delete_fee(
    fee_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    fee = db.query(Fee).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")

    db.delete(fee)
    db.commit()
    return {"message": "Fee deleted successfully"}

# ===== STUDENT MANAGEMENT =====

@router.get("/students", response_model=StudentListResponse)
def get_all_students(
    franchise_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from sqlalchemy.orm import selectinload

    query = db.query(Student).options(
        selectinload(Student.franchise),
        selectinload(Student.university),
        selectinload(Student.course)
    )

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
            university_id=student.university_id,
            university_name=student.university.name if student.university else None,
            course_id=student.course_id,
            course_name=student.course.name if student.course else None,
            fee_id=student.fee_id,
            branch_specialization=student.branch_specialization,
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

    query = db.query(Student).options(
        selectinload(Student.franchise),
        selectinload(Student.university),
        selectinload(Student.course)
    )

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
        'University', 'Course', 'Branch/Specialization',
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
            student.university.name if student.university else '',
            student.course.name if student.course else '',
            student.branch_specialization or '',
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
