from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case
from database import get_db
from models.video_source import VideoSource

router = APIRouter(prefix="/api/play", tags=["play"])

@router.get("/sources")
def get_play_sources(db: Session = Depends(get_db)):
    """
    获取所有可用播放源，按速度排序（未测速的排在最后）。
    """
    sources = db.query(VideoSource).filter_by(
        status="active"
    ).order_by(
        case((VideoSource.speed == None, 1), else_=0),
        VideoSource.speed.asc()
    ).all()
    return [
        {
            "id": s.id,
            "name": s.name,
            "url": s.url,
            "type": s.type,
            "platform": s.platform,
            "speed": s.speed,
        }
        for s in sources
    ]

@router.get("/{source_id}")
def get_play_url(source_id: int, db: Session = Depends(get_db)):
    """
    播放指定源，返回解析后的播放地址。
    """
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    if source.status != "active":
        raise HTTPException(status_code=400, detail="Source is not active")
    return {
        "id": source.id,
        "name": source.name,
        "url": source.url,
        "type": source.type,
        "platform": source.platform,
        "speed": source.speed,
    }
