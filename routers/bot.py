from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

import services.users as service
from common.dto import SubmitUserRequest, SubmitUserResponse
from common.helper import get_shared_token

router = APIRouter(prefix="/discord_bot", tags=["bot"])


@router.get("/submit_user", response_model=SubmitUserResponse)
def get_log_user(
    user_id: str, authorization: Annotated[None, Depends(get_shared_token)]
):
    res = service.get_submit_user(user_id)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find submit user!"
        )
    return res


@router.post("/submit_user")
def log_user(
    user_id: str,
    submit_user: SubmitUserRequest,
    authorization: Annotated[None, Depends(get_shared_token)],
):
    res = service.post_submit_user(user_id, submit_user)
    return res
