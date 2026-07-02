"""
中国个税累计预扣法核心计算引擎
"""

from tax_calculator.tax_brackets import TAX_BRACKETS, BASIC_DEDUCTION_PER_MONTH


def get_tax_rate(taxable_income: float) -> tuple[float, float]:
    """
    根据累计应纳税所得额查找适用税率和速算扣除数。

    Args:
        taxable_income: 累计预扣预缴应纳税所得额

    Returns:
        (税率, 速算扣除数)
    """
    for bracket in TAX_BRACKETS:
        if taxable_income <= bracket["max"]:
            return bracket["rate"], bracket["deduct"]
    return TAX_BRACKETS[-1]["rate"], TAX_BRACKETS[-1]["deduct"]


def _sum_special_deductions(special_deductions: dict) -> float:
    """计算当月专项附加扣除合计。"""
    total = 0.0
    for key, value in special_deductions.items():
        if key == "serious_illness":
            # 大病医疗按年，仅在12月累加，这里先忽略逐月处理
            continue
        if isinstance(value, (int, float)):
            total += value
    return total


def calc_monthly_tax(monthly_data: list[dict]) -> list[dict]:
    """
    按累计预扣法计算全年逐月个税。

    Args:
        monthly_data: 每月数据列表，每个元素为 dict:
            - salary: float 月工资收入
            - social_insurance: float 三险一金
            - special_deductions: dict 专项附加扣除
            - other_deductions: float 其他扣除（可选，默认0）
            - rent_tier: str 住房租金档次（可选）

    Returns:
        逐月结果列表，每个元素为 dict:
            - month: int 月份
            - salary: float 当月工资
            - cumulative_income: float 累计收入
            - cumulative_deductions: float 累计扣除总额
            - cumulative_taxable_income: float 累计应纳税所得额
            - tax_rate: float 适用税率
            - quick_deduction: float 速算扣除数
            - cumulative_tax: float 累计应纳税额
            - monthly_tax: float 本期应缴税额
            - after_tax_income: float 税后收入
    """
    results = []
    cumulative_income = 0.0
    cumulative_basic_deduction = 0.0
    cumulative_social_insurance = 0.0
    cumulative_special_deduction = 0.0
    cumulative_other_deduction = 0.0
    cumulative_tax_paid = 0.0

    for month_idx, data in enumerate(monthly_data):
        month = month_idx + 1
        salary = float(data.get("salary", 0))
        social_insurance = float(data.get("social_insurance", 0))
        special_deductions = data.get("special_deductions", {})
        other_deductions = float(data.get("other_deductions", 0))

        # 累计
        cumulative_income += salary
        cumulative_basic_deduction += BASIC_DEDUCTION_PER_MONTH
        cumulative_social_insurance += social_insurance
        cumulative_other_deduction += other_deductions

        # 专项附加扣除：每月按其当月值累加
        monthly_special = _sum_special_deductions(special_deductions)
        cumulative_special_deduction += monthly_special

        # 大病医疗：第12个月时一次性加入
        if month == 12 and "serious_illness" in special_deductions:
            illness_amount = float(special_deductions.get("serious_illness", 0))
            cumulative_special_deduction += illness_amount

        # 累计应纳税所得额
        cumulative_taxable_income = (
            cumulative_income
            - cumulative_basic_deduction
            - cumulative_social_insurance
            - cumulative_special_deduction
            - cumulative_other_deduction
        )

        # 如果累计应纳税所得额为负，取0
        if cumulative_taxable_income < 0:
            cumulative_taxable_income = 0.0

        # 查找税率
        rate, quick_deduction = get_tax_rate(cumulative_taxable_income)

        # 累计应纳税额
        cumulative_tax = cumulative_taxable_income * rate - quick_deduction
        if cumulative_tax < 0:
            cumulative_tax = 0.0

        # 本期应缴 = 累计应纳税额 - 已预缴税额
        monthly_tax = cumulative_tax - cumulative_tax_paid
        if monthly_tax < 0:
            monthly_tax = 0.0  # 负值暂不退税

        cumulative_tax_paid = cumulative_tax

        cumulative_deductions = (
            cumulative_basic_deduction
            + cumulative_social_insurance
            + cumulative_special_deduction
            + cumulative_other_deduction
        )

        results.append({
            "month": month,
            "salary": salary,
            "cumulative_income": cumulative_income,
            "cumulative_deductions": cumulative_deductions,
            "cumulative_taxable_income": cumulative_taxable_income,
            "tax_rate": rate,
            "quick_deduction": quick_deduction,
            "cumulative_tax": cumulative_tax,
            "monthly_tax": monthly_tax,
            "after_tax_income": salary - social_insurance - monthly_tax,
        })

    return results


