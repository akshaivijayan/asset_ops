from __future__ import annotations

import argparse
import hashlib
import re
from datetime import date
from pathlib import Path

import pandas as pd
from sqlalchemy.orm import Session

from backend.database import Base, SessionLocal, engine
from backend.models import Asset, AssetAssignment, AssetCategory, Employee


def norm(value) -> str:
    if value is None:
        return ""
    if isinstance(value, float) and pd.isna(value):
        return ""
    text = str(value).strip()
    return "" if text.lower() in {"nan", "none"} else text


def slugify(text: str) -> str:
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return text or "user"


def next_employee_code(db: Session) -> str:
    existing = db.query(Employee.employee_id).all()
    max_num = 0
    for (code,) in existing:
        match = re.search(r"(\d+)$", code or "")
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"EMP-{str(max_num + 1).zfill(4)}"


def next_asset_code(db: Session) -> str:
    existing = db.query(Asset.asset_id).all()
    max_num = 0
    for (code,) in existing:
        match = re.search(r"(\d+)$", code or "")
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"AST-{str(max_num + 1).zfill(5)}"


def next_assignment_code(db: Session) -> str:
    existing = db.query(AssetAssignment.assignment_id).all()
    max_num = 0
    for (code,) in existing:
        match = re.search(r"(\d+)$", code or "")
        if match:
            max_num = max(max_num, int(match.group(1)))
    return f"ASN-{str(max_num + 1).zfill(5)}"


def make_unique_id(prefix: str, *parts: str) -> str:
    raw = "|".join(parts)
    digest = hashlib.sha1(raw.encode("utf-8")).hexdigest()[:10].upper()
    return f"{prefix}-{digest}"


def clean_laptop_value(value: str) -> str:
    text = norm(value).replace("✔", "").replace("❌", "").strip()
    lowered = text.lower()
    if not text or lowered in {"personal", "na", "n/a", "no", "-"}:
        return ""
    return text


def infer_category(name: str) -> str:
    lowered = name.lower()
    if any(k in lowered for k in ["laptop", "macbook", "notebook"]):
        return "Laptop"
    if any(k in lowered for k in ["iphone", "mobile", "phone", "sim"]):
        return "Mobile"
    if "monitor" in lowered:
        return "Monitor"
    if "printer" in lowered:
        return "Printer"
    if "tablet" in lowered or "ipad" in lowered:
        return "Tablet"
    if any(k in lowered for k in ["chair", "table", "desk", "furniture"]):
        return "Furniture"
    if any(k in lowered for k in ["camera", "disk", "hard", "battery", "router", "firewall"]):
        return "Office Equipment"
    return "Office Equipment"


def get_or_create_category(db: Session, name: str) -> AssetCategory:
    category = db.query(AssetCategory).filter(AssetCategory.name == name).first()
    if category:
        return category
    category = AssetCategory(name=name)
    db.add(category)
    db.flush()
    return category


def generate_placeholder_email(db: Session, name: str) -> str:
    base = f"{slugify(name)}@example.com"
    candidate = base
    idx = 1
    while db.query(Employee).filter(Employee.email == candidate).first():
        idx += 1
        candidate = f"{slugify(name)}-{idx}@example.com"
    return candidate


def get_or_create_employee(
    db: Session,
    *,
    name: str,
    email: str = "",
    designation: str = "",
    reporting_person: str = "",
    department: str = "",
    office_location: str = "",
    active: bool = True,
    notes: str = "",
) -> Employee | None:
    name = norm(name)
    if not name:
        return None

    email = norm(email).lower()
    employee = None
    if email:
        employee = db.query(Employee).filter(Employee.email == email).first()
    if not employee:
        employee = db.query(Employee).filter(Employee.name == name, Employee.is_deleted == False).first()

    if employee:
        employee.designation = designation or employee.designation
        employee.reporting_person = reporting_person or employee.reporting_person
        employee.department = department or employee.department
        employee.office_location = office_location or employee.office_location
        employee.employment_status = "Active" if active else "Inactive"
        if notes:
            employee.notes = notes
        return employee

    employee = Employee(
        employee_id=next_employee_code(db),
        name=name,
        email=email or generate_placeholder_email(db, name),
        designation=designation or None,
        department=department or None,
        reporting_person=reporting_person or None,
        office_location=office_location or None,
        employment_status="Active" if active else "Inactive",
        notes=notes or None,
        is_deleted=not active,
    )
    db.add(employee)
    db.flush()
    return employee


