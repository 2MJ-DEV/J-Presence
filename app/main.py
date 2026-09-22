"""FastAPI application for the laboratory attendance system."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.routes.attendance import router as attendance_router
from app.routes.dashboard import router as dashboard_router
from app.routes.students import router as students_router
from src.database import models
from src.database.connection import engine

app = FastAPI(title="Lab Attendance AI")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(students_router)
app.include_router(attendance_router)
app.include_router(dashboard_router)


@app.on_event("startup")
def create_tables() -> None:
    """Create the local SQLite schema when the application starts."""

    models.Base.metadata.create_all(bind=engine)


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check."""

    return {"status": "ok"}


