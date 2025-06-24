from pydantic import BaseModel, HttpUrl
from typing import Optional


class Cinema(BaseModel):
    id: str
    name: str
    homepage_url: Optional[HttpUrl]
    region: str
    region_code: str


def to_camel(string: str) -> str:
    parts = string.split('_')
    return parts[0] + ''.join(word.capitalize() for word in parts[1:])


class CinemaSummary(BaseModel):
    name: str
    homepage_url: Optional[
        str
    ]  # skip validation because it's derived from Cinema.homepage_url

    class Config:
        alias_generator = to_camel
        populate_by_name = True
