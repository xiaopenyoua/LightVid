from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from datetime import datetime
from database import Base

class ParseConfig(Base):
    __tablename__ = "parse_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    base_url = Column(String)
    priority = Column(Integer, default=0)
    status = Column(String, default="active")  # active / inactive
    # 两轮测速延迟（秒），None 表示未测试或失败
    latency1 = Column(Float, nullable=True)  # 第一轮 httpx 延迟
    latency2 = Column(Float, nullable=True)  # 第二轮 Playwright 延迟
    # 是否正在测速中
    testing = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
