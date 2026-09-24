"""Student registration from validated face captures."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from sqlalchemy.orm import Session

from src.database.models import Student
from src.face.embedding import normalize_embedding


class FaceDetector(Protocol):
	"""Minimal detector contract needed by the registration workflow."""

	def detect(self, frame: np.ndarray) -> list[object]:
		"""Return detected faces for one frame."""


@dataclass(frozen=True)
class StudentProfile:
	"""Profile fields supplied by an administrator during registration."""

	full_name: str
	promotion: str
	laboratory: str
	machine: str
	phone: str | None = None


class RegistrationError(ValueError):
	"""Raised when a capture cannot produce a safe student registration."""


def _validate_profile(profile: StudentProfile) -> None:
	"""Reject missing required profile values before writing to the database."""

	required_fields = {
		"full_name": profile.full_name,
		"promotion": profile.promotion,
		"laboratory": profile.laboratory,
		"machine": profile.machine,
	}
	if any(not value.strip() for value in required_fields.values()):
		raise RegistrationError("All student profile fields are required.")


def _embedding_from_detection(detection: object) -> np.ndarray:
	"""Extract and normalize one detector embedding."""

	embedding = getattr(detection, "embedding", None)
	if embedding is None:
		raise RegistrationError("The detected face has no embedding.")
	try:
		return normalize_embedding(np.asarray(embedding, dtype=float))
	except ValueError as error:
		raise RegistrationError("The detected face has an invalid embedding.") from error


def _capture_embedding(detector: FaceDetector, frame: np.ndarray) -> np.ndarray:
	"""Require exactly one detectable face in a frame."""

	detections = detector.detect(frame)
	if len(detections) != 1:
		raise RegistrationError("Registration requires exactly one face per capture.")
	return _embedding_from_detection(detections[0])


def register_student_from_frames(
	db: Session,
	profile: StudentProfile,
	detector: FaceDetector,
	frames: Iterable[np.ndarray],
	minimum_captures: int = 1,
) -> Student:
	"""Create a student using the normalized average of valid face captures."""

	_validate_profile(profile)
	if minimum_captures < 1:
		raise ValueError("minimum_captures must be at least 1.")

	embeddings = [_capture_embedding(detector, frame) for frame in frames]
	if len(embeddings) < minimum_captures:
		raise RegistrationError(
			f"At least {minimum_captures} face captures are required."
		)

	try:
		average_embedding = normalize_embedding(np.mean(embeddings, axis=0))
	except (TypeError, ValueError) as error:
		raise RegistrationError("Face captures must have matching dimensions.") from error
	student = Student(
		full_name=profile.full_name.strip(),
		promotion=profile.promotion.strip(),
		laboratory=profile.laboratory.strip(),
		machine=profile.machine.strip(),
		phone=profile.phone.strip() if profile.phone else None,
		face_embedding=average_embedding.tolist(),
	)
	try:
		db.add(student)
		db.commit()
		db.refresh(student)
	except Exception:
		db.rollback()
		raise
	return student


def register_student(
	db: Session,
	profile: StudentProfile,
	detector: FaceDetector,
	frame: np.ndarray,
) -> Student:
	"""Register one student from one webcam frame."""

	return register_student_from_frames(db, profile, detector, [frame])
