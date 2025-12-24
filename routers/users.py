import re
from posixpath import curdir
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)
from fastapi.datastructures import UploadFile
from starlette.types import HTTPExceptionHandler

import services.users as service
from common.dto import ImgReturnType, User, UserChangeRequest
from common.helper import get_current_user

router = APIRouter(prefix="/users", tags=["users"])


@router.post("")
async def post_user(user: UserChangeRequest):
    res = service.insert_user(user)
    if res:
        return {"msg": "Successfully created user."}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Couldn't create user."
        )


@router.get("/name", response_model=User)
def get_user_by_name(username: str):
    res = service.get_user_by_name(username)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No user found with that name.",
        )
    return res


@router.get("/", response_model=User)
def get_user_by_id(id: int):
    res = service.get_user_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.get("/usersearch", response_model=List[User])
def get_users_by_namesearch(username: str, page: int = 1, count: int = 14):
    res = service.get_user_by_usersearch(username, page, count)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No users found."
        )
    return res


@router.get("/profile_picture")
def get_profile_picture(id: int):
    res = service.get_user_profile_picture(id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile Picture doesn't exist.",
        )
    return res


@router.put("/profile_picture")
async def put_profile_picture(
    file: UploadFile,
    user_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.id != user_id or not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden.",
        )
    res = await service.update_profile_picture(user_id, file)
    return res


@router.delete("/profile_picture")
async def delete_profile_picture(
    user_id: int, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden.",
        )
    res = service.delete_profile_picture(user_id)
    if res:
        return {"msg": "Deleted successfully."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile Picture doesn't exist.",
        )


@router.get("/count")
def get_user_count():
    return service.get_user_count()


@router.get("/me", response_model=User)
def get_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@router.delete("")
def delete_user(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin or (
        current_user.id != id and not current_user.is_admin
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden.",
        )
    res = service.delete_user(id)
    if res:
        return {"msg": "Deleted user."}
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found."
        )


@router.put("/me")
def change_user(
    new_user: UserChangeRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    username_pattern = r"^[A-Za-z0-9_]{1,32}$"
    if len(new_user.new_username.strip()) > 0 and not bool(
        re.match(username_pattern, new_user.new_username)
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username too long or contain invalid characters (max length of 32, character in A-Z, a-z, 0-9 and _)!",
        )

    if len(new_user.new_password) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password too long (max 128 characters)!",
        )

    if len(new_user.new_description) > 256:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Description too long (max 256 characters)!",
        )

    res = service.update_user(current_user.username, req=new_user)
    if res:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    else:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot find user with specified ID!",
        )