def calc_annual_summary(monthly_results: list[dict]) -> dict:
    """
    计算年度汇总。

    Args:
        monthly_results: calc_monthly_tax 的返回值

    Returns:
        dict: 年度汇总
    """
    total_income = sum(r["salary"] for r in monthly_results)
    total_tax = sum(r["monthly_tax"] for r in monthly_results)
    total_after_tax = sum(r["after_tax_income"] for r in monthly_results)

    # 查找税率跳档月份
    rate_jumps = []
    prev_rate = 0
    for r in monthly_results:
        if r["tax_rate"] > prev_rate:
            rate_jumps.append({
                "month": r["month"],
                "from_rate": prev_rate,
                "to_rate": r["tax_rate"],
            })
            prev_rate = r["tax_rate"]

    effective_tax_rate = total_tax / total_income if total_income > 0 else 0

    return {
        "total_income": total_income,
        "total_tax": total_tax,
        "total_after_tax": total_after_tax,
        "effective_tax_rate": effective_tax_rate,
        "rate_jumps": rate_jumps,
    }


def calc_old_method(monthly_data: list[dict]) -> list[dict]:
    """
    旧按月计算法（2018年及以前），用于对比。

    Args:
        monthly_data: 同 calc_monthly_tax

    Returns:
        逐月结果列表
    """
    results = []
    for month_idx, data in enumerate(monthly_data):
        month = month_idx + 1
        salary = float(data.get("salary", 0))
        social_insurance = float(data.get("social_insurance", 0))
        special_deductions = data.get("special_deductions", {})
        other_deductions = float(data.get("other_deductions", 0))

        monthly_special = _sum_special_deductions(special_deductions)

        # 旧方法按月计算
        taxable_income = (
            salary
            - BASIC_DEDUCTION_PER_MONTH
            - social_insurance
            - monthly_special
            - other_deductions
        )

        if taxable_income < 0:
            taxable_income = 0.0

        # 旧方法使用月度税率表
        rate, quick_deduction = _get_old_tax_rate(taxable_income)
        monthly_tax = taxable_income * rate - quick_deduction
        if monthly_tax < 0:
            monthly_tax = 0.0

        results.append({
            "month": month,
            "salary": salary,
            "taxable_income": taxable_income,
            "tax_rate": rate,
            "quick_deduction": quick_deduction,
            "monthly_tax": monthly_tax,
            "after_tax_income": salary - social_insurance - monthly_tax,
        })

    return results


def _get_old_tax_rate(monthly_taxable_income: float) -> tuple[float, float]:
    """
    旧方法月度税率表。
    """
    OLD_BRACKETS = [
        {"min": 0, "max": 3_000, "rate": 0.03, "deduct": 0},
        {"min": 3_000, "max": 12_000, "rate": 0.10, "deduct": 210},
        {"min": 12_000, "max": 25_000, "rate": 0.20, "deduct": 1_410},
        {"min": 25_000, "max": 35_000, "rate": 0.25, "deduct": 2_660},
        {"min": 35_000, "max": 55_000, "rate": 0.30, "deduct": 4_410},
        {"min": 55_000, "max": 80_000, "rate": 0.35, "deduct": 7_160},
        {"min": 80_000, "max": float("inf"), "rate": 0.45, "deduct": 15_160},
    ]
    for bracket in OLD_BRACKETS:
        if bracket["min"] < monthly_taxable_income <= bracket["max"]:
            return bracket["rate"], bracket["deduct"]
    return OLD_BRACKETS[-1]["rate"], OLD_BRACKETS[-1]["deduct"]
