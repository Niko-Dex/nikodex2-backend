from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel

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

class SortType(Enum):
    recently_added = "recently_added"
    oldest_added = "oldest_added"
    name_ascending = "name_ascending"
    name_descending = "name_descending"