from sqlalchemy import Integer, Column, String
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String(32), nullable=False)
    monday = Column(String(1024))
    tuesday = Column(String(1024))
    wednesday = Column(String(1024))
    thursday = Column(String(1024))
    friday = Column(String(1024))
    saturday = Column(String(1024))


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    chat_id = Column(String(32))
    name = Column(String(512))
    group_id = Column(Integer)
    access_level = Column(Integer)
    state = Column(String)
    buy_expires = Column(String)
