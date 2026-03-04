from datetime import date
from typing import Any

import pandas as pd
from sqlalchemy.orm import Session

from ..models import Asset, AssetCategory, Employee


def _string_or_none(value: Any):
    if pd.isna(value):
        return None
    return str(value).strip()


def _date_or_none(value: Any):
    if pd.isna(value):
        return None
    if isinstance(value, date):
        return value
    parsed = pd.to_datetime(value, errors="coerce")
    if pd.isna(parsed):
        return None
    return parsed.date()


def import_employees_from_excel(db: Session, file_path: str) -> dict[str, int]:
    df = pd.read_excel(file_path)
    created = 0
    updated = 0

    for _, row in df.iterrows():
        email = _string_or_none(row.get("email"))
        name = _string_or_none(row.get("name"))
        if not email or not name:
            continue

        employee = db.query(Employee).filter(Employee.email == email).first()
        payload = {
            "name": name,
            "phone": _string_or_none(row.get("phone")),
            "designation": _string_or_none(row.get("designation")),
            "department": _string_or_none(row.get("department")),
            "reporting_person": _string_or_none(row.get("reporting_person")),
            "office_location": _string_or_none(row.get("office_location")),
            "joining_date": _date_or_none(row.get("joining_date")),
            "employment_status": _string_or_none(row.get("employment_status")) or "Active",
            "notes": _string_or_none(row.get("notes")),
        }

        if employee:
            for key, value in payload.items():
                setattr(employee, key, value)
            updated += 1
        else:
            db.add(
                Employee(
                    employee_id=f"EMP-{str(db.query(Employee).count() + 1).zfill(4)}",
                    email=email,
                    **payload,
                )
            )
            created += 1

    db.commit()
    return {"created": created, "updated": updated}


def import_assets_from_excel(db: Session, file_path: str) -> dict[str, int]:
    df = pd.read_excel(file_path)
    created = 0
    updated = 0

    for _, row in df.iterrows():
        unique_id = _string_or_none(row.get("asset_unique_id"))
        asset_name = _string_or_none(row.get("asset_name"))
        category_name = _string_or_none(row.get("category"))
        if not unique_id or not asset_name:
            continue

        category = None
        if category_name:
            category = db.query(AssetCategory).filter(AssetCategory.name == category_name).first()
            if not category:
                category = AssetCategory(name=category_name)
                db.add(category)
                db.flush()

        asset = db.query(Asset).filter(Asset.asset_unique_id == unique_id).first()
        payload = {
            "asset_name": asset_name,
            "category_id": category.id if category else None,
            "brand": _string_or_none(row.get("brand")),
            "model": _string_or_none(row.get("model")),
            "serial_number": _string_or_none(row.get("serial_number")),
            "purchase_date": _date_or_none(row.get("purchase_date")),
            "purchase_cost": row.get("purchase_cost") if not pd.isna(row.get("purchase_cost")) else None,
            "vendor": _string_or_none(row.get("vendor")),
            "warranty_expiry": _date_or_none(row.get("warranty_expiry")),
            "asset_location": _string_or_none(row.get("asset_location")),
            "status": _string_or_none(row.get("status")) or "Available",
        }

        if asset:
            for key, value in payload.items():
                setattr(asset, key, value)
            updated += 1
        else:
            db.add(
                Asset(
                    asset_id=f"AST-{str(db.query(Asset).count() + 1).zfill(5)}",
                    asset_unique_id=unique_id,
                    **payload,
                )
            )
            created += 1

    db.commit()
    return {"created": created, "updated": updated}
