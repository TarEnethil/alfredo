from typing import Optional
from sqlalchemy import Integer, String, DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class TelegramUser(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String)


class AlfredoDate(Base):
    __tablename__ = "alfredo_date"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[DateTime] = mapped_column(DateTime)
    description: Mapped[Optional[String]] = mapped_column(String)
