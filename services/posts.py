import io
import os
import uuid
from datetime import datetime

from fastapi import UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import (
    select,
    func
)
from sqlalchemy.dialects.mysql import insert
from sqlalchemy.orm import selectinload

from common.dto import (
    PostRequestForm,
)
from common.models import Post
from services.images import IMAGE_DIR, MAX_IMG_SIZE
from services._shared import SessionManager


def get_posts():
    with SessionManager() as session:
        stmt = select(Post).options(selectinload(Post.user))
        return session.scalars(stmt).fetchall()


def get_posts_count():
    with SessionManager() as session:
        return session.query(func.count(Post.id)).one()[0]


def get_posts_page(page: int, count: int):
    with SessionManager() as session:
        if int(page) < 1:
            return None
        stmt = (
            select(Post)
            .options(selectinload(Post.user))
            .offset(int(count) * (int(page) - 1))
            .limit(int(count))
        )
        return session.scalars(stmt).fetchall()


def get_post_userid(user_id: int):
    with SessionManager() as session:
        stmt = (
            select(Post).where(Post.user_id == user_id).options(selectinload(Post.user))
        )
        return session.scalars(stmt).fetchall()


def get_post_id(id: int):
    with SessionManager() as session:
        stmt = select(Post).where(Post.id == id).options(selectinload(Post.user))
        return session.scalars(stmt).one_or_none()


def get_post_image(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Post).where(Post.id == id).options(selectinload(Post.user))
        ).scalar_one_or_none()
        if entity is None:
            return None
        if len(entity.image) == 0:
            return FileResponse(
                os.path.join("images/default.png"), media_type="image/png"
            )

        path = os.path.join(IMAGE_DIR, f"{entity.image}")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")


async def insert_post(user_id: int, req: PostRequestForm, file: UploadFile):
    with SessionManager() as session:
        if not file.content_type or not file.content_type.startswith("image/"):
            return {"msg": "Not a valid file!", "err": True}
        if not file.size or file.size > MAX_IMG_SIZE:
            return {"msg": "File too large!", "err": True}
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return {"msg": "Failed to open image!", "err": True}

        id_str = str(uuid.uuid4())
        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"{id_str}.png")

        image.save(path, format="PNG")

        stmt = insert(Post).values(
            user_id=user_id,
            title=req.title,
            post_datetime=datetime.now(),
            content=req.content,
            image=f"{id_str}.png",
        )

        session.execute(stmt)
        session.commit()
        return {"msg": "Inserted Post.", "err": False}
