"""Recognition helpers that compare embeddings against known students."""

from dataclasses import dataclass
from collections.abc import Mapping, Sequence

import numpy as np

from src.face.embedding import cosine_similarity


@dataclass(frozen=True)
class RecognitionResult:
    """Result of a face comparison."""

    student_id: int | None
    score: float
    is_known: bool


def recognize_embedding(
    candidate: np.ndarray,
    known_embeddings: Mapping[int, Sequence[float]],
    threshold: float,
) -> RecognitionResult:
    """Return the best matching student if the similarity reaches threshold."""

    if not 0.0 <= threshold <= 1.0:
        raise ValueError("The recognition threshold must be between 0 and 1.")

    best_student_id: int | None = None
    best_score = -1.0

    for student_id, stored_embedding in known_embeddings.items():
        try:
            score = cosine_similarity(candidate, np.asarray(stored_embedding, dtype=float))
        except ValueError:
            continue
        if score > best_score:
            best_student_id = student_id
            best_score = score

    return RecognitionResult(
        student_id=best_student_id
        if best_student_id is not None and best_score >= threshold
        else None,
        score=best_score,
        is_known=best_student_id is not None and best_score >= threshold,
    )