def get_or_create_asset(
    db: Session,
    *,
    unique_id: str,
    asset_name: str,
    category_name: str,
    serial_number: str = "",
    vendor: str = "",
    model: str = "",
    location: str = "",
    status: str = "Available",
) -> Asset:
    asset = db.query(Asset).filter(Asset.asset_unique_id == unique_id).first()
    category = get_or_create_category(db, category_name)

    if asset:
        asset.asset_name = asset_name or asset.asset_name
        asset.category_id = category.id
        asset.serial_number = serial_number or asset.serial_number
        asset.vendor = vendor or asset.vendor
        asset.model = model or asset.model
        asset.asset_location = location or asset.asset_location
        asset.status = status or asset.status
        return asset

    # If serial number already belongs to another asset, do not reuse it.
    serial_value = serial_number or None
    if serial_value:
        existing_serial = db.query(Asset).filter(Asset.serial_number == serial_value).first()
        if existing_serial:
            serial_value = None

    asset = Asset(
        asset_id=next_asset_code(db),
        asset_unique_id=unique_id,
        asset_name=asset_name,
        category_id=category.id,
        serial_number=serial_value,
        vendor=vendor or None,
        model=model or None,
        asset_location=location or None,
        status=status,
        is_deleted=False,
    )
    db.add(asset)
    db.flush()
    return asset


def ensure_assignment(db: Session, asset: Asset, employee: Employee, notes: str = "") -> None:
    active = (
        db.query(AssetAssignment)
        .filter(AssetAssignment.asset_id == asset.id, AssetAssignment.assignment_status == "Assigned")
        .first()
    )
    if active:
        return

    assignment = AssetAssignment(
        assignment_id=next_assignment_code(db),
        asset_id=asset.id,
        employee_id=employee.id,
        assigned_date=date.today(),
        assignment_status="Assigned",
        notes=notes or None,
    )
    db.add(assignment)
    asset.status = "Assigned"


def import_range_assets_sheet(db: Session, df: pd.DataFrame) -> dict[str, int]:
    counters = {"employees": 0, "assets": 0, "assignments": 0}
    before_emp = db.query(Employee).count()
    before_asset = db.query(Asset).count()
    before_asn = db.query(AssetAssignment).count()

    for _, row in df.iterrows():
        name = norm(row.get("Name"))
        email = norm(row.get("Email")).lower()
        designation = norm(row.get("Designation"))
        reporting_person = norm(row.get("Reporting Person"))
        remarks = norm(row.get("Remarks"))
        active = norm(row.get("Active/Not")).lower() in {"yes", "y", "active", "1", "true"}

        employee = get_or_create_employee(
            db,
            name=name,
            email=email,
            designation=designation,
            reporting_person=reporting_person,
            active=active,
            notes=remarks,
        )
        if not employee:
            continue

        laptop = clean_laptop_value(row.get("Laptop"))
        if not laptop:
            continue

        serial = norm(row.get("Serial Number"))
        supplier = norm(row.get("Supplier"))

        unique_id = serial or make_unique_id("RNG-LAP", email, name, laptop)
        asset = get_or_create_asset(
            db,
            unique_id=unique_id,
            asset_name=laptop,
            category_name="Laptop",
            serial_number=serial,
            vendor=supplier,
            location=employee.office_location or "",
            status="Assigned" if active else "Available",
        )
        if active:
            ensure_assignment(db, asset, employee, notes=remarks)

    counters["employees"] = db.query(Employee).count() - before_emp
    counters["assets"] = db.query(Asset).count() - before_asset
    counters["assignments"] = db.query(AssetAssignment).count() - before_asn
    return counters


def status_from_condition(condition: str, has_assignee: bool) -> str:
    c = norm(condition).lower()
    if "not working" in c or "repair" in c:
        return "Under Repair"
    if has_assignee:
        return "Assigned"
    return "Available"


