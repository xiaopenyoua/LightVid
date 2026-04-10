from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import case
from database import get_db
from models.video_source import VideoSource
from schemas.video_source import VideoSourceCreate, VideoSourceUpdate, VideoSourceResponse
from crawlers.tvbox_crawler import crawl_tvbox_sources
from services.speed_test import speed_test_source

router = APIRouter(prefix="/api/sources", tags=["sources"])

@router.get("", response_model=list[VideoSourceResponse])
def get_sources(
    type: str = None,
    platform: str = None,
    source_type: str = None,
    db: Session = Depends(get_db)
):
    q = db.query(VideoSource)
    if type:
        q = q.filter_by(type=type)
    if platform:
        q = q.filter_by(platform=platform)
    if source_type:
        q = q.filter_by(source_type=source_type)
    return q.order_by(
        case((VideoSource.speed == None, 1), else_=0),
        VideoSource.speed.asc()
    ).all()

@router.post("", response_model=VideoSourceResponse)
def create_source(data: VideoSourceCreate, db: Session = Depends(get_db)):
    existing = db.query(VideoSource).filter_by(url=data.url).first()
    if existing:
        raise HTTPException(status_code=400, detail="URL already exists")
    source = VideoSource(**data.model_dump())
    db.add(source)
    db.commit()
    db.refresh(source)
    return source

@router.delete("/{source_id}")
def delete_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    db.delete(source)
    db.commit()
    return {"ok": True}

@router.post("/crawl")
def trigger_crawl(db: Session = Depends(get_db)):
    import asyncio
    count = asyncio.run(crawl_tvbox_sources(db))
    return {"crawled": count}

@router.post("/speed-test/{source_id}")
def test_single_source(source_id: int, db: Session = Depends(get_db)):
    source = db.query(VideoSource).get(source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    duration = speed_test_source(source.url)
    source.speed = duration
    db.commit()
    return {"id": source_id, "speed": duration}
