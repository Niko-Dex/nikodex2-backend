from passlib.context import CryptContext
from sqlalchemy import (
    func,
    select,
)
from sqlalchemy.dialects.mysql import insert

from common.dto import (
    SubmitUserRequest,
    UserChangeRequest,
)
from common.models import SubmitUser, User
from services._shared import SessionManager

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_user_count():
    with SessionManager() as session:
        return session.query(func.count(User.id)).one()[0]


def get_user_by_username(username: str):
    with SessionManager() as session:
        stmt = select(User).where(User.username == username).limit(1)
        return session.scalars(stmt).one()


def get_user_by_name(username: str):
    with SessionManager() as session:
        stmt = select(User).where(User.username == username)
        return session.scalars(stmt).one()


def get_user_by_id(id: int):
    with SessionManager() as session:
        stmt = select(User).where(User.id == id)
        return session.scalars(stmt).one()


def get_user_by_usersearch(username: str, page: int, count: int):
    with SessionManager() as session:
        stmt = select(User).where(User.username.like(f"%{username}%"))
        stmt = stmt.offset(int(count) * (int(page) - 1)).limit(int(count))
        return session.scalars(stmt).fetchall()


def insert_user(req: UserChangeRequest):
    with SessionManager() as session:
        same_name_entity = session.execute(
            select(User).where(User.username == req.new_username)
        ).scalar_one_or_none()
        if same_name_entity is not None:
            return False

        if len(req.new_username) == 0:
            return False

        if len(req.new_password) == 0:
            return False

        if len(req.new_description) == 0:
            return False

        stmt = insert(User).values(
            username=req.new_username,
            hashed_pass=pwd_context.hash(req.new_password),
            description=req.new_description,
            is_admin=False,
        )

        session.execute(stmt)
        session.commit()
        return True


def update_user(username: str, req: UserChangeRequest):
    with SessionManager() as session:
        same_name_entity = session.execute(
            select(User).where(User.username == req.new_username)
        ).scalar_one_or_none()
        same_description_entity = session.execute(
            select(User).where(User.description.like(f"%{req.new_description}%"))
        ).scalar_one_or_none()
        if same_name_entity is not None and same_description_entity is not None:
            return False

        entity = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if entity is None:
            return False

        if len(req.new_username) > 0:
            entity.username = req.new_username

        if len(req.new_password) > 0:
            entity.hashed_pass = pwd_context.hash(req.new_password)

        if len(req.new_description) > 0:
            entity.description = req.new_description
        session.commit()

        return True


def get_submit_user(user_id: str):
    with SessionManager() as session:
        stmt = select(SubmitUser).where(SubmitUser.user_id == user_id).limit(1)
        return session.scalars(stmt).one_or_none()


def post_submit_user(user_id: str, req: SubmitUserRequest):
    with SessionManager() as session:
        stmt = (
            insert(SubmitUser)
            .values(
                user_id=user_id,
                last_submit_on=req.last_submit_on,
                is_banned=req.is_banned,
                ban_reason=req.ban_reason,
            )
            .on_duplicate_key_update(
                last_submit_on=req.last_submit_on,
                is_banned=req.is_banned,
                ban_reason=req.ban_reason,
            )
        )
        session.execute(stmt)
        session.commit()
        return {"msg": "Updated submit user."}
