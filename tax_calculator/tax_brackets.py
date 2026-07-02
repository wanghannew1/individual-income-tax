"""
中国个人所得税税率表与专项附加扣除标准
"""

# 居民个人工资薪金所得预扣预缴税率表
# 7级超额累进税率
TAX_BRACKETS = [
    {"min": 0, "max": 36_000, "rate": 0.03, "deduct": 0},
    {"min": 36_000, "max": 144_000, "rate": 0.10, "deduct": 2_520},
    {"min": 144_000, "max": 300_000, "rate": 0.20, "deduct": 16_920},
    {"min": 300_000, "max": 420_000, "rate": 0.25, "deduct": 31_920},
    {"min": 420_000, "max": 660_000, "rate": 0.30, "deduct": 52_920},
    {"min": 660_000, "max": 960_000, "rate": 0.35, "deduct": 85_920},
    {"min": 960_000, "max": float("inf"), "rate": 0.45, "deduct": 181_920},
]

# 基本减除费用（起征点），元/月
BASIC_DEDUCTION_PER_MONTH = 5_000

# 专项附加扣除标准（元/月）
SPECIAL_DEDUCTIONS = {
    "infant_care": {
        "label": "3岁以下婴幼儿照护",
        "amount_per_child": 2_000,
        "description": "每个婴幼儿每月2,000元，父母各扣50%或一方全额",
    },
    "children_education": {
        "label": "子女教育",
        "amount_per_child": 2_000,
        "description": "每个子女每月2,000元，从3岁到博士",
    },
    "continuing_education": {
        "label": "继续教育",
        "amount_per_month": 400,
        "amount_per_year": 3_600,
        "description": "学历教育每月400元（最长48个月），职业证书一次性3,600元",
    },
    "mortgage_interest": {
        "label": "住房贷款利息",
        "amount_per_month": 1_000,
        "description": "首套房，每月1,000元，最长240个月",
    },
    "housing_rent": {
        "label": "住房租金",
        "amount_per_month": 1_500,
        "description": "直辖市/省会1,500，百万人口城市1,100，其他800",
    },
    "elderly_care": {
        "label": "赡养老人",
        "amount_per_month": 3_000,
        "description": "独生子女3,000，非独生子女分摊（每人≤1,500）",
    },
    "serious_illness": {
        "label": "大病医疗",
        "amount_per_year": 80_000,
        "description": "年度限额80,000元，汇算清缴时申报",
    },
}

# 住房租金分档标准
RENT_DEDUCTION_TIERS = {
    "first_tier": 1_500,  # 直辖市、省会、计划单列市
    "second_tier": 1_100,  # 人口>100万的城市
    "third_tier": 800,     # 人口≤100万的城市
}
