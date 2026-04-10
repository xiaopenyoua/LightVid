from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class DoubanVideoResponse(BaseModel):
    id: int
    tmdb_id: int
    title: str
    poster_url: Optional[str]
    rating: Optional[float]
    summary: Optional[str]
    year: Optional[int]
    category: str
    genres: Optional[str]
    backdrop_url: Optional[str]
    original_title: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True
