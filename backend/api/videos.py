"""
视频相关 API 路由
提供首页、电影、剧集、搜索等接口
"""
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session
import httpx

from database import get_db
from models.tmdb_genre import TmdbGenre
from models.tmdb_cached_list import TmdbCachedList
from schemas.tmdb_genre import TmdbGenreResponse
from schemas.tmdb_cached_list import TmdbCachedItemResponse
from services.tmdb_service import tmdb_service
from config import LANGUAGE

router = APIRouter(prefix="/api/videos", tags=["videos"])


# ============ 首页全量数据 ============

@router.get("/home")
async def get_home(db: Session = Depends(get_db)):
    """
    首页全量数据：
    - 所有类型列表
    - 7个缓存的列表（trending/popular/top_rated/upcoming × movie/tv）
    - popular_all: 热门电影+剧集混合数据（第二页热门推荐用）
    """
    # 获取所有 Genre
    genres = db.query(TmdbGenre).all()

    # 获取 trending/all/day 用于首页轮播（实时，不走缓存保证新鲜度）
    trending_all_raw = await tmdb_service.get_trending(media_type="all", time_window="week")
    trending_all = [tmdb_service.format_tmdb_item(r) for r in trending_all_raw[:10]]

    # 获取 popular/all 用于第二页热门推荐（实时调用 TMDB API）
    popular_movies_raw = await tmdb_service.get_popular_movies()
    popular_tv_raw = await tmdb_service.get_popular_tv()
    popular_all = (
        [tmdb_service.format_tmdb_item(r, media_type="movie") for r in popular_movies_raw[:20]] +
        [tmdb_service.format_tmdb_item(r, media_type="tv") for r in popular_tv_raw[:20]]
    )

    # 获取所有缓存列表
    lists = {}
    for list_type in ["trending", "popular", "top_rated", "upcoming"]:
        for media_type in ["movie", "tv"]:
            key = f"{list_type}_{media_type}"
            items = db.query(TmdbCachedList).filter_by(
                list_type=list_type, media_type=media_type
            ).order_by(TmdbCachedList.popularity.desc()).limit(20).all()
            lists[key] = items

    return {
        "genres": [TmdbGenreResponse.model_validate(g) for g in genres],
        "lists": {k: [TmdbCachedItemResponse.model_validate(i) for i in v] for k, v in lists.items()},
        "trending_all": [TmdbCachedItemResponse.model_validate(t) for t in trending_all],
        "popular_all": [TmdbCachedItemResponse.model_validate(t) for t in popular_all],
    }


# ============ 类型列表 ============

@router.get("/genres", response_model=list[TmdbGenreResponse])
def get_genres(db: Session = Depends(get_db)):
    """获取所有类型列表（电影+剧集）"""
    genres = db.query(TmdbGenre).all()
    return [TmdbGenreResponse.model_validate(g) for g in genres]


# ============ 电影/剧集列表（实时） ============

@router.get("/movies")
async def get_movies(
    page: int = Query(default=1, ge=1),
    sort_by: str = "popularity.desc",
    year: int = None,
    genre: int = None,
    genres: str = None,
    language: str = None,
    vote_count_gte: int = None,
):
    """
    获取电影列表（实时调 TMDB discover）
    - genre: 单个 TMDB genre ID（兼容旧参数）
    - genres: 多个 genre ID，逗号分隔（如 "16,35"）
    - sort_by: popularity.desc / vote_average.desc / release_date.desc
    - year: 发行年份
    - language: 原始语言（如 zh, en, ja）
    - vote_count_gte: 最少投票数
    """
    results = await tmdb_service.discover_movies(
        page=page,
        sort_by=sort_by,
        year=year,
        genre_ids=genre or genres,
        language=language,
        vote_count_gte=vote_count_gte,
    )
    return [tmdb_service.format_tmdb_item(r, "movie") for r in results]


@router.get("/tv")
async def get_tv_shows(
    page: int = Query(default=1, ge=1),
    sort_by: str = "popularity.desc",
    year: int = None,
    genre: int = None,
    genres: str = None,
    language: str = None,
    vote_count_gte: int = None,
):
    """
    获取剧集列表（实时调 TMDB discover）
    """
    results = await tmdb_service.discover_tv(
        page=page,
        sort_by=sort_by,
        year=year,
        genre_ids=genre or genres,
        language=language,
        vote_count_gte=vote_count_gte,
    )
    return [tmdb_service.format_tmdb_item(r, "tv") for r in results]


