from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(String(30), unique=True, nullable=False, index=True)
    name = Column(String(120), nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(30), nullable=True)
    designation = Column(String(120), nullable=True, index=True)
    department = Column(String(120), nullable=True, index=True)
    reporting_person = Column(String(120), nullable=True)
    office_location = Column(String(120), nullable=True)
    joining_date = Column(Date, nullable=True)
    employment_status = Column(String(20), nullable=False, default="Active")
    notes = Column(Text, nullable=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    assignments = relationship("AssetAssignment", back_populates="employee")


class AssetCategory(Base):
    __tablename__ = "asset_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False)
    description = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    assets = relationship("Asset", back_populates="category_rel")


class Asset(Base):
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(String(30), unique=True, nullable=False, index=True)
    asset_unique_id = Column(String(60), unique=True, nullable=False, index=True)
    asset_name = Column(String(120), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("asset_categories.id"), nullable=True)
    brand = Column(String(120), nullable=True)
    model = Column(String(120), nullable=True)
    serial_number = Column(String(120), nullable=True, unique=True)
    purchase_date = Column(Date, nullable=True)
    purchase_cost = Column(Numeric(12, 2), nullable=True)
    vendor = Column(String(120), nullable=True)
    warranty_expiry = Column(Date, nullable=True, index=True)
    asset_location = Column(String(120), nullable=True)
    status = Column(String(20), nullable=False, default="Available", index=True)
    is_deleted = Column(Boolean, nullable=False, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    category_rel = relationship("AssetCategory", back_populates="assets")
    assignments = relationship("AssetAssignment", back_populates="asset")


class AssetAssignment(Base):
    __tablename__ = "asset_assignments"

    id = Column(Integer, primary_key=True, index=True)
    assignment_id = Column(String(30), unique=True, nullable=False, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False, index=True)
    assigned_date = Column(Date, nullable=False)
    returned_date = Column(Date, nullable=True)
    assignment_status = Column(String(20), nullable=False, default="Assigned", index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    asset = relationship("Asset", back_populates="assignments")
    employee = relationship("Employee", back_populates="assignments")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(120), nullable=False)
    entity = Column(String(80), nullable=False)
    entity_id = Column(String(80), nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
