from pydantic import BaseModel

class NikoRequest(BaseModel):
    name: str
    description: str
    image: str
    author: str
    full_desc: str