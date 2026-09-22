"""Attendance API endpoints."""

from datetime import date, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.schemas import AttendanceAction, AttendanceRead
from src.attendance.service import AttendanceService
from src.config.settings import get_settings
from src.database.connection import get_db
from src.database.repository import list_attendance

router = APIRouter(prefix="/attendance", tags=["attendance"])


def serialize_attendance(record: object) -> dict[str, object]:
    """Build the journal row expected by the API and templates."""

    student = record.student
    return {
        "id": record.id,
        "student_id": record.student_id,
        "full_name": student.full_name,
        "promotion": student.promotion,
        "laboratory": student.laboratory,
        "machine": student.machine,
        "phone": student.phone,
        "date": record.date,
        "check_in": record.check_in,
        "check_out": record.check_out,
        "status": record.status,
    }


@router.get("", response_model=list[AttendanceRead])
def get_attendance(
    attendance_date: date | None = None, db: Session = Depends(get_db)
) -> list[dict[str, object]]:
    """Return the journal, optionally filtered by date."""

    return [serialize_attendance(row) for row in list_attendance(db, attendance_date)]


@router.get("/today", response_model=list[AttendanceRead])
def get_today_attendance(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    """Return today's journal."""

    return get_attendance(date.today(), db)


@router.post("/check-in", response_model=AttendanceRead)
def check_in(payload: AttendanceAction, db: Session = Depends(get_db)) -> dict[str, object]:
    """Record an explicit check-in."""

    try:
        event = AttendanceService(db, get_settings().cooldown_seconds).record_check_in(
            payload.student_id, datetime.now()
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_attendance(event.attendance)


@router.post("/check-out", response_model=AttendanceRead)
def check_out(payload: AttendanceAction, db: Session = Depends(get_db)) -> dict[str, object]:
    """Record an explicit check-out."""

    try:
        event = AttendanceService(db, get_settings().cooldown_seconds).record_check_out(
            payload.student_id, datetime.now()
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return serialize_attendance(event.attendance)
