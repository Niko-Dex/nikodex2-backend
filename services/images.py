import io
import os

from fastapi import UploadFile
from fastapi.responses import FileResponse
from PIL import Image, ImageFile
from sqlalchemy import (
    select,
)

from common.models import Niko
from services._shared import SessionManager

IMAGE_DIR = os.environ["IMG_DIR"]
MAX_IMG_SIZE = 2 * 1024 * 1024  # 2MB
os.makedirs(IMAGE_DIR, exist_ok=True)


class ImageError(Exception):
    pass


def image_check(file: UploadFile):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise ImageError("Invalid image type")
    if not file.size or file.size > MAX_IMG_SIZE:
        raise ImageError("Image size exceeds limit")


async def upload_image(id: int, file: UploadFile):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        image_check(file)
        if entity is None:
            raise ImageError("Image not found")

        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            raise ImageError("Invalid image format")

        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")
        image.save(path, format="PNG")

        await file.close()
        session.commit()

        return True


async def edit_image(id: int, file: UploadFile):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            raise ImageError("Image not found")
        image_check(file)

        file_path = os.path.join(IMAGE_DIR, f"niko-{id}.png")

        try:
            os.remove(file_path)
        except FileNotFoundError:
            pass

        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            raise ImageError("Invalid image format")

        image = image.convert("RGBA")
        image.save(file_path, format="PNG")

        await file.close()
        session.commit()

        return True


def delete_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            raise ImageError("Image not found")

        try:
            os.remove(os.path.join(IMAGE_DIR, f"niko-{id}.png"))
        except FileNotFoundError:
            pass

        session.commit()
        return True


def get_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            raise ImageError("Image not found")

        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")
