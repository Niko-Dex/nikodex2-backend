from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel
from fastapi import Form


class AbilityRequest(BaseModel):
    name: str
    niko_id: int


class AbilityResponse(AbilityRequest):
    id: int


class NikoRequest(BaseModel):
    name: str
    description: str
    author: str
    full_desc: str
    author_id: int | None


class NikoResponse(NikoRequest):
    id: int
    abilities: List[AbilityResponse]


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


class SubmissionResponse(SubmissionRequest):
    id: int
    image: str
    user_id: int


@dataclass
class SubmitForm:
    name: str = Form()
    description: str = Form()
    full_desc: str = Form()


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
