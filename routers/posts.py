from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)

import services.posts as service
from common.dto import PostRequestForm, PostResponse, User
from common.helper import get_current_user

router = APIRouter(prefix="/posts", tags=["posts"])


@router.get("", response_model=List[PostResponse])
def get_posts():
    res = service.get_posts()
    return res


@router.get("/count")
def get_posts_count():
    res = service.get_posts_count()
    return res


@router.get("/page", response_model=List[PostResponse])
def get_posts_page(page: int, count: int):
    res = service.get_posts_page(page, count)
    return res


@router.get("/", response_model=PostResponse)
def get_post_by_id(id: int):
    res = service.get_post_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    return res


@router.get("/user", response_model=List[PostResponse])
def get_posts_by_userid(user_id: int):
    res = service.get_post_userid(user_id)
    return res


@router.get("/image")
def get_post_image(id: int):
    res = service.get_post_image(id)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Image file not found!"
        )
    return res


@router.post("")
async def post_post(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    req: PostRequestForm = Depends(),
):
    res = await service.insert_post(current_user.id, req, file)
    print(res)
    if res["err"]:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=res["msg"],
        )
    return res


@router.delete("")
def delete_post(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.get_post_id(id)
    if not res:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
    elif res.user.id != current_user.id and not current_user.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Forbidden.")
    response_deletion = service.delete_post(res.id)
    if response_deletion:
        return response_deletion
    else:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found.")
