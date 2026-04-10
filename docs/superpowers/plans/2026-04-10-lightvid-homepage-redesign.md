# LightVid 主页重构实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.
>
> **Goal:** 基于 TMDB 深度整合，重构主页为混合型布局（轮播+分区），并业务化 API 命名
>
> **Architecture:**
> - 本地 SQLite 仅存 Genre 列表（极小数据）和缓存的热门列表
> - 详情页、搜索、Genre 下内容列表实时调 TMDB
> - 前端完全无感知 TMDB，所有 API 以业务语义命名
>
> **Tech Stack:** Vue3 + Element Plus (前端), FastAPI + SQLAlchemy (后端), SQLite, TMDB API

---

## 一、文件结构变更总览

### 1.1 新增文件（后端）

```
backend/
├── models/
│   ├── tmdb_genre.py          # Genre 类型模型
│   └── tmdb_cached_list.py    # 缓存列表模型
├── schemas/
│   ├── tmdb_genre.py          # Genre Pydantic schemas
│   └── tmdb_cached_list.py    # 缓存列表 Pydantic schemas
├── services/
│   ├── sync_service.py        # TMDB 同步服务（定时任务核心）
│   └── tmdb_service.py        # 扩展 TMDB 服务，新增 discover 等方法
├── api/
│   └── videos.py              # 新业务 API 路由（替换 /douban）
└── schedulers/
    └── sync_scheduler.py      # 定时任务配置
```

### 1.2 修改文件（后端）

- `backend/models/__init__.py` — 导出新模型
- `backend/schemas/__init__.py` — 导出新 schemas
- `backend/main.py` — 注册新路由 `/api/videos`，配置定时任务
- `backend/database.py` — Base.metadata.create_all 包含新表

### 1.3 废弃文件（后端）

- `backend/api/douban.py` — 替换为 `api/videos.py`
- `backend/schemas/douban_video.py` — 可删除
- `backend/models/douban_video.py` — 可删除（若观看历史不依赖它）

### 1.4 修改文件（前端）

```
frontend/src/
├── api/index.js               # 重命名 API 函数，移除 /douban
├── views/Home.vue             # 完全重写：轮播 + 分区横向滚动
├── views/VideoDetail.vue      # 支持 media_type 参数
├── views/Search.vue           # 更新搜索 API 调用
├── components/
│   ├── Carousel.vue           # 新增：轮播组件
│   ├── VideoRow.vue           # 新增：横向滚动分区组件
│   └── PosterWall.vue         # 重写：支持横向滚动模式
└── router/index.js            # 更新路由参数
```

---

## 二、实施阶段

### Phase 1: 后端 - 数据模型层

#### Task 1: 创建 Genre 模型

**Files:**
- Create: `backend/models/tmdb_genre.py`
- Modify: `backend/models/__init__.py`

- [ ] **Step 1: 创建 Genre 模型**

```python
# backend/models/tmdb_genre.py
from sqlalchemy import Column, Integer, String
from database import Base

class TmdbGenre(Base):
    __tablename__ = "tmdb_genres"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, index=True)  # TMDB genre ID
    name = Column(String)
    media_type = Column(String)  # "movie" 或 "tv"
```

- [ ] **Step 2: 更新 models/__init__.py**

```python
from .tmdb_genre import TmdbGenre
from .tmdb_cached_list import TmdbCachedList
# ... existing imports
__all__ = ["Base", "TmdbGenre", "TmdbCachedList", ...]
```

- [ ] **Step 3: Commit**

```bash
git add backend/models/tmdb_genre.py backend/models/__init__.py
git commit -m "feat: add TmdbGenre model for genre list storage"
```

---

#### Task 2: 创建缓存列表模型

**Files:**
- Create: `backend/models/tmdb_cached_list.py`

- [ ] **Step 1: 创建缓存列表模型**

```python
# backend/models/tmdb_cached_list.py
from sqlalchemy import Column, Integer, String, Float, Text, DateTime
from datetime import datetime
from database import Base

class TmdbCachedList(Base):
    __tablename__ = "tmdb_cached_list"

    id = Column(Integer, primary_key=True, index=True)
    list_type = Column(String, index=True)  # trending / popular / top_rated / upcoming
    media_type = Column(String, index=True)  # movie / tv
    tmdb_id = Column(Integer, index=True)
    title = Column(String)
    poster_url = Column(String)
    backdrop_url = Column(String)
    vote_average = Column(Float)
    vote_count = Column(Integer)
    popularity = Column(Float)
    overview = Column(Text)
    release_date = Column(String)  # 电影用 release_date，剧集用 first_air_date
    genre_ids = Column(String)  # 逗号分隔的 genre IDs
    season_number = Column(Integer, nullable=True)  # 剧集季节号，电影为 NULL
    cached_at = Column(DateTime, default=datetime.utcnow)
```

- [ ] **Step 2: 更新 models/__init__.py 导出**

- [ ] **Step 3: Commit**

```bash
git add backend/models/tmdb_cached_list.py backend/models/__init__.py
git commit -m "feat: add TmdbCachedList model for popular lists cache"
```

---

#### Task 3: 创建 Genre Schema

**Files:**
- Create: `backend/schemas/tmdb_genre.py`

- [ ] **Step 1: 创建 Genre Pydantic schemas**

