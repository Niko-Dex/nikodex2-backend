import io
import os
import re
import uuid

from dotenv import load_dotenv
from fastapi import UploadFile
from fastapi.responses import FileResponse
from passlib.context import CryptContext
from PIL import Image
from sqlalchemy import (
    Update,
    func,
    select,
    update,
)
from sqlalchemy.dialects.mysql import insert

from common.dto import (
    ImgReturnType,
    SubmitUserRequest,
    UserChangeRequest,
)
from common.models import SubmitUser, User
from services._shared import SessionManager
from services.images import IMAGE_DIR, MAX_IMG_SIZE

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

load_dotenv()


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


def get_user_profile_picture(id: int):
    with SessionManager() as session:
        stmt = session.execute(select(User).where(User.id == id)).scalar_one_or_none()

        if not stmt:
            return None

        if stmt.profile_picture is None:
            return FileResponse("images/default_pfp.png")

        path = os.path.join(IMAGE_DIR, stmt.profile_picture)
        if stmt.profile_picture is None or not os.path.exists(path):
            return FileResponse("images/default_pfp.png")

        return FileResponse(path, headers={"ETag": stmt.profile_picture})


def delete_profile_picture(user_id: int):
    with SessionManager() as session:
        stmt = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not stmt:
            return False
        if stmt.profile_picture is not None:
            path = os.path.join(IMAGE_DIR, stmt.profile_picture)
            os.remove(path)

        stmt.profile_picture = None
        session.commit()

        return True


def get_user_by_usersearch(username: str, page: int, count: int):
    with SessionManager() as session:
        stmt = select(User).where(User.username.like(f"%{username}%"))
        stmt = stmt.offset(int(count) * (int(page) - 1)).limit(int(count))
        return session.scalars(stmt).fetchall()


def delete_user(id: int):
    with SessionManager() as session:
        user = session.execute(select(User).where(User.id == id)).scalar_one_or_none()
        if user:
            if user.is_admin:
                return False
            session.delete(user)
            session.commit()
            return True
        else:
            return False


def is_valid_username(username: str):
    return re.fullmatch(r"[A-Za-z0-9_]{1,32}", username)


def insert_user(req: UserChangeRequest):
    with SessionManager() as session:
        same_name_entity = session.execute(
            select(User).where(User.username == req.new_username)
        ).scalar_one_or_none()
        if same_name_entity is not None:
            return False

        if len(req.new_username) == 0 or not is_valid_username(req.new_username):
            return False

        if len(req.new_password) == 0:
            return False

        if len(req.new_description) == 0 or len(req.new_description) > 255:
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


async def update_profile_picture(user_id: int, file: UploadFile):
    with SessionManager() as session:
        user_entity = session.execute(
            select(User).where(User.id == user_id)
        ).scalar_one_or_none()

        if not user_entity:
            return {"msg": "User doesn't exist!", "err": True}

        if not file.content_type or not file.content_type.startswith("image/"):
            return {"msg": "Not a valid file!", "err": True}
        if not file.size or file.size > MAX_IMG_SIZE:
            return {"msg": "File too large!", "err": True}

        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return {"msg": "Failed to open image!", "err": True}

        img_path = f"u_{user_id}_{uuid.uuid4()}.png"
        if user_entity.profile_picture:
            old_profile_exists = os.path.join(IMAGE_DIR, user_entity.profile_picture)

            try:
                if os.path.exists(old_profile_exists):
                    os.remove(old_profile_exists)
            except:
                print("Couldn't remove profile picture. Skipping...")

        image.save(os.path.join(IMAGE_DIR, img_path), format="PNG")

        user_entity.profile_picture = img_path
        session.commit()

        return {"msg": "Updated profile.", "err": False}


def update_user(username: str, req: UserChangeRequest):
    with SessionManager() as session:
        entity = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()
        if entity is None:
            return False

        if len(req.new_username) > 0:
            if req.new_username != username:
                same_name_entity = session.execute(
                    select(User).where(User.username == req.new_username)
                ).scalar_one_or_none()
                if same_name_entity is not None:
                    return False

            if not is_valid_username(req.new_username):
                return False
            entity.username = req.new_username

        if len(req.new_password) > 0:
            entity.hashed_pass = pwd_context.hash(req.new_password)

        if len(req.new_description) > 0:
            if len(req.new_description) > 255:
                return False
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
