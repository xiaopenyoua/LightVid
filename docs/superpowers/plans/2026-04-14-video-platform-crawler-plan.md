# 视频平台爬虫 + 解析播放实现计划

> **For agentic workers:** REQUIRED: Use superpowers:subagent-driven-development (if subagents available) or superpowers:executing-plans to implement this plan. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现后端自动在视频平台搜索影片并获取播放链接，通过解析服务转成 m3u8 供前端播放

**Architecture:** 并行探测架构：HTTP 爬虫优先，Playwright 保底。先到先得。

**Tech Stack:** Playwright, httpx, BeautifulSoup, FastAPI, Vue3, HLS.js

---

## 文件结构

```
backend/
├── models/
│   └── video_platform_link.py     # 新增：视频平台链接缓存模型
├── services/
│   ├── browser_pool.py            # 新增：浏览器池管理
│   ├── video_searcher.py          # 新增：视频搜索调度服务
│   └── video_resolver.py          # 新增：视频解析服务
├── crawlers/
│   ├── base.py                    # 新增：爬虫基类
│   └── platforms/
│       ├── tencent.py             # 新增：腾讯视频爬虫
│       ├── iqiyi.py              # 新增：爱奇艺爬虫
│       ├── youku.py              # 新增：优酷爬虫
│       ├── bilibili.py           # 新增：哔哩哔哩爬虫
│       └── mgtv.py               # 新增：芒果TV爬虫
├── api/
│   └── search.py                  # 新增：搜索 API
├── config.py                      # 修改：添加解析服务列表
└── main.py                        # 修改：注册新路由

frontend/src/
├── views/
│   └── Play.vue                   # 修改：移除手动输入，集成 HLS.js
└── api/
    └── index.js                   # 新增：搜索相关 API 调用
```

---

## Task 1: 数据库模型

**Files:**
- Create: `backend/models/video_platform_link.py`

- [ ] **Step 1: 创建数据库模型**

```python
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime
from database import Base


class VideoPlatformLink(Base):
    """视频平台链接缓存表"""
    __tablename__ = "video_platform_links"

    id = Column(Integer, primary_key=True, index=True)
    tmdb_id = Column(Integer, nullable=False, index=True)
    media_type = Column(String, nullable=False)  # movie / tv
    platform = Column(String, nullable=False, index=True)  # tencent / iqiyi / youku / bilibili / mgtv
    platform_url = Column(String, nullable=False)
    title = Column(String)  # 平台返回的标题，用于匹配
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)  # 缓存过期时间
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from models.video_platform_link import VideoPlatformLink; print('OK')"`
Expected: OK

- [ ] **Step 2: 更新 models/__init__.py**

Add: `from models.video_platform_link import VideoPlatformLink`

- [ ] **Step 3: 提交**

```bash
git add backend/models/video_platform_link.py backend/models/__init__.py
git commit -m "feat: 添加 VideoPlatformLink 模型"
```

---

## Task 2: 爬虫基类

**Files:**
- Create: `backend/crawlers/base.py`

- [ ] **Step 1: 创建爬虫基类**

```python
from abc import ABC, abstractmethod
from typing import Optional, List
import httpx
from bs4 import BeautifulSoup


class BasePlatformCrawler(ABC):
    """视频平台爬虫基类"""

    platform_name: str = ""  # 平台标识
    platform_url: str = ""   # 平台根域名

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        """获取搜索页 URL，子类实现"""
        raise NotImplementedError

    async def search_http(self, keyword: str, year: int = None) -> Optional[str]:
        """
        HTTP 模式搜索（快速优先）
        子类可覆盖实现特定逻辑
        """
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(10.0, connect=15.0),
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
            },
            follow_redirects=True
        ) as client:
            search_url = self.get_search_url(keyword)
            try:
                resp = await client.get(search_url)
                resp.raise_for_status()
                return self.extract_play_url(resp.text, keyword, year)
            except Exception as e:
                print(f"[{self.platform_name}] HTTP 搜索失败: {e}")
                return None

    @abstractmethod
    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        """
        从 HTML 中提取播放页面 URL
        子类必须实现
        """
        pass

    def extract_title(self, html: str) -> Optional[str]:
        """从 HTML 中提取标题（可选实现）"""
        soup = BeautifulSoup(html, "lxml")
        title_tag = soup.select_one("title")
        return title_tag.text.strip() if title_tag else None


class BaseBrowserCrawler(ABC):
    """Playwright 浏览器爬虫基类（可选实现，性能较差时启用）"""

    platform_name: str = ""

    async def search_browser(self, keyword: str, year: int = None) -> Optional[str]:
        """浏览器模式搜索（保底）"""
        # 延迟导入，避免 Playwright 未安装时报错
        from services.browser_pool import get_browser

        async with get_browser() as page:
            search_url = self.get_search_url(keyword)
            try:
                await page.goto(search_url, wait_until="networkidle", timeout=20000)
                # 等待搜索结果加载
                await self.wait_for_results(page)
                return await self.extract_play_url(page, keyword, year)
            except Exception as e:
                print(f"[{self.platform_name}] 浏览器搜索失败: {e}")
                return None

    @abstractmethod
    def get_search_url(self, keyword: str) -> str:
        """获取搜索页 URL"""
        pass

    @abstractmethod
    async def wait_for_results(self, page):
        """等待搜索结果加载"""
        pass

    @abstractmethod
    async def extract_play_url(self, page, keyword: str, year: int = None) -> Optional[str]:
        """从页面提取播放 URL"""
        pass
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from crawlers.base import BasePlatformCrawler; print('OK')"`
Expected: OK