```python
# backend/schemas/tmdb_genre.py
from pydantic import BaseModel

class TmdbGenreResponse(BaseModel):
    id: int
    tmdb_id: int
    name: str
    media_type: str

    class Config:
        from_attributes = True
```

- [ ] **Step 2: Commit**

```bash
git add backend/schemas/tmdb_genre.py backend/schemas/__init__.py
git commit -m "feat: add TmdbGenre schema"
```

---

#### Task 4: 创建缓存列表 Schema

**Files:**
- Create: `backend/schemas/tmdb_cached_list.py`

- [ ] **Step 1: 创建缓存列表 Pydantic schemas**

```python
# backend/schemas/tmdb_cached_list.py
from pydantic import BaseModel
from typing import Optional

class TmdbCachedItemResponse(BaseModel):
    tmdb_id: int
    title: str
    media_type: str
    poster_url: Optional[str]
    backdrop_url: Optional[str]
    vote_average: Optional[float]
    vote_count: Optional[int]
    popularity: Optional[float]
    overview: Optional[str]
    release_date: Optional[str]
    genre_ids: Optional[str]
    season_number: Optional[int]

    class Config:
        from_attributes = True

class TmdbCachedListResponse(BaseModel):
    genres: list[TmdbGenreResponse]
    lists: dict[str, list[TmdbCachedItemResponse]]
```

- [ ] **Step 2: Commit**

```bash
git add backend/schemas/tmdb_cached_list.py backend/schemas/__init__.py
git commit -m "feat: add TmdbCachedList schema"
```

---

### Phase 2: 后端 - TMDB 服务扩展

#### Task 5: 扩展 TMDB Service

**Files:**
- Modify: `backend/services/tmdb_service.py`

- [ ] **Step 1: 扩展 tmdb_service.py，添加以下方法：**

```python
# 新增方法到 TMDBService 类：

async def get_movie_genres(self) -> list[dict]:
    """获取电影类型列表"""
    url = f"{self.base_url}/genre/movie/list"
    params = {"api_key": self.api_key, "language": LANGUAGE}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("genres", [])

async def get_tv_genres(self) -> list[dict]:
    """获取剧集类型列表"""
    url = f"{self.base_url}/genre/tv/list"
    params = {"api_key": self.api_key, "language": LANGUAGE}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("genres", [])

async def get_popular_movies(self, page: int = 1) -> list[dict]:
    """获取热门电影"""
    url = f"{self.base_url}/movie/popular"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def get_popular_tv(self, page: int = 1) -> list[dict]:
    """获取热门剧集"""
    url = f"{self.base_url}/tv/popular"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def get_top_rated_movies(self, page: int = 1) -> list[dict]:
    """获取高分电影"""
    url = f"{self.base_url}/movie/top_rated"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def get_top_rated_tv(self, page: int = 1) -> list[dict]:
    """获取高分剧集"""
    url = f"{self.base_url}/tv/top_rated"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def get_upcoming_movies(self, page: int = 1) -> list[dict]:
    """获取即将上映电影"""
    url = f"{self.base_url}/movie/upcoming"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def discover_movies(self, genre_id: int = None, page: int = 1, sort_by: str = "popularity.desc") -> list[dict]:
    """按类型发现电影"""
    url = f"{self.base_url}/discover/movie"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page, "sort_by": sort_by}
    if genre_id:
        params["with_genres"] = genre_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def discover_tv(self, genre_id: int = None, page: int = 1, sort_by: str = "popularity.desc") -> list[dict]:
    """按类型发现剧集"""
    url = f"{self.base_url}/discover/tv"
    params = {"api_key": self.api_key, "language": LANGUAGE, "page": page, "sort_by": sort_by}
    if genre_id:
        params["with_genres"] = genre_id
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

async def search_multi(self, query: str, page: int = 1) -> list[dict]:
    """混合搜索电影和剧集"""
    url = f"{self.base_url}/search/multi"
    params = {"api_key": self.api_key, "language": LANGUAGE, "query": query, "page": page}
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        return resp.json().get("results", [])

def format_tmdb_item(self, item: dict, media_type: str = None, season_number: int = None) -> dict:
    """格式化 TMDB 条目为统一结构"""
    # 判断 media_type
    if not media_type:
        media_type = "movie" if item.get("release_date") else "tv"

    # 处理剧集多季
    if media_type == "tv":
        # TMDB TV 项可能有 first_air_date 而非 release_date
        air_date = item.get("first_air_date", "")
    else:
        air_date = item.get("release_date", "")

    return {
        "tmdb_id": item.get("id"),
        "title": item.get("title") or item.get("name"),
        "media_type": media_type,
        "poster_url": self.format_poster_url(item.get("poster_path")),
        "backdrop_url": self.format_poster_url(item.get("backdrop_path"), "w780"),
        "vote_average": item.get("vote_average"),
        "vote_count": item.get("vote_count"),
        "popularity": item.get("popularity"),
        "overview": item.get("overview"),
        "release_date": air_date,
        "genre_ids": ",".join(map(str, item.get("genre_ids", []))) if item.get("genre_ids") else None,
        "season_number": season_number,
    }
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/tmdb_service.py
git commit -m "feat: expand tmdb_service with discover, search_multi and helper methods"
```

---

### Phase 3: 后端 - 同步服务

#### Task 6: 创建 TMDB 同步服务

**Files:**
- Create: `backend/services/sync_service.py`

