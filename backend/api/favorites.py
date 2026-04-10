from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models.favorite import Favorite
from models.douban_video import DoubanVideo

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def get_favorites(db: Session = Depends(get_db)):
    favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
    result = []
    for f in favorites:
        video = db.query(DoubanVideo).filter_by(tmdb_id=f.tmdb_id).first()
        if video:
            result.append({
                "id": f.id,
                "tmdb_id": f.tmdb_id,
                "created_at": f.created_at,
                "video": {
                    "title": video.title,
                    "poster_url": video.poster_url,
                    "rating": video.rating,
                    "year": video.year,
                }
            })
    return result


@router.post("")
def add_favorite(data: dict, db: Session = Depends(get_db)):
    tmdb_id = data.get("tmdb_id")
    existing = db.query(Favorite).filter_by(tmdb_id=tmdb_id).first()
    if existing:
        return {"ok": True, "message": "Already favorited"}
    favorite = Favorite(tmdb_id=tmdb_id)
    db.add(favorite)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        return {"ok": True, "message": "Already favorited"}
    return {"ok": True}


@router.delete("/{tmdb_id}")
def remove_favorite(tmdb_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter_by(tmdb_id=tmdb_id).first()
    if favorite:
        db.delete(favorite)
        db.commit()
    return {"ok": True}


@router.get("/check/{tmdb_id}")
def check_favorite(tmdb_id: int, db: Session = Depends(get_db)):
    favorite = db.query(Favorite).filter_by(tmdb_id=tmdb_id).first()
    return {"is_favorite": favorite is not None}
