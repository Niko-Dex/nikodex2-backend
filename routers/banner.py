from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from starlette.status import HTTP_404_NOT_FOUND

import services.banner as service
from common.dto import BannerRequest, BannerResponse, User
from common.helper import auth_err, get_current_user

router = APIRouter(prefix="/banner", tags=["banner"])


@router.get("", response_model=BannerResponse)
def get_banner():
    res = service.get_banner()
    if res is None:
        raise HTTPException(status_code=HTTP_404_NOT_FOUND, detail="Banner not found!")
    return res


@router.post("")
def post_banner(
    banner: BannerRequest, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err
    return service.set_banner(banner)
