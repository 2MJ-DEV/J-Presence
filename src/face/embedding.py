"""Embedding utilities."""

import numpy as np


def normalize_embedding(embedding: np.ndarray) -> np.ndarray:
    """Normalize an embedding before cosine similarity comparisons."""

    if embedding.ndim != 1 or embedding.size == 0:
        raise ValueError("An embedding must be a non-empty one-dimensional array.")
    if not np.isfinite(embedding).all():
        raise ValueError("An embedding must contain only finite values.")

    norm = np.linalg.norm(embedding)
    if norm == 0:
        raise ValueError("Cannot normalize an empty embedding.")
    return embedding / norm


def cosine_similarity(first: np.ndarray, second: np.ndarray) -> float:
    """Compute cosine similarity between two face embeddings."""

    a = normalize_embedding(first)
    b = normalize_embedding(second)
    if a.shape != b.shape:
        raise ValueError("Embeddings must have the same dimensions.")
    return float(np.dot(a, b))
