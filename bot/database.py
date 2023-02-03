import logging
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from models import Base, AlfredoDate


class Database:
    def __init__(self, output_file):
        self.log = logging.getLogger("Database")
        self.log.info("Creating Database")
        self.engine = create_engine(f"sqlite:///{output_file}", echo=False, future=True)
        Base.metadata.create_all(self.engine)
