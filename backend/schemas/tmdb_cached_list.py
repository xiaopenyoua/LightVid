from pydantic import BaseModel
from typing import Optional

from .tmdb_genre import TmdbGenreResponse


class TmdbCachedItemResponse(BaseModel):
    tmdb_id: int
    title: str
    media_type: str
    poster_url: Optional[str]
    backdrop_url: Optional[str]
    vote_average: Optional[float]
    vote_count: Optional[int]
    popularity: Optional[float]
    overview: Optional[str]
    release_date: Optional[str]
    genre_ids: Optional[str]
    season_number: Optional[int]

    class Config:
        from_attributes = True


class TmdbCachedListResponse(BaseModel):
    genres: list[TmdbGenreResponse]
    lists: dict[str, list[TmdbCachedItemResponse]]
