from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers import dashboard, employees, monthly, history
from db.database import init_db

app = FastAPI(title="个税申报数据整理工具", version="0.1.0")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

app.include_router(dashboard.router)
app.include_router(employees.router, prefix="/employees")
app.include_router(monthly.router, prefix="/monthly")
app.include_router(history.router, prefix="/history")


@app.on_event("startup")
def on_startup():
    init_db()


@app.get("/")
def root(request: Request):
    return templates.TemplateResponse(request, "dashboard.html")
