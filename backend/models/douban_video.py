from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from database import Base

class DoubanVideo(Base):
    __tablename__ = "douban_videos"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, unique=True, index=True)
    title = Column(String)
    poster_url = Column(String)
    rating = Column(Float, nullable=True)
    summary = Column(Text, nullable=True)
    year = Column(Integer, nullable=True)
    category = Column(String, default="movie")  # movie / tv
    genres = Column(String, nullable=True)  # 逗号分隔
    backdrop_url = Column(String, nullable=True)  # 背景图
    original_title = Column(String, nullable=True)  # 原标题
    created_at = Column(DateTime, default=datetime.utcnow)