- [ ] **Step 2: 提交**

```bash
git add backend/crawlers/base.py
git commit -m "feat: 添加爬虫基类 BasePlatformCrawler"
```

---

## Task 3: 腾讯视频爬虫

**Files:**
- Create: `backend/crawlers/platforms/tencent.py`

- [ ] **Step 1: 创建腾讯视频爬虫**

```python
from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class TencentCrawler(BasePlatformCrawler):
    """腾讯视频爬虫"""

    platform_name = "tencent"
    platform_url = "https://v.qq.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://v.qq.com/search.html?page={page}&q={quote(keyword)}&filter=sort=0&source=mix&cbk=1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        """
        从腾讯视频搜索页 HTML 中提取播放页面 URL
        搜索结果格式: https://v.qq.com/x/cover/{cover_id}.html
        """
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 方式1: 查找 .result_item 结构
        for item in soup.select(".result_item"):
            title_elem = item.select_one(".title a, .figure_title a")
            if title_elem:
                title = title_elem.get_text(strip=True)
                href = title_elem.get("href", "")

                # 简单匹配：标题包含关键词
                if keyword.lower() in title.lower() or title.lower() in keyword.lower():
                    if "/cover/" in href:
                        return href

        # 方式2: 直接查找包含 /cover/ 的链接
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/cover/" in href and href.startswith("http"):
                return href

        # 方式3: 查找 _main_card 里的链接
        for item in soup.select("a[href*='/cover/']"):
            href = item.get("href", "")
            if href.startswith("http"):
                return href

        return None
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from crawlers.platforms.tencent import TencentCrawler; c = TencentCrawler(); print(c.get_search_url('流浪地球'))"`
Expected: `https://v.qq.com/search.html?page=1&q=%E6%B5%81%E7%A8%8A%E5%9C%B0%E7%90%83&...`

- [ ] **Step 2: 创建 __init__.py**

```python
# 空文件，标记为 Python 包
```

Run: `touch /Volumes/ssd/projects-github/LightVid/backend/crawlers/platforms/__init__.py`

- [ ] **Step 3: 提交**

```bash
git add backend/crawlers/platforms/__init__.py backend/crawlers/platforms/tencent.py
git commit -m "feat: 实现腾讯视频爬虫 TencentCrawler"
```

---

## Task 4: 其他平台爬虫（爱奇艺、优酷、哔哩哔哩、芒果TV）

**Files:**
- Create: `backend/crawlers/platforms/iqiyi.py`
- Create: `backend/crawlers/platforms/youku.py`
- Create: `backend/crawlers/platforms/bilibili.py`
- Create: `backend/crawlers/platforms/mgtv.py`

- [ ] **Step 1: 爱奇艺爬虫**

```python
from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class IqiyiCrawler(BasePlatformCrawler):
    """爱奇艺爬虫"""

    platform_name = "iqiyi"
    platform_url = "https://www.iqiyi.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://so.iqiyi.com/so/q_{quote(keyword)}?source=input&sr=1&page=1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 查找搜索结果中的播放链接
        for item in soup.select(".qy-search-item, .result-item"):
            link = item.select_one("a[href*='/v_']")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    return href

        # 直接查找包含 /v_ 的链接
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/v_" in href and href.startswith("http"):
                return href

        return None
```

