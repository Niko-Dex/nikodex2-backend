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
    try:
        await service.upload_image(id=id, file=file)
    except service.ImageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return Response(status_code=status.HTTP_200_OK)


@router.put("")
async def put_image(
    id: int, file: UploadFile, current_user: Annotated[User, Depends(get_current_user)]
):
    try:
        await service.edit_image(id=id, file=file)
    except service.ImageError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    return Response(status_code=status.HTTP_200_OK)


@router.delete("")
def delete_image(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    try:
        service.delete_image(id=id)
    except service.ImageError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("")
def get_image(id: int):
    try:
        res = service.get_image(id)
    except service.ImageError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    return res