- [ ] **Step 1: 创建同步服务**

```python
# backend/services/sync_service.py
import httpx
from datetime import datetime
from sqlalchemy.orm import Session
from models.tmdb_genre import TmdbGenre
from models.tmdb_cached_list import TmdbCachedList
from config import TMDB_API_KEY, TMDB_BASE_URL

LANGUAGE = "zh-CN"

class SyncService:
    """TMDB 数据同步服务"""

    def __init__(self, db: Session):
        self.db = db
        self.api_key = TMDB_API_KEY
        self.base_url = TMDB_BASE_URL

    async def sync_genres(self):
        """同步电影和剧集类型列表到本地数据库"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            # 获取电影类型
            movie_resp = await client.get(
                f"{self.base_url}/genre/movie/list",
                params={"api_key": self.api_key, "language": LANGUAGE}
            )
            movie_genres = movie_resp.json().get("genres", [])

            # 获取剧集类型
            tv_resp = await client.get(
                f"{self.base_url}/genre/tv/list",
                params={"api_key": self.api_key, "language": LANGUAGE}
            )
            tv_genres = tv_resp.json().get("genres", [])

        # 写入数据库
        self.db.query(TmdbGenre).delete()  # 清空旧数据

        for g in movie_genres:
            self.db.add(TmdbGenre(tmdb_id=g["id"], name=g["name"], media_type="movie"))

        for g in tv_genres:
            self.db.add(TmdbGenre(tmdb_id=g["id"], name=g["name"], media_type="tv"))

        self.db.commit()
        return len(movie_genres) + len(tv_genres)

    def _fetch_with_retry(self, url: str, params: dict, max_retries: int = 3) -> list:
        """带重试的 HTTP GET"""
        import asyncio
        for attempt in range(max_retries):
            try:
                import httpx
                import asyncio
                response = httpx.Client(timeout=15.0).get(url, params=params)
                response.raise_for_status()
                return response.json().get("results", [])
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"[Sync] Failed after {max_retries} attempts: {e}")
                    return []
                import time
                time.sleep(1)

    def sync_list(self, list_type: str, media_type: str, fetch_func, page: int = 1):
        """同步单个列表（trending/popular/top_rated/upcoming）"""
        from services.tmdb_service import tmdb_service

        # 获取数据
        if list_type == "trending":
            results = fetch_func()  # trending 不需要 page 参数
        else:
            results = fetch_func(page=page)

        if not results:
            return 0

        # 删除旧数据
        self.db.query(TmdbCachedList).filter_by(
            list_type=list_type, media_type=media_type
        ).delete()

        # 写入新数据
        now = datetime.utcnow()
        for item in results:
            # 判断 media_type
            if list_type == "trending":
                item_media = "movie" if item.get("media_type") == "movie" or not item.get("first_air_date") else "tv"
            else:
                item_media = media_type

            formatted = tmdb_service.format_tmdb_item(item, item_media)
            self.db.add(TmdbCachedList(
                list_type=list_type,
                media_type=formatted["media_type"],
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(results)

    async def sync_trending(self):
        """同步 Trending"""
        from services.tmdb_service import tmdb_service
        url = f"{self.base_url}/trending/all/week"
        params = {"api_key": self.api_key, "language": LANGUAGE}

        results = self._fetch_with_retry(url, params)
        if not results:
            return 0

        self.db.query(TmdbCachedList).filter_by(list_type="trending").delete()

        now = datetime.utcnow()
        for item in results:
            item_media = "movie" if item.get("media_type") == "movie" or not item.get("first_air_date") else "tv"
            formatted = tmdb_service.format_tmdb_item(item, item_media)
            self.db.add(TmdbCachedList(
                list_type="trending",
                media_type=formatted["media_type"],
                tmdb_id=formatted["tmdb_id"],
                title=formatted["title"],
                poster_url=formatted["poster_url"],
                backdrop_url=formatted["backdrop_url"],
                vote_average=formatted["vote_average"],
                vote_count=formatted["vote_count"],
                popularity=formatted["popularity"],
                overview=formatted["overview"],
                release_date=formatted["release_date"],
                genre_ids=formatted["genre_ids"],
                season_number=formatted["season_number"],
                cached_at=now,
            ))

        self.db.commit()
        return len(results)

    async def sync_popular(self):
        """同步 Popular"""
        from services.tmdb_service import tmdb_service

        # 获取电影
        movie_url = f"{self.base_url}/movie/popular"
        movie_params = {"api_key": self.api_key, "language": LANGUAGE}
        movie_results = self._fetch_with_retry(movie_url, movie_params)

        self.db.query(TmdbCachedList).filter_by(list_type="popular", media_type="movie").delete()
        now = datetime.utcnow()
        for item in movie_results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="popular", media_type="movie", cached_at=now, **formatted
            ))

        # 获取剧集
        tv_url = f"{self.base_url}/tv/popular"
        tv_params = {"api_key": self.api_key, "language": LANGUAGE}
        tv_results = self._fetch_with_retry(tv_url, tv_params)

        self.db.query(TmdbCachedList).filter_by(list_type="popular", media_type="tv").delete()
        for item in tv_results:
            formatted = tmdb_service.format_tmdb_item(item, "tv")
            self.db.add(TmdbCachedList(
                list_type="popular", media_type="tv", cached_at=now, **formatted
            ))

        self.db.commit()
        return len(movie_results) + len(tv_results)

    async def sync_top_rated(self):
        """同步 Top Rated"""
        from services.tmdb_service import tmdb_service

        # 获取高分电影
        movie_url = f"{self.base_url}/movie/top_rated"
        movie_params = {"api_key": self.api_key, "language": LANGUAGE}
        movie_results = self._fetch_with_retry(movie_url, movie_params)

        self.db.query(TmdbCachedList).filter_by(list_type="top_rated", media_type="movie").delete()
        now = datetime.utcnow()
        for item in movie_results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="top_rated", media_type="movie", cached_at=now, **formatted
            ))

        # 获取高分剧集
        tv_url = f"{self.base_url}/tv/top_rated"
        tv_params = {"api_key": self.api_key, "language": LANGUAGE}
        tv_results = self._fetch_with_retry(tv_url, tv_params)

        self.db.query(TmdbCachedList).filter_by(list_type="top_rated", media_type="tv").delete()
        for item in tv_results:
            formatted = tmdb_service.format_tmdb_item(item, "tv")
            self.db.add(TmdbCachedList(
                list_type="top_rated", media_type="tv", cached_at=now, **formatted
            ))

        self.db.commit()
        return len(movie_results) + len(tv_results)

    async def sync_upcoming(self):
        """同步 Upcoming（仅电影）"""
        from services.tmdb_service import tmdb_service

        url = f"{self.base_url}/movie/upcoming"
        params = {"api_key": self.api_key, "language": LANGUAGE}
        results = self._fetch_with_retry(url, params)

        self.db.query(TmdbCachedList).filter_by(list_type="upcoming", media_type="movie").delete()
        now = datetime.utcnow()
        for item in results:
            formatted = tmdb_service.format_tmdb_item(item, "movie")
            self.db.add(TmdbCachedList(
                list_type="upcoming", media_type="movie", cached_at=now, **formatted
            ))

        self.db.commit()
        return len(results)

    def cleanup_old_cache(self, max_age_hours: int = 24):
        """清理超过指定时间的缓存"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=max_age_hours)
        deleted = self.db.query(TmdbCachedList).filter(
            TmdbCachedList.cached_at < cutoff
        ).delete()
        self.db.commit()
        return deleted
```

