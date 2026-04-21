from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from database import get_db
from models.favorite import Favorite
from services.tmdb_service import tmdb_service
import asyncio

router = APIRouter(prefix="/api/favorites", tags=["favorites"])


@router.get("")
def get_favorites(db: Session = Depends(get_db)):
    """获取收藏列表，包含视频详情"""
    favorites = db.query(Favorite).order_by(Favorite.created_at.desc()).all()
    result = []
    for f in favorites:
        # 先查 tv，因为用户主要收藏的是视频内容
        tmdb_data = asyncio.run(tmdb_service.get_tv_details(f.tmdb_id))
        media_type = "tv"
        if not tmdb_data:
            # tv 查不到再查 movie
            tmdb_data = asyncio.run(tmdb_service.get_movie_details(f.tmdb_id))
            media_type = "movie"

        if tmdb_data:
            video_info = tmdb_service.format_tmdb_item(tmdb_data, media_type=media_type)
        else:
            video_info = {
                "tmdb_id": f.tmdb_id,
                "title": f"TMDB {f.tmdb_id}",
                "media_type": media_type,
                "poster_url": "",
            }

        result.append({
            "id": f.id,
            "tmdb_id": f.tmdb_id,
            "created_at": f.created_at,
            "video": video_info,
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
