from pydantic import BaseModel, HttpUrl
from typing import Optional


class Cinema(BaseModel):
    id: str
    name: str
    homepage_url: Optional[HttpUrl]
    region: str

class CinemaSummary(BaseModel):
    cinema_id: str
    name: str
    homepage_url: Optional[HttpUrl]
    