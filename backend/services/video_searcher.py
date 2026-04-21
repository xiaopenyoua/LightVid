"""
视频搜索调度服务 - 并行探测，HTTP 优先，Playwright 保底
"""
import asyncio
import random
from typing import Optional, Dict, Any, List
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
CACHE_EXPIRY_HOURS = 24 * 7  # 一周

# 预缓存配置
PRECACHE_BATCH_SIZE = 3  # 每批预缓存集数
PRECACHE_BASE_DELAY = 0.5  # 基础延迟（秒）
PRECACHE_DELAY_VARIANCE = 0.5  # 延迟随机浮动范围（秒）
MAX_PRECACHE_CONCURRENT = 2  # 最大并发预缓存数


async def search_video_link(
    db: Session,
    tmdb_id: int,
    media_type: str,
    platform: str,
    title: str,
    year: int = None,
    season: int = None,
    episode: int = None
) -> Optional[Dict[str, Any]]:
    """
    搜索视频播放链接
    流程：查缓存 -> HTTP探测 -> 存入缓存 -> 返回
    注意：此函数只负责获取当前剧集URL，不触发预缓存
    预缓存由 continue_precache 统一处理
    """
    # 构建搜索关键词：搜索主标题（不带集信息），因为 cover 页面是针对整部剧的
    search_keyword = title

    # 1. 检查缓存（剧集需要更细粒度的缓存）
    cache_filter = [
        VideoPlatformLink.tmdb_id == tmdb_id,
        VideoPlatformLink.media_type == media_type,
        VideoPlatformLink.platform == platform,
    ]
    if media_type == "tv" and season and episode:
        cache_filter.append(VideoPlatformLink.season == season)
        cache_filter.append(VideoPlatformLink.episode == episode)

    cached = db.query(VideoPlatformLink).filter(*cache_filter).first()

    if cached:
        # 检查缓存是否过期
        if cached.expires_at and cached.expires_at > datetime.utcnow():
            # 缓存命中，更新 precache_status 为 completed
            cached.precache_status = "completed"
            cached.is_precached = True
            # 如果 title 为空，使用搜索关键词
            if not cached.title:
                cached.title = search_keyword
            db.commit()
            return {
                "platform": cached.platform,
                "platform_url": cached.platform_url,
                "title": cached.title,
                "from_cache": True,
                "cache_expired": False,
            }
        else:
            # 缓存过期，标记需要更新
            cached.updated_at = datetime.utcnow()

    # 2. 获取爬虫
    crawler = PLATFORM_CRAWLERS.get(platform)
    if not crawler:
        return None

    # 3. HTTP 模式搜索（快速优先）
    platform_url = await crawler.search_http(search_keyword, year)

    # 如果 HTTP 模式失败，尝试浏览器模式（针对 SPA 页面）
    if not platform_url and hasattr(crawler, 'search_browser'):
        print(f"[{platform}] HTTP 模式未找到结果，尝试浏览器模式...")
        platform_url = await crawler.search_browser(search_keyword, year)

    if platform_url:
        # 4. 如果是剧集且有集数信息，从 cover 页面提取具体集数的播放 URL
        final_url = platform_url
        if media_type == "tv" and season and episode and hasattr(crawler, 'get_episode_url'):
            episode_url = await crawler.get_episode_url(platform_url, season, episode)
            if episode_url:
                final_url = episode_url

        # 5. 存入缓存
        if cached:
            cached.platform_url = final_url
            cached.title = search_keyword  # 更新标题（预创建的记录 title 为空）
            cached.updated_at = datetime.utcnow()
            cached.expires_at = datetime.utcnow() + timedelta(hours=CACHE_EXPIRY_HOURS)
            cached.precache_status = "completed"
            cached.is_precached = True
        else:
            cached = VideoPlatformLink(
                tmdb_id=tmdb_id,
                media_type=media_type,
                platform=platform,
                platform_url=final_url,
                title=search_keyword,
                season=season,
                episode=episode,
                is_precached=True,
                precache_status="completed",
                expires_at=datetime.utcnow() + timedelta(hours=CACHE_EXPIRY_HOURS),
            )
            db.add(cached)

        db.commit()

        return {
            "platform": platform,
            "platform_url": final_url,
            "title": title,
            "from_cache": False,
            "cache_expired": False,
        }

    # 搜索失败，记录失败状态
    if cached:
        # 有预创建的 pending 记录，更新为 failed
        if cached.precache_status == "pending":
            cached.precache_status = "failed"
            cached.updated_at = datetime.utcnow()
            cached.error_message = "search_video_link failed"
            db.commit()
    else:
        # 没有预创建的记录（当前集不在 pending_episodes 中），创建一条 failed 记录
        failed_record = VideoPlatformLink(
            tmdb_id=tmdb_id,
            media_type=media_type,
            platform=platform,
            platform_url="",
            title=search_keyword,
            season=season,
            episode=episode,
            precache_status="failed",
            is_precached=False,
            error_message="search_video_link failed",
        )
        db.add(failed_record)
        db.commit()

    return None


