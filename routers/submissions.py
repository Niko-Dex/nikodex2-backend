from typing import Annotated, List

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    UploadFile,
    status,
)

import services.submissions as service
from common.dto import SubmissionResponse, SubmitForm, User
from common.helper import auth_err, get_current_user

router = APIRouter(prefix="/submissions", tags=["submissions"])


@router.get("", response_model=List[SubmissionResponse])
def get_submissions():
    res = service.get_submissions()
    return res


@router.get("/", response_model=SubmissionResponse)
def get_submission_by_id(id: int):
    res = service.get_submission_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.get(
    "/user",
    response_model=List[SubmissionResponse],
    tags=["submissions"],
)
def get_submission_by_userid(user_id: int):
    res = service.get_submissions_by_userid(user_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.get("/image")
def get_submission_image(id: int):
    res = service.get_submission_image(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@router.post("")
async def post_submission(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    submission: SubmitForm = Depends(),
):
    res = await service.insert_submission(submission, current_user.id, file)
    if res:
        return {"msg": "Inserted submission"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid image file, or filesize too big!",
        )


@router.delete("")
async def delete_submission(
    id: int, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err
    service.delete_submission(id)
    return {"msg": "Deleted submission"}
