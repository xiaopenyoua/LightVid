from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from database import get_db

from services.video_searcher import search_video_link, get_all_platforms, continue_precache
from services.video_resolver import resolve_with_fallback, resolve_with_browser_fallback, get_parser_list, resolve_video_url
from models.video_platform_link import VideoPlatformLink

router = APIRouter(prefix="/api/search", tags=["search"])


class VideoLinkRequest(BaseModel):
    """搜索视频链接请求"""
    tmdb_id: int
    media_type: str  # movie / tv
    platform: str  # tencent / iqiyi / youku / bilibili / mgtv
    title: str
    year: int | None = None
    season: int | None = None  # 剧集第几季
    episode: int | None = None  # 剧集第几集
    seasons_episodes: dict[int, int] | None = None  # {season_num: episode_count, ...} 用于预缓存


class VideoLinkResponse(BaseModel):
    """视频链接响应"""
    platform: str
    platform_url: str
    title: str


@router.post("/video-link", response_model=VideoLinkResponse)
async def get_video_link(request: VideoLinkRequest, db: Session = Depends(get_db)):
    """
    搜索视频播放链接

    流程:
    1. 查缓存，有且未过期直接返回
    2. HTTP 模式搜索
    3. 存入缓存
    4. 返回播放页面 URL
    5. 后台触发预缓存其他集数
    """
    # 验证平台
    if request.platform not in get_all_platforms():
        raise HTTPException(status_code=400, detail=f"不支持的平台: {request.platform}")

    result = await search_video_link(
        db=db,
        tmdb_id=request.tmdb_id,
        media_type=request.media_type,
        platform=request.platform,
        title=request.title,
        year=request.year,
        season=request.season,
        episode=request.episode,
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"未找到该影片的播放链接")

    return result


class ResolveRequest(BaseModel):
    """解析视频链接请求"""
    platform_url: str
    parser_url: str = None  # 可选，指定解析服务 URL


class ResolveResponse(BaseModel):
    """解析结果响应"""
    m3u8_url: str
    parser: str


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_video(request: ResolveRequest, db: Session = Depends(get_db)):
    """
    解析视频链接为 m3u8

    调用解析服务获取 m3u8 播放地址
    使用浏览器模式处理 JavaScript 渲染的解析服务页面
    通过拦截网络请求捕获真实的 m3u8/mp4 地址
    """

    # 如果指定了解析服务，只使用这一个
    if request.parser_url:
        try:
            # 使用 resolve_video_url 捕获视频请求
            result = await resolve_video_url(request.platform_url, request.parser_url)
            if not result:
                raise HTTPException(status_code=404, detail="该解析服务无法解析此视频，请尝试其他解析服务")
            return result
        except HTTPException:
            raise
        except Exception as e:
            print(f"[resolve] 指定解析服务失败: {e}")
            raise HTTPException(status_code=500, detail="解析失败，请稍后重试")

    # 没有指定解析服务时，使用默认行为（遍历所有解析服务）
    parsers = get_parser_list(db)
    result = await resolve_with_browser_fallback(request.platform_url, parsers)

    if not result:
        raise HTTPException(status_code=500, detail="解析失败，请稍后重试")

    return result


@router.get("/parsers")
async def get_parsers(db: Session = Depends(get_db)):
    """
    获取可用的解析服务列表
    """
    parsers = get_parser_list(db)
    return [{"name": p["name"], "url": p["url"]} for p in parsers]


@router.get("/platforms")
async def get_platforms():
    """
    获取支持的视频平台列表
    """
    return [{"name": p, "label": get_platform_label(p)} for p in get_all_platforms()]


class ClearCacheRequest(BaseModel):
    """清除缓存请求"""
    tmdb_id: int
    platform: str
    season: int | None = None  # 可选，只清除某一季


class ClearCacheResponse(BaseModel):
    """清除缓存响应"""
    deleted_count: int
    message: str


@router.delete("/cache", response_model=ClearCacheResponse)
async def clear_video_cache(request: ClearCacheRequest, db: Session = Depends(get_db)):
    """
    清除视频链接缓存

    清除指定 tmdb_id 和 platform 的缓存记录
    清除后该剧集的缓存会被标记为待重新解析
    """
    query = db.query(VideoPlatformLink).filter(
        VideoPlatformLink.tmdb_id == request.tmdb_id,
        VideoPlatformLink.platform == request.platform,
    )

    if request.season is not None:
        query = query.filter(VideoPlatformLink.season == request.season)

    # 先删除记录
    deleted_count = query.delete()
    db.commit()

    return ClearCacheResponse(
        deleted_count=deleted_count,
        message=f"已清除 {deleted_count} 条缓存记录"
    )


class ContinuePrecacheRequest(BaseModel):
    """触发预缓存请求"""
    tmdb_id: int
    platform: str
    title: str
    year: int | None = None
    current_season: int | None = None
    current_episode: int | None = None
    seasons_episodes: dict[int, int] | None = None  # {season_num: episode_count, ...}


class ContinuePrecacheResponse(BaseModel):
    """继续预缓存响应"""
    status: str
    message: str


@router.post("/continue-precache", response_model=ContinuePrecacheResponse)
async def trigger_continue_precache(request: ContinuePrecacheRequest, db: Session = Depends(get_db)):
    """
    触发预缓存任务

    当用户进入播放页时，后台预缓存所有剧集的 URL
    """
    result = await continue_precache(
        db=db,
        tmdb_id=request.tmdb_id,
        platform=request.platform,
        title=request.title,
        year=request.year,
        current_season=request.current_season,
        current_episode=request.current_episode,
        seasons_episodes=request.seasons_episodes,
    )

    return ContinuePrecacheResponse(
        status=result["status"],
        message=result["message"]
    )


def get_platform_label(platform: str) -> str:
    """获取平台中文名称"""
    labels = {
        "tencent": "腾讯视频",
        "iqiyi": "爱奇艺",
        "youku": "优酷",
        "bilibili": "哔哩哔哩",
        "mgtv": "芒果TV",
    }
    return labels.get(platform, platform)