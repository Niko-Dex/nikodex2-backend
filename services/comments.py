import math
import os
import select
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import desc, insert, select
from sqlalchemy.orm import selectinload

from common.dto import CommentRequest, PostRequest
from common.helper2 import account_of_type
from common.models import AccountType, Comment, Post, User
from services._shared import SessionManager

load_dotenv()
COMMENT_RATE_LIMIT = int(os.environ["COMMENT_RATE_LIMIT"])


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

        if not (account_of_type(user, AccountType.ADMIN) or stmt.author_id == user.id):
            return {"status_code": 401, "message": "Forbidden"}

        session.delete(stmt)
        session.commit()

        return True


async def create_comment_on_post(user_id: int, requestedRequest: CommentRequest):
    with SessionManager() as session:
        post_check = session.execute(
            select(Post).where(Post.id == requestedRequest.post_id)
        ).scalar_one_or_none()

        user_last_comment_check = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not user_last_comment_check or not post_check:
            return {"msg": "User or Comment doesn't exist.", "success": False}

        if user_last_comment_check.last_comment_at and not account_of_type(
            user_last_comment_check, AccountType.ADMIN
        ):
            total_seconds = (
                datetime.now() - user_last_comment_check.last_comment_at
            ).total_seconds()
            total_minutes = total_seconds / 60
            if total_minutes < COMMENT_RATE_LIMIT:
                return {
                    "msg": f"You have {math.floor(COMMENT_RATE_LIMIT - total_minutes)} minutes and {math.ceil((COMMENT_RATE_LIMIT * 60 - total_seconds) % 60)} seconds left before you can comment.",
                    "success": False,
                }

        user_last_comment_check.last_comment_at = datetime.now()

        if len(requestedRequest.content) > 300:
            return {"msg": "Comment too long.", "success": False}

        stmt = insert(Comment).values(
            author_id=user_id,
            post_id=requestedRequest.post_id,
            post_date=datetime.now(),
            content=requestedRequest.content,
        )
        session.execute(stmt)
        session.commit()

        return {"msg": "Inserted comment.", "success": True}
