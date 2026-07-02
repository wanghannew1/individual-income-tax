from typing import Optional
from pydantic import BaseModel, Field


class MonthlyInput(BaseModel):
    salary: float = Field(..., ge=0, description="月工资收入")
    social_insurance: float = Field(0, ge=0, description="三险一金")
    special_deductions: dict = Field(default_factory=dict, description="专项附加扣除明细")
    other_deductions: float = Field(0, ge=0, description="其他扣除")
    rent_tier: Optional[str] = Field(None, description="住房租金档次")


class MonthlyResult(BaseModel):
    month: int = Field(..., ge=1, le=12)
    salary: float
    cumulative_income: float
    cumulative_deductions: float
    cumulative_taxable_income: float
    tax_rate: float
    quick_deduction: float
    cumulative_tax: float
    monthly_tax: float
    after_tax_income: float


class OldMethodResult(BaseModel):
    month: int = Field(..., ge=1, le=12)
    salary: float
    taxable_income: float
    tax_rate: float
    quick_deduction: float
    monthly_tax: float
    after_tax_income: float


class RateJump(BaseModel):
    month: int
    from_rate: float
    to_rate: float


class AnnualSummary(BaseModel):
    total_income: float
    total_tax: float
    total_after_tax: float
    effective_tax_rate: float
    rate_jumps: list[RateJump]


class CalculationResponse(BaseModel):
    monthly_results: list[MonthlyResult]
    annual_summary: AnnualSummary
    old_method_results: Optional[list[OldMethodResult]] = None
