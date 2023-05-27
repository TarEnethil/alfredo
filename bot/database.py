import logging
import os.path
from datetime import date
from sqlalchemy import create_engine, select, func
from sqlalchemy.orm import Session
from models import Base, AlfredoDate


class Database:
    def __init__(self, output_file):
        self.log = logging.getLogger("Database")

        if os.path.isfile(output_file):
            self.log.info(f"loading Database {output_file}")
        else:
            self.log.info(f"creating Database {output_file}")

        self.engine = create_engine(f"sqlite:///{output_file}", echo=False, future=True)
        Base.metadata.create_all(self.engine)

    def create_alfredo_date(self, date, description=None, message_id=None):
        new_date = AlfredoDate(date=date, description=description, message_id=message_id)

        with Session(self.engine) as session:
            session.add(new_date)
            session.commit()

    def get_future_dates(self):
        with Session(self.engine) as session:
            dates = session.scalars(select(AlfredoDate)
                                    .where(func.DATE(AlfredoDate.date) >= date.today())
                                    .order_by(AlfredoDate.date)).all()

        return dates

    def get_by_date(self, date):
        with Session(self.engine) as session:
            return session.scalars(select(AlfredoDate).where(AlfredoDate.date.is_(date))).first()

    def delete_date(self, date):
        with Session(self.engine) as session:
            session.delete(date)
            session.commit()
