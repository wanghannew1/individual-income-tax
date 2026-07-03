import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pandas as pd


@dataclass
class PayrollRecord:
    name: str
    id_card: str
    employee_no: Optional[str]
    income: float
    tax_exempt_income: float = 0.0
    pension: float = 0.0
    unemployment: float = 0.0
    medical: float = 0.0
    housing_fund: float = 0.0
    memo: Optional[str] = None


@dataclass
class PayrollParseResult:
    filename: str
    unit: str
    year_month: str
    records: list[PayrollRecord] = field(default_factory=list)
    confidence: float = 0.0
    detected_columns: dict = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)
    needs_mapping: bool = False


KEYWORDS = {
    "name": ["姓名", "员工姓名"],
    "id_card": ["证件号码", "身份证号", "身份证"],
    "employee_no": ["工号", "职工号", "员工编号"],
    "income": ["应发工资", "应发合计", "工资合计", "本月应发"],
    "pension": ["基本养老保险", "养老保险", "养老"],
    "unemployment": ["失业保险", "失业"],
    "medical": ["基本医疗保险", "医疗保险", "医疗"],
    "housing_fund": ["住房公积金", "公积金"],
}


EXCLUDE_DEDUCTION_TERMS = ["基数", "比例", "单位"]


def extract_year_month(filename: str) -> Optional[str]:
    """Extract YYYYMM or YYYY-MM from filename and return YYYY-MM."""
    m = re.search(r"(20\d{2})(\d{2})", filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    m = re.search(r"(20\d{2})-(\d{2})", filename)
    if m:
        return f"{m.group(1)}-{m.group(2)}"
    return None


def extract_unit_name(filename: str, year_month: Optional[str] = None) -> str:
    """Extract unit name from filename by removing year/month/suffix."""
    name = Path(filename).stem
    # Remove year-month patterns
    name = re.sub(r"20\d{2}-?\d{2}", "", name)
    # Remove common suffixes
    name = re.sub(r"[（(]系统[）)]", "", name)
    name = re.sub(r"工资发放表|工资表|人员工资|劳务派遣|人才派遣|派遣", "", name)
    name = name.strip("_-\t ")
    return name or "未知单位"


def normalize_value(value) -> float:
    if pd.isna(value):
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).replace(",", "").strip()
    try:
        return float(s)
    except ValueError:
        return 0.0


def find_header_row(df: pd.DataFrame, max_rows: int = 10) -> int:
    best_row = 0
    best_score = 0
    for i in range(min(max_rows, len(df))):
        cells = [str(c).strip() if pd.notna(c) else "" for c in df.iloc[i]]
        score = 0
        for field, keywords in KEYWORDS.items():
            weight = 3 if field in {"name", "id_card", "income"} else 1
            for kw in keywords:
                score += weight * sum(1 for cell in cells if kw in cell)
        if score > best_score:
            best_score = score
            best_row = i
    return best_row


def detect_columns(df: pd.DataFrame, header_row: int) -> dict:
    result = {}
    rows_to_scan = min(4, len(df) - header_row)

    for field, keywords in KEYWORDS.items():
        sorted_keywords = sorted(keywords, key=len, reverse=True)
        for offset in range(rows_to_scan):
            row_idx = header_row + offset
            if row_idx >= len(df):
                continue
            cells = [str(c).strip() if pd.notna(c) else "" for c in df.iloc[row_idx]]
            for col_idx, cell_value in enumerate(cells):
                already_assigned = col_idx in result.values()
                if already_assigned:
                    continue
                contains_base_term = any(term in cell_value for term in EXCLUDE_DEDUCTION_TERMS)
                if field not in {"name", "id_card", "employee_no", "income"} and contains_base_term:
                    continue
                if any(kw == cell_value or cell_value.startswith(kw) for kw in sorted_keywords):
                    result[field] = col_idx
                    break
            if field in result:
                break
    return result


