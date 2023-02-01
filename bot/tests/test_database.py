from database import Database
from models import TelegramUser
from sqlalchemy import select, func
from sqlalchemy.orm import Session


def in_memory_db():
    return Database(":memory:")


class TestDatabase:
    def test_init(self):
        db = in_memory_db()

        with Session(db.engine) as session:
            count = session.scalars(select(func.count()).select_from(TelegramUser)).first()

            assert count == 0

    def test_get_or_add_user(self):
        user1 = {
            "id": 1337,
            "name": "Alfredo"
        }

        user2 = {
            "id": 1338,
            "name": "Giuseppe"
        }

        user3 = {
            "id": 1337,
            "name": "Panini"
        }

        db = in_memory_db()

        user1_db = db.get_or_add_user(user1)
        user2_db = db.get_or_add_user(user2)
        user3_db = db.get_or_add_user(user3)

        assert user1_db.id == user1["id"]
        assert user1_db.name == user1["name"]

        assert user2_db.id == user2["id"]
        assert user2_db.name == user2["name"]

        assert user3_db.id == user1_db.id
        # name was updated
        assert user3_db.name == user3["name"]

        with Session(db.engine) as session:
            count = session.scalars(select(func.count()).select_from(TelegramUser)).first()
            assert count == 2
