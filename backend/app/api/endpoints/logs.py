from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.app.core.database import get_dest_db
from backend.app.models.models import IntegLog

router = APIRouter()

class LogSchema(BaseModel):
    id: int
    process_name: Optional[str] = None
    status: Optional[str] = None
    message: Optional[str] = None
    details: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True

@router.get("/", response_model=List[LogSchema])
def get_logs(
    skip: int = 0,
    limit: int = 50,
    status: Optional[str] = None,
    db: Session = Depends(get_dest_db)
):
    query = db.query(IntegLog)
    if status:
        query = query.filter(IntegLog.status == status.upper())
    return query.order_by(IntegLog.created_at.desc()).offset(skip).limit(limit).all()

@router.get("/stats")
def get_log_stats(db: Session = Depends(get_dest_db)):
    total = db.query(IntegLog).count()
    success = db.query(IntegLog).filter(IntegLog.status == "SUCCESS").count()
    error = db.query(IntegLog).filter(IntegLog.status == "ERROR").count()
    warning = db.query(IntegLog).filter(IntegLog.status == "WARNING").count()
    return {"total": total, "success": success, "error": error, "warning": warning}
