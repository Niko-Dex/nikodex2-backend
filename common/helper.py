import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import (
    Depends,
    Header,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordBearer
from passlib.context import CryptContext

import services.users as service
from common.dto import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")
SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = os.environ["ALGORITHM"]
API_BOT_SHARED_SECRET = os.environ["API_BOT_SHARED_SECRET"]
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
auth_err = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Unauthorized.",
    headers={"WWW-Authenticate": "Bearer"},
)


def verify_password(plain_pass, hashed_pass):
    return pwd_context.verify(plain_pass, hashed_pass)


def get_password_hash(plain_pass):
    return pwd_context.hash(plain_pass)


def authenticate_user(username: str, password: str):
    user = service.get_user_by_username(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_pass):
        return None
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
    user = service.get_user_by_username(username=token_data.username or "")
    if user is None:
        raise credentials_exception
    return user


async def get_shared_token(authorization: str = Header(...)):
    if API_BOT_SHARED_SECRET == "" or API_BOT_SHARED_SECRET != authorization:
        raise HTTPException(status_code=401, detail="Invalid authorization")
    return None