- [ ] **Step 2: 优酷爬虫**

```python
from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class YoukuCrawler(BasePlatformCrawler):
    """优酷爬虫"""

    platform_name = "youku"
    platform_url = "https://www.youku.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://so.youku.com/search/q_{quote(keyword)}?spm=a2hjn.20147490.J_5254934080.1"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        for item in soup.select(".yk-packager"):
            link = item.select_one("a[href*='/show/']")
            if link:
                href = link.get("href", "")
                if href.startswith("http"):
                    return href

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/show/" in href and href.startswith("http"):
                return href

        return None
```

- [ ] **Step 3: 哔哩哔哩爬虫**

```python
from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class BilibiliCrawler(BasePlatformCrawler):
    """哔哩哔哩爬虫"""

    platform_name = "bilibili"
    platform_url = "https://www.bilibili.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://search.bilibili.com/all?keyword={quote(keyword)}&order=totalrank&duration=0&t=1&page={page}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        # 查找视频结果
        for item in soup.select(".bili-video-card"):
            link = item.select_one("a[href*='/video/']")
            if link:
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = "https:" + href
                return href

        # 备用方式
        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/video/BV" in href:
                if not href.startswith("http"):
                    href = "https://www.bilibili.com" + href
                return href

        return None
```

- [ ] **Step 4: 芒果TV爬虫**

```python
from typing import Optional
from urllib.parse import quote
from crawlers.base import BasePlatformCrawler


class MgtvCrawler(BasePlatformCrawler):
    """芒果TV爬虫"""

    platform_name = "mgtv"
    platform_url = "https://www.mgtv.com"

    def get_search_url(self, keyword: str, page: int = 1) -> str:
        return f"https://search.mgtv.com/search?q={quote(keyword)}"

    def extract_play_url(self, html: str, keyword: str, year: int = None) -> Optional[str]:
        from bs4 import BeautifulSoup

        soup = BeautifulSoup(html, "lxml")

        for item in soup.select(".result-item, .video-item"):
            link = item.select_one("a[href*='/boke/']")
            if link:
                href = link.get("href", "")
                if not href.startswith("http"):
                    href = "https://www.mgtv.com" + href
                return href

        for a in soup.find_all("a", href=True):
            href = a.get("href", "")
            if "/boke/" in href and href.startswith("http"):
                return href

        return None
```

Run: 验证每个爬虫的 get_search_url 方法

- [ ] **Step 5: 提交**

```bash
git add backend/crawlers/platforms/iqiyi.py backend/crawlers/platforms/youku.py backend/crawlers/platforms/bilibili.py backend/crawlers/platforms/mgtv.py
git commit -m "feat: 实现爱奇艺、优酷、哔哩哔哩、芒果TV爬虫"
```

---

## Task 5: 浏览器池管理

**Files:**
- Create: `backend/services/browser_pool.py`

- [ ] **Step 1: 创建浏览器池管理**

```python
"""
浏览器池管理 - 使用 Playwright 管理浏览器实例复用
"""
import asyncio
from typing import Optional
from contextlib import asynccontextmanager

# 全局浏览器实例
_browser = None
_browser_lock = asyncio.Lock()


async def get_browser():
    """获取全局浏览器实例（线程安全）"""
    global _browser

    if _browser is None or not _browser.is_connected():
        async with _browser_lock:
            if _browser is None or not _browser.is_connected():
                from playwright.async_api import async_playwright
                p = await async_playwright().start()
                _browser = await p.chromium.launch(
                    headless=True,  # 无头模式
                    args=[
                        "--disable-blink-features=AutomationControlled",
                        "--disable-dev-shm-usage",
                        "--no-sandbox",
                    ]
                )
                print("[BrowserPool] 浏览器实例已创建")

    return _browser


async def close_browser():
    """关闭全局浏览器实例"""
    global _browser

    if _browser and _browser.is_connected():
        await _browser.close()
        _browser = None
        print("[BrowserPool] 浏览器实例已关闭")


@asynccontextmanager
async def get_browser_page():
    """获取浏览器页面（上下文管理器）"""
    browser = await get_browser()
    page = await browser.new_page()

    try:
        yield page
    finally:
        await page.close()
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from services.browser_pool import get_browser; print('OK')"`
Expected: OK

- [ ] **Step 2: 提交**

```bash
git add backend/services/browser_pool.py
git commit -m "feat: 添加浏览器池管理服务"
```

---

## Task 6: 视频搜索调度服务

