from pydantic import BaseModel, HttpUrl
from typing import Optional


class Cinema(BaseModel):
    id: str
    name: str
    homepage_url: Optional[HttpUrl]
    region: str


class CinemaSummary(BaseModel):
    name: str
    homepage_url: Optional[
        str
    ]  # skip validation because it's derived from Cinema.homepage_url