- [ ] **Step 2: Commit**

```bash
git add backend/services/sync_service.py
git commit -m "feat: add sync_service for TMDB data synchronization"
```

---

### Phase 4: 后端 - API 路由

#### Task 7: 创建 /api/videos 路由

**Files:**
- Create: `backend/api/videos.py`

- [ ] **Step 1: 创建 videos API 路由**

```python
# backend/api/videos.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from database import get_db
from models.tmdb_genre import TmdbGenre
from models.tmdb_cached_list import TmdbCachedList
from schemas.tmdb_genre import TmdbGenreResponse
from schemas.tmdb_cached_list import TmdbCachedItemResponse
from services.tmdb_service import tmdb_service

router = APIRouter(prefix="/api/videos", tags=["videos"])

# ============ 首页全量数据 ============

@router.get("/home")
def get_home(db: Session = Depends(get_db)):
    """
    首页全量数据：
    - 所有类型列表
    - 7个缓存的列表（trending/popular/top_rated/upcoming × movie/tv）
    """
    # 获取所有 Genre
    genres = db.query(TmdbGenre).all()

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
    genre: int = None,
    page: int = Query(default=1, ge=1),
    sort_by: str = "popularity.desc",
    db: Session = Depends(get_db)
):
    """
    获取电影列表（实时调 TMDB discover）
    - genre: 可选，TMDB genre ID
    - sort_by: popularity.desc / vote_average.desc / release_date.desc
    """
    results = await tmdb_service.discover_movies(
        genre_id=genre, page=page, sort_by=sort_by
    )
    return [tmdb_service.format_tmdb_item(r, "movie") for r in results]

@router.get("/tv")
async def get_tv_shows(
    genre: int = None,
    page: int = Query(default=1, ge=1),
    sort_by: str = "popularity.desc",
    db: Session = Depends(get_db)
):
    """
    获取剧集列表（实时调 TMDB discover）
    """
    results = await tmdb_service.discover_tv(
        genre_id=genre, page=page, sort_by=sort_by
    )
    return [tmdb_service.format_tmdb_item(r, "tv") for r in results]

# ============ 详情（实时） ============

@router.get("/{media_type}/{tmdb_id}")
async def get_detail(media_type: str, tmdb_id: int):
    """
    获取电影/剧集详情（实时调 TMDB）
    media_type: "movie" 或 "tv"
    """
    if media_type == "movie":
        details = await tmdb_service.get_movie_details(tmdb_id)
    else:
        details = await tmdb_service.get_tv_details(tmdb_id)

    if not details:
        return {"error": "Not found"}, 404

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
        return {"error": "Only TV shows have seasons"}, 400

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
    except Exception as e:
        return {"error": str(e)}, 500

# ============ 搜索（实时） ============

@router.get("/search")
async def search_videos(
    q: str = Query(..., min_length=1),
    page: int = Query(default=1, ge=1)
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
```

- [ ] **Step 2: Commit**

```bash
git add backend/api/videos.py
git commit -m "feat: add /api/videos routes replacing /api/douban"
```

---

