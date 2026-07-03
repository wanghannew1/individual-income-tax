from datetime import date, datetime
from typing import Optional

import pandas as pd
from sqlmodel import Session, select

from db.models import Employee


PERSONNEL_KEYWORDS = {
    "name": ["姓名", "name", "员工姓名"],
    "id_card": ["证件号码", "身份证号", "身份证", "身份证号码"],
    "employee_no": ["工号", "员工编号", "编号"],
    "status": ["人员状态", "状态"],
    "hire_date": ["任职受雇从业日期", "入职日期", "参加工作日期"],
    "leave_date": ["离职日期"],
    "phone": ["手机号码", "手机号", "电话"],
    "bank_name": ["开户银行", "银行名称"],
    "bank_account": ["银行账号", "银行卡号", "账号"],
    "memo": ["备注"],
}


def detect_columns(df: pd.DataFrame) -> dict:
    """Auto-detect column indices by header keywords."""
    result = {}
    headers = [str(h).strip() if pd.notna(h) else "" for h in df.iloc[0]]
    for field, keywords in PERSONNEL_KEYWORDS.items():
        for idx, header in enumerate(headers):
            if any(kw in header for kw in keywords):
                result[field] = idx
                break
    return result


def parse_date(value) -> Optional[date]:
    if pd.isna(value):
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        s = str(value).strip()
        if not s or s in ["None", "nan"]:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(s, fmt).date()
            except ValueError:
                continue
    except Exception:
        pass
    return None


def id_card_gender(id_card: str) -> str:
    if len(id_card) == 18:
        try:
            return "男" if int(id_card[16]) % 2 == 1 else "女"
        except ValueError:
            pass
    return ""


def id_card_birth_date(id_card: str) -> Optional[date]:
    if len(id_card) == 18:
        try:
            return datetime.strptime(id_card[6:14], "%Y%m%d").date()
        except ValueError:
            pass
    return None


def normalize_status(value) -> str:
    if pd.isna(value):
        return "在岗"
    s = str(value).strip()
    if s in ["正常", "在岗", "任职"]:
        return "在岗"
    if s in ["非正常", "离职", "终止"]:
        return "离职"
    return s or "在岗"


def import_personnel_file(file_path: str, session: Session) -> dict:
    df = pd.read_excel(file_path, header=None)
    cols = detect_columns(df)
    if "name" not in cols or "id_card" not in cols:
        raise ValueError("无法识别姓名或证件号码列，请检查文件格式")

    created = 0
    updated = 0
    skipped = 0

    for idx in range(1, len(df)):
        row = df.iloc[idx]
        name = str(row.iloc[cols["name"]]).strip() if pd.notna(row.iloc[cols["name"]]) else ""
        id_card = str(row.iloc[cols["id_card"]]).strip() if pd.notna(row.iloc[cols["id_card"]]) else ""
        if not name or not id_card:
            skipped += 1
            continue

        employee_no = (
            str(row.iloc[cols["employee_no"]]).strip()
            if "employee_no" in cols and pd.notna(row.iloc[cols["employee_no"]])
            else None
        )
        status = normalize_status(row.iloc[cols["status"]]) if "status" in cols else "在岗"
        hire_date = parse_date(row.iloc[cols["hire_date"]]) if "hire_date" in cols else None
        leave_date = parse_date(row.iloc[cols["leave_date"]]) if "leave_date" in cols else None
        phone = (
            str(row.iloc[cols["phone"]]).strip()
            if "phone" in cols and pd.notna(row.iloc[cols["phone"]])
            else None
        )
        bank_name = (
            str(row.iloc[cols["bank_name"]]).strip()
            if "bank_name" in cols and pd.notna(row.iloc[cols["bank_name"]])
            else None
        )
        bank_account = (
            str(row.iloc[cols["bank_account"]]).strip()
            if "bank_account" in cols and pd.notna(row.iloc[cols["bank_account"]])
            else None
        )
        memo = (
            str(row.iloc[cols["memo"]]).strip()
            if "memo" in cols and pd.notna(row.iloc[cols["memo"]])
            else None
        )

        existing = session.exec(select(Employee).where(Employee.id_card == id_card)).first()
        if existing:
            existing.name = name
            existing.employee_no = employee_no or existing.employee_no
            existing.status = status
            existing.hire_date = hire_date or existing.hire_date
            existing.leave_date = leave_date or existing.leave_date
            existing.phone = phone or existing.phone
            existing.bank_name = bank_name or existing.bank_name
            existing.bank_account = bank_account or existing.bank_account
            existing.memo = memo or existing.memo
            existing.updated_at = datetime.now()
            session.add(existing)
            updated += 1
        else:
            emp = Employee(
                id_card=id_card,
                name=name,
                employee_no=employee_no,
                status=status,
                hire_date=hire_date,
                leave_date=leave_date,
                phone=phone,
                bank_name=bank_name,
                bank_account=bank_account,
                memo=memo,
            )
            session.add(emp)
            created += 1

    session.commit()
    return {"created": created, "updated": updated, "skipped": skipped, "columns": cols}
