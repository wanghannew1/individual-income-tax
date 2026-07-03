from io import BytesIO
from typing import Optional

import pandas as pd
from sqlmodel import Session, select

from db.models import Employee, MonthlyRecord, Unit


def get_tax_report_data(session: Session, year_month: str) -> list[dict]:
    records = session.exec(
        select(MonthlyRecord, Employee, Unit)
        .join(Employee, MonthlyRecord.employee_id == Employee.id)
        .outerjoin(Unit, MonthlyRecord.unit_id == Unit.id)
        .where(MonthlyRecord.year_month == year_month)
        .where(MonthlyRecord.is_skipped == False)
        .order_by(Employee.name)
    ).all()

    rows = []
    for mr, emp, unit in records:
        rows.append({
            "工号": emp.employee_no or "",
            "*姓名": emp.name,
            "*证件类型": "居民身份证",
            "*证件号码": emp.id_card,
            "本期收入": round(mr.income, 2),
            "本期免税收入": round(mr.tax_exempt_income, 2),
            "基本养老保险费": round(mr.pension, 2),
            "失业保险费": round(mr.unemployment, 2),
            "基本医疗保险费": round(mr.medical, 2),
            "住房公积金": round(mr.housing_fund, 2),
            "累计子女教育": 0,
            "累计继续教育": 0,
            "累计住房贷款利息": 0,
            "累计住房租金": 0,
            "累计赡养老人": 0,
            "累计3岁以下婴幼儿照护": 0,
            "累计个人养老金": 0,
            "企业(职业)年金": 0,
            "商业健康保险": 0,
            "税延养老保险": 0,
            "其他": 0,
            "准予扣除的捐赠额": 0,
            "减免税额": 0,
            "备注": unit.name if unit else (mr.memo or ""),
        })
    return rows


def get_personnel_data(session: Session, year_month: str) -> list[dict]:
    # Personnel who are newly active or changed status this month
    records = session.exec(
        select(MonthlyRecord, Employee)
        .join(Employee, MonthlyRecord.employee_id == Employee.id)
        .where(MonthlyRecord.year_month == year_month)
        .where(MonthlyRecord.is_skipped == False)
    ).all()

    rows = []
    seen = set()
    for mr, emp in records:
        if emp.id_card in seen:
            continue
        seen.add(emp.id_card)
        gender = ""
        birth_date = ""
        if len(emp.id_card) == 18:
            try:
                gender = "男" if int(emp.id_card[16]) % 2 == 1 else "女"
                birth_date = f"{emp.id_card[6:10]}-{emp.id_card[10:12]}-{emp.id_card[12:14]}"
            except ValueError:
                pass

        rows.append({
            "工号": emp.employee_no or "",
            "*姓名": emp.name,
            "*证件类型": "居民身份证",
            "*证件号码": emp.id_card,
            "*国籍（地区）": "中国",
            "性别": gender,
            "出生日期": birth_date,
            "*人员状态": emp.status if emp.status != "新增待确认" else "正常",
            "*任职受雇从业类型": "雇员",
            "手机号码": emp.phone or "",
            "*任职受雇从业日期": emp.hire_date.isoformat() if emp.hire_date else "",
            "离职日期": emp.leave_date.isoformat() if emp.leave_date else "",
            "户籍所在地": "",
            "开户银行": emp.bank_name or "",
            "银行账号": emp.bank_account or "",
            "备注": emp.latest_unit or "",
        })
    return rows


def get_unit_summary(session: Session, year_month: str) -> list[dict]:
    records = session.exec(
        select(MonthlyRecord, Unit)
        .outerjoin(Unit, MonthlyRecord.unit_id == Unit.id)
        .where(MonthlyRecord.year_month == year_month)
        .where(MonthlyRecord.is_skipped == False)
    ).all()

    summary = {}
    for mr, unit in records:
        unit_name = unit.name if unit else (mr.memo or "未知单位")
        if unit_name not in summary:
            summary[unit_name] = {
                "unit": unit_name,
                "total_count": 0,
                "income_count": 0,
                "zero_count": 0,
                "income": 0.0,
                "pension": 0.0,
                "unemployment": 0.0,
                "medical": 0.0,
                "housing_fund": 0.0,
            }
        summary[unit_name]["total_count"] += 1
        if mr.is_zero_report:
            summary[unit_name]["zero_count"] += 1
        else:
            summary[unit_name]["income_count"] += 1
        summary[unit_name]["income"] += mr.income
        summary[unit_name]["pension"] += mr.pension
        summary[unit_name]["unemployment"] += mr.unemployment
        summary[unit_name]["medical"] += mr.medical
        summary[unit_name]["housing_fund"] += mr.housing_fund

    rows = []
    for unit_name in sorted(summary.keys()):
        s = summary[unit_name]
        rows.append({
            "甲方单位": s["unit"],
            "申报人数": s["total_count"],
            "有收入人数": s["income_count"],
            "零申报人数": s["zero_count"],
            "本月收入合计": round(s["income"], 2),
            "养老保险合计": round(s["pension"], 2),
            "失业保险合计": round(s["unemployment"], 2),
            "医疗保险合计": round(s["medical"], 2),
            "公积金合计": round(s["housing_fund"], 2),
            "扣除合计": round(s["pension"] + s["unemployment"] + s["medical"] + s["housing_fund"], 2),
        })
    return rows


def build_excel_bytes(rows: list[dict]) -> bytes:
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")
    buffer.seek(0)
    return buffer.getvalue()
