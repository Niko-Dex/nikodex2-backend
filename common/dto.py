from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List

from fastapi import Form
from pydantic import BaseModel


class UserResponse(BaseModel):
    id: int
    username: str


class AbilityRequest(BaseModel):
    name: str
    niko_id: int


class AbilityResponse(AbilityRequest):
    id: int


class NikoRequest(BaseModel):
    name: str
    description: str
    full_desc: str
    is_blacklisted: bool
    author_id: int | None


class NikoResponse(NikoRequest):
    id: int
    abilities: List[AbilityResponse]
    user: UserResponse | None
    author_name: str


class BlogRequest(BaseModel):
    title: str
    author: str
    content: str


class BlogResponse(BlogRequest):
    id: int
    post_datetime: datetime


class UserChangeRequest(BaseModel):
    new_username: str
    new_password: str
    new_description: str


class SubmissionRequest(BaseModel):
    name: str
    description: str
    full_desc: str
    is_blacklisted: bool


class CommentRequest(BaseModel):
    content: str
    post_id: int


class CommentResponse(CommentRequest):
    id: int
    user: UserResponse
    author_id: int
    post_date: datetime
    content: str


class SubmissionResponse(SubmissionRequest):
    id: int
    image: str
    user_id: int


@dataclass
class SubmitForm:
    name: str = Form()
    description: str = Form()
    full_desc: str = Form()
    is_blacklisted: bool = Form()


class SortType(Enum):
    recently_added = "recently_added"
    oldest_added = "oldest_added"
    name_ascending = "name_ascending"
    name_descending = "name_descending"


class SubmitUserRequest(BaseModel):
    last_submit_on: int
    is_banned: bool
    ban_reason: str


class SubmitUserResponse(BaseModel):
    id: int
    user_id: str
    last_submit_on: int
    is_banned: bool
    ban_reason: str


class PostRequest(BaseModel):
    title: str
    content: str


@dataclass
class PostRequestForm:
    title: str = Form()
    content: str = Form()


class PostResponse(BaseModel):
    id: int
    title: str
    content: str
    post_datetime: datetime
    user: UserResponse


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


class ImgReturnType(str, Enum):
    image = "image"
    niko_id = "niko_id"


class UserInDb(User):
    password: str


class BannerRequest(BaseModel):
    title: str
    content: str
    banner_color: str
    is_dismissable: bool


class BannerResponse(BannerRequest):
    id: int
    banner_identifier: str
    banner_color: str