**Files:**
- Create: `backend/services/video_searcher.py`

- [ ] **Step 1: 创建视频搜索调度服务**

```python
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

    # 5. HTTP 失败，尝试 Playwright（可选，这里简化处理）
    # 实际项目中可以在这里添加 Playwright 备选逻辑

    return None


def get_all_platforms() -> list:
    """获取所有支持的平台"""
    return list(PLATFORM_CRAWLERS.keys())
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from services.video_searcher import get_all_platforms; print(get_all_platforms())"`
Expected: `['tencent', 'iqiyi', 'youku', 'bilibili', 'mgtv']`

- [ ] **Step 2: 提交**

```bash
git add backend/services/video_searcher.py
git commit -m "feat: 添加视频搜索调度服务"
```

---

## Task 7: 视频解析服务

**Files:**
- Create: `backend/services/video_resolver.py`

- [ ] **Step 1: 创建视频解析服务**

```python
"""
视频解析服务 - 调用第三方解析服务获取 m3u8 链接
"""
import httpx
import re
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from models.parse_config import ParseConfig


# 默认解析服务列表（备用）
DEFAULT_PARSERS = [
    {"name": "虾米视频解析", "url": "https://jx.xmflv.com/?url="},
    {"name": "七七云解析", "url": "https://jx.77flv.cc/?url="},
    {"name": "Player-JY", "url": "https://jx.playerjy.com/?url="},
    {"name": "789解析", "url": "https://jiexi.789jiexi.icu:4433/?url="},
    {"name": "极速解析", "url": "https://jx.2s0.cn/player/?url="},
]


async def resolve_video_url(
    platform_url: str,
    parser_url: Optional[str] = None,
    parser_name: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    使用解析服务解析视频链接

    Args:
        platform_url: 视频平台播放页面 URL
        parser_url: 解析服务 URL（不含参数）
        parser_name: 解析服务名称

    Returns:
        {"m3u8_url": "...", "parser": "..."} 或 None
    """
    if not parser_url:
        # 使用默认解析服务
        parser = DEFAULT_PARSERS[0]
        parser_url = parser["url"]
        parser_name = parser["name"]

    # 拼接完整 URL
    full_url = parser_url + platform_url

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=15.0),
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            }
        ) as client:
            resp = await client.get(full_url)
            resp.raise_for_status()

            # 尝试从响应中提取 m3u8 URL
            m3u8_url = extract_m3u8_url(resp.text)

            if m3u8_url:
                return {
                    "m3u8_url": m3u8_url,
                    "parser": parser_name or "未知解析服务",
                }

    except Exception as e:
        print(f"[VideoResolver] 解析失败: {e}")

    return None


def extract_m3u8_url(html: str) -> Optional[str]:
    """
    从 HTML 响应中提取 m3u8 URL
    常见模式:
    - 直接包含 .m3u8
    - 在 video/src 属性中
    - 在 JSON 响应中
    """
    # 模式1: 直接匹配 .m3u8 URL
    patterns = [
        r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*',
        r'"m3u8"\s*:\s*"([^"]+)"',
        r"'m3u8'\s*:\s*'([^']+)'",
        r'src\s*=\s*["\']([^"\']+\.m3u8[^"\']*)["\']',
    ]

    for pattern in patterns:
        match = re.search(pattern, html, re.IGNORECASE)
        if match:
            url = match.group(1) if match.lastindex else match.group(0)
            if url.startswith("//"):
                url = "https:" + url
            return url

    return None


async def resolve_with_fallback(
    platform_url: str,
    parsers: Optional[List[Dict[str, str]]] = None
) -> Optional[Dict[str, Any]]:
    """
    使用多个解析服务尝试解析，自动切换
    """
    if parsers is None:
        parsers = DEFAULT_PARSERS

    for parser in parsers:
        result = await resolve_video_url(
            platform_url,
            parser_url=parser["url"],
            parser_name=parser["name"]
        )
        if result:
            return result

    return None


def get_parser_list(db: Session) -> List[Dict[str, Any]]:
    """从数据库获取解析服务列表"""
    configs = db.query(ParseConfig).filter_by(status="active").order_by(ParseConfig.priority.asc()).all()

    if not configs:
        return DEFAULT_PARSERS

    return [
        {"name": cfg.name, "url": cfg.base_url}
        for cfg in configs
    ]
```

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python -c "from services.video_resolver import extract_m3u8_url; print(extract_m3u8_url('https://example.com/video.m3u8'))"`
Expected: `https://example.com/video.m3u8`

