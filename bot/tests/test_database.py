from database import Database
from models import AlfredoDate
from sqlalchemy import select, func
from sqlalchemy.orm import Session


def in_memory_db():
    return Database(":memory:")


class TestDatabase:
    def test_init(self):
        db = in_memory_db()

        with Session(db.engine) as session:
            count = session.scalars(select(func.count()).select_from(AlfredoDate)).first()

            assert count == 0
