from datetime import datetime, timedelta, timezone
from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, Response
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
    {
        "name": "nikos"
    },
    {
        "name": "abilities"
    },
    {
        "name": "blogs"
    },
    {
        "name": "auth"
    },
]

SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = os.environ['ALGORITHM']
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    description: str
    
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
    to_encode.update({"exp":expire})
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
        username = payload.get('sub')
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except jwt.InvalidTokenError:
        raise credentials_exception
    user = service.get_user_by_username(username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    service.close_connection()

origins = os.environ["FASTAPI_ALLOWED_ORIGIN"].split(",")

app = FastAPI(
    title="NikodexV2 API",
    lifespan=lifespan
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/nikos", response_model=List[dto.NikoResponse], tags=['nikos'])
def get_all_nikos():
    return service.get_all()

@app.get("/nikos/name", response_model=List[dto.NikoResponse], tags=['nikos'])
def get_niko_by_name(name = "Niko"):
    return service.get_by_name(name)

@app.get("/nikos/page", response_model=List[dto.NikoResponse], tags=['nikos'])
def get_nikos_page(page = 1):
    res = service.get_nikos_page(page)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res

@app.get("/nikos/", response_model=dto.NikoResponse, tags=['nikos'])
def get_niko_by_id(id = 1):
    res = service.get_niko_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found")
    return res

@app.post("/nikos", tags=['nikos'])
async def post_niko(niko: dto.NikoRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.insert_niko(niko)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.put("/nikos", tags=['nikos'])
def update_niko(id: int, niko: dto.NikoRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.update_niko(id, niko)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.delete("/nikos", tags=['nikos'])
def delete_niko(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_niko(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.get("/nikos/count", tags=['nikos'])
def get_niko_count():
    return service.get_nikos_count()

@app.get("/abilities", response_model=List[dto.AbilityResponse], tags=['abilities'])
def get_abilities():
    return service.get_abilities()

@app.get("/abilities/", response_model=dto.AbilityResponse, tags=['abilities'])
def get_ability_by_id(id = 1):
    res = service.get_ability_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.post("/abilities", tags=['abilities'])
def post_ability(ability: dto.AbilityRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.insert_ability(ability)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.put("/abilities", tags=['abilities'])
def update_ability(id: int, ability: dto.AbilityRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.update_ability(id, ability)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.delete("/abilities", tags=['abilities'])
def delete_ability(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_ability(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.get("/blogs", response_model=List[dto.BlogResponse], tags=['blogs'])
def get_all_blogs():
    return service.get_blogs()

@app.get("/blogs/", response_model=dto.BlogResponse, tags=['blogs'])
def get_blog_by_id(id: int):
    res = service.get_blog_by_id(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.post("/blogs", tags=['blogs'])
def post_blog(blog: dto.BlogRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.post_blog(blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.put("/blogs", tags=['blogs'])
def update_blog(id: int, blog: dto.BlogRequest, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.update_blog(id, blog)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.delete("/blogs", tags=['blogs'])
def delete_blog(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_blog(id)
    if res is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not Found.")
    return res

@app.post("/token", tags=['auth'])
async def login_token(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub":user.username}, expires_delta=access_token_expires)
    return Token(access_token=access_token, token_type="bearer")

@app.get("/users/me", response_model=User, tags=['auth'])
def get_user_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

app.mount("/images", StaticFiles(directory="images"), name="images")
@app.post("/image")
async def upload_image(id: int, file: UploadFile, current_user: Annotated[User, Depends(get_current_user)]):
    res = await service.upload_image(id=id, file=file)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not a valid image file, or filesize too big!"
        )
    return Response(
        status_code=status.HTTP_200_OK
    )
@app.delete("/image")
def delete_image(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    res = service.delete_image(id=id)
    if not res:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot find image file!"
        )
    return Response(
        status_code=status.HTTP_204_NO_CONTENT
    )
@app.get("/image")
def get_image(id: int):
    res = service.get_image(id)
    if not res:
        return Response(
            status_code=status.HTTP_404_NOT_FOUND
        )
    return res