import uuid

from sqlalchemy import (
    select,
)

from common.dto import (
    BannerRequest,
)
from common.models import Banner
from services._shared import SessionManager


def get_banner():
    with SessionManager() as session:
        stmt = select(Banner)
        res = session.scalars(stmt).first()
        if res is None:
            return {
                "id": 1,
                "title": "",
                "content": "",
                "is_dismissable": True,
                "banner_identifier": "0",
            }
        return res


def set_banner(req: BannerRequest):
    with SessionManager() as session:
        session.merge(
            Banner(
                id=1,
                title=req.title,
                content=req.content,
                is_dismissable=req.is_dismissable,
                banner_identifier=str(uuid.uuid4()),
            )
        )
        session.commit()
        return {"msg": "Banner posted."}
