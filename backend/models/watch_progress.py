from database import Base
from sqlalchemy import Column, Integer, Float, DateTime, UniqueConstraint
from datetime import datetime


class WatchProgress(Base):
    __tablename__ = "watch_progress"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, index=True)
    season = Column(Integer, nullable=True)       # null 表示电影
    episode = Column(Integer, nullable=True)      # null 表示电影
    current_time = Column(Float, default=0)       # 当前播放位置（秒）
    duration = Column(Float, nullable=True)       # 视频总时长（秒）
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        UniqueConstraint('tmdb_id', 'season', 'episode', name='uix_tmdb_season_episode'),
    )