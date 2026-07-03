from fastapi import APIRouter, Request, Depends, Form, Query, File, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select

from db.database import get_session
from db.models import Employee
from services.personnel_import import import_personnel_file

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/")
def list_employees(
    request: Request,
    q: str = Query(None),
    session: Session = Depends(get_session),
):
    statement = select(Employee)
    if q:
        statement = statement.where(
            (Employee.name.contains(q)) | (Employee.id_card.contains(q))
        )
    employees = session.exec(statement.order_by(Employee.name)).all()
    return templates.TemplateResponse(
        request,
        "employees.html",
        {"employees": employees, "q": q},
    )


@router.post("/import")
def import_personnel(
    request: Request,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
):
    upload_dir = Path(__file__).resolve().parent.parent.parent / "uploads"
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    with open(file_path, "wb") as f:
        f.write(file.file.read())
    result = import_personnel_file(str(file_path), session)
    return templates.TemplateResponse(
        request,
        "employees.html",
        {"employees": session.exec(select(Employee).order_by(Employee.name)).all(), "import_result": result},
    )


@router.post("/{employee_id}/update")
def update_employee(
    employee_id: int,
    status: str = Form(...),
    phone: str = Form(None),
    bank_name: str = Form(None),
    bank_account: str = Form(None),
    memo: str = Form(None),
    session: Session = Depends(get_session),
):
    employee = session.get(Employee, employee_id)
    if employee:
        employee.status = status
        employee.phone = phone or None
        employee.bank_name = bank_name or None
        employee.bank_account = bank_account or None
        employee.memo = memo or None
        session.add(employee)
        session.commit()
    return RedirectResponse(url="/employees", status_code=303)
