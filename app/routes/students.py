"""Student CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.schemas import StudentCreate, StudentRead
from src.database.connection import get_db
from src.database.repository import create_student, delete_student, get_student, list_students

router = APIRouter(prefix="/students", tags=["students"])


@router.get("", response_model=list[StudentRead])
def list_registered_students(db: Session = Depends(get_db)) -> list[object]:
    """List students without returning stored face embeddings."""

    return list_students(db)


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
