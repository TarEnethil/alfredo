from database import Database
from datetime import date, timedelta
from models import AlfredoDate
from sqlalchemy import select, func
from sqlalchemy.orm import Session


def in_memory_db():
    return Database(":memory:")


def add_default_dates(db):
    db.create_alfredo_date(date.fromisoformat("2001-02-03"), "first description", 123)
    db.create_alfredo_date(date.fromisoformat("2002-03-04"), "", 456)
    db.create_alfredo_date(date.fromisoformat("2003-04-05"), None, 789)


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

        add_default_dates(db)

        assert_row_count(db, AlfredoDate, 3)

        with Session(db.engine) as session:
            d1 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(1))).first()
            d2 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(2))).first()
            d3 = session.scalars(select(AlfredoDate).where(AlfredoDate.id.is_(3))).first()

            assert d1 is not None
            assert d2 is not None
            assert d3 is not None

            assert d1.date == date.fromisoformat("2001-02-03")
            assert d2.date == date.fromisoformat("2002-03-04")
            assert d3.date == date.fromisoformat("2003-04-05")

            assert d1.description == "first description"
            assert d2.description == ""
            assert d3.description is None

            assert d1.message_id == 123
            assert d2.message_id == 456
            assert d3.message_id == 789

    def test_get_future_dates(self):
        db = in_memory_db()

        assert len(db.get_future_dates()) == 0

        one_day = timedelta(days=1)

        today = date.today()
        tomorrow = today + one_day
        overmorrow = tomorrow + one_day
        yesterday = today - one_day
        ereyesterday = yesterday - one_day

        db.create_alfredo_date(yesterday, None, 1)
        db.create_alfredo_date(today, None, 2)
        db.create_alfredo_date(tomorrow, None, 3)
        db.create_alfredo_date(overmorrow, None, 4)
        db.create_alfredo_date(ereyesterday, None, 5)

        future_dates = db.get_future_dates()
        assert len(future_dates) == 3

        assert future_dates[0].message_id == 2
        assert future_dates[1].message_id == 3
        assert future_dates[2].message_id == 4