- [ ] **Step 2: 提交**

```bash
git add backend/services/video_resolver.py
git commit -m "feat: 添加视频解析服务"
```

---

## Task 8: 搜索 API

**Files:**
- Create: `backend/api/search.py`

- [ ] **Step 1: 创建搜索 API**

```python
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import get_db

from services.video_searcher import search_video_link, get_all_platforms
from services.video_resolver import resolve_with_fallback, get_parser_list

router = APIRouter(prefix="/api/search", tags=["search"])


class VideoLinkRequest(BaseModel):
    """搜索视频链接请求"""
    tmdb_id: int
    media_type: str  # movie / tv
    platform: str  # tencent / iqiyi / youku / bilibili / mgtv
    title: str
    year: int = None


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
    )

    if not result:
        raise HTTPException(status_code=404, detail=f"未找到该影片的播放链接")

    return result


class ResolveRequest(BaseModel):
    """解析视频链接请求"""
    platform_url: str
    parser_id: int = None  # 可选，使用默认解析服务


class ResolveResponse(BaseModel):
    """解析结果响应"""
    m3u8_url: str
    parser: str


@router.post("/resolve", response_model=ResolveResponse)
async def resolve_video(request: ResolveRequest, db: Session = Depends(get_db)):
    """
    解析视频链接为 m3u8

    调用解析服务获取 m3u8 播放地址
    """
    # 获取解析服务列表
    parsers = get_parser_list(db)

    result = await resolve_with_fallback(request.platform_url, parsers)

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
```

- [ ] **Step 2: 注册路由到 main.py**

在 `backend/main.py` 中添加:

```python
from api.search import router as search_router

# 注册路由
app.include_router(search_router)
```

- [ ] **Step 3: 提交**

```bash
git add backend/api/search.py
git commit -m "feat: 添加搜索 API（video-link, resolve, parsers, platforms）"
```

---

## Task 9: 前端 API 调用

**Files:**
- Create: `frontend/src/api/search.js`

- [ ] **Step 1: 创建搜索 API 调用模块**

```javascript
import axios from 'axios'

const api = axios.create({
    baseURL: '/api'
})

/**
 * 获取支持的视频平台列表
 */
export function getPlatforms() {
    return api.get('/search/platforms')
}

/**
 * 获取可用的解析服务列表
 */
export function getParsers() {
    return api.get('/search/parsers')
}

/**
 * 搜索视频播放链接
 */
export function searchVideoLink(params) {
    return api.post('/search/video-link', params)
}

/**
 * 解析视频链接为 m3u8
 */
export function resolveVideo(params) {
    return api.post('/search/resolve', params)
}
```

- [ ] **Step 2: 更新 frontend/src/api/index.js（如果存在）**

Add exports for search functions

- [ ] **Step 3: 提交**

```bash
git add frontend/src/api/search.js
git commit -m "feat: 添加搜索相关 API 调用"
```

---

## Task 10: 前端 Play.vue 改造

**Files:**
- Modify: `frontend/src/views/Play.vue`

- [ ] **Step 1: 添加 HLS.js 依赖**

Run: `cd /Volumes/ssd/projects-github/LightVid/frontend && npm install hls.js`

- [ ] **Step 2: 修改 Play.vue script 部分**

替换现有的 `<script setup>` 部分的核心逻辑:

