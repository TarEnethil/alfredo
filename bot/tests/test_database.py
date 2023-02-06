from database import Database
from datetime import date
from models import AlfredoDate
from sqlalchemy import select, func
from sqlalchemy.orm import Session


def in_memory_db():
    return Database(":memory:")


def assert_row_count(db, table, count):
    with Session(db.engine) as session:
        actual = session.scalars(select(func.count()).select_from(table)).first()

    assert count == actual


class TestDatabase:
    def test_init(self):
        db = in_memory_db()

        assert_row_count(db, AlfredoDate, 0)

    def test_create_alfredo_date(self):
        db = in_memory_db()

        date1 = date.fromisoformat("2001-02-03")
        date2 = date.fromisoformat("2002-03-04")
        date3 = date.fromisoformat("2003-04-05")

        db.create_alfredo_date(date1, "first description", 123)
        db.create_alfredo_date(date2, "", 456)
        db.create_alfredo_date(date3, None, 789)

        assert_row_count(db, AlfredoDate, 3)

        with Session(db.engine) as session:
            d1 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(1))).first()
            d2 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(2))).first()
            d3 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(3))).first()

            assert d1 is not None
            assert d2 is not None
            assert d3 is not None

            assert d1.date == date1
            assert d2.date == date2
            assert d3.date == date3

            assert d1.description == "first description"
            assert d2.description == ""
            assert d3.description is None

            assert d1.message_id == 123
            assert d2.message_id == 456
            assert d3.message_id == 789