# ============ 详情（实时） ============

@router.get("/{media_type}/{tmdb_id}")
async def get_detail(media_type: str, tmdb_id: int):
    """
    获取电影/剧集详情（实时调 TMDB）
    media_type: "movie" 或 "tv"
    """
    if media_type not in ["movie", "tv"]:
        raise HTTPException(status_code=400, detail="media_type must be 'movie' or 'tv'")

    if media_type == "movie":
        details = await tmdb_service.get_movie_details(tmdb_id)
    else:
        details = await tmdb_service.get_tv_details(tmdb_id)

    if not details:
        raise HTTPException(status_code=404, detail="Not found")

    # 格式化详情
    title = details.get("title") or details.get("name")
    release_date = details.get("release_date") or details.get("first_air_date", "")

    genres_list = details.get("genres", [])
    genres_str = ",".join(g.get("name", "") for g in genres_list) if genres_list else ""
    genre_ids_str = ",".join(str(g.get("id", "")) for g in genres_list) if genres_list else ""

    # 处理剧集季节
    seasons = details.get("seasons", [])
    formatted_seasons = []
    for s in seasons:
        if s.get("season_number") == 0:
            continue  # 跳过特别篇
        formatted_seasons.append({
            "season_number": s.get("season_number"),
            "name": s.get("name"),
            "episode_count": s.get("episode_count"),
            "air_date": s.get("air_date"),
            "poster_url": tmdb_service.format_poster_url(s.get("poster_path")) if s.get("poster_path") else None,
        })

    return {
        "tmdb_id": details.get("id"),
        "title": title,
        "media_type": media_type,
        "poster_url": tmdb_service.format_poster_url(details.get("poster_path")),
        "backdrop_url": tmdb_service.format_poster_url(details.get("backdrop_path"), "w780"),
        "vote_average": details.get("vote_average"),
        "vote_count": details.get("vote_count"),
        "overview": details.get("overview"),
        "release_date": release_date,
        "genres": genres_str,
        "genre_ids": genre_ids_str,
        "runtime": details.get("runtime") or details.get("episode_run_time", []),
        "status": details.get("status"),
        "tagline": details.get("tagline"),
        "seasons": formatted_seasons if media_type == "tv" else None,
    }


@router.get("/{media_type}/{tmdb_id}/seasons/{season}")
async def get_season_detail(media_type: str, tmdb_id: int, season: int):
    """
    获取剧集某季详情（实时调 TMDB）
    """
    if media_type != "tv":
        raise HTTPException(status_code=400, detail="Only TV shows have seasons")

    url = f"{tmdb_service.base_url}/tv/{tmdb_id}/season/{season}"
    params = {"api_key": tmdb_service.api_key, "language": LANGUAGE}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(url, params=params)
            resp.raise_for_status()
            data = resp.json()

        episodes = []
        for ep in data.get("episodes", []):
            episodes.append({
                "episode_number": ep.get("episode_number"),
                "name": ep.get("name"),
                "still_path": tmdb_service.format_poster_url(ep.get("still_path")) if ep.get("still_path") else None,
                "overview": ep.get("overview"),
                "air_date": ep.get("air_date"),
                "runtime": ep.get("runtime"),
            })

        return {
            "season_number": data.get("season_number"),
            "name": data.get("name"),
            "overview": data.get("overview"),
            "poster_url": tmdb_service.format_poster_url(data.get("poster_path")) if data.get("poster_path") else None,
            "episodes": episodes,
        }
    except httpx.HTTPStatusError as e:
        if e.response.status_code == 404:
            raise HTTPException(status_code=404, detail="Season not found")
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============ 搜索（实时） ============

@router.get("/search")
async def search_videos(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1),
):
    """
    搜索电影和剧集（实时调 TMDB search/multi）
    """
    results = await tmdb_service.search_multi(q, page)

    formatted = []
    for item in results:
        if item.get("media_type") == "person":
            continue  # 跳过人物
        media_type = item.get("media_type")
        if media_type not in ["movie", "tv"]:
            continue

        formatted.append(tmdb_service.format_tmdb_item(item, media_type))

    return formatted
