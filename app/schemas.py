from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from .models import UserRole, AdmissionStatus

# User schemas
class UserCreate(BaseModel):
    username: str
    password: str
    role: UserRole
    full_name: str

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    full_name: str
    created_at: datetime
    is_active: bool

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Student schemas
class StudentCreate(BaseModel):
    student_name: str = Field(..., min_length=1)
    father_name: str = Field(..., min_length=1)
    mother_name: str = Field(..., min_length=1)
    previous_class: str = Field(..., min_length=1)

    # NEW: Replace course_applied and affiliating_university with FKs
    university_id: int
    course_id: int
    # fee_id will be auto-derived from course

    branch_specialization: Optional[str] = None
    street_locality: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    state: str = Field(..., min_length=1)
    pincode: str = Field(..., min_length=1)
    contact_number: str = Field(..., min_length=1)
    aadhar_number: str = Field(..., min_length=12, max_length=12)  # 12 digits

class StudentResponse(BaseModel):
    id: int
    student_name: str
    father_name: str
    mother_name: str
    previous_class: str
    # New FK relationships
    university_id: Optional[int]
    university_name: Optional[str]
    course_id: Optional[int]
    course_name: Optional[str]
    fee_id: Optional[int]
    branch_specialization: Optional[str]
    street_locality: str
    city: str
    state: str
    pincode: str
    contact_number: str
    aadhar_number: str
    franchise_id: int
    franchise_name: str
    status: AdmissionStatus
    created_at: datetime
    updated_at: datetime

class StudentListResponse(BaseModel):
    students: List[StudentResponse]
    total: int

# Filter schemas
class DateFilter(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None

class StudentFilter(DateFilter):
    franchise_id: Optional[int] = None

# Status update schema
class StatusUpdate(BaseModel):
    status: AdmissionStatus

# Statistics schemas
class StudentStats(BaseModel):
    total: int
    pending: int
    confirmed: int
    rejected: int

class FranchiseStats(BaseModel):
    id: int
    username: str
    full_name: str
    total_students: int
    pending: int
    confirmed: int
    rejected: int
    created_at: datetime
    is_active: bool

# ===== UNIVERSITY SCHEMAS =====
class UniversityCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    accreditation: Optional[str] = Field(None, max_length=100)
    is_active: bool = True

class UniversityUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    location: Optional[str] = Field(None, max_length=255)
    accreditation: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None

class UniversityResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    location: Optional[str]
    accreditation: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class UniversitySelectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]

    class Config:
        from_attributes = True

# ===== COURSE SCHEMAS =====
class CourseCreate(BaseModel):
    university_id: int
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    duration_years: Optional[int] = Field(None, ge=1, le=10)
    degree_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: bool = True

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    duration_years: Optional[int] = Field(None, ge=1, le=10)
    degree_type: Optional[str] = Field(None, max_length=50)
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    university_id: int
    name: str
    code: Optional[str]
    duration_years: Optional[int]
    degree_type: Optional[str]
    description: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseSelectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    duration_years: Optional[int]

    class Config:
        from_attributes = True

# ===== FEE SCHEMAS =====
class FeeCreate(BaseModel):
    course_id: int
    tuition_fee: Decimal = Field(..., ge=0, decimal_places=2)
    registration_fee: Decimal = Field(..., ge=0, decimal_places=2)
    exam_fee_yearly: Decimal = Field(..., ge=0, decimal_places=2)
    other_fees: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    currency: str = Field(default="INR", max_length=10)
    academic_year: Optional[str] = Field(None, max_length=20)
    effective_from: Optional[date] = None
    is_active: bool = True

class FeeUpdate(BaseModel):
    tuition_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    registration_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    exam_fee_yearly: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    other_fees: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=10)
    academic_year: Optional[str] = Field(None, max_length=20)
    effective_from: Optional[date] = None
    is_active: Optional[bool] = None

class CourseInFeeResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    university: UniversityResponse

    class Config:
        from_attributes = True

class FeeResponse(BaseModel):
    id: int
    course_id: int
    course: Optional[CourseInFeeResponse] = None
    tuition_fee: Decimal
    registration_fee: Decimal
    exam_fee_yearly: Decimal
    other_fees: Decimal
    total_first_year: Decimal
    total_yearly: Decimal
    currency: str
    academic_year: Optional[str]
    effective_from: Optional[date]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @computed_field
    @property
    def total_fee(self) -> Decimal:
        """Alias for total_first_year for frontend compatibility"""
        return self.total_first_year

    class Config:
        from_attributes = True

class CourseWithFeeResponse(CourseResponse):
    fee: Optional[FeeResponse] = None
    university: UniversityResponse
