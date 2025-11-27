from datetime import timezone
from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    status,
)

import services.nikos as service
from common.dto import NikoRequest, NikoResponse, SortType, User
from common.helper import auth_err, get_current_user

router = APIRouter(prefix="/nikos", tags=["nikos"])


@router.get("", response_model=List[NikoResponse])
def get_all_nikos(sort_by: SortType = SortType.oldest_added):
    return service.get_all(sort_by)


@router.get("/random", response_model=NikoResponse)
def get_random_nikos():
    return service.get_random_niko()


@router.get("/notd", response_model=NikoResponse)
def get_notd(response: Response):
    notd = service.get_notd()
    if notd is None:
        raise HTTPException(status_code=status.HTTP_418_IM_A_TEAPOT)
    data, refresh = notd
    response.headers["X-RefreshAt"] = refresh.astimezone(timezone.utc).isoformat()
    return data


@router.get("/name", response_model=List[NikoResponse])
def get_niko_by_name(name="Niko"):
    return service.get_by_name(name)


@router.get("/page", response_model=List[NikoResponse])
def get_nikos_page(page=1, count=14, sort_by: SortType = SortType.oldest_added):
    res = service.get_nikos_page(page, count, sort_by)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@router.get("/", response_model=NikoResponse)
def get_niko_by_id(id=1):
    res = service.get_niko_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@router.get("/user", response_model=List[NikoResponse])
def get_niko_by_userid(id: int):
    res = service.get_niko_by_userid(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@router.get("/user/latestid")
def get_latest_niko_of_user(user_id: int):
    res = service.get_niko_by_userid(user_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")
    return res[-1].id


@router.post("")
async def post_niko(
    niko: NikoRequest, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err

    res = service.insert_niko(niko)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.put("")
def update_niko(
    id: int,
    niko: NikoRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.update_niko(id, niko, current_user.id)
    print(res)
    if res["err"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res["msg"])
    return res


@router.delete("")
def delete_niko(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise auth_err

    res = service.delete_niko(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.get("/count")
def get_niko_count():
    return service.get_nikos_count()
