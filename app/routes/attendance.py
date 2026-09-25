"""Attendance API endpoints."""

import base64
import binascii
from datetime import date, datetime
from functools import lru_cache

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.schemas import AttendanceAction, AttendanceRead, DetectionFrame
from src.attendance.service import AttendanceService
from src.config.settings import get_settings
from src.database.connection import get_db
from src.database.models import UnknownDetection
from src.database.repository import list_attendance, list_students, list_unknown_detections
from src.face.detector import InsightFaceDetector

router = APIRouter(prefix="/attendance", tags=["attendance"])


@lru_cache(maxsize=1)
def get_detector() -> InsightFaceDetector:
    """Load InsightFace once instead of reloading the model for every frame."""

    settings = get_settings()
    return InsightFaceDetector(settings.model_name)


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


@router.get("/unknown")
def get_unknown_detections(db: Session = Depends(get_db)) -> list[dict[str, object]]:
    """Return the latest unknown face detections."""

    return [
        {
            "id": detection.id,
            "detected_at": detection.detected_at,
            "confidence": detection.confidence,
            "bbox": detection.bbox,
            "image_url": f"/attendance/unknown/{detection.id}/image"
            if detection.image_data
            else None,
        }
        for detection in list_unknown_detections(db)
    ]


@router.get("/unknown/{detection_id}/image")
def get_unknown_detection_image(
    detection_id: int, db: Session = Depends(get_db)
) -> Response:
    """Return the cropped face image for one unknown detection."""

    detection = db.get(UnknownDetection, detection_id)
    if detection is None or detection.image_data is None:
        raise HTTPException(status_code=404, detail="Unknown face image not found.")
    return Response(content=detection.image_data, media_type="image/jpeg")


@router.post("/detect")
def detect_frame(
    payload: DetectionFrame, db: Session = Depends(get_db)
) -> dict[str, object]:
    """Detect and recognize faces from one browser camera frame."""

    encoded_image = payload.image.split(",", 1)[-1]
    try:
        image_bytes = base64.b64decode(encoded_image, validate=True)
    except (ValueError, binascii.Error) as error:
        raise HTTPException(status_code=400, detail="Invalid camera image.") from error

    frame = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None:
        raise HTTPException(status_code=400, detail="Unsupported camera image.")

    settings = get_settings()
    service = AttendanceService(db, settings.cooldown_seconds)
    students = list_students(db)
    students_by_id = {student.id: student for student in students}
    results = service.process_frame(
        frame,
        get_detector(),
        students,
        settings.face_recognition_threshold,
    )
    detections = []
    for result in results:
        student = students_by_id.get(result.recognition.student_id)
        detections.append(
            {
                "bbox": result.bbox,
                "score": round(result.recognition.score, 3),
                "student_id": result.recognition.student_id,
                "full_name": student.full_name if student else None,
                "action": result.attendance.action if result.attendance else None,
            }
        )
    return {"detections": detections}


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
