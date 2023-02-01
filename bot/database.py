import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, TelegramUser, AlfredoDate


class Database:
    def __init__(self, output_file):
        self.log = logging.getLogger("Database")
        self.log.info("Creating Database")
        self.engine = create_engine(f"sqlite:///{output_file}", echo=False, future=True)
        Base.metadata.create_all(self.engine)

    def get_or_add_user(self, userdata):
        with Session(self.engine, expire_on_commit=False) as session:
            user = session.scalars(select(TelegramUser).where(TelegramUser.id.is_(userdata["id"]))).first()

            if user is None:
                user = TelegramUser(id=userdata["id"], name=userdata["name"])

                session.add(user)
                session.commit()
            elif user.name != userdata["name"]:
                self.log.info(f"user {user.id} changed their name from {user.name} to {userdata['name']}")

                user.name = userdata["name"]
                session.add(user)
                session.commit()

            return user
