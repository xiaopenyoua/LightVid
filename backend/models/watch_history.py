from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey
from datetime import datetime
from database import Base

class WatchHistory(Base):
    __tablename__ = "watch_history"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, index=True)
    source_id = Column(Integer, ForeignKey("video_sources.id"), nullable=True)
    progress = Column(Float, default=0)  # 秒
    duration = Column(Float, nullable=True)  # 视频总时长
    last_watched = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
