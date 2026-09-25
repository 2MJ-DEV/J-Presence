"""Student CRUD endpoints."""

import base64
import binascii

import cv2
import numpy as np
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import StudentCreate, StudentRead, StudentRegistration
from app.routes.attendance import get_detector
from src.database.connection import get_db
from src.database.repository import create_student, delete_student, get_student, list_students
from src.face.registration import RegistrationError, StudentProfile, register_student_from_frames

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
def list_registered_students(db: Session = Depends(get_db)) -> list[object]:
    """List students without returning stored face embeddings."""

    return list_students(db)


@router.post("/register", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def register_student_from_camera(
    payload: StudentRegistration, db: Session = Depends(get_db)
) -> object:
    """Register one student from several browser camera captures."""

    frames = []
    for encoded_frame in payload.frames:
        encoded_image = encoded_frame.split(",", 1)[-1]
        try:
            image_bytes = base64.b64decode(encoded_image, validate=True)
        except (ValueError, binascii.Error) as error:
            raise HTTPException(status_code=400, detail="Invalid camera image.") from error
        frame = cv2.imdecode(
            np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR
        )
        if frame is None:
            raise HTTPException(status_code=400, detail="Unsupported camera image.")
        frames.append(frame)

    profile = StudentProfile(
        full_name=payload.full_name,
        promotion=payload.promotion,
        laboratory=payload.laboratory,
        machine=payload.machine,
        phone=payload.phone,
    )
    try:
        return register_student_from_frames(
            db, profile, get_detector(), frames, minimum_captures=len(frames)
        )
    except RegistrationError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@router.post("", response_model=StudentRead, status_code=status.HTTP_201_CREATED)
def create_registered_student(
    payload: StudentCreate, db: Session = Depends(get_db)
) -> object:
    """Create a student profile with a manually validated embedding."""

    return create_student(db, **payload.model_dump())


@router.get("/{student_id}", response_model=StudentRead)
def get_registered_student(student_id: int, db: Session = Depends(get_db)) -> object:
    """Return one registered student."""

    student = get_student(db, student_id)
    if student is None:
        raise HTTPException(status_code=404, detail="Student not found.")
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_registered_student(student_id: int, db: Session = Depends(get_db)) -> None:
    """Delete a student and the related attendance records."""

    if not delete_student(db, student_id):
        raise HTTPException(status_code=404, detail="Student not found.")
