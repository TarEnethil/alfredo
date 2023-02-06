import logging
import os.path
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from models import Base, AlfredoDate


class Database:
    def __init__(self, output_file):
        self.log = logging.getLogger("Database")

        if os.path.isfile(output_file):
            self.log.info(f"Loading Database {output_file}")
        else:
            self.log.info(f"Creating Database {output_file}")

        self.engine = create_engine(f"sqlite:///{output_file}", echo=False, future=True)
        Base.metadata.create_all(self.engine)

    def create_alfredo_date(self, date, description, message_id):
        new_date = AlfredoDate(date=date, description=description, message_id=message_id)

        with Session(self.engine) as session:
            session.add(new_date)
            session.commit()
