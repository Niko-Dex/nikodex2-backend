from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

import services.abilities as service
from common.dto import AbilityRequest, AbilityResponse, User
from common.helper import get_current_user

router = APIRouter(prefix="/abilities", tags=["abilities"])


@router.get("", response_model=List[AbilityResponse])
def get_abilities():
    return service.get_abilities()


@router.get("/", response_model=AbilityResponse)
def get_ability_by_id(id=1):
    res = service.get_ability_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.post("")
def post_ability(
    ability: AbilityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.insert_ability(ability, current_user.id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    if res["err"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["msg"])
    return res


@router.put("")
def update_ability(
    id: int,
    ability: AbilityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.update_ability(id, ability, current_user.id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    if res["err"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["msg"])
    return res


@router.delete("")
def delete_ability(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_ability(id, current_user.id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    if type(res) is dict:
        if res["err"]:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail=res["msg"]
            )
    return res
