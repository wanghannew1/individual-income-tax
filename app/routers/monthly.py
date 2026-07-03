import io
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import Session, select

from db.database import get_session
from db.models import Employee, MonthlyRecord, Unit
from services.export_service import (
    build_excel_bytes,
    get_personnel_data,
    get_tax_report_data,
    get_unit_summary,
)
from services.monthly_service import generate_monthly_records, parse_uploaded_files
from services.payroll_parser import parse_payroll_file

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")

UPLOAD_DIR = Path(__file__).resolve().parent.parent.parent / "uploads"


@router.get("/")
def monthly_index(request: Request):
    return templates.TemplateResponse(request, "monthly.html")


@router.post("/upload")
def upload_payroll(
    request: Request,
    year_month: str = Form(...),
    files: list[UploadFile] = File(...),
    session: Session = Depends(get_session),
):
    UPLOAD_DIR.mkdir(exist_ok=True)
    month_dir = UPLOAD_DIR / year_month / uuid.uuid4().hex[:8]
    month_dir.mkdir(parents=True, exist_ok=True)

    parse_results = parse_uploaded_files(session, files, year_month, month_dir)

    needs_mapping = any(r.needs_mapping or r.confidence < 1.0 for r in parse_results)

    return templates.TemplateResponse(
        request,
        "monthly_preview.html",
        {
            "year_month": year_month,
            "parse_results": parse_results,
            "needs_mapping": needs_mapping,
            "generated": False,
        },
    )


@router.post("/generate")
def generate_records(
    request: Request,
    year_month: str = Form(...),
    skip: list[str] = Form(default=[]),
    session: Session = Depends(get_session),
):
    month_dirs = sorted((UPLOAD_DIR / year_month).glob("*")) if (UPLOAD_DIR / year_month).exists() else []
    if not month_dirs:
        return templates.TemplateResponse(
            request,
            "monthly_preview.html",
            {"year_month": year_month, "error": "未找到上传文件，请重新上传"},
        )

    latest_dir = month_dirs[-1]
    parse_results = []
    for file_path in latest_dir.glob("*"):
        if file_path.suffix.lower() in {".xls", ".xlsx"}:
            unit_name = None
            for unit in session.exec(select(Unit)).all():
                if unit.name in file_path.name:
                    unit_name = unit.name
                    break
            config = None
            if unit_name:
                unit = session.exec(select(Unit).where(Unit.name == unit_name)).first()
                if unit:
                    from services.monthly_service import get_parser_config
                    config = get_parser_config(session, unit.id)
            result = parse_payroll_file(str(file_path), manual_config=config)
            parse_results.append(result)

    stats = generate_monthly_records(session, year_month, parse_results, skipped_id_cards=skip)

    records = session.exec(
        select(MonthlyRecord, Employee, Unit)
        .join(Employee, MonthlyRecord.employee_id == Employee.id)
        .outerjoin(Unit, MonthlyRecord.unit_id == Unit.id)
        .where(MonthlyRecord.year_month == year_month)
        .where(MonthlyRecord.is_skipped == False)
        .order_by(Employee.name)
    ).all()

    return templates.TemplateResponse(
        request,
        "monthly_preview.html",
        {
            "year_month": year_month,
            "parse_results": parse_results,
            "generated": True,
            "stats": stats,
            "records": records,
        },
    )


@router.get("/export/tax-report")
def export_tax_report(
    year_month: str = Query(...),
    session: Session = Depends(get_session),
):
    rows = get_tax_report_data(session, year_month)
    filename = f"综合所得申报表_{year_month}.xlsx"
    content = build_excel_bytes(rows)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/export/personnel")
def export_personnel(
    year_month: str = Query(...),
    session: Session = Depends(get_session),
):
    rows = get_personnel_data(session, year_month)
    filename = f"人员信息采集表_{year_month}.xlsx"
    content = build_excel_bytes(rows)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


@router.get("/export/summary")
def export_summary(
    year_month: str = Query(...),
    session: Session = Depends(get_session),
):
    rows = get_unit_summary(session, year_month)
    filename = f"甲方单位汇总表_{year_month}.xlsx"
    content = build_excel_bytes(rows)
    return StreamingResponse(
        io.BytesIO(content),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )
