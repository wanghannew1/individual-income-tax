import io
import os
import tempfile
from pathlib import Path

import pandas as pd
import pytest
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from db.models import Employee, MonthlyRecord, Unit, PayrollFile
from services.export_service import (
    build_excel_bytes,
    get_personnel_data,
    get_tax_report_data,
    get_unit_summary,
)
from services.monthly_service import (
    generate_monthly_records,
    get_or_create_unit,
    save_uploaded_file,
)
from services.payroll_parser import PayrollRecord


@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


@pytest.fixture(name="sample_employees")
def sample_employees_fixture(session: Session):
    employees = [
        Employee(id_card="220101199001011234", name="张三", status="在岗", latest_unit="测试单位A", employee_no="EMP001"),
        Employee(id_card="220101199002022345", name="李四", status="在岗", latest_unit="测试单位A", employee_no="EMP002"),
        Employee(id_card="220101199003033456", name="王五", status="在岗", latest_unit="测试单位A", employee_no="EMP003"),
        Employee(id_card="220101199004044567", name="赵六", status="离职", latest_unit="测试单位B", employee_no="EMP004"),
    ]
    for emp in employees:
        session.add(emp)
    session.commit()
    return employees


def test_get_or_create_unit_new(session: Session):
    unit = get_or_create_unit(session, "新单位", "2026-06")
    assert unit.id is not None
    assert unit.name == "新单位"
    assert unit.first_seen_month == "2026-06"


def test_get_or_create_unit_existing(session: Session):
    unit1 = get_or_create_unit(session, "现有单位", "2026-05")
    unit2 = get_or_create_unit(session, "现有单位", "2026-06")
    assert unit1.id == unit2.id
    assert unit2.record_count == 1


def test_save_uploaded_file(session: Session):
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_dir = Path(tmpdir)

        class FakeUpload:
            filename = "test_payroll.xlsx"
            file = io.BytesIO(b"fake content")

        result = save_uploaded_file(FakeUpload(), upload_dir)
        assert result.exists()
        assert result.read_bytes() == b"fake content"


def test_generate_monthly_records(session: Session, sample_employees):
    pr = type("PayrollParseResult", (), {
        "unit": "测试单位A",
        "year_month": "2026-06",
        "records": [
            PayrollRecord(name="张三", id_card="220101199001011234", employee_no="EMP001", income=8000.0, pension=640.0, unemployment=40.0, medical=160.0, housing_fund=960.0, tax_exempt_income=0.0),
            PayrollRecord(name="李四", id_card="220101199002022345", employee_no="EMP002", income=10000.0, pension=800.0, unemployment=50.0, medical=200.0, housing_fund=1200.0, tax_exempt_income=0.0),
        ],
        "confidence": 1.0,
        "needs_mapping": False,
        "detected_columns": {
            "header_row": 0,
            "data_start_row": 1,
            "name_col": 0,
            "id_card_col": 1,
            "income_col": 2,
        },
        "errors": [],
        "headers": [],
    })()

    stats = generate_monthly_records(session, "2026-06", [pr])

    assert stats["income_records"] == 2
    assert stats["zero_records"] == 1  # 王五 is 在岗 but not in payroll
    assert stats["total_records"] == 3


def test_generate_monthly_records_skips_resigned(session: Session, sample_employees):
    pr = type("PayrollParseResult", (), {
        "unit": "测试单位A",
        "year_month": "2026-06",
        "records": [
            PayrollRecord(name="张三", id_card="220101199001011234", employee_no="EMP001", income=8000.0, pension=640.0, unemployment=40.0, medical=160.0, housing_fund=960.0, tax_exempt_income=0.0),
        ],
        "confidence": 1.0,
        "needs_mapping": False,
        "detected_columns": {
            "header_row": 0,
            "data_start_row": 1,
            "name_col": 0,
            "id_card_col": 1,
            "income_col": 2,
        },
        "errors": [],
        "headers": [],
    })()

    stats = generate_monthly_records(session, "2026-06", [pr])

    assert stats["income_records"] == 1
    assert stats["zero_records"] == 2  # 李四 and 王五 are 在岗 and not in payroll; 赵六 is 离职
    assert stats["total_records"] == 3


def test_get_tax_report_data(session: Session, sample_employees):
    unit = get_or_create_unit(session, "测试单位A", "2026-06")
    emp = sample_employees[0]
    mr = MonthlyRecord(
        employee_id=emp.id,
        unit_id=unit.id,
        year_month="2026-06",
        income=8000.0,
        pension=640.0,
        unemployment=40.0,
        medical=160.0,
        housing_fund=960.0,
        is_zero_report=False,
    )
    session.add(mr)
    session.commit()

    rows = get_tax_report_data(session, "2026-06")
    assert len(rows) == 1
    assert rows[0]["*姓名"] == "张三"
    assert rows[0]["本期收入"] == 8000.0


def test_get_personnel_data(session: Session, sample_employees):
    unit = get_or_create_unit(session, "测试单位A", "2026-06")
    emp = sample_employees[0]
    mr = MonthlyRecord(
        employee_id=emp.id,
        unit_id=unit.id,
        year_month="2026-06",
        income=8000.0,
        is_zero_report=False,
    )
    session.add(mr)
    session.commit()

    rows = get_personnel_data(session, "2026-06")
    assert len(rows) == 1
    assert rows[0]["*姓名"] == "张三"
    assert rows[0]["*证件号码"] == "220101199001011234"


def test_get_unit_summary(session: Session, sample_employees):
    unit = get_or_create_unit(session, "测试单位A", "2026-06")
    for emp in sample_employees[:2]:
        mr = MonthlyRecord(
            employee_id=emp.id,
            unit_id=unit.id,
            year_month="2026-06",
            income=8000.0,
            pension=640.0,
            unemployment=40.0,
            medical=160.0,
            housing_fund=960.0,
            is_zero_report=False,
        )
        session.add(mr)
    session.commit()

    rows = get_unit_summary(session, "2026-06")
    assert len(rows) == 1
    assert rows[0]["甲方单位"] == "测试单位A"
    assert rows[0]["申报人数"] == 2
    assert rows[0]["本月收入合计"] == 16000.0


def test_build_excel_bytes():
    rows = [
        {"姓名": "张三", "收入": 8000.0},
        {"姓名": "李四", "收入": 10000.0},
    ]
    content = build_excel_bytes(rows)
    assert isinstance(content, bytes)
    assert len(content) > 0

    df = pd.read_excel(io.BytesIO(content))
    assert len(df) == 2
    assert list(df.columns) == ["姓名", "收入"]
