from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.watch_history import WatchHistory

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def get_history(db: Session = Depends(get_db)):
    items = db.query(WatchHistory).order_by(WatchHistory.last_watched.desc()).limit(50).all()
    return [
        {
            "id": item.id,
            "tmdb_id": item.tmdb_id,
            "source_id": item.source_id,
            "progress": item.progress,
            "duration": item.duration,
            "last_watched": item.last_watched,
        }
        for item in items
    ]


@router.get("/{tmdb_id}")
def get_history_by_tmdb(tmdb_id: int, db: Session = Depends(get_db)):
    item = db.query(WatchHistory).filter_by(tmdb_id=tmdb_id).first()
    if not item:
        return None
    return {
        "id": item.id,
        "tmdb_id": item.tmdb_id,
        "source_id": item.source_id,
        "progress": item.progress,
        "duration": item.duration,
        "last_watched": item.last_watched,
    }


@router.post("")
def update_history(data: dict, db: Session = Depends(get_db)):
    tmdb_id = data.get("tmdb_id")
    history = db.query(WatchHistory).filter_by(tmdb_id=tmdb_id).first()
    if history:
        history.progress = data.get("progress", history.progress)
        history.duration = data.get("duration", history.duration)
        history.source_id = data.get("source_id", history.source_id)
        from datetime import datetime
        history.last_watched = datetime.utcnow()
    else:
        from datetime import datetime
        history = WatchHistory(
            tmdb_id=tmdb_id,
            progress=data.get("progress", 0),
            duration=data.get("duration"),
            source_id=data.get("source_id"),
        )
        db.add(history)
    db.commit()
    return {"ok": True}


@router.delete("/{tmdb_id}")
def delete_history(tmdb_id: int, db: Session = Depends(get_db)):
    history = db.query(WatchHistory).filter_by(tmdb_id=tmdb_id).first()
    if history:
        db.delete(history)
        db.commit()
    return {"ok": True}
