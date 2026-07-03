from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from pathlib import Path
from sqlmodel import Session, select, func

from db.database import get_session
from db.models import MonthlyRecord, Employee, Unit

router = APIRouter()
templates = Jinja2Templates(directory=Path(__file__).resolve().parent.parent / "templates")


@router.get("/")
def history_index(request: Request, session: Session = Depends(get_session)):
    # Get all distinct year_months with counts
    rows = session.exec(
        select(
            MonthlyRecord.year_month,
            func.count(MonthlyRecord.id),
            func.sum(MonthlyRecord.income),
        )
        .where(MonthlyRecord.is_skipped == False)
        .group_by(MonthlyRecord.year_month)
        .order_by(MonthlyRecord.year_month.desc())
    ).all()

    history = []
    for year_month, count, total_income in rows:
        zero_count = session.exec(
            select(func.count(MonthlyRecord.id))
            .where(MonthlyRecord.year_month == year_month)
            .where(MonthlyRecord.is_zero_report == True)
            .where(MonthlyRecord.is_skipped == False)
        ).one()
        history.append({
            "year_month": year_month,
            "total_count": count,
            "income_count": count - zero_count,
            "zero_count": zero_count,
            "total_income": total_income or 0,
        })

    return templates.TemplateResponse(
        request,
        "history.html",
        {"history": history},
    )
