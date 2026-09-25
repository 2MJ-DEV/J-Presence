"""FastAPI application for the laboratory attendance system."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from sqlalchemy import inspect, text

from app.routes.attendance import router as attendance_router
from app.routes.dashboard import router as dashboard_router
from app.routes.students import router as students_router
from src.database import models
from src.database.connection import engine

app = FastAPI(title="Lab Attendance AI")
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(dashboard_router)
app.include_router(students_router)
app.include_router(attendance_router)


@app.on_event("startup")
def create_tables() -> None:
    """Create the local SQLite schema when the application starts."""

    models.Base.metadata.create_all(bind=engine)
    if engine.dialect.name == "sqlite":
        columns = {column["name"] for column in inspect(engine).get_columns("unknown_detections")}
        if "image_data" not in columns:
            with engine.begin() as connection:
                connection.execute(
                    text("ALTER TABLE unknown_detections ADD COLUMN image_data BLOB")
                )


@app.get("/health")
def health() -> dict[str, str]:
    """Simple health check."""

    return {"status": "ok"}


