from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

import services.comments as service
from common.dto import CommentRequest, CommentResponse
from common.helper import get_current_user
from common.models import User

router = APIRouter(prefix="/comments", tags=["comments", "posts"])


@router.get("/post_id", response_model=List[CommentResponse])
def get_all_comments_by_post_id(post_id: int):
    res = service.get_all_comments_by_post_id(post_id)
    return res


@router.get("/user_id", response_model=List[CommentResponse])
def get_all_comments_by_user_id(user_id: int):
    res = service.get_all_comments_by_user_id(user_id)
    return res


@router.delete("")
def delete_comment_on_post(
    comment_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.delete_comment_on_post(current_user, comment_id)
    if res:
        return {"msg": "Deleted comment."}
    else:
        raise HTTPException(status_code=res["status_code"], detail=res["message"])


@router.post("")
def create_comment_on_post(
    commentModel: CommentRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.create_comment_on_post(current_user.id, commentModel)
    if res:
        return {"msg": "Inserted comment."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Couldn't insert comment!"
        )
