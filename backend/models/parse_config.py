from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base

class ParseConfig(Base):
    __tablename__ = "parse_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    base_url = Column(String)
    priority = Column(Integer, default=0)
    status = Column(String, default="active")  # active / inactive
    created_at = Column(DateTime, default=datetime.utcnow)
