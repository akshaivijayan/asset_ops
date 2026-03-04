from datetime import date, timedelta
from io import BytesIO, StringIO
import tempfile

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Asset, AssetAssignment, Employee
from ..schemas import DashboardStats
from ..utils.excel_import import import_assets_from_excel, import_employees_from_excel

router = APIRouter(prefix="/api/reports", tags=["Reports"])


@router.get("/dashboard", response_model=DashboardStats)
def dashboard_stats(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    return DashboardStats(
        total_employees=db.query(Employee).filter(Employee.is_deleted == False).count(),
        total_assets=db.query(Asset).filter(Asset.is_deleted == False).count(),
        assigned_assets=db.query(Asset).filter(Asset.status == "Assigned", Asset.is_deleted == False).count(),
        available_assets=db.query(Asset).filter(Asset.status == "Available", Asset.is_deleted == False).count(),
        under_repair_assets=db.query(Asset).filter(Asset.status == "Under Repair", Asset.is_deleted == False).count(),
    )


@router.get("/recent-assignments")
def recent_assignments(
    limit: int = 10,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    rows = db.query(AssetAssignment).order_by(AssetAssignment.id.desc()).limit(limit).all()
    return [
        {
            "assignment_id": row.assignment_id,
            "asset_name": row.asset.asset_name if row.asset else None,
            "asset_unique_id": row.asset.asset_unique_id if row.asset else None,
            "employee_name": row.employee.name if row.employee else None,
            "assigned_date": row.assigned_date,
            "status": row.assignment_status,
        }
        for row in rows
    ]


@router.get("/assets-by-employee")
def assets_by_employee(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    rows = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.assignment_status == "Assigned")
        .order_by(AssetAssignment.id.desc())
        .all()
    )
    return [
        {
            "employee_id": row.employee.employee_id if row.employee else None,
            "employee_name": row.employee.name if row.employee else None,
            "department": row.employee.department if row.employee else None,
            "asset_id": row.asset.asset_id if row.asset else None,
            "asset_unique_id": row.asset.asset_unique_id if row.asset else None,
            "asset_name": row.asset.asset_name if row.asset else None,
            "category": row.asset.category_rel.name if row.asset and row.asset.category_rel else None,
            "assigned_date": row.assigned_date,
        }
        for row in rows
    ]


@router.get("/unassigned-assets")
def unassigned_assets(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    rows = db.query(Asset).filter(Asset.status == "Available", Asset.is_deleted == False).all()
    return [
        {
            "asset_id": row.asset_id,
            "asset_unique_id": row.asset_unique_id,
            "asset_name": row.asset_name,
            "category": row.category_rel.name if row.category_rel else None,
            "location": row.asset_location,
            "status": row.status,
        }
        for row in rows
    ]


@router.get("/under-repair")
def under_repair_assets(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    rows = db.query(Asset).filter(Asset.status == "Under Repair", Asset.is_deleted == False).all()
    return [
        {
            "asset_id": row.asset_id,
            "asset_unique_id": row.asset_unique_id,
            "asset_name": row.asset_name,
            "location": row.asset_location,
            "vendor": row.vendor,
        }
        for row in rows
    ]


@router.get("/warranty-expiring")
def warranty_expiring(
    days: int = 30,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    start = date.today()
    end = start + timedelta(days=days)
    rows = (
        db.query(Asset)
        .filter(Asset.warranty_expiry.isnot(None), Asset.warranty_expiry.between(start, end), Asset.is_deleted == False)
        .all()
    )
    return [
        {
            "asset_id": row.asset_id,
            "asset_unique_id": row.asset_unique_id,
            "asset_name": row.asset_name,
            "warranty_expiry": row.warranty_expiry,
            "vendor": row.vendor,
        }
        for row in rows
    ]


def _export_dataframe(data: list[dict], fmt: str, filename_base: str):
    df = pd.DataFrame(data)
    if fmt == "csv":
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.csv"},
        )

    if fmt == "excel":
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="report")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment; filename={filename_base}.xlsx"},
        )

    raise HTTPException(status_code=400, detail="Format must be csv or excel")


@router.get("/export/{report_name}")
def export_report(
    report_name: str,
    fmt: str = "csv",
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    loaders = {
        "assets-by-employee": assets_by_employee,
        "unassigned-assets": unassigned_assets,
        "under-repair": under_repair_assets,
        "warranty-expiring": warranty_expiring,
    }

    if report_name not in loaders:
        raise HTTPException(status_code=404, detail="Unknown report name")

    data = loaders[report_name](db=db, _=None)
    return _export_dataframe(data=data, fmt=fmt, filename_base=report_name)


@router.post("/import/employees")
def import_employees(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    suffix = ".xlsx" if file.filename and file.filename.endswith(".xlsx") else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file.file.read())
        temp_path = temp.name

    result = import_employees_from_excel(db, temp_path)
    return {"message": "Employees imported", **result}


@router.post("/import/assets")
def import_assets(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    suffix = ".xlsx" if file.filename and file.filename.endswith(".xlsx") else ".xls"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
        temp.write(file.file.read())
        temp_path = temp.name

    result = import_assets_from_excel(db, temp_path)
    return {"message": "Assets imported", **result}
