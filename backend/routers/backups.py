from io import BytesIO

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..auth import require_roles
from ..database import get_db
from ..utils.backup_manager import (
    backup_summary,
    build_backup_archive_bytes,
    create_snapshot_file,
    parse_backup_archive_bytes,
    restore_from_payload,
)

router = APIRouter(prefix="/api/backups", tags=["Backups"])


@router.get("/summary")
def get_backup_summary(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    return {"counts": backup_summary(db)}


@router.get("/export")
def export_backup(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    archive_bytes, filename = build_backup_archive_bytes(db)
    return StreamingResponse(
        BytesIO(archive_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/snapshot")
def snapshot_backup(
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    return {"message": "Backup snapshot created", **create_snapshot_file(db)}


@router.post("/restore")
def restore_backup(
    mode: str = Query("replace", description="replace|merge"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_roles("admin")),
):
    if mode not in {"replace", "merge"}:
        raise HTTPException(status_code=400, detail="mode must be replace or merge")

    try:
        content = file.file.read()
        payload = parse_backup_archive_bytes(content)
        counts = restore_from_payload(db, payload, mode=mode)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:  # noqa: BLE001
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Restore failed: {exc}")

    return {"message": "Backup restored", "mode": mode, "restored_counts": counts}
