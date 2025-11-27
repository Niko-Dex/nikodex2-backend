from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
    UploadFile,
    status,
)

import services.images as service
from common.dto import User
from common.helper import get_current_user

router = APIRouter(prefix="/image", tags=["images"])


@router.post("")
async def upload_image(
    id: int, file: UploadFile, current_user: Annotated[User, Depends(get_current_user)]
):
    res = await service.upload_image(id=id, file=file)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid image file, or filesize too big!",
        )
    return Response(status_code=status.HTTP_200_OK)


@router.delete("")
def delete_image(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_image(id=id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot find image file to delete!",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("")
def get_image(id: int):
    res = service.get_image(id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find image file!"
        )
    return res
