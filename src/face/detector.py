"""InsightFace detector wrapper."""

from dataclasses import dataclass

import numpy as np
from insightface.app import FaceAnalysis


@dataclass(frozen=True)
class FaceDetection:
    """Detected face data returned by InsightFace."""

    bbox: tuple[int, int, int, int]
    confidence: float
    embedding: np.ndarray | None


class InsightFaceDetector:
    """Small wrapper around a pre-trained InsightFace model."""

    def __init__(self, model_name: str, providers: list[str] | None = None) -> None:
        self.model_name = model_name
        self.providers = providers or ["CPUExecutionProvider"]
        self.app = FaceAnalysis(name=model_name, providers=self.providers)
        self.app.prepare(ctx_id=0, det_size=(640, 640))

    def detect(self, frame: np.ndarray) -> list[FaceDetection]:
        """Detect faces in a BGR image returned by OpenCV."""

        faces = self.app.get(frame)
        detections: list[FaceDetection] = []
        for face in faces:
            x1, y1, x2, y2 = face.bbox.astype(int).tolist()
            confidence = float(face.det_score)
            embedding = getattr(face, "embedding", None)
            detections.append(
                FaceDetection(
                    bbox=(x1, y1, x2, y2),
                    confidence=confidence,
                    embedding=embedding,
                )
            )
        return detections