#### Task 8: 更新 main.py 注册新路由

**Files:**
- Modify: `backend/main.py`

- [ ] **Step 1: 替换 douban 路由为 videos 路由**

```python
# backend/main.py 修改：

# 原来：
from api.douban import router as douban_router
# ...
app.include_router(douban_router)

# 改为：
from api.videos import router as videos_router
# ...
app.include_router(videos_router)
```

- [ ] **Step 2: 添加定时任务调度**

```python
# 在 startup_event 中添加：

# 启动时立即同步一次所有数据
from services.sync_service import SyncService

@app.on_event("startup")
async def startup_event():
    init_default_configs()

    # 初始化/同步 TMDB 数据
    from database import SessionLocal
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

    # ... 现有定时任务代码
```

- [ ] **Step 3: Commit**

```bash
git add backend/main.py
git commit -m "feat: update main.py to use videos router and sync TMDB on startup"
```

---

### Phase 5: 后端 - 清理旧代码

#### Task 9: 废弃 /douban API

**Files:**
- Delete: `backend/api/douban.py`
- Delete: `backend/schemas/douban_video.py`
- Delete: `backend/models/douban_video.py`
- Modify: `backend/models/__init__.py`
- Modify: `backend/schemas/__init__.py`

- [ ] **Step 1: 更新 __init__ 文件移除旧导出**

- [ ] **Step 2: Commit**

```bash
git rm backend/api/douban.py backend/schemas/douban_video.py backend/models/douban_video.py
git add backend/models/__init__.py backend/schemas/__init__.py
git commit -m "feat: remove deprecated /douban API and DoubanVideo model"
```

---

### Phase 6: 前端 - API 层重构

#### Task 10: 重构前端 API 调用

**Files:**
- Modify: `frontend/src/api/index.js`

- [ ] **Step 1: 更新 API 函数**

```javascript
// frontend/src/api/index.js

// Videos（替换原来的 /douban）
export const getHome = () => api.get('/videos/home')
export const getGenres = () => api.get('/videos/genres')
export const getMovies = (params) => api.get('/videos/movies', { params })
export const getTvShows = (params) => api.get('/videos/tv', { params })
export const getVideoDetail = (mediaType, tmdbId) => api.get(`/videos/${mediaType}/${tmdbId}`)
export const getSeasonDetail = (tmdbId, season) => api.get(`/videos/tv/${tmdbId}/seasons/${season}`)
export const searchVideos = (q, page) => api.get('/videos/search', { params: { q, page } })

// 移除旧的 Douban API：
// export const getVideos = ...
// export const getVideo = ...
// export const searchVideos = ...
// export const searchTmdb = ...
// export const crawlVideo = ...
// export const getTrending = ...

// 保留其他 API（不变）：
// Sources, Play, Parse Configs, History, Favorites
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/api/index.js
git commit -m "refactor: update frontend API to use /videos endpoints"
```

---

### Phase 7: 前端 - 主页重构

#### Task 11: 创建轮播组件

**Files:**
- Create: `frontend/src/components/Carousel.vue`

- [ ] **Step 1: 创建 Carousel.vue**

```vue
<template>
  <div class="carousel" @mouseenter="stopAutoPlay" @mouseleave="startAutoPlay">
    <div class="carousel-inner" :style="{ transform: `translateX(-${currentIndex * 100}%)` }">
      <div v-for="(item, index) in items" :key="index" class="carousel-item">
        <img :src="item.backdrop_url || item.poster_url" :alt="item.title" />
        <div class="carousel-caption">
          <h2>{{ item.title }}</h2>
          <p>{{ item.overview?.slice(0, 100) }}...</p>
        </div>
      </div>
    </div>
    <div class="carousel-indicators">
      <span
        v-for="(_, index) in items"
        :key="index"
        :class="{ active: index === currentIndex }"
        @click="goTo(index)"
      />
    </div>
    <button class="carousel-prev" @click="prev">&#10094;</button>
    <button class="carousel-next" @click="next">&#10095;</button>
  </div>
</template>

<script setup>
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = defineProps({
  items: {
    type: Array,
    default: () => []
  },
  autoPlay: {
    type: Boolean,
    default: true
  },
  interval: {
    type: Number,
    default: 5000
  }
})

const currentIndex = ref(0)
let timer = null

const goTo = (index) => {
  currentIndex.value = index
}

const next = () => {
  currentIndex.value = (currentIndex.value + 1) % props.items.length
}

const prev = () => {
  currentIndex.value = (currentIndex.value - 1 + props.items.length) % props.items.length
}

const startAutoPlay = () => {
  if (props.autoPlay && props.items.length > 1) {
    timer = setInterval(next, props.interval)
  }
}

const stopAutoPlay = () => {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onMounted(startAutoPlay)
onBeforeUnmount(stopAutoPlay)

watch(() => props.items, () => {
  if (currentIndex.value >= props.items.length) {
    currentIndex.value = 0
  }
  startAutoPlay()
})
</script>

<style scoped>
.carousel {
  position: relative;
  width: 100%;
  height: 400px;
  overflow: hidden;
  border-radius: 8px;
}
.carousel-inner {
  display: flex;
  height: 100%;
  transition: transform 0.5s ease;
}
.carousel-item {
  min-width: 100%;
  height: 100%;
  position: relative;
}
.carousel-item img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.carousel-caption {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 20px;
  background: linear-gradient(transparent, rgba(0,0,0,0.8));
  color: white;
}
.carousel-caption h2 {
  margin: 0 0 8px 0;
}
.carousel-caption p {
  margin: 0;
  font-size: 14px;
  color: #ccc;
}
.carousel-indicators {
  position: absolute;
  bottom: 10px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  gap: 8px;
}
.carousel-indicators span {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: rgba(255,255,255,0.5);
  cursor: pointer;
}
.carousel-indicators span.active {
  background: white;
}
.carousel-prev, .carousel-next {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(0,0,0,0.5);
  color: white;
  border: none;
  padding: 12px 16px;
  cursor: pointer;
  font-size: 18px;
}
.carousel-prev { left: 10px; }
.carousel-next { right: 10px; }
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/Carousel.vue
git commit -m "feat: add Carousel component for homepage banner"
```

