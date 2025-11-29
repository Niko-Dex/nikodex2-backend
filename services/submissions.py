import io
import os
import uuid
from datetime import datetime

from fastapi import UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import (
    desc,
    select,
)
from sqlalchemy.dialects.mysql import insert

from common.dto import (
    SubmitForm,
)
from common.models import Submission
from services._shared import SessionManager
from services.images import IMAGE_DIR, MAX_IMG_SIZE


def get_submissions():
    with SessionManager() as session:
        stmt = select(Submission).order_by(desc(Submission.submit_date))
        return session.scalars(stmt).fetchall()


def get_submission_by_id(id: int):
    with SessionManager() as session:
        stmt = select(Submission).where(Submission.id == id).limit(1)
        return session.scalars(stmt).one()


def get_submissions_by_userid(user_id: int):
    with SessionManager() as session:
        stmt = select(Submission).where(Submission.user_id == user_id)
        return session.scalars(stmt).fetchall()


def get_submission_image(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Submission).where(Submission.id == id)
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


async def insert_submission(req: SubmitForm, user_id: int, file: UploadFile):
    with SessionManager() as session:
        if not file.content_type or not file.content_type.startswith("image/"):
            return False
        if not file.size or file.size > MAX_IMG_SIZE:
            return False
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return False

        id_str = str(uuid.uuid4())
        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"{id_str}.png")

        image.save(path, format="PNG")

        stmt = insert(Submission).values(
            user_id=user_id,
            name=req.name,
            description=req.description,
            full_desc=req.full_desc,
            image=f"{id_str}.png",
            submit_date=datetime.now(),
            is_blacklisted=req.is_blacklisted,
        )
        session.execute(stmt)
        session.commit()
        return True


def delete_submission(id: int):
    with SessionManager() as session:
        entity = session.execute(
            select(Submission).where(Submission.id == id)
        ).scalar_one()

        if len(entity.image) > 0:
            path = os.path.join(IMAGE_DIR, entity.image)
            if os.path.exists(path):
                os.remove(path)

        session.delete(entity)
        session.commit()
