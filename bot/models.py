from typing import Optional
from sqlalchemy import Integer, String, Date
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class AlfredoDate(Base):
    __tablename__ = "alfredo_date"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date)
    description: Mapped[Optional[String]] = mapped_column(String)
    message_id: Mapped[Optional[Integer]] = mapped_column(Integer)