```javascript
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getVideoDetail, getSeasonDetail } from '../api'
import { getPlatforms, searchVideoLink, resolveVideo } from '../api/search'
import LoadingSpinner from '../components/LoadingSpinner.vue'
import Hls from 'hls.js'

// 视频源列表（平台选择）
const videoSources = [
    { value: 'tencent', label: '腾讯视频' },
    { value: 'iqiyi', label: '爱奇艺' },
    { value: 'youku', label: '优酷' },
    { value: 'bilibili', label: '哔哩哔哩' },
    { value: 'mgtv', label: '芒果TV' }
]

const route = useRoute()
const video = ref(null)
const loading = ref(false)
const currentUrl = ref('')
const selectedSource = ref('tencent')
const videoUrl = ref('')
const currentSeason = ref(1)
const currentEpisode = ref(1)
const platforms = ref(videoSources)  // 可用平台列表
const m3u8Url = ref('')  // 解析后的 m3u8 URL
const hlsInstance = ref(null)  // HLS.js 实例

// ... 其他 ref 和 computed ...

const handlePlay = async () => {
    if (!video.value) {
        ElMessage.warning('请先选择要播放的影片')
        return
    }

    loading.value = true
    try {
        // 1. 搜索视频播放链接
        const searchRes = await searchVideoLink({
            tmdb_id: video.value.tmdb_id || parseInt(route.params.id),
            media_type: mediaType(),
            platform: selectedSource.value,
            title: video.value.title,
            year: video.value.release_date ? parseInt(video.value.release_date.slice(0, 4)) : null
        })

        const platformUrl = searchRes.data.platform_url

        // 2. 解析为 m3u8
        const resolveRes = await resolveVideo({
            platform_url: platformUrl
        })

        const m3u8 = resolveRes.data.m3u8_url

        // 3. 使用 HLS.js 播放
        playM3u8(m3u8)

        ElMessage.success('正在播放...')
    } catch (err) {
        const msg = err.response?.data?.detail || '播放失败'
        ElMessage.error(msg)
    } finally {
        loading.value = false
    }
}

const playM3u8 = (url) => {
    const videoEl = document.querySelector('.player-video')

    // 清理旧实例
    if (hlsInstance.value) {
        hlsInstance.value.destroy()
    }

    if (Hls.isSupported()) {
        const hls = new Hls()
        hls.loadSource(url)
        hls.attachMedia(videoEl)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
            videoEl.play()
        })
        hlsInstance.value = hls
    } else if (videoEl.canPlayType('application/vnd.apple.mpegurl')) {
        // Safari 原生支持 HLS
        videoEl.src = url
        videoEl.play()
    }
}

// 清理
onUnmounted(() => {
    if (hlsInstance.value) {
        hlsInstance.value.destroy()
    }
})
```

- [ ] **Step 3: 修改 Play.vue template 部分**

将 `<iframe>` 替换为 `<video>`:

```html
<div class="player-main">
    <video
        v-if="m3u8Url"
        class="player-video"
        controls
        autoplay
    ></video>
    <iframe
        v-else-if="currentUrl"
        :src="currentUrl"
        class="player-iframe"
        frameborder="0"
        allowfullscreen
    ></iframe>
    <div v-else class="player-placeholder">
        <!-- 保持原有 placeholder -->
    </div>
</div>
```

将"视频链接输入"部分替换为"播放按钮":

```html
<!-- 视频链接输入 -> 播放按钮 -->
<div class="play-action-section">
    <h3 class="section-title">播放</h3>
    <button class="play-btn-large" @click="handlePlay" :disabled="!video || loading">
        {{ loading ? '正在搜索...' : '播放' }}
    </button>
</div>
```

- [ ] **Step 4: 添加样式**

```css
.play-action-section {
    padding: 20px 24px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

.play-btn-large {
    width: 100%;
    padding: 16px;
    background: linear-gradient(135deg, #6366f1, #8b5cf6);
    border: none;
    border-radius: 12px;
    color: #fff;
    font-size: 16px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.play-btn-large:hover:not(:disabled) {
    transform: scale(1.02);
    box-shadow: 0 4px 20px rgba(99, 102, 241, 0.4);
}

.play-btn-large:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.player-video {
    width: 100%;
    height: 100%;
    background: #000;
}
```

- [ ] **Step 5: 提交**

```bash
git add frontend/src/views/Play.vue frontend/package.json frontend/package-lock.json
git commit -m "feat: 改造 Play.vue，支持自动搜索播放"
```

---

## Task 11: 完整流程测试

- [ ] **Step 1: 安装 Playwright**

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && pip install playwright && playwright install chromium`

- [ ] **Step 2: 启动后端测试**

Run: `cd /Volumes/ssd/projects-github/LightVid/backend && python main.py`

- [ ] **Step 3: 测试搜索 API**

```bash
curl -X POST http://127.0.0.1:18668/api/search/video-link \
  -H "Content-Type: application/json" \
  -d '{"tmdb_id": 672, "media_type": "movie", "platform": "tencent", "title": "流浪地球2"}'
```

Expected: 返回 platform_url

- [ ] **Step 4: 测试解析 API**

```bash
curl -X POST http://127.0.0.1:18668/api/search/resolve \
  -H "Content-Type: application/json" \
  -d '{"platform_url": "https://v.qq.com/x/cover/xxx.html"}'
```

Expected: 返回 m3u8_url

- [ ] **Step 5: 提交**

```bash
git add -A
git commit -m "feat: 视频平台爬虫+解析播放功能完成"
```