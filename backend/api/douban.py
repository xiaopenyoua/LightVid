from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from database import get_db
from models.douban_video import DoubanVideo
from schemas.douban_video import DoubanVideoResponse
from services.tmdb_service import tmdb_service

router = APIRouter(prefix="/api/douban", tags=["douban"])


@router.get("/videos", response_model=list[DoubanVideoResponse])
def get_videos(
    category: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    q = db.query(DoubanVideo)
    if category:
        q = q.filter_by(category=category)
    return q.order_by(DoubanVideo.created_at.desc()).offset(skip).limit(limit).all()


@router.get("/videos/{tmdb_id}", response_model=DoubanVideoResponse)
def get_video(tmdb_id: int, db: Session = Depends(get_db)):
    video = db.query(DoubanVideo).filter_by(tmdb_id=tmdb_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/search")
def search_videos(q: str, db: Session = Depends(get_db)):
    """搜索本地数据库"""
    videos = db.query(DoubanVideo).filter(
        DoubanVideo.title.like(f"%{q}%")
    ).limit(20).all()
    return videos


@router.get("/tmdb/search")
async def search_tmdb(q: str, media_type: str = "movie"):
    """
    搜索 TMDB（仅返回搜索结果，不存储）
    media_type: "movie" 或 "tv"
    """
    if media_type == "tv":
        results = await tmdb_service.search_tv(q)
    else:
        results = await tmdb_service.search_movies(q)

    formatted = []
    for item in results:
        formatted.append({
            "tmdb_id": item.get("id"),
            "title": item.get("title") or item.get("name"),
            "poster_url": tmdb_service.format_poster_url(item.get("poster_path")),
            "backdrop_url": tmdb_service.format_poster_url(item.get("backdrop_path"), "w780"),
            "rating": item.get("vote_average"),
            "year": None,
            "category": "tv" if media_type == "tv" else "movie",
            "release_date": item.get("release_date") or item.get("first_air_date", ""),
            "overview": item.get("overview", ""),
        })
    return formatted


@router.post("/crawl/{tmdb_id}")
async def crawl_video(tmdb_id: int, category: str = "movie", db: Session = Depends(get_db)):
    """从 TMDB 爬取视频信息并存储到本地数据库"""
    # 检查是否已存在
    existing = db.query(DoubanVideo).filter_by(tmdb_id=tmdb_id).first()
    if existing:
        return existing

    # 从 TMDB 获取详情
    if category == "tv":
        details = await tmdb_service.get_tv_details(tmdb_id)
    else:
        details = await tmdb_service.get_movie_details(tmdb_id)

    if not details:
        raise HTTPException(status_code=500, detail="Failed to fetch from TMDB")

    # 解析数据
    title = details.get("title") or details.get("name")
    release_date = details.get("release_date") or details.get("first_air_date", "")
    year = int(release_date[:4]) if release_date else None

    genres_list = details.get("genres", [])
    genres = ",".join(g.get("name", "") for g in genres_list) if genres_list else None

    video = DoubanVideo(
        tmdb_id=tmdb_id,
        title=title,
        poster_url=tmdb_service.format_poster_url(details.get("poster_path")),
        backdrop_url=tmdb_service.format_poster_url(details.get("backdrop_path"), "w780"),
        rating=details.get("vote_average"),
        summary=details.get("overview"),
        year=year,
        category=category,
        genres=genres,
        original_title=details.get("original_title") or details.get("original_name"),
    )

    db.add(video)
    db.commit()
    db.refresh(video)
    return video


@router.get("/trending")
async def get_trending(media_type: str = "movie"):
    """获取 TMDB 热门内容"""
    results = await tmdb_service.get_trending(media_type=media_type)

    formatted = []
    for item in results:
        is_movie = item.get("media_type") == "movie" or not item.get("first_air_date")
        formatted.append({
            "tmdb_id": item.get("id"),
            "title": item.get("title") or item.get("name"),
            "poster_url": tmdb_service.format_poster_url(item.get("poster_path")),
            "backdrop_url": tmdb_service.format_poster_url(item.get("backdrop_path"), "w780"),
            "rating": item.get("vote_average"),
            "category": "movie" if is_movie else "tv",
            "release_date": item.get("release_date") or item.get("first_air_date", ""),
        })
    return formatted
