from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class ParseConfigBase(BaseModel):
    name: str
    base_url: str
    priority: int = 0

class ParseConfigCreate(ParseConfigBase):
    pass

class ParseConfigUpdate(BaseModel):
    name: Optional[str] = None
    base_url: Optional[str] = None
    priority: Optional[int] = None
    status: Optional[str] = None

class ParseConfigResponse(ParseConfigBase):
    id: int
    status: str
    created_at: datetime
    latency1: Optional[float] = None  # 第一轮延迟
    latency2: Optional[float] = None  # 第二轮延迟
    testing: bool = False  # 是否正在测速中

    class Config:
        from_attributes = True
