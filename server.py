from datetime import datetime, timedelta, timezone
from enum import Enum
import re
from typing import Annotated, List
from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    Header,
    status,
    UploadFile,
    Response,
    Form
)
from dataclasses import dataclass
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import jwt
from passlib.context import CryptContext
from contextlib import asynccontextmanager
import service
import dto
import os

tags_metadata = [
    {"name": "nikos"},
    {"name": "abilities"},
    {"name": "blogs"},
    {"name": "auth"},
]

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
API_BOT_SHARED_SECRET = os.environ["API_BOT_SHARED_SECRET"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

auth_err = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized.",
    headers={"WWW-Authenticate": "Bearer"},
)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


class User(BaseModel):
    id: int
    username: str
    description: str
    is_admin: bool


class UserInDb(User):
    password: str


def verify_password(plain_pass, hashed_pass):
    return pwd_context.verify(plain_pass, hashed_pass)


def get_password_hash(plain_pass):
    return pwd_context.hash(plain_pass)


def authenticate_user(username: str, password: str):
    user = service.get_user_by_username(username)
    if not user:
        return False
    if not verify_password(password, user.hashed_pass):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = service.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_shared_token(authorization: str = Header(...)):
    if API_BOT_SHARED_SECRET == "" or API_BOT_SHARED_SECRET != authorization:
        raise HTTPException(status_code=401, detail="Invalid authorization")
    return None


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    service.close_connection()


origins = os.environ["FASTAPI_ALLOWED_ORIGIN"].split(",")

app = FastAPI(title="NikodexV2 API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/nikos", response_model=List[dto.NikoResponse], tags=["nikos"])
def get_all_nikos(sort_by: dto.SortType = dto.SortType.oldest_added):
    return service.get_all(sort_by)


@app.get("/nikos/random", response_model=dto.NikoResponse, tags=["nikos"])
def get_random_nikos():
    return service.get_random_niko()


@app.get("/nikos/name", response_model=List[dto.NikoResponse], tags=["nikos"])
def get_niko_by_name(name="Niko"):
    return service.get_by_name(name)


@app.get("/nikos/page", response_model=List[dto.NikoResponse], tags=["nikos"])
def get_nikos_page(page=1, count=14, sort_by: dto.SortType = dto.SortType.oldest_added):
    res = service.get_nikos_page(page, count, sort_by)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@app.get("/nikos/", response_model=dto.NikoResponse, tags=["nikos"])
def get_niko_by_id(id=1):
    res = service.get_niko_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@app.get("/nikos/user", response_model=List[dto.NikoResponse], tags=["nikos"])