def import_other_assets_sheet(db: Session, df: pd.DataFrame) -> dict[str, int]:
    counters = {"employees": 0, "assets": 0, "assignments": 0}
    before_emp = db.query(Employee).count()
    before_asset = db.query(Asset).count()
    before_asn = db.query(AssetAssignment).count()

    for _, row in df.iterrows():
        entries = [
            {
                "asset_name": norm(row.get("Asset name ")),
                "assignee": norm(row.get("Name")),
                "serial": "",
                "condition": norm(row.get("Condition")),
                "remarks": norm(row.get("Remarks")),
            },
            {
                "asset_name": norm(row.get("Item Name")),
                "assignee": norm(row.get("Assign to")),
                "serial": norm(row.get("Serial Code")),
                "condition": norm(row.get("Condition")),
                "remarks": norm(row.get("Remarks")),
            },
        ]

        for item in entries:
            asset_name = item["asset_name"]
            if not asset_name:
                continue

            assignee_name = item["assignee"]
            has_assignee = bool(assignee_name)
            status = status_from_condition(item["condition"], has_assignee)

            unique_id = item["serial"] or make_unique_id("OTH", asset_name, assignee_name)
            category = infer_category(asset_name)
            asset = get_or_create_asset(
                db,
                unique_id=unique_id,
                asset_name=asset_name,
                category_name=category,
                serial_number=item["serial"],
                status=status,
            )

            if has_assignee and status == "Assigned":
                employee = get_or_create_employee(db, name=assignee_name, active=True, notes="Imported from Other Assets")
                if employee:
                    ensure_assignment(db, asset, employee, notes=item["remarks"])

    counters["employees"] = db.query(Employee).count() - before_emp
    counters["assets"] = db.query(Asset).count() - before_asset
    counters["assignments"] = db.query(AssetAssignment).count() - before_asn
    return counters


def import_printers_sheet(db: Session, df: pd.DataFrame) -> dict[str, int]:
    counters = {"assets": 0}
    before_asset = db.query(Asset).count()

    for _, row in df.iterrows():
        name = norm(row.get("Name"))
        if not name:
            continue

        serial = norm(row.get("Serial No"))
        product_no = norm(row.get("Product No"))
        location = norm(row.get("Location"))
        unique_id = serial or make_unique_id("PRN", name, location, product_no)
        get_or_create_asset(
            db,
            unique_id=unique_id,
            asset_name=name,
            category_name="Printer",
            serial_number=serial,
            model=product_no,
            location=location,
            status="Available",
        )

    counters["assets"] = db.query(Asset).count() - before_asset
    return counters


def main() -> None:
    parser = argparse.ArgumentParser(description="Import Range assets workbook into existing Asset Tracker schema.")
    parser.add_argument("--file", required=True, help="Path to Excel workbook")
    args = parser.parse_args()

    workbook = Path(args.file)
    if not workbook.exists():
        raise FileNotFoundError(f"Workbook not found: {workbook}")

    Base.metadata.create_all(bind=engine)
    xls = pd.ExcelFile(workbook)

    db = SessionLocal()
    try:
        report: dict[str, dict[str, int]] = {}

        if "Range Assets" in xls.sheet_names:
            df = pd.read_excel(xls, "Range Assets")
            report["Range Assets"] = import_range_assets_sheet(db, df)

        if "Other Assets List" in xls.sheet_names:
            df = pd.read_excel(xls, "Other Assets List")
            report["Other Assets List"] = import_other_assets_sheet(db, df)

        if "Printer Details" in xls.sheet_names:
            df = pd.read_excel(xls, "Printer Details")
            report["Printer Details"] = import_printers_sheet(db, df)

        db.commit()

        total_employees = db.query(Employee).filter(Employee.is_deleted == False).count()
        total_assets = db.query(Asset).filter(Asset.is_deleted == False).count()
        total_assignments = db.query(AssetAssignment).count()

        print("Import completed.")
        print("Sheet deltas:", report)
        print(
            f"Current totals -> employees: {total_employees}, assets: {total_assets}, assignments: {total_assignments}"
        )
    finally:
        db.close()


if __name__ == "__main__":
    main()
