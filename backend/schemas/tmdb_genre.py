from pydantic import BaseModel


class TmdbGenreResponse(BaseModel):
    id: int
    tmdb_id: int
    name: str
    media_type: str

    class Config:
        from_attributes = True
