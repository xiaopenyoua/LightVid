from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from database import Base


class TmdbCachedList(Base):
    __tablename__ = "tmdb_cached_lists"

    id = Column(Integer, primary_key=True, index=True)
    list_type = Column(String, index=True)
    media_type = Column(String, index=True)
    tmdb_id = Column(Integer)
    title = Column(String)
    poster_url = Column(String)
    backdrop_url = Column(String)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    overview = Column(Text)
    release_date = Column(String)
    genre_ids = Column(String)
    season_number = Column(Integer, nullable=True)
    cached_at = Column(DateTime)
