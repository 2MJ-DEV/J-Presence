"""Register one student from webcam captures."""

import argparse

import cv2

from src.config.settings import get_settings
from src.database.connection import SessionLocal
from src.face.detector import InsightFaceDetector
from src.face.registration import StudentProfile, register_student_from_frames
from src.camera.webcam import open_camera, release_camera


def parse_args() -> argparse.Namespace:
    """Parse profile fields supplied by the operator."""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--name", required=True)
    parser.add_argument("--promotion", required=True)
    parser.add_argument("--laboratory", required=True)
    parser.add_argument("--machine", required=True)
    parser.add_argument("--phone")
    parser.add_argument("--captures", type=int, default=3)
    return parser.parse_args()


def main() -> None:
    """Capture several single-face frames and persist their averaged embedding."""

    args = parse_args()
    if args.captures < 1:
        raise SystemExit("--captures must be at least 1")

    settings = get_settings()
    detector = InsightFaceDetector(settings.model_name)
    capture = open_camera(settings.camera_index)
    frames = []
    try:
        print("Cadrez un seul visage. Appuyez sur ESPACE pour capturer, Q pour annuler.")
        while len(frames) < args.captures:
            ok, frame = capture.read()
            if not ok:
                raise RuntimeError("Unable to read a frame from the camera.")
            cv2.imshow("Student registration", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == ord("q"):
                raise SystemExit("Registration cancelled.")
            if key == ord(" "):
                frames.append(frame.copy())
                print(f"Capture {len(frames)}/{args.captures}")
    finally:
        release_camera(capture)

    profile = StudentProfile(
        full_name=args.name,
        promotion=args.promotion,
        laboratory=args.laboratory,
        machine=args.machine,
        phone=args.phone,
    )
    with SessionLocal() as db:
        student = register_student_from_frames(db, profile, detector, frames, args.captures)
    print(f"Student registered with id={student.id}.")


if __name__ == "__main__":
    main()