---

#### Task 12: 创建横向滚动分区组件

**Files:**
- Create: `frontend/src/components/VideoRow.vue`

- [ ] **Step 1: 创建 VideoRow.vue**

```vue
<template>
  <div class="video-row">
    <h3 class="row-title">{{ title }}</h3>
    <div class="row-content" ref="rowRef" @mousedown="startDrag" @mousemove="onDrag" @mouseup="endDrag" @mouseleave="endDrag">
      <div v-for="item in items" :key="`${item.tmdb_id}-${item.season_number || 0}`" class="video-card" @click="$emit('select', item)">
        <div class="card-poster">
          <img :src="item.poster_url" :alt="item.title" loading="lazy" />
          <span v-if="item.season_number" class="season-badge">第{{ item.season_number }}季</span>
          <span class="rating" v-if="item.vote_average">{{ item.vote_average.toFixed(1) }}</span>
        </div>
        <p class="card-title">{{ item.title }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  title: String,
  items: Array
})

defineEmits(['select'])

const rowRef = ref(null)
const isDragging = ref(false)
const startX = ref(0)
const scrollLeft = ref(0)

const startDrag = (e) => {
  isDragging.value = true
  startX.value = e.pageX - rowRef.value.offsetLeft
  scrollLeft.value = rowRef.value.scrollLeft
  rowRef.value.style.cursor = 'grabbing'
}

const onDrag = (e) => {
  if (!isDragging.value) return
  e.preventDefault()
  const x = e.pageX - rowRef.value.offsetLeft
  const walk = (x - startX.value) * 2
  rowRef.value.scrollLeft = scrollLeft.value - walk
}

const endDrag = () => {
  isDragging.value = false
  if (rowRef.value) rowRef.value.style.cursor = 'grab'
}
</script>

<style scoped>
.video-row {
  margin-bottom: 30px;
}
.row-title {
  padding: 0 20px;
  margin-bottom: 10px;
  font-size: 18px;
  font-weight: 600;
}
.row-content {
  display: flex;
  gap: 16px;
  padding: 10px 20px;
  overflow-x: auto;
  scroll-behavior: smooth;
  cursor: grab;
  -webkit-overflow-scrolling: touch;
}
.row-content::-webkit-scrollbar {
  display: none;
}
.video-card {
  min-width: 180px;
  max-width: 180px;
  cursor: pointer;
}
.card-poster {
  position: relative;
  width: 100%;
  aspect-ratio: 2/3;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}
.card-poster img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s;
}
.video-card:hover .card-poster img {
  transform: scale(1.05);
}
.season-badge {
  position: absolute;
  top: 8px;
  left: 8px;
  background: rgba(0,0,0,0.8);
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
}
.rating {
  position: absolute;
  bottom: 8px;
  right: 8px;
  background: rgba(0,0,0,0.8);
  color: #f5a623;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 12px;
}
.card-title {
  margin: 8px 0 0 0;
  font-size: 14px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/components/VideoRow.vue
git commit -m "feat: add VideoRow component for horizontal scroll sections"
```

---

#### Task 13: 重写 Home.vue

**Files:**
- Modify: `frontend/src/views/Home.vue`

- [ ] **Step 1: 完全重写 Home.vue**

