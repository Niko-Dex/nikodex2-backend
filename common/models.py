from datetime import datetime
from typing import List

from sqlalchemy import (
    TIMESTAMP,
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    String,
    Text,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from sqlalchemy.sql.schema import CheckConstraint
from sqlalchemy.sql.sqltypes import Integer


class Base(DeclarativeBase):
    pass


class Niko(Base):
    __tablename__ = "nikos"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(127))
    description: Mapped[str] = mapped_column(String(255))
    doc: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    full_desc: Mapped[str] = mapped_column(String(1023))
    is_blacklisted: Mapped[bool] = mapped_column(default=False)
    author_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=True
    )
    abilities: Mapped[List["Ability"]] = relationship(
        back_populates="niko", passive_deletes=True
    )
    user: Mapped["User"] = relationship(back_populates="nikos", passive_deletes=True)

    @hybrid_property
    def author_name(self):
        if self.author_id is None:
            return self.author
        else:
            if self.user is None:
                return "Could not find author_name.."
            else:
                return self.user.username

    def __init__(self, id, name, description, full_desc, image):
        self.id = id
        self.name = name
        self.description = description
        self.full_desc = full_desc
        self.abilities = list()

    def __repr__(self):
        return f"Niko(id={self.id};name={self.name};description={self.description};full_desc={self.full_desc};author_id={self.author_id})"

    def set_abilities_list(self, lis: list):
        self.abilities = lis


class Notd(Base):
    __tablename__ = "notd"
    niko_id: Mapped[int] = mapped_column(
        ForeignKey("nikos.id", ondelete="CASCADE"), primary_key=True
    )
    chosen_at: Mapped[datetime] = mapped_column(
        TIMESTAMP, server_default=func.now(), server_onupdate=func.now(), index=True
    )


class Ability(Base):
    __tablename__ = "abilities"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    niko_id: Mapped[int] = mapped_column(ForeignKey("nikos.id", ondelete="CASCADE"))

    niko: Mapped["Niko"] = relationship(
        back_populates="abilities", passive_deletes=True
    )

    def __init__(self, id, name, niko_id):
        self.id = id
        self.name = name
        self.niko_id = niko_id

    def __repr__(self):
        return f"Ability(id={self.id};name={self.name};niko_id={self.niko_id})"


class Blog(Base):
    __tablename__ = "blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255))
    author: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(Text())
    post_datetime: Mapped[datetime] = mapped_column(DateTime())


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(255), unique=True)
    description: Mapped[str] = mapped_column(String(255))
    hashed_pass: Mapped[str] = mapped_column(String(1023))
    is_admin: Mapped[bool] = mapped_column(Boolean)

    nikos: Mapped[List["Niko"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    profile_picture: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    last_comment_at: Mapped[datetime | None] = mapped_column(DateTime(), nullable=True)
    posts: Mapped[List["Post"]] = relationship(
        back_populates="user", passive_deletes=True
    )
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="user", passive_deletes=True
    )


class SubmitUser(Base):
    __tablename__ = "submit_users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[str] = mapped_column(String(255), unique=True)
    last_submit_on: Mapped[int] = mapped_column(BigInteger())
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False)
    ban_reason: Mapped[str] = mapped_column(String(1023), default="")


class Submission(Base):
    __tablename__ = "submissions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    submit_date: Mapped[datetime] = mapped_column(DateTime())
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(String(255))
    full_desc: Mapped[str] = mapped_column(String(1023))
    image: Mapped[str] = mapped_column(String(1023))
    is_blacklisted: Mapped[bool] = mapped_column(Boolean(), default=False)


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    post_datetime: Mapped[datetime] = mapped_column(DateTime())
    title: Mapped[str] = mapped_column(String(255))
    content: Mapped[str] = mapped_column(String(1023))
    image: Mapped[str] = mapped_column(String(1023))
    comments: Mapped[List["Comment"]] = relationship(
        back_populates="post", passive_deletes=True
    )
    user: Mapped["User"] = relationship(back_populates="posts", passive_deletes=True)


class Comment(Base):
    __tablename__ = "comments"
    id: Mapped[int] = mapped_column(primary_key=True)
    author_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    content: Mapped[str] = mapped_column(String(1024))
    post_date: Mapped[datetime] = mapped_column(DateTime())
    post: Mapped["Post"] = relationship(back_populates="comments", passive_deletes=True)
    user: Mapped["User"] = relationship(back_populates="comments", passive_deletes=True)


class PostNikoAgenda(Base):
    __tablename__ = "postniko_agenda"

    id: Mapped[int] = mapped_column(primary_key=True)
    niko_id: Mapped[int] = mapped_column(ForeignKey("nikos.id", ondelete="CASCADE"))
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))


class Banner(Base):
    __tablename__ = "banner"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    title: Mapped[str] = mapped_column(String(120))
    content: Mapped[str] = mapped_column(String(500))
    is_dismissable: Mapped[bool] = mapped_column(Boolean())
    banner_identifier: Mapped[str] = mapped_column(String(100))

    __table_args__ = (CheckConstraint("id = 1", name="one_row_only"),)
