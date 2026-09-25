"""Business rules for recording recognized student passages."""

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta
from typing import Literal

import numpy as np
from sqlalchemy.orm import Session

from src.attendance.session import DetectionCooldown
from src.database.models import Attendance, Student, UnknownDetection
from src.database.repository import get_attendance_for_day, get_student
from src.face.recognition import RecognitionResult, recognize_embedding

AttendanceAction = Literal[
	"check_in", "check_out", "ignored_cooldown", "already_present", "already_closed"
]


@dataclass(frozen=True)
class AttendanceEvent:
	"""Result of processing one recognized student detection."""

	action: AttendanceAction
	student_id: int
	attendance: Attendance | None
	occurred_at: datetime


@dataclass(frozen=True)
class FrameRecognition:
	"""Recognition and attendance result for one detected face."""

	bbox: tuple[int, int, int, int]
	recognition: RecognitionResult
	attendance: AttendanceEvent | None


class AttendanceService:
	"""Persist one daily entry and one daily exit per recognized student."""

	def __init__(self, db: Session, cooldown_seconds: int = 10) -> None:
		self.db = db
		self.cooldown = DetectionCooldown(cooldown_seconds)

	def record_detection(
		self, student_id: int, occurred_at: datetime | None = None
	) -> AttendanceEvent:
		"""Convert an accepted face detection into an entry or an exit."""

		event_time = occurred_at or datetime.now()
		if get_student(self.db, student_id) is None:
			raise ValueError(f"Unknown student id: {student_id}")

		attendance_date: date = event_time.date()
		attendance = get_attendance_for_day(self.db, student_id, attendance_date)
		event_clock: time = event_time.time().replace(microsecond=0)

		if attendance is None:
			if not self.cooldown.should_accept(student_id, event_time):
				return AttendanceEvent("ignored_cooldown", student_id, None, event_time)
			attendance = Attendance(
				student_id=student_id,
				date=attendance_date,
				check_in=event_clock,
				status="present",
			)
			self.db.add(attendance)
			action: AttendanceAction = "check_in"
		elif attendance.check_out is None:
			if attendance.check_in is None:
				return AttendanceEvent("already_present", student_id, attendance, event_time)
			check_in_dt = datetime.combine(event_time.date(), attendance.check_in)
			if event_time - check_in_dt < timedelta(hours=1):
				return AttendanceEvent("already_present", student_id, attendance, event_time)
			attendance.check_out = event_clock
			attendance.status = "completed"
			action = "check_out"
		else:
			return AttendanceEvent("already_closed", student_id, attendance, event_time)

		try:
			self.db.commit()
			self.db.refresh(attendance)
		except Exception:
			self.db.rollback()
			raise
		return AttendanceEvent(action, student_id, attendance, event_time)

	def record_check_in(
		self, student_id: int, occurred_at: datetime | None = None
	) -> AttendanceEvent:
		"""Explicitly create today's check-in without toggling it to check-out."""

		event_time = occurred_at or datetime.now()
		self._require_student(student_id)
		attendance = get_attendance_for_day(self.db, student_id, event_time.date())
		if attendance is not None:
			if attendance.check_out is not None:
				return AttendanceEvent("already_closed", student_id, attendance, event_time)
			return AttendanceEvent("ignored_cooldown", student_id, attendance, event_time)
		if not self.cooldown.should_accept(student_id, event_time):
			return AttendanceEvent("ignored_cooldown", student_id, None, event_time)
		attendance = Attendance(
			student_id=student_id,
			date=event_time.date(),
			check_in=event_time.time().replace(microsecond=0),
			status="present",
		)
		return self._commit_attendance(attendance, "check_in", student_id, event_time)

	def record_check_out(
		self, student_id: int, occurred_at: datetime | None = None
	) -> AttendanceEvent:
		"""Explicitly close today's open attendance record."""

		event_time = occurred_at or datetime.now()
		self._require_student(student_id)
		attendance = get_attendance_for_day(self.db, student_id, event_time.date())
		if attendance is None:
			raise ValueError("Cannot check out a student without a check-in.")
		if attendance.check_out is not None:
			return AttendanceEvent("already_closed", student_id, attendance, event_time)
		attendance.check_out = event_time.time().replace(microsecond=0)
		attendance.status = "completed"
		return self._commit_attendance(attendance, "check_out", student_id, event_time)

	def _require_student(self, student_id: int) -> None:
		if get_student(self.db, student_id) is None:
			raise ValueError(f"Unknown student id: {student_id}")

	def record_unknown_detection(
		self,
		bbox: tuple[int, int, int, int],
		confidence: float,
		occurred_at: datetime | None = None,
	) -> UnknownDetection | None:
		"""Persist an unknown face once per cooldown window."""

		event_time = occurred_at or datetime.now()
		if not self.cooldown.should_accept(0, event_time):
			return None
		detection = UnknownDetection(
			detected_at=event_time,
			confidence=confidence,
			bbox=list(bbox),
		)
		try:
			self.db.add(detection)
			self.db.commit()
			self.db.refresh(detection)
		except Exception:
			self.db.rollback()
			raise
		return detection

	def _commit_attendance(
		self,
		attendance: Attendance,
		action: AttendanceAction,
		student_id: int,
		event_time: datetime,
	) -> AttendanceEvent:
		self.db.add(attendance)
		try:
			self.db.commit()
			self.db.refresh(attendance)
		except Exception:
			self.db.rollback()
			raise
		return AttendanceEvent(action, student_id, attendance, event_time)

	def process_frame(
		self,
		frame: np.ndarray,
		detector: object,
		students: list[Student],
		threshold: float,
		occurred_at: datetime | None = None,
	) -> list[FrameRecognition]:
		"""Recognize every face in a frame and record known students only."""

		known_embeddings = {
			student.id: student.face_embedding
			for student in students
			if student.id is not None and student.face_embedding is not None
		}
		results: list[FrameRecognition] = []
		for detection in detector.detect(frame):
			bbox = tuple(getattr(detection, "bbox", (0, 0, 0, 0)))
			confidence = float(getattr(detection, "confidence", -1.0))
			embedding = getattr(detection, "embedding", None)
			if embedding is None:
				recognition = RecognitionResult(None, -1.0, False)
			else:
				recognition = recognize_embedding(
					np.asarray(embedding, dtype=float), known_embeddings, threshold
				)
			attendance = (
				self.record_detection(recognition.student_id, occurred_at)
				if recognition.is_known and recognition.student_id is not None
				else None
			)
			if not recognition.is_known:
				self.record_unknown_detection(bbox, confidence, occurred_at)
			results.append(FrameRecognition(bbox, recognition, attendance))
		return results


def record_detection(
	db: Session,
	student_id: int,
	occurred_at: datetime | None = None,
	cooldown: DetectionCooldown | None = None,
) -> AttendanceEvent:
	"""Convenience wrapper for applications that own the cooldown instance."""

	service = AttendanceService(db, cooldown_seconds=0)
	if cooldown is not None:
		service.cooldown = cooldown
	return service.record_detection(student_id, occurred_at)
