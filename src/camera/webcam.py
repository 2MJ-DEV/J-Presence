"""Webcam helpers used by the first notebooks."""

import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)


def open_camera(camera_index: int) -> cv2.VideoCapture:
    """Open a webcam and raise a clear error if it is unavailable."""

    capture = cv2.VideoCapture(camera_index)
    if not capture.isOpened():
        raise RuntimeError(f"Unable to open camera with index {camera_index}.")
    logger.info("Camera opened with index %s", camera_index)
    return capture


def read_frame(capture: cv2.VideoCapture) -> np.ndarray:
    """Read one frame from an opened webcam."""

    ok, frame = capture.read()
    if not ok or frame is None:
        raise RuntimeError("Unable to read a frame from the camera.")
    return frame


def release_camera(capture: cv2.VideoCapture) -> None:
    """Release the webcam resource."""

    capture.release()
    cv2.destroyAllWindows()
