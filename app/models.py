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
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    university = relationship("University", back_populates="courses")
    fee = relationship("Fee", back_populates="course", uselist=False, cascade="all, delete-orphan")
    students = relationship("Student", back_populates="course")

    __table_args__ = (
        UniqueConstraint('university_id', 'code', name='uq_course_university_code'),
    )

class Fee(Base):
    __tablename__ = "fee"

    id = Column(Integer, primary_key=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
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
    course = relationship("Course", back_populates="fee")
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
    degree_type = Column(String(20), nullable=True)  # UG, PG, Diploma
    previous_class = Column(String, nullable=True)
    branch_specialization = Column(String, nullable=True)
    skills = Column(Text, nullable=True)

    # 10th Details
    tenth_board = Column(String(50), nullable=True)  # MP Board, CBSE, Others
    tenth_board_other = Column(String(100), nullable=True)
    tenth_school = Column(String(255), nullable=True)
    tenth_passing_year = Column(String(4), nullable=True)
    tenth_percentage = Column(String(10), nullable=True)

    # 12th Details (for UG and PG)
    twelfth_board = Column(String(50), nullable=True)
    twelfth_board_other = Column(String(100), nullable=True)
    twelfth_school = Column(String(255), nullable=True)
    twelfth_passing_year = Column(String(4), nullable=True)
    twelfth_percentage = Column(String(10), nullable=True)

    # Graduation Details (for PG)
    grad_university = Column(String(255), nullable=True)
    grad_degree = Column(String(255), nullable=True)
    grad_passing_year = Column(String(4), nullable=True)
    grad_percentage = Column(String(10), nullable=True)
    grad_subject = Column(String(255), nullable=True)

    # Commission
    commission_percentage = Column(Numeric(5, 2), nullable=True)
    commission_amount = Column(Numeric(10, 2), nullable=True)

    # Contact & Address
    street_locality = Column(String, nullable=False)
    city = Column(String, nullable=False)
    state = Column(String, nullable=False)
    pincode = Column(String, nullable=False)
    contact_number = Column(String, nullable=False)
    aadhar_number = Column(String, nullable=False)  # 12 digits, stored as string

    # Metadata
    franchise_id = Column(Integer, ForeignKey("user.id"), nullable=False)
    franchise = relationship("User", back_populates="students")

    # NEW FK columns for University, Course, Fee
    university_id = Column(Integer, ForeignKey("university.id", ondelete="SET NULL"), nullable=True, index=True)
    course_id = Column(Integer, ForeignKey("course.id", ondelete="SET NULL"), nullable=True, index=True)
    fee_id = Column(Integer, ForeignKey("fee.id", ondelete="SET NULL"), nullable=True, index=True)

    # NEW Relationships
    university = relationship("University", back_populates="students")
    course = relationship("Course", back_populates="students")
    fee = relationship("Fee", back_populates="students")

    status = Column(SQLEnum(AdmissionStatus), default=AdmissionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
