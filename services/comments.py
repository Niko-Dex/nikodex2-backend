import select
from datetime import datetime
from turtle import pos

from sqlalchemy import desc, func, insert, select
from sqlalchemy.orm import selectinload

from common.dto import CommentRequest, PostRequest
from common.models import Comment, Post, User
from services._shared import SessionManager


def get_all_comments_by_user_id(user_id: int):
    with SessionManager() as session:
        stmt = (
            select(Comment)
            .where(Comment.author_id == user_id)
            .options(selectinload(Comment.user))
        )
        stmt = stmt.order_by(desc(Comment.id))
        return session.execute(stmt).scalars().fetchall()


def get_all_comments_by_post_id(post_id: int):
    with SessionManager() as session:
        stmt = (
            select(Comment)
            .where(Comment.post_id == post_id)
            .options(selectinload(Comment.user))
        )
        stmt = stmt.order_by(desc(Comment.id))
        return session.execute(stmt).scalars().fetchall()


def delete_comment_on_post(user: User, comment_id: int):
    with SessionManager() as session:
        stmt = session.execute(
            select(Comment).where(Comment.id == comment_id)
        ).scalar_one_or_none()

        if not stmt:
            return {"status_code": 404, "message": "Comment not found"}

        if not (user.is_admin or stmt.author_id == user.id):
            return {"status_code": 401, "message": "Forbidden"}

        session.delete(stmt)
        session.commit()

        return True


def create_comment_on_post(user_id: int, requestedRequest: CommentRequest):
    with SessionManager() as session:
        post_check = session.execute(
            select(Post).where(Post.id == requestedRequest.post_id)
        ).scalar_one_or_none()
        if not post_check:
            return False

        if requestedRequest.content.__len__() > 300:
            return False

        stmt = insert(Comment).values(
            author_id=user_id,
            post_id=requestedRequest.post_id,
            post_date=datetime.now(),
            content=requestedRequest.content,
        )
        session.execute(stmt)
        session.commit()

        return True
