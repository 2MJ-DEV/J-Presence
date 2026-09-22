"""Run the webcam recognition and attendance pipeline."""

import cv2

from src.attendance.service import AttendanceService
from src.camera.webcam import open_camera, release_camera
from src.config.settings import get_settings
from src.database.connection import SessionLocal
from src.database.repository import list_students
from src.face.detector import InsightFaceDetector


def main() -> None:
    """Recognize known students until the operator presses Q."""

    settings = get_settings()
    detector = InsightFaceDetector(settings.model_name)
    capture = open_camera(settings.camera_index)
    try:
        with SessionLocal() as db:
            service = AttendanceService(db, settings.cooldown_seconds)
            while True:
                ok, frame = capture.read()
                if not ok:
                    raise RuntimeError("Unable to read a frame from the camera.")
                students = list_students(db)
                results = service.process_frame(
                    frame,
                    detector,
                    students,
                    settings.face_recognition_threshold,
                )
                for result in results:
                    x1, y1, x2, y2 = result.bbox
                    color = (0, 180, 0) if result.recognition.is_known else (0, 0, 220)
                    label = (
                        f"student {result.recognition.student_id} "
                        f"{result.recognition.score:.2f}"
                        if result.recognition.is_known
                        else f"UNKNOWN {result.recognition.score:.2f}"
                    )
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    cv2.putText(
                        frame, label, (x1, max(20, y1 - 8)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2,
                    )
                    if result.attendance is not None:
                        print(
                            f"student={result.attendance.student_id} "
                            f"action={result.attendance.action}"
                        )
                cv2.imshow("Lab Attendance AI", frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    finally:
        release_camera(capture)


if __name__ == "__main__":
    main()
