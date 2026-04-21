from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from models.watch_progress import WatchProgress
from models.watch_history import WatchHistory
from services.tmdb_service import tmdb_service
import asyncio

router = APIRouter(prefix="/api/history", tags=["history"])


@router.get("")
def get_history(db: Session = Depends(get_db)):
    """获取观看历史（使用 WatchProgress 表，支持剧集续播）"""
    items = db.query(WatchProgress).order_by(WatchProgress.updated_at.desc()).limit(100).all()

    # 合并同一季的记录，每季只保留最新的一条
    merged = {}
    for item in items:
        if item.season is not None:
            # 剧集：按 tmdb_id + season 合并
            key = (item.tmdb_id, item.season)
            if key not in merged or item.updated_at > merged[key].updated_at:
                merged[key] = item
        else:
            # 电影：按 tmdb_id 合并
            key = (item.tmdb_id,)
            if key not in merged or item.updated_at > merged[key].updated_at:
                merged[key] = item

    result = []
    for item in merged.values():
        # 如果没有 media_type，通过TMDB判断
        media_type = item.media_type
        if not media_type:
            # 尝试通过TMDB判断，先查tv（因为播放历史主要是剧集）
            tmdb_data = asyncio.run(tmdb_service.get_tv_details(item.tmdb_id))
            if tmdb_data:
                media_type = "tv"
            else:
                tmdb_data = asyncio.run(tmdb_service.get_movie_details(item.tmdb_id))
                if tmdb_data:
                    media_type = "movie"
        else:
            # 获取TMDB数据
            if media_type == "movie":
                tmdb_data = asyncio.run(tmdb_service.get_movie_details(item.tmdb_id))
            else:
                tmdb_data = asyncio.run(tmdb_service.get_tv_details(item.tmdb_id))

        if tmdb_data:
            video_info = tmdb_service.format_tmdb_item(tmdb_data, media_type=media_type)
        else:
            video_info = {
                "tmdb_id": item.tmdb_id,
                "title": f"TMDB {item.tmdb_id}",
                "media_type": media_type or "movie",
                "poster_url": "",
            }

        result.append({
            "id": item.id,
            "tmdb_id": item.tmdb_id,
            "media_type": video_info["media_type"],
            "title": video_info["title"],
            "poster_url": video_info.get("poster_url", ""),
            "season": item.season,
            "episode": item.episode,
            "current_time": item.current_time,
            "duration": item.duration,
            "progress": item.current_time,
            "updated_at": item.updated_at,
        })

    # 按 updated_at 降序排序
    result.sort(key=lambda x: x["updated_at"], reverse=True)
    return result[:50]


@router.get("/{tmdb_id}")
def get_history_by_tmdb(tmdb_id: int, db: Session = Depends(get_db)):
    item = db.query(WatchProgress).filter_by(tmdb_id=tmdb_id).first()
    if not item:
        return None
    return {
        "id": item.id,
        "tmdb_id": item.tmdb_id,
        "season": item.season,
        "episode": item.episode,
        "current_time": item.current_time,
        "duration": item.duration,
        "updated_at": item.updated_at,
    }


@router.post("")
def update_history(data: dict, db: Session = Depends(get_db)):
    """保留旧接口，兼容现有代码"""
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
def delete_history(tmdb_id: int, season: int = None, episode: int = None, db: Session = Depends(get_db)):
    """删除历史记录，剧集按季删除，电影按整部删除"""
    if season is not None:
        # 删除指定季的所有历史
        items = db.query(WatchProgress).filter_by(
            tmdb_id=tmdb_id, season=season
        ).all()
        for item in items:
            db.delete(item)
        db.commit()
    else:
        # 删除电影（season=None, episode=None）
        items = db.query(WatchProgress).filter_by(
            tmdb_id=tmdb_id, season=None
        ).all()
        for item in items:
            db.delete(item)
        db.commit()
    return {"ok": True}
