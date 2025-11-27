from datetime import datetime

from sqlalchemy import (
    desc,
    select,
)
from sqlalchemy.dialects.mysql import insert

from common.dto import (
    BlogRequest,
)
from common.models import Blog
from services._shared import SessionManager


def get_blogs():
    with SessionManager() as session:
        stmt = select(Blog).order_by(desc(Blog.post_datetime))
        return session.scalars(stmt).fetchall()


def get_blog_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Blog).where(Blog.id == id).limit(1)
        return session.scalars(stmt).one()


def post_blog(req: BlogRequest):
    with SessionManager() as session:
        stmt = insert(Blog).values(
            title=req.title,
            content=req.content,
            author=req.author,
            post_datetime=datetime.now(),
        )
        session.execute(stmt)
        session.commit()
        return {"msg": "Posted Blog."}


def update_blog(id: int, req: BlogRequest):
    with SessionManager() as session:
        entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one_or_none()
        if entity is None:
            return None
        entity.title = req.title
        entity.content = req.content
        entity.author = req.author
        session.commit()
        return {"msg": "Updated Blog."}


def delete_blog(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Blog).where(Blog.id == id)).scalar_one()
        if entity is None:
            return None
        else:
            session.delete(entity)
            session.commit()
            return entity
