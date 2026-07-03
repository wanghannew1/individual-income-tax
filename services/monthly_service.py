from datetime import datetime
from pathlib import Path
from typing import Optional

from sqlmodel import Session, select

from db.models import Employee, MonthlyRecord, ParserConfig, PayrollFile, Unit
from services.payroll_parser import PayrollParseResult, PayrollRecord, parse_payroll_file


def get_or_create_unit(session: Session, unit_name: str, year_month: str) -> Unit:
    unit = session.exec(select(Unit).where(Unit.name == unit_name)).first()
    if not unit:
        unit = Unit(name=unit_name, first_seen_month=year_month)
        session.add(unit)
        session.commit()
        session.refresh(unit)
    else:
        unit.record_count += 1
        unit.updated_at = datetime.now()
        session.add(unit)
        session.commit()
    return unit


def get_parser_config(session: Session, unit_id: int) -> Optional[dict]:
    config = session.exec(select(ParserConfig).where(ParserConfig.unit_id == unit_id)).first()
    if not config:
        return None
    return {
        "header_row": config.header_row,
        "data_start_row": config.data_start_row,
        "name_col": config.name_col,
        "id_card_col": config.id_card_col,
        "income_col": config.income_col,
        "pension_col": config.pension_col,
        "unemployment_col": config.unemployment_col,
        "medical_col": config.medical_col,
        "housing_fund_col": config.housing_fund_col,
    }


def save_parser_config(session: Session, unit_id: int, config: dict) -> ParserConfig:
    existing = session.exec(select(ParserConfig).where(ParserConfig.unit_id == unit_id)).first()
    if existing:
        existing.header_row = config.get("header_row", 0)
        existing.data_start_row = config.get("data_start_row", config.get("header_row", 0) + 1)
        existing.name_col = config["name_col"]
        existing.id_card_col = config["id_card_col"]
        existing.income_col = config["income_col"]
        existing.pension_col = config.get("pension_col")
        existing.unemployment_col = config.get("unemployment_col")
        existing.medical_col = config.get("medical_col")
        existing.housing_fund_col = config.get("housing_fund_col")
        existing.updated_at = datetime.now()
        session.add(existing)
        session.commit()
        session.refresh(existing)
        return existing
    cfg = ParserConfig(
        unit_id=unit_id,
        header_row=config.get("header_row", 0),
        data_start_row=config.get("data_start_row", config.get("header_row", 0) + 1),
        name_col=config["name_col"],
        id_card_col=config["id_card_col"],
        income_col=config["income_col"],
        pension_col=config.get("pension_col"),
        unemployment_col=config.get("unemployment_col"),
        medical_col=config.get("medical_col"),
        housing_fund_col=config.get("housing_fund_col"),
    )
    session.add(cfg)
    session.commit()
    session.refresh(cfg)
    return cfg


def update_employee_from_payroll(session: Session, record: PayrollRecord, unit_name: str, year_month: str):
    employee = session.exec(select(Employee).where(Employee.id_card == record.id_card)).first()
    if not employee:
        employee = Employee(
            id_card=record.id_card,
            name=record.name,
            employee_no=record.employee_no,
            status="新增待确认",
            latest_unit=unit_name,
            latest_pay_month=year_month,
        )
        session.add(employee)
    else:
        employee.name = record.name
        employee.employee_no = record.employee_no or employee.employee_no
        employee.latest_unit = unit_name
        employee.latest_pay_month = year_month
        if employee.status == "新增待确认":
            employee.status = "在岗"
        session.add(employee)
    session.commit()
    session.refresh(employee)
    return employee


def generate_monthly_records(
    session: Session,
    year_month: str,
    parse_results: list[PayrollParseResult],
    skipped_id_cards: list[str] = None,
) -> dict:
    skipped_id_cards = skipped_id_cards or []

    # Clear existing records for this month
    existing = session.exec(select(MonthlyRecord).where(MonthlyRecord.year_month == year_month))
    for rec in existing:
        session.delete(rec)
    session.commit()

    # Track employees with income this month
    paid_id_cards = set()
    record_count = 0

    for pr in parse_results:
        if not pr.records:
            continue
        unit = get_or_create_unit(session, pr.unit, year_month)

        # Save parser config if auto-detected successfully
        if pr.confidence == 1.0 and not pr.needs_mapping:
            save_parser_config(session, unit.id, {
                "header_row": 0,  # Will be refined later if needed
                "data_start_row": 0,
                **pr.detected_columns,
            })

        for rec in pr.records:
            paid_id_cards.add(rec.id_card)
            employee = update_employee_from_payroll(session, rec, pr.unit, year_month)
            monthly = MonthlyRecord(
                employee_id=employee.id,
                unit_id=unit.id,
                year_month=year_month,
                income=rec.income,
                tax_exempt_income=rec.tax_exempt_income,
                pension=rec.pension,
                unemployment=rec.unemployment,
                medical=rec.medical,
                housing_fund=rec.housing_fund,
                is_zero_report=False,
                memo=pr.unit,
            )
            session.add(monthly)
            record_count += 1

    # Auto-generate zero reports for active employees not in payroll
    zero_report_count = 0
    active_employees = session.exec(select(Employee).where(Employee.status == "在岗")).all()
    for emp in active_employees:
        if emp.id_card in paid_id_cards:
            continue
        if emp.id_card in skipped_id_cards:
            continue
        if not emp.latest_unit:
            continue

        unit = get_or_create_unit(session, emp.latest_unit, year_month)
        monthly = MonthlyRecord(
            employee_id=emp.id,
            unit_id=unit.id,
            year_month=year_month,
            income=0.0,
            tax_exempt_income=0.0,
            pension=0.0,
            unemployment=0.0,
            medical=0.0,
            housing_fund=0.0,
            is_zero_report=True,
            memo=emp.latest_unit,
        )
        session.add(monthly)
        zero_report_count += 1

    session.commit()
    return {
        "income_records": record_count,
        "zero_records": zero_report_count,
        "total_records": record_count + zero_report_count,
    }


def save_uploaded_file(upload_file, upload_dir: Path) -> Path:
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / upload_file.filename
    with open(file_path, "wb") as f:
        f.write(upload_file.file.read())
    return file_path


def parse_uploaded_files(
    session: Session,
    uploaded_files: list,
    year_month: str,
    upload_dir: Path,
) -> list[PayrollParseResult]:
    results = []
    for upload_file in uploaded_files:
        file_path = save_uploaded_file(upload_file, upload_dir)
        result = parse_payroll_file(str(file_path))

        # Try saved config if auto-detect failed
        if result.needs_mapping or result.confidence < 1.0:
            unit = session.exec(select(Unit).where(Unit.name == result.unit)).first()
            if unit:
                config = get_parser_config(session, unit.id)
                if config:
                    result = parse_payroll_file(str(file_path), manual_config=config)

        # Save payroll file record
        unit = get_or_create_unit(session, result.unit, year_month)
        pf = PayrollFile(
            filename=upload_file.filename,
            unit_id=unit.id,
            year_month=year_month,
            upload_path=str(file_path),
            record_count=len(result.records),
        )
        session.add(pf)
        session.commit()

        results.append(result)
    return results
