from typing import List, Optional
from pydantic import BaseModel, HttpUrl

from models.cinema import CinemaSummary, to_camel


class Movie(BaseModel):
    id: str
    title: str
    release_year: int
    image_url: Optional[HttpUrl]
    region: str
    region_code: str
    cinemas: List[CinemaSummary]
    showtimes: List[str]
    last_showtime: str

    class Config:
        alias_generator = to_camel
        populate_by_name = True
