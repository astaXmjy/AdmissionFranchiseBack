from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum
from app.database import Base

class UserRole(str, Enum):
    ADMIN = "admin"
    FRANCHISE = "franchise"

class AdmissionStatus(str, Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    REJECTED = "rejected"

class User(Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    # Relationship to students
    students = relationship("Student", back_populates="franchise")

class Student(Base):
    __tablename__ = "student"

    id = Column(Integer, primary_key=True, index=True)

    # Student Details
    student_name = Column(String, nullable=False)

    # Family Details
    father_name = Column(String, nullable=False)
    mother_name = Column(String, nullable=False)

    # Academic Details
    previous_class = Column(String, nullable=False)
    course_applied = Column(String, nullable=False)
    branch_specialization = Column(String, nullable=True)
    affiliating_university = Column(String, nullable=True)

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
    status = Column(SQLEnum(AdmissionStatus), default=AdmissionStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