```vue
<template>
  <div class="home">
    <div v-loading="loading" class="content">
      <!-- 顶部轮播 -->
      <div class="carousel-section" v-if="homeData?.lists?.trending_movie?.length">
        <Carousel :items="homeData.lists.trending_movie.slice(0, 10)" @select="handleSelect" />
      </div>

      <!-- 横向滚动分区 -->
      <VideoRow
        v-if="homeData?.lists?.popular_movie?.length"
        title="热门电影"
        :items="homeData.lists.popular_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.popular_tv?.length"
        title="热门剧集"
        :items="homeData.lists.popular_tv"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.trending_movie?.length"
        title="本周热门"
        :items="homeData.lists.trending_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.top_rated_movie?.length"
        title="高分电影"
        :items="homeData.lists.top_rated_movie"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.top_rated_tv?.length"
        title="高分剧集"
        :items="homeData.lists.top_rated_tv"
        @select="handleSelect"
      />

      <VideoRow
        v-if="homeData?.lists?.upcoming_movie?.length"
        title="即将上映"
        :items="homeData.lists.upcoming_movie"
        @select="handleSelect"
      />

      <!-- Genre 分区（按类型） -->
      <template v-if="movieGenres.length">
        <VideoRow
          v-for="genre in movieGenres"
          :key="`movie-${genre.tmdb_id}`"
          :title="`${genre.name}电影`"
          :items="genreMovies[genre.tmdb_id] || []"
          :loading="genreLoading[genre.tmdb_id]"
          @select="handleSelect"
        />
      </template>

      <template v-if="tvGenres.length">
        <VideoRow
          v-for="genre in tvGenres"
          :key="`tv-${genre.tmdb_id}`"
          :title="`${genre.name}剧集`"
          :items="genreTv[genre.tmdb_id] || []"
          :loading="genreLoading[genre.tmdb_id]"
          @select="handleSelect"
        />
      </template>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getHome, getMovies, getTvShows } from '../api'
import Carousel from '../components/Carousel.vue'
import VideoRow from '../components/VideoRow.vue'

const router = useRouter()
const loading = ref(false)
const homeData = ref(null)
const genreMovies = ref({})
const genreTv = ref({})
const genreLoading = ref({})

const movieGenres = computed(() => homeData.value?.genres?.filter(g => g.media_type === 'movie') || [])
const tvGenres = computed(() => homeData.value?.genres?.filter(g => g.media_type === 'tv') || [])

const loadHome = async () => {
  loading.value = true
  try {
    const { data } = await getHome()
    homeData.value = data
  } catch {
    ElMessage.error('加载首页数据失败')
  } finally {
    loading.value = false
  }
}

const loadGenreMovies = async (genreId) => {
  if (genreMovies.value[genreId]) return  // 已加载
  genreLoading.value[genreId] = true
  try {
    const { data } = await getMovies({ genre: genreId, page: 1 })
    genreMovies.value[genreId] = data.slice(0, 20)
  } catch {
    genreMovies.value[genreId] = []
  } finally {
    genreLoading.value[genreId] = false
  }
}

const loadGenreTv = async (genreId) => {
  if (genreTv.value[genreId]) return
  genreLoading.value[genreId] = true
  try {
    const { data } = await getTvShows({ genre: genreId, page: 1 })
    genreTv.value[genreId] = data.slice(0, 20)
  } catch {
    genreTv.value[genreId] = []
  } finally {
    genreLoading.value[genreId] = false
  }
}

const handleSelect = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

onMounted(async () => {
  await loadHome()
  // 预加载前3个 genre 的内容
  movieGenres.value.slice(0, 3).forEach(g => loadGenreMovies(g.tmdb_id))
  tvGenres.value.slice(0, 3).forEach(g => loadGenreTv(g.tmdb_id))
})
</script>

<style scoped>
.home {
  min-height: 100vh;
}
.content {
  padding: 0;
}
.carousel-section {
  padding: 20px 20px 0 20px;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Home.vue
git commit -m "feat: rewrite Home.vue with carousel and VideoRow sections"
```

---

### Phase 8: 前端 - 详情页适配

#### Task 14: 更新 VideoDetail.vue 支持 media_type

**Files:**
- Modify: `frontend/src/views/VideoDetail.vue`

- [ ] **Step 1: 更新 VideoDetail.vue**

```vue
<template>
  <div class="video-detail" v-if="video">
    <div class="backdrop" v-if="video.backdrop_url">
      <img :src="video.backdrop_url" />
    </div>
    <div class="detail-content">
      <div class="poster">
        <img :src="video.poster_url" />
      </div>
      <div class="info">
        <h1>{{ video.title }}</h1>
        <div class="meta">
          <span v-if="video.vote_average">评分: {{ video.vote_average.toFixed(1) }}</span>
          <span v-if="video.release_date">{{ video.release_date.slice(0, 4) }}年</span>
          <span v-if="video.genres">{{ video.genres }}</span>
        </div>
        <p class="tagline" v-if="video.tagline">{{ video.tagline }}</p>
        <p class="overview">{{ video.overview }}</p>

        <!-- 剧集季节选择 -->
        <div v-if="video.seasons?.length" class="seasons">
          <span
            v-for="season in video.seasons"
            :key="season.season_number"
            :class="{ active: currentSeason === season.season_number }"
            @click="selectSeason(season.season_number)"
          >
            {{ season.name }}
          </span>
        </div>

        <div class="actions">
          <el-button type="primary" size="large" @click="goPlay">
            开始播放
          </el-button>
          <el-button size="large" @click="toggleFavorite">
            {{ isFavorite ? '取消收藏' : '收藏' }}
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, addFavorite, removeFavorite, checkFavorite } from '../api'

const route = useRoute()
const router = useRouter()
const video = ref(null)
const isFavorite = ref(false)
const currentSeason = ref(1)

const mediaType = () => route.params.media_type || 'movie'
const tmdbId = () => parseInt(route.params.id)

const loadDetail = async () => {
  try {
    const { data } = await getVideoDetail(mediaType(), tmdbId())
    video.value = data
    if (video.value?.seasons?.length) {
      currentSeason.value = video.value.seasons[0].season_number
    }
    // 检查收藏
    try {
      const { data: fav } = await checkFavorite(tmdbId())
      isFavorite.value = fav.is_favorite
    } catch {}
  } catch {
    ElMessage.error('加载详情失败')
  }
}

const selectSeason = (season) => {
  currentSeason.value = season
  router.replace({
    query: { ...route.query, season }
  })
}

const toggleFavorite = async () => {
  try {
    if (isFavorite.value) {
      await removeFavorite(tmdbId())
      isFavorite.value = false
      ElMessage.success('已取消收藏')
    } else {
      await addFavorite(tmdbId())
      isFavorite.value = true
      ElMessage.success('已添加收藏')
    }
  } catch {
    ElMessage.error('操作失败')
  }
}

const goPlay = () => {
  router.push(`/video/${mediaType()}/${tmdbId()}/play?season=${currentSeason.value}`)
}

watch(() => route.params.id, loadDetail)

onMounted(loadDetail)
</script>

<style scoped>
.video-detail {
  position: relative;
  min-height: 100vh;
  padding: 40px;
}
.backdrop {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: -1;
}
.backdrop img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  filter: blur(30px);
  opacity: 0.3;
}
.detail-content {
  display: flex;
  gap: 40px;
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
}
.poster img {
  width: 300px;
  border-radius: 12px;
}
.info {
  flex: 1;
}
.info h1 {
  margin: 0 0 16px 0;
}
.meta {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
  color: #999;
}
.tagline {
  font-style: italic;
  color: #666;
  margin-bottom: 16px;
}
.overview {
  line-height: 1.6;
  color: #ccc;
  margin-bottom: 20px;
}
.seasons {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}
.seasons span {
  padding: 4px 12px;
  background: rgba(255,255,255,0.1);
  border-radius: 16px;
  cursor: pointer;
}
.seasons span.active {
  background: #409eff;
  color: white;
}
.actions {
  display: flex;
  gap: 12px;
}
</style>
```

