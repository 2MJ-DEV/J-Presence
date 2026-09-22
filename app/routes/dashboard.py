"""HTML dashboard routes."""

from datetime import date

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.routes.attendance import serialize_attendance
from src.database.connection import get_db
from src.database.repository import list_attendance, list_students

router = APIRouter(tags=["dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render today's digital journal."""

    rows = [serialize_attendance(row) for row in list_attendance(db, date.today())]
    return templates.TemplateResponse(
        "dashboard.html",
        {"request": request, "title": "Journal du laboratoire", "rows": rows},
    )


@router.get("/students", response_class=HTMLResponse)
def students_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render registered students."""

    return templates.TemplateResponse(
        "students.html",
        {"request": request, "title": "Etudiants", "students": list_students(db)},
    )


@router.get("/attendance", response_class=HTMLResponse)
def attendance_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the complete attendance journal."""

    rows = [serialize_attendance(row) for row in list_attendance(db)]
    return templates.TemplateResponse(
        "attendance.html",
        {"request": request, "title": "Presences", "rows": rows},
    )
