import os
from pathlib import Path

from sqlmodel import SQLModel, create_engine, Session

# Import all models so SQLModel can create tables
from db.models import Employee, Unit, MonthlyRecord, PayrollFile, ParserConfig  # noqa: F401

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'tax_declaration.db'}")

engine = create_engine(DATABASE_URL, echo=False, connect_args={"check_same_thread": False})


def init_db():
    SQLModel.metadata.create_all(engine)


def get_session() -> Session:
    with Session(engine) as session:
        yield session


def get_engine():
    return engine