- [ ] **Step 2: 更新 router/index.js**

```javascript
// router/index.js 更新路由
{ path: '/video/:media_type/:id', component: () => import('../views/VideoDetail.vue') },
{ path: '/video/:media_type/:id/play', component: () => import('../views/Play.vue') },
```

- [ ] **Step 3: Commit**

```bash
git add frontend/src/views/VideoDetail.vue frontend/src/router/index.js
git commit -m "feat: update VideoDetail to support media_type and season selection"
```

---

### Phase 9: 前端 - 搜索页适配

#### Task 15: 更新 Search.vue

**Files:**
- Modify: `frontend/src/views/Search.vue`

- [ ] **Step 1: 查看并更新 Search.vue（使用新的 searchVideos API）**

```vue
<template>
  <div class="search-page">
    <div class="search-header">
      <h1>搜索</h1>
      <el-input v-model="keyword" placeholder="输入关键词搜索..." style="width: 400px" @keyup.enter="doSearch" />
    </div>
    <div v-loading="loading" class="search-results">
      <div v-if="results.length" class="results-grid">
        <div v-for="item in results" :key="`${item.tmdb_id}-${item.season_number || 0}`" class="result-item" @click="goDetail(item)">
          <img :src="item.poster_url" />
          <div class="result-info">
            <h3>{{ item.title }}</h3>
            <span class="media-type">{{ item.media_type === 'movie' ? '电影' : '剧集' }}</span>
          </div>
        </div>
      </div>
      <el-empty v-else-if="!loading && searched" description="未找到结果" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { searchVideos } from '../api'

const route = useRoute()
const router = useRouter()
const keyword = ref('')
const results = ref([])
const loading = ref(false)
const searched = ref(false)

const doSearch = async () => {
  if (!keyword.value.trim()) return
  loading.value = true
  searched.value = false
  try {
    const { data } = await searchVideos(keyword.value)
    results.value = data
  } catch {
    results.value = []
  } finally {
    loading.value = false
    searched.value = true
  }
}

const goDetail = (item) => {
  router.push(`/video/${item.media_type}/${item.tmdb_id}`)
}

onMounted(() => {
  if (route.query.q) {
    keyword.value = route.query.q
    doSearch()
  }
})
</script>

<style scoped>
.search-page {
  padding: 20px;
}
.search-header {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 30px;
}
.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 20px;
}
.result-item {
  cursor: pointer;
  border-radius: 8px;
  overflow: hidden;
  background: #1a1a1a;
}
.result-item img {
  width: 100%;
  aspect-ratio: 2/3;
  object-fit: cover;
}
.result-info {
  padding: 12px;
}
.result-info h3 {
  margin: 0 0 8px 0;
  font-size: 14px;
}
.media-type {
  font-size: 12px;
  color: #999;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/views/Search.vue
git commit -m "feat: update Search.vue to use new search API"
```

---

## 三、测试验证

完成所有 Task 后，验证步骤：

1. **后端启动测试**
```bash
cd backend && python main.py
# 访问 http://127.0.0.1:18668/api/videos/home 验证返回数据
```

2. **前端启动测试**
```bash
cd frontend && npm run dev
# 访问 http://localhost:18778 验证主页布局
```

3. **功能验证清单**
- [ ] 首页轮播自动切换
- [ ] 各分区横向滚动拖动
- [ ] 点击海报进入详情页
- [ ] 剧集详情页季节切换
- [ ] 搜索功能正常
- [ ] 收藏功能正常
- [ ] 观看历史正常

---

## 四、部署注意事项

1. 首次启动会调用 TMDB 同步 Genre 和列表数据，等待约 10-20 秒
2. 定时任务每 30 分钟刷新 Trending，每小时刷新 Popular
3. 确保 `.env` 中配置了 `TMDB_API_KEY`
