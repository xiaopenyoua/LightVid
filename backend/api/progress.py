from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models.watch_progress import WatchProgress
from datetime import datetime

router = APIRouter(prefix="/api/progress", tags=["progress"])


@router.get("")
def get_progress(tmdb_id: int, season: int = None, episode: int = None, db: Session = Depends(get_db)):
    """获取指定剧集的播放进度"""
    query = db.query(WatchProgress).filter_by(tmdb_id=tmdb_id, season=season, episode=episode)
    item = query.first()
    if not item:
        return None
    return {
        "tmdb_id": item.tmdb_id,
        "season": item.season,
        "episode": item.episode,
        "current_time": item.current_time,
        "duration": item.duration,
        "updated_at": item.updated_at,
    }


@router.post("")
def save_progress(data: dict, db: Session = Depends(get_db)):
    """保存播放进度"""
    tmdb_id = data.get("tmdb_id")
    season = data.get("season")
    episode = data.get("episode")

    existing = db.query(WatchProgress).filter_by(
        tmdb_id=tmdb_id, season=season, episode=episode
    ).first()

    if existing:
        existing.current_time = data.get("current_time", existing.current_time)
        existing.duration = data.get("duration", existing.duration)
        existing.updated_at = datetime.utcnow()
    else:
        progress = WatchProgress(
            tmdb_id=tmdb_id,
            season=season,
            episode=episode,
            current_time=data.get("current_time", 0),
            duration=data.get("duration"),
        )
        db.add(progress)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # 竞态条件：再次尝试更新
        existing = db.query(WatchProgress).filter_by(
            tmdb_id=tmdb_id, season=season, episode=episode
        ).first()
        if existing:
            existing.current_time = data.get("current_time", existing.current_time)
            existing.duration = data.get("duration", existing.duration)
            db.commit()

    return {"ok": True}


@router.get("/list/{tmdb_id}")
def get_progress_list(tmdb_id: int, db: Session = Depends(get_db)):
    """获取某影片所有剧集的播放进度"""
    items = db.query(WatchProgress).filter_by(tmdb_id=tmdb_id).all()
    return [
        {
            "tmdb_id": item.tmdb_id,
            "season": item.season,
            "episode": item.episode,
            "current_time": item.current_time,
            "duration": item.duration,
            "updated_at": item.updated_at,
        }
        for item in items
    ]