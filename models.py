from datetime import datetime
from typing import List
from sqlalchemy import DateTime, String
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship

class Base(DeclarativeBase):
    pass

class Niko(Base):
    __tablename__ = "nikos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String())
    image: Mapped[str] = mapped_column(String())
    doc: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    full_desc: Mapped[str] = mapped_column(String())

    abilities: Mapped[List["Ability"]] = relationship(
        back_populates="niko"
    )

    def __init__(self, id, name, description, full_desc, image):
        self.id = id
        self.name = name
        self.description = description
        self.full_desc = full_desc
        self.image = image
        self.abilities = list()

    def __repr__(self):
        return f"Niko(id={self.id};name={self.name};description={self.description};full_desc={self.full_desc};image={self.image})"

    def set_abilities_list(self, lis: list):
        self.abilities = lis

class Ability(Base):
    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    niko_id: Mapped[int] = mapped_column(ForeignKey("nikos.id"))

    niko: Mapped["Niko"] = relationship(back_populates="abilities")

    def __init__(self, id, name, niko_id):
        self.id = id
        self.name = name;
        self.niko_id = niko_id

    def __repr__(self):
        return f"Ability(id={self.id};name={self.name};niko_id={self.niko_id})"

class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String())
    post_datetime: Mapped[datetime] = mapped_column(DateTime())

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String())
    hashed_pass: Mapped[str] = mapped_column(String())


