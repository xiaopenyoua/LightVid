from sqlalchemy import Column, Integer, String
from database import Base


class TmdbGenre(Base):
    __tablename__ = "tmdb_genres"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, index=True)
    name = Column(String)
    media_type = Column(String)  # "movie" or "tv"
