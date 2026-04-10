from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class WatchHistoryResponse(BaseModel):
    id: int
    tmdb_id: int
    source_id: Optional[int]
    progress: float
    duration: Optional[float]
    last_watched: datetime
    video: Optional[dict] = None

    class Config:
        from_attributes = True

class WatchHistoryUpdate(BaseModel):
    progress: float
    duration: Optional[float] = None
    source_id: Optional[int] = None
