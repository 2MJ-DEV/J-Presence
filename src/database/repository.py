"""Small repository helpers used by scripts, notebooks, and routes."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from src.database.models import Attendance, Student


def list_students(db: Session) -> list[Student]:
    """Return registered students ordered by name."""

    return list(db.scalars(select(Student).order_by(Student.full_name)).all())


def get_student(db: Session, student_id: int) -> Student | None:
    """Return one student by id."""

    return db.get(Student, student_id)


def create_student(db: Session, **student_data: object) -> Student:
    """Create and persist a student profile."""

    student = Student(**student_data)
    try:
        db.add(student)
        db.commit()
        db.refresh(student)
    except Exception:
        db.rollback()
        raise
    return student


def delete_student(db: Session, student_id: int) -> bool:
    """Delete a student and its attendance records."""

    student = get_student(db, student_id)
    if student is None:
        return False
    db.delete(student)
    db.commit()
    return True


def get_attendance_for_day(
    db: Session, student_id: int, attendance_date: date
) -> Attendance | None:
    """Return one student's attendance record for a given day."""

    return db.scalar(
        select(Attendance).where(
            Attendance.student_id == student_id,
            Attendance.date == attendance_date,
        )
    )


def list_attendance(
    db: Session, attendance_date: date | None = None
) -> list[Attendance]:
    """Return attendance records with their student relationship loaded."""

    query = select(Attendance).join(Attendance.student).order_by(
        Attendance.date.desc(), Attendance.check_in.desc(), Attendance.id
    )
    if attendance_date is not None:
        query = query.where(Attendance.date == attendance_date)
    return list(db.scalars(query).all())
