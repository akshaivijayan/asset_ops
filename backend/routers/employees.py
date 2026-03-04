from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import AssetAssignment, Employee
from ..schemas import EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/api/employees", tags=["Employees"])


def _generate_employee_code(db: Session) -> str:
    return f"EMP-{str(db.query(Employee).count() + 1).zfill(4)}"


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

    employee.employment_status = "Inactive"
    employee.is_deleted = True
    db.commit()
    return {"message": "Employee deactivated"}


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