async def precache_video_links(
    tmdb_id: int,
    platform: str,
    title: str,
    year: int = None,
    current_season: int = None,
    current_episode: int = None,
    seasons_episodes: Dict[int, int] = None  # {season_num: episode_count, ...}
) -> None:
    """
    预缓存视频链接 - 后台异步执行

    直接为每一集调用 search_video_link 获取 platform_url
    search_video_link 内部有多级降级逻辑（HTTP -> 浏览器）

    预缓存完成后会检查数据库，对未成功的集数进行重试，直到全部完成

    注意：此函数会在后台创建自己的 db session，不依赖请求期间的 session
    """
    from database import SessionLocal

    # 创建独立的 db session
    db = SessionLocal()
    try:
        # 如果没有传入 seasons_episodes，使用默认值（每季 12 集）
        if seasons_episodes is None:
            seasons_episodes = {1: 12}

        # 构建待预缓存列表（按优先级排序）
        pending_episodes = _build_precache_priority_list(
            current_season=current_season,
            current_episode=current_episode,
            seasons_episodes=seasons_episodes
        )

        if not pending_episodes:
            return

        print(f"[precache] {platform} {title} 开始预缓存，共 {len(pending_episodes)} 个集数待处理")

        # 预创建所有待处理集数的 pending 记录，避免后续处理失败时漏查
        _ensure_precache_records(db, tmdb_id, platform, title, pending_episodes)

        # 分批预缓存，每批之间有延迟避免请求过快
        for i in range(0, len(pending_episodes), PRECACHE_BATCH_SIZE):
            batch = pending_episodes[i:i + PRECACHE_BATCH_SIZE]

            # 并发处理这一批 - 直接调用 search_video_link
            tasks = [
                _precache_single_episode_v2(
                    db=db,
                    tmdb_id=tmdb_id,
                    platform=platform,
                    title=title,
                    year=year,
                    season=ep["season"],
                    episode=ep["episode"]
                )
                for ep in batch
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # 批次间延迟（动态：基础延迟 + 随机浮动 + 递增）
            if i + PRECACHE_BATCH_SIZE < len(pending_episodes):
                batch_index = i // PRECACHE_BATCH_SIZE
                delay = PRECACHE_BASE_DELAY + random.uniform(0, PRECACHE_DELAY_VARIANCE) + batch_index * 0.1
                await asyncio.sleep(delay)

        # 预缓存完成后，检查是否有未成功的集数并重试
        max_retries = sum(seasons_episodes.values())
        print(f"[precache] {platform} {title} 最大重试次数: {max_retries}")
        for retry_round in range(max_retries):
            # 查找未完成的记录（pending, in_progress, failed）
            incomplete_records = db.query(VideoPlatformLink).filter(
                VideoPlatformLink.tmdb_id == tmdb_id,
                VideoPlatformLink.platform == platform,
                VideoPlatformLink.precache_status.in_(["pending", "in_progress", "failed"])
            ).all()

            if not incomplete_records:
                break  # 所有集数都已完成

            print(f"[precache] {platform} {title} 第 {retry_round + 1} 轮补全：发现 {len(incomplete_records)} 个未完成的集数")

            # 重试这些未完成的集数
            tasks = [
                _precache_single_episode_v2(
                    db=db,
                    tmdb_id=tmdb_id,
                    platform=platform,
                    title=title,
                    year=year,
                    season=record.season,
                    episode=record.episode
                )
                for record in incomplete_records
            ]

            await asyncio.gather(*tasks, return_exceptions=True)

            # 重试间隔
            await asyncio.sleep(2)

        # 最终检查
        final_incomplete = db.query(VideoPlatformLink).filter(
            VideoPlatformLink.tmdb_id == tmdb_id,
            VideoPlatformLink.platform == platform,
            VideoPlatformLink.precache_status.in_(["pending", "in_progress", "failed"])
        ).count()

        if final_incomplete == 0:
            print(f"[precache] {platform} {title} 预缓存完成，所有集数都已成功")
        else:
            print(f"[precache] {platform} {title} 预缓存完成，仍有 {final_incomplete} 个集数未成功（已重试 {max_retries} 轮）")

    except Exception as e:
        print(f"[precache] {platform} {title} 预缓存异常: {e}")
    finally:
        db.close()


async def _precache_single_episode_v2(
    db: Session,
    tmdb_id: int,
    platform: str,
    title: str,
    year: int,
    season: int,
    episode: int
) -> None:
    """
    预缓存单个剧集 - 直接调用 search_video_link
    """
    try:
        # 直接调用 search_video_link（它内部有缓存检查和多级降级逻辑）
        result = await search_video_link(
            db=db,
            tmdb_id=tmdb_id,
            media_type="tv",
            platform=platform,
            title=title,
            year=year,
            season=season,
            episode=episode
        )

        if result:
            print(f"[precache] {platform} S{season}E{episode} 预缓存成功")
        else:
            # search_video_link 返回 None，说明搜索失败（链接不存在或异常）
            # 更新预创建的 pending 记录为 failed
            _mark_precache_failed(db, tmdb_id, platform, season, episode, "未找到播放链接")
            print(f"[precache] {platform} S{season}E{episode} 预缓存失败: 未找到播放链接")

    except Exception as e:
        # 异常情况下，更新预创建的 pending 记录为 failed
        _mark_precache_failed(db, tmdb_id, platform, season, episode, str(e))
        print(f"[precache] {platform} S{season}E{episode} 预缓存失败: {e}")


def _ensure_precache_records(
    db: Session,
    tmdb_id: int,
    platform: str,
    title: str,
    pending_episodes: List[Dict[str, int]]
) -> None:
    """
    预创建所有待处理集数的 pending 记录

    确保每个待预缓存的集数都有对应的数据库记录（状态为 pending），
    避免后续处理失败时数据库无记录，导致最终检查漏掉这些集数。
    如果记录已存在且状态为 completed/in_progress，则不覆盖。
    """
    for ep in pending_episodes:
        season = ep["season"]
        episode = ep["episode"]

        existing = db.query(VideoPlatformLink).filter(
            VideoPlatformLink.tmdb_id == tmdb_id,
            VideoPlatformLink.platform == platform,
            VideoPlatformLink.season == season,
            VideoPlatformLink.episode == episode
        ).first()

        if not existing:
            # 记录不存在，创建 pending 记录
            # platform_url 暂时用空字符串占位，后续成功时会更新
            # title 使用传入的 title 参数
            new_record = VideoPlatformLink(
                tmdb_id=tmdb_id,
                media_type="tv",
                platform=platform,
                platform_url="",
                title=title,
                season=season,
                episode=episode,
                precache_status="pending",
                is_precached=False,
            )
            db.add(new_record)
        elif existing.precache_status == "pending":
            # 记录已存在且为 pending，保持不变
            pass

    db.commit()


def _mark_precache_failed(
    db: Session,
    tmdb_id: int,
    platform: str,
    season: int,
    episode: int,
    reason: str = None
) -> None:
    """
    将预缓存记录标记为失败

    用于预缓存过程中搜索失败或异常时，更新数据库中的记录状态。
    """
    record = db.query(VideoPlatformLink).filter(
        VideoPlatformLink.tmdb_id == tmdb_id,
        VideoPlatformLink.platform == platform,
        VideoPlatformLink.season == season,
        VideoPlatformLink.episode == episode
    ).first()

    if record:
        record.precache_status = "failed"
        record.updated_at = datetime.utcnow()
        if reason:
            record.error_message = reason  # 使用 error_message 字段存储失败原因
        db.commit()


def _build_precache_priority_list(
    current_season: int,
    current_episode: int,
    seasons_episodes: Dict[int, int]  # {season_num: episode_count, ...}
) -> List[Dict[str, int]]:
    """
    构建预缓存优先级列表

    返回格式: [{"season": 1, "episode": 5}, {"season": 1, "episode": 6}, ...]

    优先级策略（从高到低）：
    1. 当前集后面的集数（最多 5 集）- 用户最可能接下来看
    2. 当前集前面的集数（已完成或已看过的）- 需要缓存
    3. 当前季剩余集数
    4. 其他季所有集数
    """
    if not current_season or not current_episode or not seasons_episodes:
        return []

    result = []

    # 获取当前季的总集数
    current_season_total = seasons_episodes.get(current_season, 0)

    # 第一优先：当前集后面的集数（最多 5 集）- 最高优先
    for offset in range(1, 6):
        ep = current_episode + offset
        if ep <= current_season_total:
            result.append({"season": current_season, "episode": ep})
        else:
            break

    # 第二优先：当前集前面的集数（1 到 current_episode-1）
    for ep in range(1, current_episode):
        result.append({"season": current_season, "episode": ep})

    # 第三优先：当前季剩余集数（从 current_episode+6 开始，避免与第一优先重复）
    for ep in range(current_episode + 6, current_season_total + 1):
        if ep > current_episode:  # 避免重复
            result.append({"season": current_season, "episode": ep})

    # 第四优先：其他季所有集数（按季顺序）
    all_seasons = sorted(seasons_episodes.keys())
    for s in all_seasons:
        if s == current_season:
            continue
        season_episode_count = seasons_episodes.get(s, 0)
        for ep in range(1, season_episode_count + 1):
            result.append({"season": s, "episode": ep})

    return result


async def continue_precache(
    db: Session,
    tmdb_id: int,
    platform: str,
    title: str,
    year: int = None,
    current_season: int = None,
    current_episode: int = None,
    seasons_episodes: Dict[int, int] = None  # {season_num: episode_count, ...}
) -> Dict[str, Any]:
    """
    触发预缓存任务
    用于用户进入播放页时，后台预缓存所有剧集的 URL

    注意：此函数只负责触发预缓存任务，立即返回
    实际的预缓存工作在 precache_video_links 后台任务中完成
    precache_video_links 会在内部自己获取 cover_url
    """
    # 如果没有传入 seasons_episodes，使用默认值（每季 12 集）
    if seasons_episodes is None:
        seasons_episodes = {1: 12}

    # 提交当前事务，避免后台任务使用已关闭的 db session
    db.commit()

    # 触发后台预缓存任务（precache_video_links 内部会自己获取 cover_url）
    asyncio.create_task(
        precache_video_links(
            tmdb_id=tmdb_id,
            platform=platform,
            title=title,
            year=year,
            current_season=current_season,
            current_episode=current_episode,
            seasons_episodes=seasons_episodes
        )
    )

    return {"status": "triggered", "message": "预缓存任务已触发"}


def get_all_platforms() -> list:
    """获取所有支持的平台"""
    return list(PLATFORM_CRAWLERS.keys())