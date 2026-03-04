from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Asset, AssetAssignment, Employee
from ..schemas import EmployeeCreate, EmployeeOffboardRequest, EmployeeOnboardRequest, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _generate_employee_code(db: Session) -> str:
    return f"EMP-{str(db.query(Employee).count() + 1).zfill(4)}"


def _generate_assignment_code(db: Session) -> str:
    return f"ASN-{str(db.query(AssetAssignment).count() + 1).zfill(5)}"


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    search: str | None = None,
    designation: str | None = None,
    department: str | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    query = db.query(Employee).filter(Employee.is_deleted == False)

    if search:
        term = f"%{search}%"
        query = query.filter(or_(Employee.name.ilike(term), Employee.email.ilike(term), Employee.employee_id.ilike(term)))
    if designation:
        query = query.filter(Employee.designation.ilike(f"%{designation}%"))
    if department:
        query = query.filter(Employee.department.ilike(f"%{department}%"))

    return query.order_by(Employee.id.desc()).offset(skip).limit(limit).all()


@router.post("", response_model=EmployeeOut)
def create_employee(
    payload: EmployeeCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    exists = db.query(Employee).filter(Employee.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Employee email already exists")

    employee = Employee(employee_id=_generate_employee_code(db), **payload.model_dump())
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


@router.post("/onboard")
def onboard_employee(
    payload: EmployeeOnboardRequest,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    exists = db.query(Employee).filter(Employee.email == payload.email).first()
    if exists:
        raise HTTPException(status_code=400, detail="Employee email already exists")

    assets = []
    for asset_id in payload.asset_ids:
        asset = db.query(Asset).filter(Asset.id == asset_id, Asset.is_deleted == False).first()
        if not asset:
            raise HTTPException(status_code=404, detail=f"Asset not found: {asset_id}")
        if asset.status != "Available":
            raise HTTPException(status_code=400, detail=f"Asset is not available: {asset.asset_unique_id}")
        assets.append(asset)

    employee_data = payload.model_dump(exclude={"asset_ids", "assignment_notes"})
    employee = Employee(employee_id=_generate_employee_code(db), **employee_data)
    db.add(employee)
    db.flush()

    assigned_count = 0
    for asset in assets:
        assignment = AssetAssignment(
            assignment_id=_generate_assignment_code(db),
            asset_id=asset.id,
            employee_id=employee.id,
            assigned_date=date.today(),
            assignment_status="Assigned",
            notes=payload.assignment_notes,
        )
        db.add(assignment)
        asset.status = "Assigned"
        assigned_count += 1

    db.commit()
    db.refresh(employee)
    return {
        "message": "Employee onboarded successfully",
        "employee_id": employee.id,
        "employee_code": employee.employee_id,
        "assigned_assets": assigned_count,
    }


@router.put("/{employee_pk}", response_model=EmployeeOut)
def update_employee(
    employee_pk: int,
    payload: EmployeeUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    employee = db.query(Employee).filter(Employee.id == employee_pk, Employee.is_deleted == False).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(employee, field, value)

    db.commit()
    db.refresh(employee)
    return employee


@router.delete("/{employee_pk}")
def deactivate_employee(
    employee_pk: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    employee = db.query(Employee).filter(Employee.id == employee_pk, Employee.is_deleted == False).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    active_assignments = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.employee_id == employee.id, AssetAssignment.assignment_status == "Assigned")
        .all()
    )
    for assignment in active_assignments:
        assignment.assignment_status = "Returned"
        assignment.returned_date = date.today()
        asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
        if asset and asset.status == "Assigned":
            asset.status = "Available"

    employee.employment_status = "Inactive"
    employee.is_deleted = True
    db.commit()
    return {"message": "Employee deactivated", "returned_assets": len(active_assignments)}


@router.post("/offboard")
def offboard_employee(
    payload: EmployeeOffboardRequest,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    if not payload.confirm:
        raise HTTPException(status_code=400, detail="Confirmation is required")

    employee = db.query(Employee).filter(Employee.id == payload.employee_id, Employee.is_deleted == False).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    active_assignments = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.employee_id == employee.id, AssetAssignment.assignment_status == "Assigned")
        .all()
    )

    for assignment in active_assignments:
        assignment.assignment_status = "Returned"
        assignment.returned_date = date.today()
        if payload.notes:
            assignment.notes = payload.notes
        asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
        if asset and asset.status == "Assigned":
            asset.status = "Available"

    employee.employment_status = "Inactive"
    employee.is_deleted = True
    db.commit()
    return {
        "message": "Employee offboarded successfully",
        "employee_id": employee.id,
        "employee_code": employee.employee_id,
        "returned_assets": len(active_assignments),
    }


@router.get("/{employee_pk}/assets")
def employee_assets(
    employee_pk: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    employee = db.query(Employee).filter(Employee.id == employee_pk, Employee.is_deleted == False).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    assignments = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.employee_id == employee_pk)
        .order_by(AssetAssignment.id.desc())
        .all()
    )

    return assignments
