import os
import shutil
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from datetime import datetime
import csv
import io
from ..database import get_db
from ..auth import get_current_franchise
from ..models import User, Student, University, Course, CourseVariant, Fee, Branch
from ..schemas import (
    StudentCreate, StudentUpdate, StudentResponse, StudentListResponse, StudentStats,
    UniversitySelectResponse, CourseSelectResponse, BranchSelectResponse, FeeResponse
)
from sqlalchemy import func
from sqlalchemy.orm import joinedload

ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/jpg"}
ALLOWED_DOC_TYPES = {"image/jpeg", "image/png", "image/jpg", "application/pdf"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter()

# Allow franchises to view universities and courses for form dropdowns
@router.get("/me/degree-types")
def get_my_degree_types(
    current_franchise: User = Depends(get_current_franchise)
):
    """Return allowed degree types for the logged-in franchise"""
    all_types = ["UG", "PG", "Diploma/Certificate", "Class"]
    if current_franchise.allowed_degree_types:
        return current_franchise.allowed_degree_types.split(',')
    return all_types

@router.get("/universities/select", response_model=List[UniversitySelectResponse])
def get_universities_for_select(
    degree_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    """Get active universities for dropdown selection"""
    DEGREE_MAP = {"UG": ["Undergraduate"], "PG": ["Postgraduate"], "Diploma/Certificate": ["Diploma/Certificate"], "Class": ["Class"]}
    query = db.query(University).filter(University.is_active == True)
    if degree_type and degree_type in DEGREE_MAP:
        db_values = DEGREE_MAP[degree_type]
        query = query.filter(University.courses.any(Course.degree_type.in_(db_values) & (Course.is_active == True)))
    universities = query.all()
    return universities

@router.get("/courses/select/{university_id}", response_model=List[CourseSelectResponse])
def get_courses_for_select(
    university_id: int,
    degree_type: Optional[str] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
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

@router.get("/branches/select", response_model=List[BranchSelectResponse])
def get_branches_for_select(
    course_id: int,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    """Get active branches for a course (for dropdown selection)"""
    branches = db.query(Branch).options(
        selectinload(Branch.variants)
    ).filter(
        Branch.course_id == course_id,
        Branch.is_active == True
    ).all()
    return branches

@router.get("/fees", response_model=List[FeeResponse])
def get_fee_for_variant(
    course_variant_id: int,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    """Get fee for a specific course variant (for admission form display)"""
    fees = db.query(Fee).options(
        joinedload(Fee.course_variant).options(
            joinedload(CourseVariant.course).joinedload(Course.university),
            joinedload(CourseVariant.branch)
        )
    ).filter(Fee.course_variant_id == course_variant_id).all()

    from ..routers.admin import build_fee_response
    return [build_fee_response(f) for f in fees]


@router.post("/students", response_model=StudentResponse)
def create_student(
    student_data: StudentCreate,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    # Verify university exists
    university = db.query(University).filter(University.id == student_data.university_id).first()
    if not university:
        raise HTTPException(status_code=404, detail="University not found")

    # Verify course exists and belongs to the university
    course = db.query(Course).filter(
        Course.id == student_data.course_id,
        Course.university_id == student_data.university_id
    ).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found or doesn't belong to the selected university")

    # Verify course variant exists and belongs to the course (or course's branch)
    variant = db.query(CourseVariant).filter(
        CourseVariant.id == student_data.course_variant_id,
        CourseVariant.course_id == student_data.course_id
    ).first()
    if not variant:
        raise HTTPException(status_code=404, detail="Course variant not found or doesn't belong to the selected course")

    # Get fee for the variant (if exists)
    fee = db.query(Fee).filter(Fee.course_variant_id == student_data.course_variant_id).first()

    # Create student record
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
        franchise_id=current_franchise.id
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
        franchise_name=current_franchise.full_name,
        status=student.status.value,
        registration_number=student.registration_number,
        created_at=student.created_at,
        updated_at=student.updated_at,
        passport_photo=student.passport_photo,
        aadhar_card_doc=student.aadhar_card_doc,
        doc_eighth=student.doc_eighth,
        doc_tenth=student.doc_tenth,
        doc_twelfth=student.doc_twelfth,
        doc_graduation=student.doc_graduation,
    )

@router.patch("/students/{student_id}", response_model=StudentResponse)
def update_student(
    student_id: int,
    student_data: StudentUpdate,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    from ..models import AdmissionStatus
    student = db.query(Student).options(
        selectinload(Student.university),
        selectinload(Student.course),
        selectinload(Student.branch),
        selectinload(Student.course_variant),
        selectinload(Student.fee)
    ).filter(
        Student.id == student_id,
        Student.franchise_id == current_franchise.id
    ).first()

    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    if student.status != AdmissionStatus.PENDING:
        raise HTTPException(status_code=400, detail="Only PENDING students can be edited")

    update_data = student_data.dict(exclude_unset=True)
    update_data.pop('franchise_id', None)  # franchise cannot change ownership

    # If course_variant_id is changing, update fee_id too
    if 'course_variant_id' in update_data:
        fee = db.query(Fee).filter(Fee.course_variant_id == update_data['course_variant_id']).first()
        student.fee_id = fee.id if fee else None

    for field, value in update_data.items():
        setattr(student, field, value)

    student.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(student)

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
        franchise_name=current_franchise.full_name,
        status=student.status.value,
        registration_number=student.registration_number,
        created_at=student.created_at,
        updated_at=student.updated_at,
        passport_photo=student.passport_photo,
        aadhar_card_doc=student.aadhar_card_doc,
        doc_eighth=student.doc_eighth,
        doc_tenth=student.doc_tenth,
        doc_twelfth=student.doc_twelfth,
        doc_graduation=student.doc_graduation,
    )

@router.post("/students/{student_id}/upload-documents")
async def upload_student_documents(
    student_id: int,
    passport_photo: Optional[UploadFile] = File(None),
    aadhar_card: Optional[UploadFile] = File(None),
    doc_eighth: Optional[UploadFile] = File(None),
    doc_tenth: Optional[UploadFile] = File(None),
    doc_twelfth: Optional[UploadFile] = File(None),
    doc_graduation: Optional[UploadFile] = File(None),
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    student = db.query(Student).filter(
        Student.id == student_id,
        Student.franchise_id == current_franchise.id
    ).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    student_dir = f"media/students/{student_id}"
    os.makedirs(student_dir, exist_ok=True)

    saved = {}

    async def save_file(upload: UploadFile, field_name: str, allowed_types: set, filename: str):
        if upload.content_type not in allowed_types:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name}: unsupported file type '{upload.content_type}'. Allowed: {', '.join(allowed_types)}"
            )
        content = await upload.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(status_code=400, detail=f"{field_name}: file size must be under 5 MB")
        ext = upload.filename.rsplit(".", 1)[-1] if "." in upload.filename else "bin"
        file_path = f"{student_dir}/{filename}.{ext}"
        with open(file_path, "wb") as f:
            f.write(content)
        return file_path

    if passport_photo and passport_photo.filename:
        path = await save_file(passport_photo, "Passport Photo", ALLOWED_IMAGE_TYPES, "passport_photo")
        student.passport_photo = path
        saved["passport_photo"] = path

    if aadhar_card and aadhar_card.filename:
        path = await save_file(aadhar_card, "Aadhar Card", ALLOWED_DOC_TYPES, "aadhar_card")
        student.aadhar_card_doc = path
        saved["aadhar_card_doc"] = path

    if doc_eighth and doc_eighth.filename:
        path = await save_file(doc_eighth, "8th Marksheet", ALLOWED_DOC_TYPES, "doc_eighth")
        student.doc_eighth = path
        saved["doc_eighth"] = path

    if doc_tenth and doc_tenth.filename:
        path = await save_file(doc_tenth, "10th Marksheet", ALLOWED_DOC_TYPES, "doc_tenth")
        student.doc_tenth = path
        saved["doc_tenth"] = path

    if doc_twelfth and doc_twelfth.filename:
        path = await save_file(doc_twelfth, "12th Marksheet", ALLOWED_DOC_TYPES, "doc_twelfth")
        student.doc_twelfth = path
        saved["doc_twelfth"] = path

    if doc_graduation and doc_graduation.filename:
        path = await save_file(doc_graduation, "Graduation Certificate", ALLOWED_DOC_TYPES, "doc_graduation")
        student.doc_graduation = path
        saved["doc_graduation"] = path

    student.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Documents uploaded successfully", "files": saved}


@router.get("/students", response_model=StudentListResponse)
def get_my_students(
    status: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    from ..models import AdmissionStatus
    query = db.query(Student).options(
        selectinload(Student.university),
        selectinload(Student.course),
        selectinload(Student.branch),
        selectinload(Student.course_variant),
        selectinload(Student.fee)
    ).filter(Student.franchise_id == current_franchise.id)

    if status:
        try:
            query = query.filter(Student.status == AdmissionStatus[status])
        except KeyError:
            pass
    if start_date:
        query = query.filter(Student.created_at >= start_date)
    if end_date:
        query = query.filter(Student.created_at <= end_date)

    students = query.all()

    student_responses = []
    for student in students:
        student_responses.append(StudentResponse(
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
            total_fee=student.fee.total_first_year if student.fee else None,
            commission_percentage=student.commission_percentage,
            commission_amount=student.commission_amount,
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

    total = db.query(func.count(Student.id)).filter(Student.franchise_id == current_franchise.id).scalar()
    pending = db.query(func.count(Student.id)).filter(Student.franchise_id == current_franchise.id, Student.status == AdmissionStatus.PENDING).scalar()
    approved = db.query(func.count(Student.id)).filter(Student.franchise_id == current_franchise.id, Student.status == AdmissionStatus.APPROVED).scalar()
    failed = db.query(func.count(Student.id)).filter(Student.franchise_id == current_franchise.id, Student.status == AdmissionStatus.FAILED).scalar()

    return StudentStats(total=total, pending=pending, approved=approved, failed=failed)

@router.get("/students/csv")
def export_students_csv(
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    db: Session = Depends(get_db),
    current_franchise: User = Depends(get_current_franchise)
):
    query = db.query(Student).options(
        selectinload(Student.university),
        selectinload(Student.course),
        selectinload(Student.course_variant)
    ).filter(Student.franchise_id == current_franchise.id)

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
        'Franchise', 'Status', 'Created At', 'Updated At'
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
            current_franchise.full_name,
            student.status.value,
            student.created_at.isoformat(),
            student.updated_at.isoformat()
        ])

    output.seek(0)

    return StreamingResponse(
        io.StringIO(output.getvalue()),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=students.csv"}
    )
