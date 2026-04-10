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

    class Config:
        from_attributes = True
