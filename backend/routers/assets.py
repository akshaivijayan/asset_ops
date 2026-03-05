from io import BytesIO, StringIO

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..models import Asset, AssetCategory, AssetAssignment, Employee
from ..schemas import AssetCreate, AssetOut, AssetUpdate

router = APIRouter(prefix="/api/assets", tags=["Assets"])


def _generate_asset_code(db: Session) -> str:
    return f"AST-{str(db.query(Asset).count() + 1).zfill(5)}"


def _get_or_create_category(db: Session, name: str | None) -> AssetCategory | None:
    if not name:
        return None
    category = db.query(AssetCategory).filter(AssetCategory.name == name.strip()).first()
    if not category:
        category = AssetCategory(name=name.strip())
        db.add(category)
        db.flush()
    return category


def _to_asset_out(asset: Asset) -> AssetOut:
    return AssetOut(
        id=asset.id,
        asset_id=asset.asset_id,
        asset_unique_id=asset.asset_unique_id,
        asset_name=asset.asset_name,
        category=asset.category_rel.name if asset.category_rel else None,
        brand=asset.brand,
        model=asset.model,
        serial_number=asset.serial_number,
        purchase_date=asset.purchase_date,
        purchase_cost=asset.purchase_cost,
        vendor=asset.vendor,
        warranty_expiry=asset.warranty_expiry,
        asset_location=asset.asset_location,
        status=asset.status,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


@router.get("", response_model=list[AssetOut])
def list_assets(
    search: str | None = None,
    category: str | None = None,
    status: str | None = None,
    assigned_employee: str | None = None,
    skip: int = 0,
    limit: int = Query(50, le=200),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    query = db.query(Asset).filter(Asset.is_deleted == False)

    if search:
        term = f"%{search}%"
        query = query.filter(or_(Asset.asset_id.ilike(term), Asset.asset_unique_id.ilike(term), Asset.asset_name.ilike(term)))
    if category:
        query = query.join(AssetCategory, isouter=True).filter(AssetCategory.name.ilike(f"%{category}%"))
    if status:
        query = query.filter(Asset.status == status)
    if assigned_employee:
        query = (
            query.join(AssetAssignment, AssetAssignment.asset_id == Asset.id)
            .join(Employee, Employee.id == AssetAssignment.employee_id)
            .filter(Employee.name.ilike(f"%{assigned_employee}%"), AssetAssignment.assignment_status == "Assigned")
        )

    assets = query.order_by(Asset.id.desc()).offset(skip).limit(limit).all()
    return [_to_asset_out(asset) for asset in assets]


@router.get("/export")
def export_assets(
    fmt: str = "csv",
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    rows = db.query(Asset).filter(Asset.is_deleted == False).order_by(Asset.id.desc()).all()
    data = [
        {
            "asset_id": row.asset_id,
            "asset_unique_id": row.asset_unique_id,
            "asset_name": row.asset_name,
            "category": row.category_rel.name if row.category_rel else None,
            "brand": row.brand,
            "model": row.model,
            "serial_number": row.serial_number,
            "purchase_date": row.purchase_date,
            "purchase_cost": row.purchase_cost,
            "vendor": row.vendor,
            "warranty_expiry": row.warranty_expiry,
            "asset_location": row.asset_location,
            "status": row.status,
        }
        for row in rows
    ]

    df = pd.DataFrame(data)
    if fmt == "csv":
        buffer = StringIO()
        df.to_csv(buffer, index=False)
        buffer.seek(0)
        return StreamingResponse(
            iter([buffer.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=assets.csv"},
        )

    if fmt == "excel":
        buffer = BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name="assets")
        buffer.seek(0)
        return StreamingResponse(
            buffer,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": "attachment; filename=assets.xlsx"},
        )

    raise HTTPException(status_code=400, detail="Format must be csv or excel")


@router.post("", response_model=AssetOut)
def create_asset(
    payload: AssetCreate,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    existing = db.query(Asset).filter(Asset.asset_unique_id == payload.asset_unique_id).first()
    if existing:
        raise HTTPException(status_code=400, detail="Asset unique ID already exists")

    category = _get_or_create_category(db, payload.category)
    body = payload.model_dump()
    body.pop("category", None)
    asset = Asset(asset_id=_generate_asset_code(db), category_id=category.id if category else None, **body)

    db.add(asset)
    db.commit()
    db.refresh(asset)
    return _to_asset_out(asset)


@router.put("/{asset_pk}", response_model=AssetOut)
def update_asset(
    asset_pk: int,
    payload: AssetUpdate,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    asset = db.query(Asset).filter(Asset.id == asset_pk, Asset.is_deleted == False).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    data = payload.model_dump(exclude_unset=True)
    if "category" in data:
        category = _get_or_create_category(db, data.pop("category"))
        asset.category_id = category.id if category else None

    for field, value in data.items():
        setattr(asset, field, value)

    db.commit()
    db.refresh(asset)
    return _to_asset_out(asset)


@router.delete("/{asset_pk}")
def delete_asset(
    asset_pk: int,
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    asset = db.query(Asset).filter(Asset.id == asset_pk, Asset.is_deleted == False).first()
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")

    asset.status = "Inactive"
    asset.is_deleted = True
    db.commit()
    return {"message": "Asset deactivated"}


@router.get("/categories")
def list_categories(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin", "viewer")),
):
    return db.query(AssetCategory).order_by(AssetCategory.name.asc()).all()
