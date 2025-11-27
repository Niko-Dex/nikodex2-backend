import io
import os

from fastapi import UploadFile
from fastapi.responses import FileResponse
from PIL import Image
from sqlalchemy import (
    select,
)

from common.models import Niko
from services._shared import SessionManager

IMAGE_DIR = os.environ["IMG_DIR"]
MAX_IMG_SIZE = 2 * 1024 * 1024  # 2MB
os.makedirs(IMAGE_DIR, exist_ok=True)


async def upload_image(id: int, file: UploadFile):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        if not file.content_type or not file.content_type.startswith("image/"):
            return None
        if not file.size or file.size > MAX_IMG_SIZE:
            return None
        data = await file.read()
        try:
            image = Image.open(io.BytesIO(data))
        except Exception:
            return None

        image = image.convert("RGBA")
        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")

        image.save(path, format="PNG")

        await file.close()
        session.commit()

        return True


def delete_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        try:
            os.remove(os.path.join(IMAGE_DIR, f"niko-{id}.png"))
        except Exception:
            return None

        session.commit()
        return True


def get_image(id: int):
    with SessionManager() as session:
        entity = session.execute(select(Niko).where(Niko.id == id)).scalar_one_or_none()
        if entity is None:
            return None

        path = os.path.join(IMAGE_DIR, f"niko-{id}.png")
        if not os.path.exists(path):
            path = os.path.join("images/default.png")
        return FileResponse(path, media_type="image/png")
