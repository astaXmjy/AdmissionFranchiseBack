from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import csv
import io
from ..database import get_db
from ..auth import get_current_admin, get_password_hash
from ..models import User, Student, University, Course, CourseVariant, Fee, Branch
from ..schemas import (
    UserCreate, UserUpdate, UserResponse, StudentListResponse, StudentResponse,
    StudentFilter, StatusUpdate, CommissionUpdate, StudentStats, FranchiseStats,
    UniversityCreate, UniversityUpdate, UniversityResponse, UniversitySelectResponse,
    CourseCreate, CourseUpdate, CourseResponse, CourseSelectResponse, CourseWithFeeResponse,
    FeeCreate, FeeUpdate, FeeResponse,
    CourseVariantResponse,
    BranchCreate, BranchUpdate, BranchResponse,
    StudentCreateAdmin
)

router = APIRouter()

# ===== FRANCHISE MANAGEMENT =====

@router.post("/franchises", response_model=UserResponse)
def create_franchise(
    user_data: UserCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")

    hashed_password = get_password_hash(user_data.password)
    franchise = User(
        username=user_data.username,
        password_hash=hashed_password,
        role=user_data.role,
        full_name=user_data.full_name,
        address=user_data.address,
        gst_number=user_data.gst_number,
        pan_number=user_data.pan_number,
        phone_number=user_data.phone_number,
        email=user_data.email
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

@router.patch("/franchises/{franchise_id}", response_model=UserResponse)
def update_franchise(
    franchise_id: int,
    user_data: UserUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    franchise = db.query(User).filter(User.id == franchise_id, User.role == "franchise").first()
    if not franchise:
        raise HTTPException(status_code=404, detail="Franchise not found")

    update_data = user_data.dict(exclude_unset=True)

    if "password" in update_data:
        password = update_data.pop("password")
        if password:
            franchise.password_hash = get_password_hash(password)

    for field, value in update_data.items():
        setattr(franchise, field, value)

    db.commit()
    db.refresh(franchise)
    return franchise

@router.delete("/franchises/{franchise_id}")
def delete_franchise(
    franchise_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    franchise = db.query(User).filter(User.id == franchise_id, User.role == "franchise").first()
    if not franchise:
        raise HTTPException(status_code=404, detail="Franchise not found")

    db.query(Student).filter(Student.franchise_id == franchise_id).delete()
    db.delete(franchise)
    db.commit()
    return {"message": "Franchise deleted successfully"}

# ===== UNIVERSITY MANAGEMENT =====

@router.post("/universities", response_model=UniversityResponse)
def create_university(
    university_data: UniversityCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    existing = db.query(University).filter(University.name == university_data.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="University with this name already exists")

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
    university = db.query(University).filter(University.id == course_data.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    if course_data.code:
        existing = db.query(Course).filter(
            Course.university_id == course_data.university_id,
            Course.code == course_data.code
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Course with this code already exists for this university")

    # Create the course (exclude course_types which is not a column)
    course_dict = course_data.dict(exclude={"course_types"})
    # Convert eligible_education list to comma-separated string
    if course_dict.get("eligible_education") and isinstance(course_dict["eligible_education"], list):
        course_dict["eligible_education"] = ",".join(course_dict["eligible_education"])
    course = Course(**course_dict)
    db.add(course)
    db.flush()  # Get the course ID

    # Auto-create variants from course_types
    if course_data.course_types:
        for ct in course_data.course_types:
            variant = CourseVariant(course_id=course.id, course_type=ct)
            db.add(variant)

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
    query = db.query(Course).options(
        selectinload(Course.university),
        selectinload(Course.variants).selectinload(CourseVariant.fee),
        selectinload(Course.branches).selectinload(Branch.variants).selectinload(CourseVariant.fee)
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
    degree_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get active courses for dropdown selection by university"""
    DEGREE_MAP = {"UG": ["Undergraduate"], "PG": ["Postgraduate"], "Diploma/Certificate": ["Diploma/Certificate"], "Class": ["Class"]}
    query = db.query(Course).options(
        selectinload(Course.variants),
        selectinload(Course.branches).selectinload(Branch.variants)
    ).filter(
        Course.university_id == university_id,
        Course.is_active == True
    )
    if degree_type and degree_type in DEGREE_MAP:
        query = query.filter(Course.degree_type.in_(DEGREE_MAP[degree_type]))
    courses = query.all()
    return courses

@router.get("/courses/{course_id}", response_model=CourseWithFeeResponse)
def get_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).options(
        selectinload(Course.university),
        selectinload(Course.variants).selectinload(CourseVariant.fee),
        selectinload(Course.branches).selectinload(Branch.variants).selectinload(CourseVariant.fee)
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
    course = db.query(Course).options(
        selectinload(Course.variants)
    ).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    update_dict = course_data.dict(exclude_unset=True)
    course_types = update_dict.pop("course_types", None)

    # Convert eligible_education list to comma-separated string
    if "eligible_education" in update_dict and isinstance(update_dict["eligible_education"], list):
        update_dict["eligible_education"] = ",".join(update_dict["eligible_education"])

    # Update course fields
    for field, value in update_dict.items():
        setattr(course, field, value)

    # Update course-level variants if course_types provided (branch variants are managed separately)
    if course_types is not None:
        course_level_variants = [v for v in course.variants if v.branch_id is None]
        existing_types = {v.course_type for v in course_level_variants}
        new_types = set(course_types)

        # Add new course-level variants
        for ct in new_types - existing_types:
            variant = CourseVariant(course_id=course.id, course_type=ct)
            db.add(variant)

        # Deactivate removed course-level variants (don't delete — they may have fees/students)
        for variant in course_level_variants:
            if variant.course_type not in new_types:
                variant.is_active = False
            else:
                variant.is_active = True

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

    students_count = db.query(func.count(Student.id)).filter(Student.course_id == course_id).scalar()
    if students_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete course with {students_count} enrolled students. Deactivate the course instead."
        )

    db.delete(course)
    db.commit()
    return {"message": "Course deleted successfully"}

# ===== COURSE VARIANT MANAGEMENT =====

@router.get("/courses/{course_id}/variants", response_model=List[CourseVariantResponse])
def get_course_variants(
    course_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    """Get course-level variants (no branch) for a course"""
    variants = db.query(CourseVariant).filter(
        CourseVariant.course_id == course_id,
        CourseVariant.branch_id == None,
        CourseVariant.is_active == True
    ).all()
    return variants

# ===== BRANCH MANAGEMENT =====

@router.post("/branches", response_model=BranchResponse)
def create_branch(
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    course = db.query(Course).filter(Course.id == branch_data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    existing = db.query(Branch).filter(
        Branch.course_id == branch_data.course_id,
        Branch.name == branch_data.name
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Branch with this name already exists for this course")

    branch = Branch(
        course_id=branch_data.course_id,
        name=branch_data.name,
        is_active=branch_data.is_active
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return branch

@router.get("/branches", response_model=List[BranchResponse])
def get_branches(
    course_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(Branch).options(selectinload(Branch.variants))
    if course_id:
        query = query.filter(Branch.course_id == course_id)
    return query.all()

@router.get("/branches/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    branch = db.query(Branch).options(
        selectinload(Branch.variants)
    ).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return branch

@router.patch("/branches/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    branch_data: BranchUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    branch = db.query(Branch).options(
        selectinload(Branch.variants)
    ).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    update_dict = branch_data.dict(exclude_unset=True)

    for field, value in update_dict.items():
        setattr(branch, field, value)

    branch.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(branch)
    return branch

@router.delete("/branches/{branch_id}")
def delete_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    students_count = db.query(func.count(Student.id)).filter(Student.branch_id == branch_id).scalar()
    if students_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete branch with {students_count} enrolled students. Deactivate the branch instead."
        )

    db.delete(branch)
    db.commit()
    return {"message": "Branch deleted successfully"}

# ===== FEE MANAGEMENT =====

@router.post("/fees", response_model=FeeResponse)
def create_fee(
    fee_data: FeeCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    # Check if course variant exists
    variant = db.query(CourseVariant).options(
        joinedload(CourseVariant.course).joinedload(Course.university)
    ).filter(CourseVariant.id == fee_data.course_variant_id).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Course variant not found")

    # Check if fee already exists for this variant
    existing_fee = db.query(Fee).filter(Fee.course_variant_id == fee_data.course_variant_id).first()
    if existing_fee:
        raise HTTPException(status_code=400, detail="Fee structure already exists for this course variant. Use update instead.")

    fee = Fee(**fee_data.dict())
    db.add(fee)
    db.commit()
    db.refresh(fee)

    # Reload with relationships
    fee = db.query(Fee).options(
        joinedload(Fee.course_variant).joinedload(CourseVariant.course).joinedload(Course.university)
    ).filter(Fee.id == fee.id).first()
    return fee

@router.get("/fees", response_model=List[FeeResponse])
def get_fees(
    course_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(Fee).options(
        joinedload(Fee.course_variant).joinedload(CourseVariant.course).joinedload(Course.university)
    )

    if course_id:
        query = query.join(CourseVariant).filter(CourseVariant.course_id == course_id)
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
    fee = db.query(Fee).options(
        joinedload(Fee.course_variant).joinedload(CourseVariant.course).joinedload(Course.university)
    ).filter(Fee.id == fee_id).first()
    if not fee:
        raise HTTPException(status_code=404, detail="Fee not found")
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

def build_student_response(student):
    """Helper to build StudentResponse from a Student model instance."""
    return StudentResponse(
        id=student.id,
        first_name=student.first_name,
        middle_name=student.middle_name,
        last_name=student.last_name,
        dob=student.dob,
        email=student.email,
        father_name=student.father_name,
        mother_name=student.mother_name,
        degree_type=student.degree_type,
        previous_class=student.previous_class,
        university_id=student.university_id,
        university_name=student.university.name if student.university else None,
        course_id=student.course_id,
        course_name=student.course.name if student.course else None,
        branch_id=student.branch_id,
        branch_name=student.branch.name if student.branch else None,
        course_variant_id=student.course_variant_id,
        course_type=student.course_variant.course_type if student.course_variant else None,
        fee_id=student.fee_id,
        branch_specialization=student.branch_specialization,
        skills=student.skills,
        tenth_board=student.tenth_board,
        tenth_board_other=student.tenth_board_other,
        tenth_school=student.tenth_school,
        tenth_passing_year=student.tenth_passing_year,
        tenth_percentage=student.tenth_percentage,
        twelfth_board=student.twelfth_board,
        twelfth_board_other=student.twelfth_board_other,
        twelfth_school=student.twelfth_school,
        twelfth_passing_year=student.twelfth_passing_year,
        twelfth_percentage=student.twelfth_percentage,
        grad_university=student.grad_university,
        grad_degree=student.grad_degree,
        grad_passing_year=student.grad_passing_year,
        grad_percentage=student.grad_percentage,
        grad_subject=student.grad_subject,
        apaar_id=student.apaar_id,
        session=student.session,
        total_fee=student.fee.total_first_year if student.fee else None,
        commission_percentage=student.commission_percentage,
        commission_amount=student.commission_amount,
        street_locality=student.street_locality,
        city=student.city,
        district=student.district,
        state=student.state,
        pincode=student.pincode,
        contact_number=student.contact_number,
        aadhar_number=student.aadhar_number,
        franchise_id=student.franchise_id,
        franchise_name=student.franchise.full_name,
        status=student.status.value,
        created_at=student.created_at,
        updated_at=student.updated_at
    )

@router.post("/students", response_model=StudentResponse)
def create_student_as_admin(
    student_data: StudentCreateAdmin,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    franchise = db.query(User).filter(User.id == student_data.franchise_id, User.role == "franchise").first()
    if not franchise:
        raise HTTPException(status_code=404, detail="Franchise not found")

    university = db.query(University).filter(University.id == student_data.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    course = db.query(Course).filter(
        Course.id == student_data.course_id,
        Course.university_id == student_data.university_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or doesn't belong to the selected university")

    variant = db.query(CourseVariant).filter(
        CourseVariant.id == student_data.course_variant_id,
        CourseVariant.course_id == student_data.course_id
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Course variant not found or doesn't belong to the selected course")

    fee = db.query(Fee).filter(Fee.course_variant_id == student_data.course_variant_id).first()

    student = Student(
        first_name=student_data.first_name,
        middle_name=student_data.middle_name,
        last_name=student_data.last_name,
        dob=student_data.dob,
        email=student_data.email,
        father_name=student_data.father_name,
        mother_name=student_data.mother_name,
        degree_type=student_data.degree_type,
        previous_class=student_data.previous_class,
        university_id=student_data.university_id,
        course_id=student_data.course_id,
        branch_id=student_data.branch_id,
        course_variant_id=student_data.course_variant_id,
        fee_id=fee.id if fee else None,
        branch_specialization=student_data.branch_specialization,
        skills=student_data.skills,
        tenth_board=student_data.tenth_board,
        tenth_board_other=student_data.tenth_board_other,
        tenth_school=student_data.tenth_school,
        tenth_passing_year=student_data.tenth_passing_year,
        tenth_percentage=student_data.tenth_percentage,
        twelfth_board=student_data.twelfth_board,
        twelfth_board_other=student_data.twelfth_board_other,
        twelfth_school=student_data.twelfth_school,
        twelfth_passing_year=student_data.twelfth_passing_year,
        twelfth_percentage=student_data.twelfth_percentage,
        grad_university=student_data.grad_university,
        grad_degree=student_data.grad_degree,
        grad_passing_year=student_data.grad_passing_year,
        grad_percentage=student_data.grad_percentage,
        grad_subject=student_data.grad_subject,
        apaar_id=student_data.apaar_id,
        session=student_data.session,
        street_locality=student_data.street_locality,
        city=student_data.city,
        district=student_data.district,
        state=student_data.state,
        pincode=student_data.pincode,
        contact_number=student_data.contact_number,
        aadhar_number=student_data.aadhar_number,
        franchise_id=student_data.franchise_id
    )
    db.add(student)
    db.commit()
    db.refresh(student)

    branch = db.query(Branch).filter(Branch.id == student_data.branch_id).first() if student_data.branch_id else None

    return StudentResponse(
        id=student.id,
        first_name=student.first_name,
        middle_name=student.middle_name,
        last_name=student.last_name,
        dob=student.dob,
        email=student.email,
        father_name=student.father_name,
        mother_name=student.mother_name,
        degree_type=student.degree_type,
        previous_class=student.previous_class,
        university_id=student.university_id,
        university_name=university.name,
        course_id=student.course_id,
        course_name=course.name,
        branch_id=student.branch_id,
        branch_name=branch.name if branch else None,
        course_variant_id=student.course_variant_id,
        course_type=variant.course_type,
        fee_id=student.fee_id,
        branch_specialization=student.branch_specialization,
        skills=student.skills,
        tenth_board=student.tenth_board,
        tenth_board_other=student.tenth_board_other,
        tenth_school=student.tenth_school,
        tenth_passing_year=student.tenth_passing_year,
        tenth_percentage=student.tenth_percentage,
        twelfth_board=student.twelfth_board,
        twelfth_board_other=student.twelfth_board_other,
        twelfth_school=student.twelfth_school,
        twelfth_passing_year=student.twelfth_passing_year,
        twelfth_percentage=student.twelfth_percentage,
        grad_university=student.grad_university,
        grad_degree=student.grad_degree,
        grad_passing_year=student.grad_passing_year,
        grad_percentage=student.grad_percentage,
        grad_subject=student.grad_subject,
        apaar_id=student.apaar_id,
        session=student.session,
        total_fee=fee.total_first_year if fee else None,
        commission_percentage=student.commission_percentage,
        commission_amount=student.commission_amount,
        street_locality=student.street_locality,
        city=student.city,
        district=student.district,
        state=student.state,
        pincode=student.pincode,
        contact_number=student.contact_number,
        aadhar_number=student.aadhar_number,
        franchise_id=student.franchise_id,
        franchise_name=franchise.full_name,
        status=student.status.value,
        created_at=student.created_at,
        updated_at=student.updated_at
    )

@router.get("/students", response_model=StudentListResponse)
def get_all_students(
    franchise_id: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    query = db.query(Student).options(
        selectinload(Student.franchise),
        selectinload(Student.university),
        selectinload(Student.course),
        selectinload(Student.branch),
        selectinload(Student.course_variant),
        selectinload(Student.fee)
    )

    if franchise_id:
        query = query.filter(Student.franchise_id == franchise_id)
    if start_date:
        query = query.filter(Student.created_at >= start_date)
    if end_date:
        query = query.filter(Student.created_at <= end_date)

    students = query.all()
    student_responses = [build_student_response(s) for s in students]
    return StudentListResponse(students=student_responses, total=len(student_responses))

@router.patch("/students/{student_id}/status")
def update_student_status(
    student_id: int,
    status_update: StatusUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from decimal import Decimal

    student = db.query(Student).options(
        joinedload(Student.fee)
    ).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.status = status_update.status

    if status_update.commission_percentage is not None:
        student.commission_percentage = status_update.commission_percentage
        if student.fee and student.fee.total_first_year:
            student.commission_amount = (student.fee.total_first_year * status_update.commission_percentage) / Decimal("100")
        else:
            student.commission_amount = Decimal("0.00")

    student.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(student)

    return {"message": "Status updated successfully", "status": student.status.value}

@router.patch("/students/{student_id}/commission")
def update_student_commission(
    student_id: int,
    commission_data: CommissionUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from decimal import Decimal

    student = db.query(Student).options(
        joinedload(Student.fee)
    ).filter(Student.id == student_id).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student.commission_percentage = commission_data.commission_percentage
    if student.fee and student.fee.total_first_year:
        student.commission_amount = (student.fee.total_first_year * commission_data.commission_percentage) / Decimal("100")
    else:
        student.commission_amount = Decimal("0.00")

    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)

    return {
        "message": "Commission updated successfully",
        "commission_percentage": str(student.commission_percentage),
        "commission_amount": str(student.commission_amount)
    }

@router.get("/statistics", response_model=StudentStats)
def get_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from ..models import AdmissionStatus

    total = db.query(func.count(Student.id)).scalar()
    pending = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.PENDING).scalar()
    approved = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.APPROVED).scalar()
    failed = db.query(func.count(Student.id)).filter(Student.status == AdmissionStatus.FAILED).scalar()

    return StudentStats(total=total, pending=pending, approved=approved, failed=failed)

@router.get("/franchises/statistics", response_model=List[FranchiseStats])
def get_franchise_statistics(
    db: Session = Depends(get_db),
    current_admin: User = Depends(get_current_admin)
):
    from ..models import AdmissionStatus

    franchises = db.query(User).filter(User.role == "franchise").all()

    franchise_stats = []
    for franchise in franchises:
        total = db.query(func.count(Student.id)).filter(Student.franchise_id == franchise.id).scalar()
        pending = db.query(func.count(Student.id)).filter(Student.franchise_id == franchise.id, Student.status == AdmissionStatus.PENDING).scalar()
        approved = db.query(func.count(Student.id)).filter(Student.franchise_id == franchise.id, Student.status == AdmissionStatus.APPROVED).scalar()
        failed = db.query(func.count(Student.id)).filter(Student.franchise_id == franchise.id, Student.status == AdmissionStatus.FAILED).scalar()

        franchise_stats.append(FranchiseStats(
            id=franchise.id,
            username=franchise.username,
            full_name=franchise.full_name,
            total_students=total,
            pending=pending,
            approved=approved,
            failed=failed,
            created_at=franchise.created_at,
            is_active=franchise.is_active,
            address=franchise.address,
            gst_number=franchise.gst_number,
            pan_number=franchise.pan_number,
            phone_number=franchise.phone_number,
            email=franchise.email
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
    query = db.query(Student).options(
        selectinload(Student.franchise),
        selectinload(Student.university),
        selectinload(Student.course),
        selectinload(Student.course_variant)
    )

    if franchise_id:
        query = query.filter(Student.franchise_id == franchise_id)
    if start_date:
        query = query.filter(Student.created_at >= start_date)
    if end_date:
        query = query.filter(Student.created_at <= end_date)

    students = query.all()

    output = io.StringIO()
    writer = csv.writer(output)

    writer.writerow([
        'ID', 'First Name', 'Middle Name', 'Last Name', 'DOB', 'Email',
        'Father Name', 'Mother Name', 'Previous Class',
        'University', 'Course', 'Course Type', 'Branch/Specialization',
        'Street/Locality', 'City', 'State', 'Pincode', 'Contact Number', 'Aadhar Number',
        'Franchise ID', 'Franchise Name', 'Status', 'Created At', 'Updated At'
    ])

    for student in students:
        writer.writerow([
            student.id,
            student.first_name,
            student.middle_name or '',
            student.last_name,
            student.dob.isoformat() if student.dob else '',
            student.email or '',
            student.father_name,
            student.mother_name,
            student.previous_class,
            student.university.name if student.university else '',
            student.course.name if student.course else '',
            student.course_variant.course_type if student.course_variant else '',
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

    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=all_students.csv"}
    )
