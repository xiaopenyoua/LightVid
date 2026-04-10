from sqlalchemy import Column, Integer, String, Float, DateTime
from datetime import datetime
from database import Base

class VideoSource(Base):
    __tablename__ = "video_sources"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    url = Column(String, nullable=False, unique=True)
    type = Column(String, default="m3u8")  # m3u8 / direct / parse
    platform = Column(String, default="tvbox")  # tvbox / tencent / mango / youku / iqiyi
    source_type = Column(String, default="crawl")  # crawl / user
    speed = Column(Float, nullable=True)  # 秒，NULL 表示未测速
    status = Column(String, default="active")  # active / inactive / expired
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
