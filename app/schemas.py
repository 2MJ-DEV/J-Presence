"""Validated request and response models for the FastAPI application."""

from datetime import date, datetime, time
from math import isfinite

from pydantic import BaseModel, ConfigDict, Field
from pydantic import field_validator


class StudentCreate(BaseModel):
    """Data required to register a student through the API."""

    full_name: str = Field(min_length=1, max_length=150)
    promotion: str = Field(min_length=1, max_length=80)
    laboratory: str = Field(min_length=1, max_length=80)
    machine: str = Field(min_length=1, max_length=80)
    phone: str | None = Field(default=None, max_length=40)
    face_embedding: list[float] = Field(min_length=1)

    @field_validator("face_embedding")
    @classmethod
    def validate_embedding(cls, embedding: list[float]) -> list[float]:
        """Reject malformed embeddings before they reach SQLite."""

        if not all(isfinite(value) for value in embedding):
            raise ValueError("face_embedding must contain only finite values")
        if sum(value * value for value in embedding) == 0:
            raise ValueError("face_embedding must not be a zero vector")
        return embedding


class StudentRead(BaseModel):
    """Student returned by the API without exposing the embedding."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str
    promotion: str
    laboratory: str
    machine: str
    phone: str | None
    created_at: datetime
    updated_at: datetime


class AttendanceRead(BaseModel):
    """Attendance row enriched with the student's profile."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    student_id: int
    full_name: str
    promotion: str
    laboratory: str
    machine: str
    phone: str | None
    date: date
    check_in: time | None
    check_out: time | None
    status: str


class AttendanceAction(BaseModel):
    """Payload for a manual attendance action."""

    student_id: int = Field(gt=0)
