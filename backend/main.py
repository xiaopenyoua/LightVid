from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
import asyncio

from database import engine, Base, SessionLocal
from api.sources import router as sources_router
from api.videos import router as videos_router
from api.parse_configs import router as parse_configs_router
from api.play import router as play_router
from api.history import router as history_router
from api.favorites import router as favorites_router
from models import ParseConfig

# 创建所有表
Base.metadata.create_all(bind=engine)

app = FastAPI(title="LightVid API")

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(sources_router)
app.include_router(videos_router)
app.include_router(parse_configs_router)
app.include_router(play_router)
app.include_router(history_router)
app.include_router(favorites_router)

scheduler = AsyncIOScheduler()


async def scheduled_crawl_tvbox():
    """定时爬取 TV Box 源"""
    from crawlers.tvbox_crawler import crawl_tvbox_sources
    db = SessionLocal()
    try:
        count = await crawl_tvbox_sources(db)
        print(f"[Scheduler] TV Box 源爬取完成，新增 {count} 个源")
    except Exception as e:
        print(f"[Scheduler] TV Box 源爬取失败: {e}")
    finally:
        db.close()


def init_default_configs():
    """初始化默认解析接口"""
    from config import DEFAULT_PARSE_CONFIGS
    db = SessionLocal()
    try:
        count = db.query(ParseConfig).count()
        if count == 0:
            for cfg in DEFAULT_PARSE_CONFIGS:
                db.add(ParseConfig(**cfg))
            db.commit()
            print(f"[Startup] 已自动初始化 {len(DEFAULT_PARSE_CONFIGS)} 个解析接口")
        else:
            print(f"[Startup] 解析接口已存在 ({count} 个)，跳过初始化")
    except Exception as e:
        print(f"[Startup] 初始化解析接口失败: {e}")
        db.rollback()
    finally:
        db.close()


@app.on_event("startup")
async def startup_event():
    """启动时初始化"""
    # 初始化默认解析接口
    init_default_configs()

    # 初始化/同步 TMDB 数据
    from database import SessionLocal
    from services.sync_service import SyncService

    db = SessionLocal()
    try:
        sync = SyncService(db)
        # 同步 Genre（阻塞式，确保启动后立即可用）
        count = await sync.sync_genres()
        print(f"[Startup] 已同步 {count} 个 Genre")

        # 异步同步列表（后台进行）
        asyncio.create_task(sync.sync_trending())
        asyncio.create_task(sync.sync_popular())
        asyncio.create_task(sync.sync_top_rated())
        asyncio.create_task(sync.sync_upcoming())
    finally:
        db.close()

    # 启动定时任务 - 每6小时爬取TV Box源
    scheduler.add_job(
        scheduled_crawl_tvbox,
        trigger=IntervalTrigger(hours=6),
        id="crawl_tvbox_sources",
        name="定时爬取 TV Box 源",
        replace_existing=True
    )
    scheduler.start()
    print("[Scheduler] 定时任务已启动 (TV Box 源爬取: 每6小时)")

    # 启动时立即执行一次爬取
    print("[Scheduler] 立即执行首次爬取任务...")
    asyncio.create_task(scheduled_crawl_tvbox())


@app.on_event("shutdown")
async def shutdown_event():
    """关闭时清理"""
    scheduler.shutdown()


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18668)
