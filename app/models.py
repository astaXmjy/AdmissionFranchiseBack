from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum, Numeric, Date, Text, UniqueConstraint, Computed
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from decimal import Decimal
from app.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    FRANCHISE = "franchise"

class AdmissionStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    FAILED = "FAILED"

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    address = Column(String, nullable=True)
    gst_number = Column(String(15), nullable=True)
    pan_number = Column(String(10), nullable=True)
    phone_number = Column(String(15), nullable=True)
    email = Column(String, nullable=True)

    # Relationship to students
    students = relationship("Student", back_populates="franchise")

class University(Base):
    __tablename__ = "university"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, unique=True, index=True)
    code = Column(String(50), unique=True, nullable=True)
    location = Column(String(255), nullable=True)
    accreditation = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    courses = relationship("Course", back_populates="university", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="university")

class Course(Base):
    __tablename__ = "course"

    id = Column(Integer, primary_key=True, index=True)
    university_id = Column(Integer, ForeignKey("university.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), nullable=True)
    duration_years = Column(Integer, nullable=True)
    degree_type = Column(String(50), nullable=True)
    eligible_education = Column(String(255), nullable=True)  # Comma-separated: Class 8, Class 10, Class 12, UG, PG
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    university = relationship("University", back_populates="courses")
    branches = relationship("Branch", back_populates="course", cascade="all, delete-orphan")
    # cascade="all" (not delete-orphan) because branch-level variants also have course_id set;
    # delete-orphan would conflict when a variant belongs to both Course and Branch collections
    variants = relationship("CourseVariant", back_populates="course", cascade="all", overlaps="branch,variants")
    students = relationship("Student", back_populates="course")

    __table_args__ = (
        UniqueConstraint('university_id', 'code', name='uq_course_university_code'),
    )

class Branch(Base):
    __tablename__ = "branch"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="branches")
    variants = relationship("CourseVariant", back_populates="branch", cascade="all, delete-orphan", overlaps="course,variants")
    students = relationship("Student", back_populates="branch")

    __table_args__ = (
        UniqueConstraint('course_id', 'name', name='uq_branch_course_name'),
    )

class CourseVariant(Base):
    __tablename__ = "course_variant"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(Integer, ForeignKey("branch.id", ondelete="CASCADE"), nullable=True, index=True)
    course_type = Column(String(50), nullable=False)  # Regular, Private, Online, Distance
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course = relationship("Course", back_populates="variants", overlaps="branch,variants")
    branch = relationship("Branch", back_populates="variants", overlaps="course,variants")
    fee = relationship("Fee", back_populates="course_variant", uselist=False, cascade="all, delete-orphan")
    students = relationship("Student", back_populates="course_variant")


class Fee(Base):
    __tablename__ = "fee"

    id = Column(Integer, primary_key=True, index=True)
    course_variant_id = Column(Integer, ForeignKey("course_variant.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    tuition_fee = Column(Numeric(10, 2), nullable=False)
    registration_fee = Column(Numeric(10, 2), nullable=False)
    exam_fee_yearly = Column(Numeric(10, 2), nullable=False)
    other_fees = Column(Numeric(10, 2), default=Decimal("0.00"), nullable=False)

    # PostgreSQL Generated Columns
    total_first_year = Column(Numeric(10, 2), Computed("tuition_fee + registration_fee + exam_fee_yearly + other_fees", persisted=True))
    total_yearly = Column(Numeric(10, 2), Computed("tuition_fee + exam_fee_yearly + other_fees", persisted=True))

    currency = Column(String(10), default="INR", nullable=False)
    academic_year = Column(String(20), nullable=True)
    effective_from = Column(Date, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    course_variant = relationship("CourseVariant", back_populates="fee")
    students = relationship("Student", back_populates="fee")

class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)

    # Student Details
    first_name = Column(String, nullable=False)
    middle_name = Column(String, nullable=True)
    last_name = Column(String, nullable=False)
    dob = Column(Date, nullable=False)
    email = Column(String, nullable=True)

    # Family Details
    father_name = Column(String, nullable=False)
    mother_name = Column(String, nullable=False)

    # Academic Details
    degree_type = Column(String(20), nullable=True)
    previous_class = Column(String, nullable=True)
    branch_specialization = Column(String, nullable=True)
    skills = Column(Text, nullable=True)

    # 8th Details
    eighth_board = Column(String(50), nullable=True)
    eighth_board_other = Column(String(100), nullable=True)
    eighth_school = Column(String(255), nullable=True)
    eighth_passing_year = Column(String(4), nullable=True)
    eighth_percentage = Column(String(10), nullable=True)

    # 10th Details
    tenth_board = Column(String(50), nullable=True)
    tenth_board_other = Column(String(100), nullable=True)
    tenth_school = Column(String(255), nullable=True)
    tenth_passing_year = Column(String(4), nullable=True)
    tenth_percentage = Column(String(10), nullable=True)

    # 12th Details
    twelfth_board = Column(String(50), nullable=True)
    twelfth_board_other = Column(String(100), nullable=True)
    twelfth_school = Column(String(255), nullable=True)
    twelfth_passing_year = Column(String(4), nullable=True)
    twelfth_percentage = Column(String(10), nullable=True)

    # Graduation Details
    grad_university = Column(String(255), nullable=True)
    grad_degree = Column(String(255), nullable=True)
    grad_passing_year = Column(String(4), nullable=True)
    grad_percentage = Column(String(10), nullable=True)
    grad_subject = Column(String(255), nullable=True)

    # Commission
    commission_percentage = Column(Numeric(5, 2), nullable=True)
    commission_amount = Column(Numeric(10, 2), nullable=True)

    # IDs
    apaar_id = Column(String(50), nullable=True)
    session = Column(String(50), nullable=True)

    # Contact & Address
    street_locality = Column(String, nullable=False)
    city = Column(String, nullable=False)
    district = Column(String, nullable=True)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    aadhar_number = Column(String, nullable=False)

    # Metadata
    franchise_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    franchise = relationship("User", back_populates="students")

    # FK columns for University, Course, Branch, CourseVariant, Fee
    university_id = Column(Integer, ForeignKey("university.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="SET NULL"), nullable=True, index=True)
    branch_id = Column(Integer, ForeignKey("branch.id", ondelete="SET NULL"), nullable=True, index=True)
    course_variant_id = Column(Integer, ForeignKey("course_variant.id", ondelete="SET NULL"), nullable=True, index=True)
    fee_id = Column(Integer, ForeignKey("fee.id", ondelete="SET NULL"), nullable=True, index=True)

    # Relationships
    university = relationship("University", back_populates="students")
    course = relationship("Course", back_populates="students")
    branch = relationship("Branch", back_populates="students")
    course_variant = relationship("CourseVariant", back_populates="students")
    fee = relationship("Fee", back_populates="students")

    # Document uploads
    passport_photo = Column(String, nullable=True)
    aadhar_card_doc = Column(String, nullable=True)
    doc_eighth = Column(String, nullable=True)
    doc_tenth = Column(String, nullable=True)
    doc_twelfth = Column(String, nullable=True)
    doc_graduation = Column(String, nullable=True)

    status = Column(SQLEnum(AdmissionStatus), default=AdmissionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
