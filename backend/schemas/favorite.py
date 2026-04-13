from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class FavoriteResponse(BaseModel):
    id: int
    tmdb_id: int
    created_at: datetime

    class Config:
        from_attributes = True
