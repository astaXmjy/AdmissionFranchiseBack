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
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class UserResponse(BaseModel):
    id: int
    username: str
    role: UserRole
    full_name: str
    created_at: datetime
    is_active: bool
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# Student schemas
class StudentCreate(BaseModel):
    first_name: str = Field(..., min_length=1)
    middle_name: Optional[str] = None
    last_name: str = Field(..., min_length=1)
    dob: date
    email: Optional[str] = None
    father_name: str = Field(..., min_length=1)
    mother_name: str = Field(..., min_length=1)

    # Academic Details
    degree_type: str = Field(..., min_length=1)
    previous_class: Optional[str] = None
    university_id: int
    course_id: int
    branch_id: Optional[int] = None
    course_variant_id: int
    branch_specialization: Optional[str] = None
    skills: Optional[str] = None

    # 8th Details
    eighth_board: Optional[str] = None
    eighth_board_other: Optional[str] = None
    eighth_school: Optional[str] = None
    eighth_passing_year: Optional[str] = None
    eighth_percentage: Optional[str] = None

    # 10th Details
    tenth_board: Optional[str] = None
    tenth_board_other: Optional[str] = None
    tenth_school: Optional[str] = None
    tenth_passing_year: Optional[str] = None
    tenth_percentage: Optional[str] = None

    # 12th Details
    twelfth_board: Optional[str] = None
    twelfth_board_other: Optional[str] = None
    twelfth_school: Optional[str] = None
    twelfth_passing_year: Optional[str] = None
    twelfth_percentage: Optional[str] = None

    # Graduation Details
    grad_university: Optional[str] = None
    grad_degree: Optional[str] = None
    grad_passing_year: Optional[str] = None
    grad_percentage: Optional[str] = None
    grad_subject: Optional[str] = None

    # IDs
    apaar_id: Optional[str] = None
    session: Optional[str] = None

    # Contact & Address
    street_locality: str = Field(..., min_length=1)
    city: str = Field(..., min_length=1)
    district: Optional[str] = None
    state: str = Field(..., min_length=1)
    pincode: str = Field(..., min_length=1)
    contact_number: str = Field(..., min_length=1)
    aadhar_number: str = Field(..., min_length=12, max_length=12)

class StudentCreateAdmin(StudentCreate):
    franchise_id: int

class StudentUpdate(BaseModel):
    first_name: Optional[str] = None
    middle_name: Optional[str] = None
    last_name: Optional[str] = None
    dob: Optional[date] = None
    email: Optional[str] = None
    father_name: Optional[str] = None
    mother_name: Optional[str] = None
    degree_type: Optional[str] = None
    previous_class: Optional[str] = None
    university_id: Optional[int] = None
    course_id: Optional[int] = None
    branch_id: Optional[int] = None
    course_variant_id: Optional[int] = None
    branch_specialization: Optional[str] = None
    skills: Optional[str] = None
    eighth_board: Optional[str] = None
    eighth_board_other: Optional[str] = None
    eighth_school: Optional[str] = None
    eighth_passing_year: Optional[str] = None
    eighth_percentage: Optional[str] = None
    tenth_board: Optional[str] = None
    tenth_board_other: Optional[str] = None
    tenth_school: Optional[str] = None
    tenth_passing_year: Optional[str] = None
    tenth_percentage: Optional[str] = None
    twelfth_board: Optional[str] = None
    twelfth_board_other: Optional[str] = None
    twelfth_school: Optional[str] = None
    twelfth_passing_year: Optional[str] = None
    twelfth_percentage: Optional[str] = None
    grad_university: Optional[str] = None
    grad_degree: Optional[str] = None
    grad_passing_year: Optional[str] = None
    grad_percentage: Optional[str] = None
    grad_subject: Optional[str] = None
    apaar_id: Optional[str] = None
    session: Optional[str] = None
    street_locality: Optional[str] = None
    city: Optional[str] = None
    district: Optional[str] = None
    state: Optional[str] = None
    pincode: Optional[str] = None
    contact_number: Optional[str] = None
    aadhar_number: Optional[str] = None
    franchise_id: Optional[int] = None

class StudentResponse(BaseModel):
    id: int
    first_name: str
    middle_name: Optional[str]
    last_name: str
    dob: date
    email: Optional[str]
    father_name: str
    mother_name: str

    # Academic Details
    degree_type: Optional[str] = None
    previous_class: Optional[str] = None
    university_id: Optional[int]
    university_name: Optional[str]
    course_id: Optional[int]
    course_name: Optional[str]
    branch_id: Optional[int] = None
    branch_name: Optional[str] = None
    course_variant_id: Optional[int] = None
    course_type: Optional[str] = None
    fee_id: Optional[int]
    branch_specialization: Optional[str]
    skills: Optional[str] = None

    # 8th Details
    eighth_board: Optional[str] = None
    eighth_board_other: Optional[str] = None
    eighth_school: Optional[str] = None
    eighth_passing_year: Optional[str] = None
    eighth_percentage: Optional[str] = None

    # 10th Details
    tenth_board: Optional[str] = None
    tenth_board_other: Optional[str] = None
    tenth_school: Optional[str] = None
    tenth_passing_year: Optional[str] = None
    tenth_percentage: Optional[str] = None

    # 12th Details
    twelfth_board: Optional[str] = None
    twelfth_board_other: Optional[str] = None
    twelfth_school: Optional[str] = None
    twelfth_passing_year: Optional[str] = None
    twelfth_percentage: Optional[str] = None

    # Graduation Details
    grad_university: Optional[str] = None
    grad_degree: Optional[str] = None
    grad_passing_year: Optional[str] = None
    grad_percentage: Optional[str] = None
    grad_subject: Optional[str] = None

    # Fee & Commission
    total_fee: Optional[Decimal] = None
    commission_percentage: Optional[Decimal] = None
    commission_amount: Optional[Decimal] = None

    # IDs
    apaar_id: Optional[str] = None
    session: Optional[str] = None

    # Contact & Address
    street_locality: str
    city: str
    district: Optional[str] = None
    state: str
    pincode: str
    contact_number: str
    aadhar_number: str
    franchise_id: int
    franchise_name: str
    status: AdmissionStatus
    created_at: datetime
    updated_at: datetime

    # Document uploads
    passport_photo: Optional[str] = None
    aadhar_card_doc: Optional[str] = None
    doc_eighth: Optional[str] = None
    doc_tenth: Optional[str] = None
    doc_twelfth: Optional[str] = None
    doc_graduation: Optional[str] = None

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
    commission_percentage: Optional[Decimal] = None

