import uuid
from sqlmodel import Session

from db.database import engine
from db.models import Employee, Unit


def test_create_employee():
    uid = uuid.uuid4().hex[:8]
    with Session(engine) as session:
        emp = Employee(id_card=f"2201011990{uid[:6]}", name=f"测试{uid}")
        session.add(emp)
        session.commit()
        session.refresh(emp)
        assert emp.id is not None
        assert emp.id_card == f"2201011990{uid[:6]}"
        session.delete(emp)
        session.commit()


def test_create_unit():
    uid = uuid.uuid4().hex[:8]
    with Session(engine) as session:
        unit = Unit(name=f"测试单位{uid}")
        session.add(unit)
        session.commit()
        session.refresh(unit)
        assert unit.id is not None
        assert unit.name == f"测试单位{uid}"
        session.delete(unit)
        session.commit()
