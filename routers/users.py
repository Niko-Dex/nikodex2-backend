import re
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

import services.users as service
from common.dto import User, UserChangeRequest
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


@router.get("/count")
def get_user_count():
    return service.get_user_count()


@router.get("/me", response_model=User)
def get_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


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
