from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class VideoPlatformLink(Base):
    """视频平台链接缓存表"""
    __tablename__ = "video_platform_links"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, nullable=False, index=True)
    media_type = Column(String, nullable=False)  # movie / tv
    platform = Column(String, nullable=False, index=True)  # tencent / iqiyi / youku / bilibili / mgtv
    platform_url = Column(String, nullable=False)
    title = Column(String)  # 平台返回的标题，用于匹配
    season = Column(Integer, nullable=True)  # 剧集第几季
    episode = Column(Integer, nullable=True)  # 剧集第几集
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 缓存过期时间