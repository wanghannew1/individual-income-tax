from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, SQLModel, Relationship


class Unit(SQLModel, table=True):
    __tablename__ = "units"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    aliases: Optional[str] = None  # JSON array of alternative names
    first_seen_month: Optional[str] = None  # YYYY-MM
    record_count: int = Field(default=0)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    records: list["MonthlyRecord"] = Relationship(back_populates="unit")
    payroll_files: list["PayrollFile"] = Relationship(back_populates="unit")
    parser_configs: list["ParserConfig"] = Relationship(back_populates="unit")


class Employee(SQLModel, table=True):
    __tablename__ = "employees"

    id: Optional[int] = Field(default=None, primary_key=True)
    id_card: str = Field(index=True, unique=True)
    name: str = Field(index=True)
    employee_no: Optional[str] = None
    status: str = Field(default="在岗")  # 在岗 / 离职 / 新增待确认
    hire_date: Optional[date] = None
    leave_date: Optional[date] = None
    latest_unit: Optional[str] = None
    latest_pay_month: Optional[str] = None  # YYYY-MM
    phone: Optional[str] = None
    bank_name: Optional[str] = None
    bank_account: Optional[str] = None
    memo: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    records: list["MonthlyRecord"] = Relationship(back_populates="employee")


class MonthlyRecord(SQLModel, table=True):
    __tablename__ = "monthly_records"

    id: Optional[int] = Field(default=None, primary_key=True)
    employee_id: int = Field(foreign_key="employees.id", index=True)
    unit_id: Optional[int] = Field(default=None, foreign_key="units.id", index=True)
    year_month: str = Field(index=True)  # YYYY-MM
    income: float = Field(default=0.0)  # 本期收入
    tax_exempt_income: float = Field(default=0.0)  # 本期免税收入
    pension: float = Field(default=0.0)  # 基本养老保险费
    unemployment: float = Field(default=0.0)  # 失业保险费
    medical: float = Field(default=0.0)  # 基本医疗保险费
    housing_fund: float = Field(default=0.0)  # 住房公积金
    is_zero_report: bool = Field(default=False)
    is_skipped: bool = Field(default=False)  # 用户取消勾选
    memo: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)

    employee: Employee = Relationship(back_populates="records")
    unit: Optional[Unit] = Relationship(back_populates="records")


class PayrollFile(SQLModel, table=True):
    __tablename__ = "payroll_files"

    id: Optional[int] = Field(default=None, primary_key=True)
    filename: str
    unit_id: Optional[int] = Field(default=None, foreign_key="units.id")
    year_month: str  # YYYY-MM
    upload_path: str
    record_count: int = Field(default=0)
    parsed_at: datetime = Field(default_factory=datetime.now)

    unit: Optional[Unit] = Relationship(back_populates="payroll_files")


class ParserConfig(SQLModel, table=True):
    __tablename__ = "parser_configs"

    id: Optional[int] = Field(default=None, primary_key=True)
    unit_id: int = Field(foreign_key="units.id", index=True)
    header_row: int = Field(default=2)  # 0-indexed
    data_start_row: int = Field(default=5)  # 0-indexed
    name_col: int
    id_card_col: int
    income_col: int
    pension_col: Optional[int] = None
    unemployment_col: Optional[int] = None
    medical_col: Optional[int] = None
    housing_fund_col: Optional[int] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    unit: Unit = Relationship(back_populates="parser_configs")
