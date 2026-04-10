import httpx
from sqlalchemy.orm import Session
from models.video_source import VideoSource
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

TVBOX_SOURCE_URLS = [
    "https://raw.githubusercontent.com/zbh2535/TVBox/main/lives.json",
    "https://raw.githubusercontent.com/zbh2535/TVBox/main/movies.json",
]

MAX_RETRIES = 3


async def fetch_with_retry(client: httpx.AsyncClient, url: str, retries: int = MAX_RETRIES):
    """带重试的 HTTP GET 请求"""
    for attempt in range(retries):
        try:
            resp = await client.get(url)
            resp.raise_for_status()
            return resp
        except (httpx.ConnectTimeout, httpx.ConnectError) as e:
            if attempt < retries - 1:
                print(f"请求失败，重试 {attempt + 1}/{retries}: {url}")
                continue
            raise
        except httpx.HTTPStatusError as e:
            print(f"HTTP 错误 {e.response.status_code}: {url}")
            raise


async def crawl_tvbox_sources(db: Session):
    discovered = []
    async with httpx.AsyncClient(
        timeout=httpx.Timeout(10.0, connect=30.0)
    ) as client:
        for url in TVBOX_SOURCE_URLS:
            try:
                resp = await fetch_with_retry(client, url)
                data = resp.json()
                channels = data.get("data", [])
                print(f"[TVBox Crawler] 从 {url} 获取到 {len(channels)} 个频道")
                for ch in channels:
                    name = ch.get("name", "未知")
                    url_val = ch.get("url", "")
                    # URL 验证：必须是 http/https 开头
                    if url_val and url_val.startswith(("http://", "https://")):
                        source = VideoSource(
                            name=name,
                            url=url_val,
                            type="m3u8",
                            platform="tvbox",
                            source_type="crawl",
                            status="active"
                        )
                        discovered.append(source)
            except httpx.ConnectTimeout:
                print(f"[TVBox Crawler] 连接超时: {url}")
            except httpx.ConnectError as e:
                print(f"[TVBox Crawler] 连接错误: {url} - {e}")
            except httpx.HTTPStatusError as e:
                print(f"[TVBox Crawler] HTTP 错误 {e.response.status_code}: {url}")
            except Exception as e:
                print(f"[TVBox Crawler] 爬取失败: {url} - {e}")

    # 去重
    existing = {s.url for s in db.query(VideoSource).filter_by(source_type="crawl").all()}
    new_sources = [s for s in discovered if s.url not in existing]
    if new_sources:
        db.add_all(new_sources)
        db.commit()
        print(f"[TVBox Crawler] 新增 {len(new_sources)} 个源（已去重）")
    else:
        print(f"[TVBox Crawler] 没有新增源（可能已存在或爬取失败）")
    return len(new_sources)