class CommissionUpdate(BaseModel):
    commission_percentage: Decimal = Field(..., ge=0, le=100)

# Statistics schemas
class StudentStats(BaseModel):
    total: int
    pending: int
    approved: int
    failed: int

class FranchiseStats(BaseModel):
    id: int
    username: str
    full_name: str
    total_students: int
    pending: int
    approved: int
    failed: int
    created_at: datetime
    is_active: bool
    address: Optional[str] = None
    gst_number: Optional[str] = None
    pan_number: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None

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

# ===== COURSE VARIANT SCHEMAS =====
class CourseVariantCreate(BaseModel):
    course_type: str = Field(..., min_length=1, max_length=50)
    is_active: bool = True

class CourseVariantResponse(BaseModel):
    id: int
    course_id: int
    branch_id: Optional[int] = None
    course_type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseVariantSelectResponse(BaseModel):
    id: int
    course_type: str
    branch_id: Optional[int] = None

    class Config:
        from_attributes = True

# ===== BRANCH SCHEMAS =====
class BranchCreate(BaseModel):
    course_id: int
    name: str = Field(..., min_length=1, max_length=255)
    is_active: bool = True

class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    is_active: Optional[bool] = None

class BranchResponse(BaseModel):
    id: int
    course_id: int
    name: str
    is_active: bool
    variants: List[CourseVariantResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class BranchSelectResponse(BaseModel):
    id: int
    name: str
    variants: List[CourseVariantSelectResponse] = []

    class Config:
        from_attributes = True

# ===== COURSE SCHEMAS =====
class CourseCreate(BaseModel):
    university_id: int
    name: str = Field(..., min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    duration_years: Optional[int] = Field(None, ge=1, le=10)
    degree_type: Optional[str] = Field(None, max_length=50)
    eligible_education: Optional[List[str]] = None  # e.g., ["Class 10", "Class 12"]
    course_types: Optional[List[str]] = None  # List of types to auto-create variants
    description: Optional[str] = None
    is_active: bool = True

class CourseUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    code: Optional[str] = Field(None, max_length=50)
    duration_years: Optional[int] = Field(None, ge=1, le=10)
    degree_type: Optional[str] = Field(None, max_length=50)
    eligible_education: Optional[List[str]] = None  # e.g., ["Class 10", "Class 12"]
    course_types: Optional[List[str]] = None  # Update variants
    description: Optional[str] = None
    is_active: Optional[bool] = None

class CourseResponse(BaseModel):
    id: int
    university_id: int
    name: str
    code: Optional[str]
    duration_years: Optional[int]
    degree_type: Optional[str]
    eligible_education: Optional[str]
    description: Optional[str]
    is_active: bool
    variants: List[CourseVariantResponse] = []
    branches: List[BranchResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class CourseSelectResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    duration_years: Optional[int]
    eligible_education: Optional[str]
    variants: List[CourseVariantSelectResponse] = []
    branches: List[BranchSelectResponse] = []

    class Config:
        from_attributes = True

# ===== FEE SCHEMAS =====
class FeeCreate(BaseModel):
    course_variant_id: int
    tuition_fee: Decimal = Field(..., ge=0, decimal_places=2)
    registration_fee: Decimal = Field(..., ge=0, decimal_places=2)
    exam_fee_yearly: Decimal = Field(..., ge=0, decimal_places=2)
    other_fees: Decimal = Field(default=Decimal("0.00"), ge=0, decimal_places=2)
    currency: str = Field(default="INR", max_length=10)
    academic_year: Optional[str] = Field(None, max_length=20)
    effective_from: Optional[date] = None
    is_active: bool = True

class FeeUpdate(BaseModel):
    course_variant_id: Optional[int] = None
    tuition_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    registration_fee: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    exam_fee_yearly: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    other_fees: Optional[Decimal] = Field(None, ge=0, decimal_places=2)
    currency: Optional[str] = Field(None, max_length=10)
    academic_year: Optional[str] = Field(None, max_length=20)
    effective_from: Optional[date] = None
    is_active: Optional[bool] = None

class BranchInFeeResponse(BaseModel):
    id: int
    name: str

    class Config:
        from_attributes = True

class CourseVariantInFeeResponse(BaseModel):
    id: int
    course_type: str
    branch_id: Optional[int] = None
    branch: Optional[BranchInFeeResponse] = None
    course: Optional["CourseInFeeResponse"] = None

    class Config:
        from_attributes = True

class CourseInFeeResponse(BaseModel):
    id: int
    name: str
    code: Optional[str]
    university: UniversityResponse

    class Config:
        from_attributes = True

class FeeResponse(BaseModel):
    id: int
    course_variant_id: int
    course_variant: Optional[CourseVariantInFeeResponse] = None
    branch_name: Optional[str] = None
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
    university: UniversityResponse