def get_niko_by_userid(id: int):
    res = service.get_niko_by_userid(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res


@app.post("/nikos", tags=["nikos"])
async def post_niko(
    niko: dto.NikoRequest, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err

    res = service.insert_niko(niko)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.put("/nikos", tags=["nikos"])
def update_niko(
    id: int,
    niko: dto.NikoRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    res = service.update_niko(id, niko, current_user.id)
    print(res)
    if res["err"]:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=res.msg)
    return res


@app.delete("/nikos", tags=["nikos"])
def delete_niko(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise auth_err

    res = service.delete_niko(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.get("/nikos/count", tags=["nikos"])
def get_niko_count():
    return service.get_nikos_count()


@app.get("/abilities", response_model=List[dto.AbilityResponse], tags=["abilities"])
def get_abilities():
    return service.get_abilities()


@app.get("/abilities/", response_model=dto.AbilityResponse, tags=["abilities"])
def get_ability_by_id(id=1):
    res = service.get_ability_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.post("/abilities", tags=["abilities"])
def post_ability(
    ability: dto.AbilityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_admin:
        raise auth_err

    res = service.insert_ability(ability)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.put("/abilities", tags=["abilities"])
def update_ability(
    id: int,
    ability: dto.AbilityRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_admin:
        raise auth_err

    res = service.update_ability(id, ability)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.delete("/abilities", tags=["abilities"])
def delete_ability(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise auth_err

    res = service.delete_ability(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.get("/blogs", response_model=List[dto.BlogResponse], tags=["blogs"])
def get_all_blogs():
    return service.get_blogs()


@app.get("/blogs/", response_model=dto.BlogResponse, tags=["blogs"])
def get_blog_by_id(id: int):
    res = service.get_blog_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.post("/blogs", tags=["blogs"])
def post_blog(
    blog: dto.BlogRequest, current_user: Annotated[User, Depends(get_current_user)]
):
    if not current_user.is_admin:
        raise auth_err

    res = service.post_blog(blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.put("/blogs", tags=["blogs"])
def update_blog(
    id: int,
    blog: dto.BlogRequest,
    current_user: Annotated[User, Depends(get_current_user)],
):
    if not current_user.is_admin:
        raise auth_err

    res = service.update_blog(id, blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.delete("/blogs", tags=["blogs"])
def delete_blog(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    if not current_user.is_admin:
        raise auth_err

    res = service.delete_blog(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.get(
    "/submissions", response_model=List[dto.SubmissionResponse], tags=["submissions"]
)
def get_submissions():
    res = service.get_submissions()
    return res


@app.get("/submissions/", response_model=dto.SubmissionResponse, tags=["submissions"])
def get_submission_by_id(id: int):
    res = service.get_submission_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.get(
    "/submissions/user",
    response_model=List[dto.SubmissionResponse],
    tags=["submissions"],
)
def get_submission_by_userid(user_id: int):
    res = service.get_submission_by_userid(user_id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.get("/submissions/image", tags=["submissions"])
def get_submission_image(id: int):
    res = service.get_submission_image(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res


@app.post("/submissions", tags=["submissions"])
async def post_submission(
    file: UploadFile,
    current_user: Annotated[User, Depends(get_current_user)],
    submission: dto.SubmitForm = Depends()
):
    res = await service.insert_submission(submission, current_user.id, file)
    if (res):
        return {"msg": "Inserted submission"}
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid image file, or filesize too big!",
        )

@app.delete("/submissions", tags=["submissions"])
async def delete_submission(
    id: int, current_user: Annotated[User, Depends(get_current_user)]
):
    if (not current_user.is_admin):
        raise auth_err
    service.delete_submission(id)
    return {"msg": "Deleted submission"}


@app.post("/users", tags=["auth"])
async def post_user(user: dto.UserChangeRequest):
    res = service.insert_user(user)
    if res:
        return {"msg": "Successfully created user."}
    else:
        return {"msg": "Creation failed."}


@app.post("/token", tags=["auth"])
async def login_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/name", response_model=User, tags=["auth"])
def get_user_by_name(username: str):
    res = service.get_user_by_name(username)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No user found with that name.")
    return res

@app.get("/users/", response_model=User, tags=["auth"])
def get_user_by_id(id: int):
    res = service.get_user_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.get("/users/usersearch", response_model=List[User], tags=["auth"])
def get_users_by_namesearch(username: str, page: int = 1, count: int = 14):
    res = service.get_user_by_usersearch(username, page, count)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No users found.")
    return res

@app.get("/users/count", tags=["auth"])
def get_user_count():
    return service.get_user_count()


@app.get("/users/me", response_model=User, tags=["auth"])
def get_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user


@app.put("/users/me", tags=["auth"])
def change_user(
    new_user: dto.UserChangeRequest,
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


@app.post("/image", tags=["images"])
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


@app.delete("/image", tags=["images"])
def delete_image(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_image(id=id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Cannot find image file to delete!",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/image", tags=["images"])
def get_image(id: int):
    res = service.get_image(id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find image file!"
        )
    return res


@app.get("/ping")
def ping():
    return Response(status_code=status.HTTP_200_OK)


@app.get(
    "/discord_bot/submit_user", response_model=dto.SubmitUserResponse, tags=["bot"]
)
def log_user(user_id: str, authorization: Annotated[None, Depends(get_shared_token)]):
    res = service.get_submit_user(user_id)
    if res is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cannot find submit user!"
        )
    return res


@app.post("/discord_bot/submit_user", tags=["bot"])
def log_user(
    user_id: str,
    submit_user: dto.SubmitUserRequest,
    authorization: Annotated[None, Depends(get_shared_token)],
):
    res = service.post_submit_user(user_id, submit_user)
    return res
