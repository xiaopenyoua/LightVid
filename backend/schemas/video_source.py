from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional

class VideoSourceBase(BaseModel):
    name: str
    url: str
    type: str = "m3u8"
    platform: str = "tvbox"
    source_type: str = "user"

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class VideoSourceCreate(VideoSourceBase):
    pass

class VideoSourceUpdate(BaseModel):
    name: Optional[str] = None
    url: Optional[str] = None
    type: Optional[str] = None
    platform: Optional[str] = None
    status: Optional[str] = None
    speed: Optional[float] = None

    @field_validator('url')
    @classmethod
    def validate_url(cls, v: str):
        if v is not None and not v.startswith(('http://', 'https://')):
            raise ValueError('URL must start with http:// or https://')
        return v

class VideoSourceResponse(VideoSourceBase):
    id: int
    speed: Optional[float]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
