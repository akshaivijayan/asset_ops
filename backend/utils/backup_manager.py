from __future__ import annotations

from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import io
import json
from pathlib import Path
import zipfile

from sqlalchemy.orm import Session

from ..config import settings
from ..models import Asset, AssetAssignment, AssetCategory, AuditLog, Employee, User

BACKUP_VERSION = 1

TABLES = [
    ("users", User),
    ("employees", Employee),
    ("asset_categories", AssetCategory),
    ("assets", Asset),
    ("asset_assignments", AssetAssignment),
    ("audit_logs", AuditLog),
]

DELETE_ORDER = [AssetAssignment, Asset, AssetCategory, Employee, AuditLog, User]


def _serialize_value(value):
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    return value


def _deserialize_value(model, column_name: str, value):
    if value is None:
        return None
    col = model.__table__.columns[column_name]
    col_type = col.type.__class__.__name__.lower()
    if "date" in col_type and isinstance(value, str):
        if "datetime" in col_type:
            return datetime.fromisoformat(value)
        return date.fromisoformat(value)
    if "numeric" in col_type and isinstance(value, str):
        return Decimal(value)
    if "integer" in col_type and isinstance(value, str) and value.isdigit():
        return int(value)
    if "boolean" in col_type and isinstance(value, str):
        return value.lower() in {"1", "true", "yes"}
    return value


def _row_to_dict(row) -> dict:
    payload = {}
    for col in row.__table__.columns:
        payload[col.name] = _serialize_value(getattr(row, col.name))
    return payload


def _rows_for_model(db: Session, model) -> list[dict]:
    rows = db.query(model).order_by(model.id.asc()).all() if hasattr(model, "id") else db.query(model).all()
    return [_row_to_dict(row) for row in rows]


def build_backup_payload(db: Session) -> dict:
    tables: dict[str, list[dict]] = {}
    counts: dict[str, int] = {}

    for name, model in TABLES:
        records = _rows_for_model(db, model)
        tables[name] = records
        counts[name] = len(records)

    return {
        "version": BACKUP_VERSION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "tables": tables,
    }


def build_backup_archive_bytes(db: Session) -> tuple[bytes, str]:
    payload = build_backup_payload(db)
    payload_bytes = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    checksum = hashlib.sha256(payload_bytes).hexdigest()

    manifest = {
        "version": BACKUP_VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sha256": checksum,
        "counts": payload.get("counts", {}),
    }
    manifest_bytes = json.dumps(manifest, ensure_ascii=False, indent=2).encode("utf-8")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("backup.json", payload_bytes)
        zf.writestr("manifest.json", manifest_bytes)

    filename = f"asset-backup-{datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')}.zip"
    return buffer.getvalue(), filename


def _validate_payload_and_checksum(payload_bytes: bytes, manifest_bytes: bytes | None) -> dict:
    payload = json.loads(payload_bytes.decode("utf-8"))
    if payload.get("version") != BACKUP_VERSION:
        raise ValueError(f"Unsupported backup version: {payload.get('version')}")

    if manifest_bytes:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
        expected = manifest.get("sha256")
        actual = hashlib.sha256(payload_bytes).hexdigest()
        if expected and expected != actual:
            raise ValueError("Backup checksum validation failed")
    return payload


def parse_backup_archive_bytes(archive_bytes: bytes) -> dict:
    with zipfile.ZipFile(io.BytesIO(archive_bytes), "r") as zf:
        names = set(zf.namelist())
        if "backup.json" not in names:
            raise ValueError("Invalid archive: backup.json missing")
        payload_bytes = zf.read("backup.json")
        manifest_bytes = zf.read("manifest.json") if "manifest.json" in names else None
    return _validate_payload_and_checksum(payload_bytes, manifest_bytes)


def restore_from_payload(db: Session, payload: dict, mode: str = "replace") -> dict:
    if mode not in {"replace", "merge"}:
        raise ValueError("mode must be 'replace' or 'merge'")

    table_data = payload.get("tables", {})
    if not isinstance(table_data, dict):
        raise ValueError("Invalid payload format")

    if mode == "replace":
        for model in DELETE_ORDER:
            db.query(model).delete(synchronize_session=False)
        db.flush()

    restored_counts: dict[str, int] = {}

    for table_name, model in TABLES:
        rows = table_data.get(table_name, [])
        if not isinstance(rows, list):
            raise ValueError(f"Invalid rows format for {table_name}")

        count = 0
        for row in rows:
            normalized = {
                key: _deserialize_value(model, key, value)
                for key, value in row.items()
                if key in model.__table__.columns
            }

            if mode == "merge":
                entity_id = normalized.get("id")
                existing = db.query(model).filter(model.id == entity_id).first() if entity_id is not None else None
                if existing:
                    for key, value in normalized.items():
                        setattr(existing, key, value)
                else:
                    db.add(model(**normalized))
            else:
                db.add(model(**normalized))
            count += 1

        restored_counts[table_name] = count

    db.commit()
    return restored_counts


def backup_summary(db: Session) -> dict:
    counts = {}
    for name, model in TABLES:
        counts[name] = db.query(model).count()
    return counts


def create_snapshot_file(db: Session) -> dict:
    archive_bytes, filename = build_backup_archive_bytes(db)
    backup_dir = Path(settings.BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    target = backup_dir / filename
    target.write_bytes(archive_bytes)

    cutoff = datetime.now(timezone.utc) - timedelta(days=settings.BACKUP_RETENTION_DAYS)
    for file in backup_dir.glob("asset-backup-*.zip"):
        mtime = datetime.fromtimestamp(file.stat().st_mtime, tz=timezone.utc)
        if mtime < cutoff:
            file.unlink(missing_ok=True)

    return {"path": str(target), "filename": filename, "size_bytes": len(archive_bytes)}
