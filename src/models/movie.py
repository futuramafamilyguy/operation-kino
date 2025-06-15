from typing import List, Optional
from pydantic import BaseModel, HttpUrl

from models.cinema import CinemaSummary


class Movie(BaseModel):
    id: str
    title: str
    release_year: int
    image_url: Optional[HttpUrl]
    region: str
    region_code: str
    cinemas: List[CinemaSummary]
    showtimes: List[str]
