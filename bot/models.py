from typing import Optional, List
from sqlalchemy import Column, Integer, String, Date, Table, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


participation_table = Table(
    "participation_table",
    Base.metadata,
    Column("user_id", ForeignKey("user.id"), primary_key=True),
    Column("date_id", ForeignKey("alfredo_date.id"), primary_key=True)
)


class TelegramUser(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[String] = mapped_column(String)
    participations: Mapped[List["AlfredoDate"]] = relationship(secondary=participation_table, back_populates="participants")


class AlfredoDate(Base):
    __tablename__ = "alfredo_date"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    date: Mapped[Date] = mapped_column(Date)
    description: Mapped[Optional[String]] = mapped_column(String)
    participants: Mapped[List["TelegramUser"]] = relationship(secondary=participation_table, back_populates="participations")