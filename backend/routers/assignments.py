from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Asset, AssetAssignment, Employee
from ..schemas import AssignmentCreate, AssignmentOut, AssignmentReturn

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


def _generate_assignment_code(db: Session) -> str:
    return f"ASN-{str(db.query(AssetAssignment).count() + 1).zfill(5)}"


def _to_assignment_out(item: AssetAssignment) -> AssignmentOut:
    return AssignmentOut(
        id=item.id,
        assignment_id=item.assignment_id,
        asset_id=item.asset_id,
        employee_id=item.employee_id,
        assigned_date=item.assigned_date,
        returned_date=item.returned_date,
        assignment_status=item.assignment_status,
        notes=item.notes,
        asset_name=item.asset.asset_name if item.asset else None,
        asset_unique_id=item.asset.asset_unique_id if item.asset else None,
        employee_name=item.employee.name if item.employee else None,
        employee_code=item.employee.employee_id if item.employee else None,
    )


@router.get("", response_model=list[AssignmentOut])
def list_assignments(
    status: str | None = None,
    employee_id: int | None = None,
    asset_id: int | None = None,
    skip: int = 0,
    limit: int = Query(100, le=300),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    query = db.query(AssetAssignment)
    if status:
        query = query.filter(AssetAssignment.assignment_status == status)
    if employee_id:
        query = query.filter(AssetAssignment.employee_id == employee_id)
    if asset_id:
        query = query.filter(AssetAssignment.asset_id == asset_id)

    records = query.order_by(AssetAssignment.id.desc()).offset(skip).limit(limit).all()
    return [_to_assignment_out(row) for row in records]


@router.post("", response_model=AssignmentOut)
def assign_asset(
    payload: AssignmentCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    asset = db.query(Asset).filter(Asset.id == payload.asset_id, Asset.is_deleted == False).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    if asset.status != "Available":
        raise HTTPException(status_code=400, detail="Only available assets can be assigned")

    employee = db.query(Employee).filter(Employee.id == payload.employee_id, Employee.is_deleted == False).first()
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if employee.employment_status != "Active":
        raise HTTPException(status_code=400, detail="Asset cannot be assigned to inactive employee")

    assignment = AssetAssignment(
        assignment_id=_generate_assignment_code(db),
        asset_id=payload.asset_id,
        employee_id=payload.employee_id,
        assigned_date=payload.assigned_date,
        assignment_status="Assigned",
        notes=payload.notes,
    )
    asset.status = "Assigned"

    db.add(assignment)
    db.commit()
    db.refresh(assignment)
    return _to_assignment_out(assignment)


@router.put("/{assignment_pk}/return", response_model=AssignmentOut)
def return_asset(
    assignment_pk: int,
    payload: AssignmentReturn,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    assignment = db.query(AssetAssignment).filter(AssetAssignment.id == assignment_pk).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    if assignment.assignment_status == "Returned":
        raise HTTPException(status_code=400, detail="Asset already returned")

    if payload.returned_date < assignment.assigned_date:
        raise HTTPException(status_code=400, detail="Returned date cannot be before assigned date")

    assignment.returned_date = payload.returned_date
    assignment.assignment_status = "Returned"
    assignment.notes = payload.notes or assignment.notes

    asset = db.query(Asset).filter(Asset.id == assignment.asset_id).first()
    if asset and asset.status == "Assigned":
        asset.status = "Available"

    db.commit()
    db.refresh(assignment)
    return _to_assignment_out(assignment)


@router.put("/{assignment_pk}", response_model=AssignmentOut)
def update_assignment_notes(
    assignment_pk: int,
    notes: str,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    assignment = db.query(AssetAssignment).filter(AssetAssignment.id == assignment_pk).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    assignment.notes = notes
    db.commit()
    db.refresh(assignment)
    return _to_assignment_out(assignment)
