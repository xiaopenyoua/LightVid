"""
视频搜索调度服务 - 并行探测，HTTP 优先，Playwright 保底
"""
import asyncio
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from crawlers.platforms.tencent import TencentCrawler
from crawlers.platforms.iqiyi import IqiyiCrawler
from crawlers.platforms.youku import YoukuCrawler
from crawlers.platforms.bilibili import BilibiliCrawler
from crawlers.platforms.mgtv import MgtvCrawler
from models.video_platform_link import VideoPlatformLink


# 平台爬虫映射
PLATFORM_CRAWLERS = {
    "tencent": TencentCrawler(),
    "iqiyi": IqiyiCrawler(),
    "youku": YoukuCrawler(),
    "bilibili": BilibiliCrawler(),
    "mgtv": MgtvCrawler(),
}

# 缓存有效期（小时）
CACHE_EXPIRY_HOURS = 24


async def search_video_link(
    db: Session,
    tmdb_id: int,
    media_type: str,
    platform: str,
    title: str,
    year: int = None
) -> Optional[Dict[str, Any]]:
    """
    搜索视频播放链接
    流程：查缓存 -> HTTP探测 -> 存入缓存 -> 返回
    """
    # 1. 检查缓存
    cached = db.query(VideoPlatformLink).filter(
        VideoPlatformLink.tmdb_id == tmdb_id,
        VideoPlatformLink.media_type == media_type,
        VideoPlatformLink.platform == platform,
    ).first()

    if cached:
        # 检查缓存是否过期
        if cached.expires_at and cached.expires_at > datetime.utcnow():
            return {
                "platform": cached.platform,
                "platform_url": cached.platform_url,
                "title": cached.title,
            }
        else:
            # 缓存过期，更新
            cached.updated_at = datetime.utcnow()

    # 2. 获取爬虫
    crawler = PLATFORM_CRAWLERS.get(platform)
    if not crawler:
        return None

    # 3. HTTP 模式搜索
    platform_url = await crawler.search_http(title, year)

    if platform_url:
        # 4. 存入缓存
        if cached:
            cached.platform_url = platform_url
            cached.updated_at = datetime.utcnow()
            cached.expires_at = datetime.utcnow() + timedelta(hours=CACHE_EXPIRY_HOURS)
        else:
            cached = VideoPlatformLink(
                tmdb_id=tmdb_id,
                media_type=media_type,
                platform=platform,
                platform_url=platform_url,
                title=title,
                expires_at=datetime.utcnow() + timedelta(hours=CACHE_EXPIRY_HOURS),
            )
            db.add(cached)

        db.commit()

        return {
            "platform": platform,
            "platform_url": platform_url,
            "title": title,
        }

    return None


def get_all_platforms() -> list:
    """获取所有支持的平台"""
    return list(PLATFORM_CRAWLERS.keys())