def is_personal_deduction_col(df: pd.DataFrame, header_row: int, col_idx: int) -> bool:
    """Check if a column is the personal contribution (个人) by scanning rows below header."""
    for offset in range(1, min(4, len(df) - header_row)):
        row_idx = header_row + offset
        cell = str(df.iloc[row_idx, col_idx]).strip() if pd.notna(df.iloc[row_idx, col_idx]) else ""
        if cell == "个人":
            return True
        if cell == "单位":
            return False
    return True


def parse_payroll_file(file_path: str, manual_config: Optional[dict] = None) -> PayrollParseResult:
    filename = Path(file_path).name
    year_month = extract_year_month(filename)
    unit = extract_unit_name(filename, year_month)

    result = PayrollParseResult(
        filename=filename,
        unit=unit,
        year_month=year_month or "",
    )

    if not year_month:
        result.errors.append("无法从文件名解析申报月份")
        result.needs_mapping = True

    try:
        df = pd.read_excel(file_path, header=None)
    except Exception as e:
        result.errors.append(f"读取 Excel 失败: {e}")
        return result

    if manual_config:
        header_row = manual_config.get("header_row", 0)
        data_start_row = manual_config.get("data_start_row", header_row + 1)
        cols = {
            "name": manual_config["name_col"],
            "id_card": manual_config["id_card_col"],
            "income": manual_config["income_col"],
            "pension": manual_config.get("pension_col"),
            "unemployment": manual_config.get("unemployment_col"),
            "medical": manual_config.get("medical_col"),
            "housing_fund": manual_config.get("housing_fund_col"),
        }
    else:
        header_row = find_header_row(df)
        cols = detect_columns(df, header_row)
        data_start_row = header_row + 1
        # Skip sub-header rows if no data there
        while data_start_row < len(df):
            first_cell = df.iloc[data_start_row, 0]
            if pd.notna(first_cell) and str(first_cell).strip() not in ["", "NaN", "单位"]:
                try:
                    int(first_cell)
                    break
                except ValueError:
                    break
            data_start_row += 1

    result.detected_columns = cols

    required = {"name", "id_card", "income"}
    missing = required - set(cols.keys())
    if missing:
        result.errors.append(f"缺少必需列: {missing}")
        result.needs_mapping = True
        return result

    # For merged/multi-row headers, refine social insurance columns to personal part
    if not manual_config:
        for field in ["pension", "unemployment", "medical", "housing_fund"]:
            if field in cols and not is_personal_deduction_col(df, header_row, cols[field]):
                # Try to find next column with "个人" in the sub-header
                for c in range(cols[field] + 1, min(cols[field] + 4, df.shape[1])):
                    if is_personal_deduction_col(df, header_row, c):
                        cols[field] = c
                        break

    required_found = sum(1 for k in required if k in cols)
    result.confidence = required_found / len(required)

    for row_idx in range(data_start_row, len(df)):
        row = df.iloc[row_idx]
        name = str(row.iloc[cols["name"]]).strip() if pd.notna(row.iloc[cols["name"]]) else ""
        id_card = str(row.iloc[cols["id_card"]]).strip() if pd.notna(row.iloc[cols["id_card"]]) else ""
        if not name and not id_card:
            continue
        if not name or not id_card:
            result.errors.append(f"第 {row_idx + 1} 行缺少姓名或身份证，已跳过")
            continue

        employee_no = None
        if "employee_no" in cols and pd.notna(row.iloc[cols["employee_no"]]):
            employee_no = str(row.iloc[cols["employee_no"]]).strip()

        record = PayrollRecord(
            name=name,
            id_card=id_card,
            employee_no=employee_no,
            income=normalize_value(row.iloc[cols["income"]]),
            pension=normalize_value(row.iloc[cols["pension"]]) if "pension" in cols else 0.0,
            unemployment=normalize_value(row.iloc[cols["unemployment"]]) if "unemployment" in cols else 0.0,
            medical=normalize_value(row.iloc[cols["medical"]]) if "medical" in cols else 0.0,
            housing_fund=normalize_value(row.iloc[cols["housing_fund"]]) if "housing_fund" in cols else 0.0,
        )
        result.records.append(record)

    return result
