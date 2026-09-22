"""Behavior tests for face registration, recognition, and attendance."""

from dataclasses import dataclass
from datetime import datetime

import numpy as np
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from src.attendance.service import AttendanceService
from src.database.models import Base, Student
from src.face.registration import (
    RegistrationError,
    StudentProfile,
    register_student_from_frames,
)
from src.face.recognition import recognize_embedding


@dataclass
class FakeDetection:
    embedding: np.ndarray


class FakeDetector:
    def __init__(self, detections: list[list[FakeDetection]]) -> None:
        self.detections = detections

    def detect(self, frame: np.ndarray) -> list[FakeDetection]:
        del frame
        return self.detections.pop(0)


@pytest.fixture
def db() -> Session:
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_registration_requires_one_face_and_stores_average(db: Session) -> None:
    detector = FakeDetector(
        [
            [FakeDetection(np.array([1.0, 0.0]))],
            [FakeDetection(np.array([0.0, 1.0]))],
        ]
    )
    profile = StudentProfile("Ada Lovelace", "BAC 4 IA", "IA", "PERSO")

    student = register_student_from_frames(
        db, profile, detector, [np.zeros((2, 2)), np.ones((2, 2))], minimum_captures=2
    )

    assert student.id is not None
    assert student.full_name == "Ada Lovelace"
    assert len(student.face_embedding or []) == 2
    assert np.isclose(np.linalg.norm(student.face_embedding or []), 1.0)


def test_registration_rejects_multiple_faces(db: Session) -> None:
    detector = FakeDetector(
        [[FakeDetection(np.array([1.0, 0.0])), FakeDetection(np.array([0.0, 1.0]))]]
    )

    with pytest.raises(RegistrationError, match="exactly one face"):
        register_student_from_frames(
            db,
            StudentProfile("Ada", "BAC 4", "IA", "PERSO"),
            detector,
            [np.zeros((2, 2))],
        )


def test_recognition_returns_unknown_for_empty_or_below_threshold() -> None:
    unknown = recognize_embedding(np.array([1.0, 0.0]), {}, threshold=0.55)
    below_threshold = recognize_embedding(
        np.array([1.0, 0.0]), {1: [0.0, 1.0]}, threshold=0.55
    )

    assert unknown.student_id is None
    assert not unknown.is_known
    assert below_threshold.student_id is None
    assert not below_threshold.is_known


def test_recognition_returns_best_known_student() -> None:
    result = recognize_embedding(
        np.array([1.0, 0.0]),
        {1: [0.7, 0.7], 2: [1.0, 0.0]},
        threshold=0.8,
    )

    assert result.student_id == 2
    assert result.is_known


def test_attendance_records_check_in_check_out_and_ignores_repeated_frames(
    db: Session,
) -> None:
    student = Student(
        full_name="Ada Lovelace",
        promotion="BAC 4 IA",
        laboratory="IA",
        machine="PERSO",
        face_embedding=[1.0, 0.0],
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    service = AttendanceService(db, cooldown_seconds=10)
    first = datetime(2026, 9, 22, 8, 2)

    check_in = service.record_detection(student.id, first)
    repeated = service.record_detection(student.id, first.replace(second=5))
    check_out = service.record_detection(student.id, first.replace(hour=12, minute=17))
    already_closed = service.record_detection(student.id, first.replace(hour=14))

    assert check_in.action == "check_in"
    assert repeated.action == "already_present"
    assert check_out.action == "check_out"
    assert already_closed.action == "already_closed"
    assert check_in.attendance is check_out.attendance
    assert check_out.attendance is not None
    assert check_out.attendance.check_in is not None
    assert check_out.attendance.check_out is not None


def test_unknown_frame_does_not_create_attendance(db: Session) -> None:
    student = Student(
        full_name="Ada Lovelace",
        promotion="BAC 4 IA",
        laboratory="IA",
        machine="PERSO",
        face_embedding=[1.0, 0.0],
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    service = AttendanceService(db)
    detector = FakeDetector([ [FakeDetection(np.array([0.0, 1.0]))] ])

    results = service.process_frame(
        np.zeros((2, 2)), detector, [student], threshold=0.8,
        occurred_at=datetime(2026, 9, 22, 8, 2),
    )

    assert len(results) == 1
    assert not results[0].recognition.is_known
    assert results[0].attendance is None
    assert student.attendance_records == []


def test_explicit_check_in_and_check_out_are_idempotent(db: Session) -> None:
    student = Student(
        full_name="Ada Lovelace",
        promotion="BAC 4 IA",
        laboratory="IA",
        machine="PERSO",
        face_embedding=[1.0, 0.0],
    )
    db.add(student)
    db.commit()
    db.refresh(student)
    service = AttendanceService(db)
    moment = datetime(2026, 9, 22, 8, 2)

    first = service.record_check_in(student.id, moment)
    repeated = service.record_check_in(student.id, moment.replace(minute=3))
    checkout = service.record_check_out(student.id, moment.replace(hour=12))
    repeated_checkout = service.record_check_out(student.id, moment.replace(hour=13))

    assert first.action == "check_in"
    assert repeated.action == "ignored_cooldown"
    assert checkout.action == "check_out"
    assert repeated_checkout.action == "already_closed"