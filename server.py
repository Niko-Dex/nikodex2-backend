from datetime import datetime, timedelta, timezone
from typing import Annotated, List
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
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
        "name": "auth"
    }
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

@app.get("/nikos/", response_model=dto.NikoResponse, tags=['nikos'])
def get_niko_by_id(id = 1):
    return service.get_niko_by_id(id)

@app.post("/nikos", tags=['nikos'])
async def post_niko(niko: dto.NikoRequest, current_user: Annotated[User, Depends(get_current_user)]):
    service.insert_niko(niko)
    return {"msg":"Inserted Niko."}

@app.put("/nikos", tags=['nikos'])
def update_niko(id: int, niko: dto.NikoRequest, current_user: Annotated[User, Depends(get_current_user)]):
    service.update_niko(id, niko)
    return {"msg":"Updated Niko."}

@app.delete("/nikos", tags=['nikos'])
def delete_niko(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    service.delete_niko(id)
    return {"msg":"Deleted Niko."}

@app.get("/nikos/count", tags=['nikos'])
def get_niko_count():
    return service.get_nikos_count()

@app.get("/abilities", response_model=List[dto.AbilityResponse], tags=['abilities'])
def get_abilities():
    return service.get_abilities()

@app.get("/abilities/", response_model=dto.AbilityResponse, tags=['abilities'])
def get_ability_by_id(id = 1):
    return service.get_ability_by_id(id)

@app.post("/abilities", tags=['abilities'])
def post_ability(ability: dto.AbilityRequest, current_user: Annotated[User, Depends(get_current_user)]):
    service.insert_ability(ability)
    return {"msg":"Inserted Ability."}

@app.put("/abilities", tags=['abilities'])
def update_ability(id: int, ability: dto.AbilityRequest, current_user: Annotated[User, Depends(get_current_user)]):
    service.update_ability(id, ability)
    return {"msg":"Updated Ability."}

@app.delete("/abilities", tags=['abilities'])
def delete_ability(id: int, current_user: Annotated[User, Depends(get_current_user)]):
    service.delete_ability(id)
    return {"msg":"Deleted Ability."}

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
    