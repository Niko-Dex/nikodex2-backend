from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

import services.blogs as service
from common.dto import BlogRequest, BlogResponse, User
from common.helper import auth_err, get_current_user

router = APIRouter(prefix="/blogs", tags=["blogs"])


@router.get("", response_model=List[BlogResponse])
def get_all_blogs():
    return service.get_blogs()


@router.get("/", response_model=BlogResponse)
def get_blog_by_id(id: int):
    res = service.get_blog_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.post("")
def post_blog(
    blog: BlogRequest, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err

    res = service.post_blog(blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.put("")
def update_blog(
    id: int,
    blog: BlogRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_admin:
        raise auth_err

    res = service.update_blog(id, blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.delete("")
def delete_blog(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise auth_err

    res = service.delete_blog(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res
