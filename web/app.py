import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from starlette.templating import _TemplateResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape
import uvicorn

from tax_calculator.core import calc_monthly_tax, calc_annual_summary, calc_old_method
from tax_calculator.tax_brackets import SPECIAL_DEDUCTIONS

app = FastAPI(title="个税累计预扣计算器")

base_dir = os.path.dirname(__file__)
templates_dir = os.path.join(base_dir, "templates")

jinja_env = Environment(
    loader=FileSystemLoader(templates_dir),
    autoescape=select_autoescape(),
)

static_dir = os.path.join(base_dir, "static")
if os.path.isdir(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


DEDUCTION_KEYS = [
    "infant_care",
    "children_education",
    "continuing_education",
    "mortgage_interest",
    "housing_rent",
    "elderly_care",
    "serious_illness",
]


def _render(name: str, context: dict, request: Request) -> _TemplateResponse:
    template = jinja_env.get_template(name)
    return _TemplateResponse(template, {**context, "request": request})


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _render(
        "index.html",
        {
            "special_deductions": SPECIAL_DEDUCTIONS,
            "deduction_keys": DEDUCTION_KEYS,
            "months": 12,
        },
        request,
    )


def _parse_float(value) -> float:
    try:
        v = float(value)
        return max(v, 0.0)
    except (ValueError, TypeError):
        return 0.0


def _parse_deductions(form_data: dict, prefix: str) -> dict:
    deductions = {}
    for key in DEDUCTION_KEYS:
        field_name = f"{prefix}_{key}"
        val = _parse_float(form_data.get(field_name, 0))
        if val > 0:
            deductions[key] = val
    return deductions


@app.post("/calculate", response_class=HTMLResponse)
async def calculate(request: Request, months: int = Form(12), comparison: bool = Form(False)):
    form_data = await request.form()

    monthly_data = []
    for i in range(1, months + 1):
        prefix = f"m{i}"
        salary = _parse_float(form_data.get(f"{prefix}_salary", 0))
        social = _parse_float(form_data.get(f"{prefix}_social", 0))
        other = _parse_float(form_data.get(f"{prefix}_other", 0))
        deductions = _parse_deductions(form_data, prefix)

        monthly_data.append({
            "salary": salary,
            "social_insurance": social,
            "special_deductions": deductions,
            "other_deductions": other,
        })

    results = calc_monthly_tax(monthly_data)
    summary = calc_annual_summary(results)

    old_results = None
    if comparison:
        old_results = calc_old_method(monthly_data)

    return _render(
        "results.html",
        {
            "results": results,
            "summary": summary,
            "old_results": old_results,
            "comparison": comparison,
        },
        request,
    )


if __name__ == "__main__":
    uvicorn.run("web.app:app", host="0.0.0.0", port=8000, reload=False)
