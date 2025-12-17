from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
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
    course_applied: str = Field(..., min_length=1)
    branch_specialization: Optional[str] = None
    affiliating_university: Optional[str] = None
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
    course_applied: str
    branch_specialization: Optional[str]
    affiliating_university: Optional[str]
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
