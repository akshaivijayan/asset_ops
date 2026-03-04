from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    name: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class UserBase(BaseModel):
    name: str
    email: EmailStr
    role: str


class UserCreate(UserBase):
    password: str


class UserOut(UserBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeBase(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    reporting_person: Optional[str] = None
    office_location: Optional[str] = None
    joining_date: Optional[date] = None
    employment_status: str = "Active"
    notes: Optional[str] = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    designation: Optional[str] = None
    department: Optional[str] = None
    reporting_person: Optional[str] = None
    office_location: Optional[str] = None
    joining_date: Optional[date] = None
    employment_status: Optional[str] = None
    notes: Optional[str] = None


class EmployeeOut(EmployeeBase):
    id: int
    employee_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EmployeeOnboardRequest(EmployeeBase):
    asset_ids: list[int] = []
    assignment_notes: Optional[str] = None


class EmployeeOffboardRequest(BaseModel):
    employee_id: int
    confirm: bool = False
    notes: Optional[str] = None


class AssetCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class AssetCategoryOut(AssetCategoryBase):
    id: int

    model_config = ConfigDict(from_attributes=True)


class AssetBase(BaseModel):
    asset_unique_id: str
    asset_name: str
    category: str
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    vendor: Optional[str] = None
    warranty_expiry: Optional[date] = None
    asset_location: Optional[str] = None
    status: str = "Available"


class AssetCreate(AssetBase):
    pass


class AssetUpdate(BaseModel):
    asset_unique_id: Optional[str] = None
    asset_name: Optional[str] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    vendor: Optional[str] = None
    warranty_expiry: Optional[date] = None
    asset_location: Optional[str] = None
    status: Optional[str] = None


class AssetOut(BaseModel):
    id: int
    asset_id: str
    asset_unique_id: str
    asset_name: str
    category: Optional[str] = None
    brand: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    purchase_date: Optional[date] = None
    purchase_cost: Optional[Decimal] = None
    vendor: Optional[str] = None
    warranty_expiry: Optional[date] = None
    asset_location: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AssignmentBase(BaseModel):
    asset_id: int
    employee_id: int
    assigned_date: date
    notes: Optional[str] = None


class AssignmentCreate(AssignmentBase):
    pass


class AssignmentReturn(BaseModel):
    returned_date: date
    notes: Optional[str] = None


class AssignmentOut(BaseModel):
    id: int
    assignment_id: str
    asset_id: int
    employee_id: int
    assigned_date: date
    returned_date: Optional[date] = None
    assignment_status: str
    notes: Optional[str] = None
    asset_name: Optional[str] = None
    asset_unique_id: Optional[str] = None
    employee_name: Optional[str] = None
    employee_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class DashboardStats(BaseModel):
    total_employees: int
    total_assets: int
    assigned_assets: int
    available_assets: int
    under_repair_assets: int
