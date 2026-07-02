"""
核心计算引擎测试
"""

import sys
sys.path.insert(0, '/home/ubuntu/tax-tools/individual-income-tax')

import pytest
from tax_calculator.core import (
    get_tax_rate,
    calc_monthly_tax,
    calc_annual_summary,
    calc_old_method,
)


class TestGetTaxRate:
    """税率查找函数测试"""

    def test_3_percent_bracket(self):
        """不超过36,000 -> 3%"""
        rate, deduct = get_tax_rate(0)
        assert rate == 0.03
        assert deduct == 0

        rate, deduct = get_tax_rate(36_000)
        assert rate == 0.03
        assert deduct == 0

    def test_10_percent_bracket(self):
        """36,000 ~ 144,000 -> 10%"""
        rate, deduct = get_tax_rate(36_001)
        assert rate == 0.10
        assert deduct == 2_520

        rate, deduct = get_tax_rate(100_000)
        assert rate == 0.10
        assert deduct == 2_520

    def test_45_percent_bracket(self):
        """超过960,000 -> 45%"""
        rate, deduct = get_tax_rate(1_000_000)
        assert rate == 0.45
        assert deduct == 181_920


class TestCalcMonthlyTax:
    """累计预扣法计算测试"""

    def test_low_income_steady(self):
        """
        低收入稳定工资：月薪11,000，三险一金1,700，住房租金1,500
        全年应纳税所得额33,600元，始终3%税率，每月税84元
        """
        data = [
            {
                "salary": 11_000,
                "social_insurance": 1_700,
                "special_deductions": {"housing_rent": 1_500},
            }
        ] * 12

        results = calc_monthly_tax(data)

        # 前三个月都是84
        assert results[0]["monthly_tax"] == 84, f"1月: {results[0]['monthly_tax']}"
        assert results[1]["monthly_tax"] == 84, f"2月: {results[1]['monthly_tax']}"
        assert results[2]["monthly_tax"] == 84, f"3月: {results[2]['monthly_tax']}"

        # 全年税率始终3%
        for r in results:
            assert r["tax_rate"] == 0.03

        # 全年合计
        total_tax = sum(r["monthly_tax"] for r in results)
        assert total_tax == 1_008, f"全年合计: {total_tax}"

    def test_mid_income_rate_jump(self):
        """
        中高收入：月薪40,000，三险一金6,000，附加扣除3,000（子女教育+房贷+赡养老人）
        1月：26,000×3%=780
        2月：52,000×10%-2,520-780=1,900
        3月：78,000×10%-2,520-2,680=2,600
        """
        data = [
            {
                "salary": 40_000,
                "social_insurance": 6_000,
                "special_deductions": {
                    "children_education": 1_000,
                    "mortgage_interest": 1_000,
                    "elderly_care": 1_000,
                },
            }
        ] * 12

        results = calc_monthly_tax(data)

        assert results[0]["monthly_tax"] == 780, f"1月: {results[0]['monthly_tax']}"
        assert results[1]["monthly_tax"] == 1_900, f"2月: {results[1]['monthly_tax']}"
        assert results[2]["monthly_tax"] == 2_600, f"3月: {results[2]['monthly_tax']}"
        assert results[3]["monthly_tax"] == 2_600, f"4月: {results[3]['monthly_tax']}"

        # 1月3%，2月起10%
        assert results[0]["tax_rate"] == 0.03
        assert results[1]["tax_rate"] == 0.10

    def test_variable_income_smoothing(self):
        """
        收入波动：月薪15,000/45,000/15,000
        验证累计预扣法对收入波动的平滑效果
        """
        data = [
            {"salary": 15_000, "social_insurance": 3_000, "other_deductions": 200, "special_deductions": {
                "children_education": 1_000, "mortgage_interest": 1_000, "elderly_care": 2_000,
            }},
            {"salary": 45_000, "social_insurance": 3_000, "other_deductions": 200, "special_deductions": {
                "children_education": 1_000, "mortgage_interest": 1_000, "elderly_care": 2_000,
            }},
            {"salary": 15_000, "social_insurance": 3_000, "other_deductions": 200, "special_deductions": {
                "children_education": 1_000, "mortgage_interest": 1_000, "elderly_care": 2_000,
            }},
        ]

        results = calc_monthly_tax(data)

        # 验证结果
        assert results[0]["monthly_tax"] == 84
        # 2月税率不跳档（累计应纳税所得额35,600仍在3%区间）
        assert results[0]["tax_rate"] == 0.03
        # 3月累计应纳税所得额38,400跳档到10%
        assert results[2]["tax_rate"] == 0.10

    def test_zero_income(self):
        """零收入：应缴税额为0"""
        data = [{"salary": 0, "social_insurance": 0, "special_deductions": {}}] * 12
        results = calc_monthly_tax(data)

        for r in results:
            assert r["monthly_tax"] == 0
            assert r["cumulative_taxable_income"] == 0

    def test_very_high_income(self):
        """极高收入：验证45%税率"""
        data = [
            {"salary": 200_000, "social_insurance": 10_000, "special_deductions": {}}
        ] * 12

        results = calc_monthly_tax(data)

        # 最后一个月的税率应该是45%
        assert results[-1]["tax_rate"] == 0.45


class TestCalcAnnualSummary:
    """年度汇总测试"""

    def test_summary_basic(self):
        """年度汇总基本测试"""
        data = [
            {
                "salary": 40_000,
                "social_insurance": 6_000,
                "special_deductions": {
                    "children_education": 1_000,
                    "mortgage_interest": 1_000,
                    "elderly_care": 1_000,
                },
            }
        ] * 12

        results = calc_monthly_tax(data)
        summary = calc_annual_summary(results)

        assert summary["total_income"] == 480_000
        assert summary["total_tax"] > 0
        assert len(summary["rate_jumps"]) > 0


class TestCalcOldMethod:
    """旧按月计算法测试"""

    def test_old_method_high_tax(self):
        """
        旧方法下月薪55,000，50,000应纳税所得额适用30%税率
        """
        data = [
            {"salary": 55_000, "social_insurance": 0, "special_deductions": {}}
        ] * 12

        results = calc_old_method(data)

        # 50,000应纳税所得额，30%税率，速算扣除4,410
        assert results[0]["tax_rate"] == 0.30
        assert results[0]["monthly_tax"] == 10_590
