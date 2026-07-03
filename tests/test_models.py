from sqlmodel import Session

from db.database import engine
from db.models import Employee, Unit


def test_create_employee():
    with Session(engine) as session:
        emp = Employee(id_card="220101199001011234", name="张三")
        session.add(emp)
        session.commit()
        session.refresh(emp)
        assert emp.id is not None
        assert emp.id_card == "220101199001011234"


def test_create_unit():
    with Session(engine) as session:
        unit = Unit(name="测试单位")
        session.add(unit)
        session.commit()
        session.refresh(unit)
        assert unit.id is not None
        assert unit.name == "测试单位"
