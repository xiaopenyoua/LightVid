"""
TMDB API 服务
用于获取电影/剧集信息，替代不稳定的豆瓣爬虫
"""
import httpx
from typing import Optional
from config import TMDB_API_KEY, TMDB_BASE_URL

# 语言设置
LANGUAGE = "zh-CN"  # 获取中文信息


class TMDBService:
    """TMDB API 服务类"""

    def __init__(self, api_key: str = None, base_url: str = None):
        self.api_key = api_key or TMDB_API_KEY
        self.base_url = base_url or TMDB_BASE_URL

    async def search_movies(self, query: str, page: int = 1) -> list[dict]:
        """
        搜索电影
        返回: [{"id": 123, "title": "...", "poster_path": "...", ...}]
        """
        if not self.api_key:
            print("[TMDB] API key 未配置，请设置 TMDB_API_KEY 环境变量")
            return []

        url = f"{self.base_url}/search/movie"
        params = {
            "api_key": self.api_key,
            "query": query,
            "page": page,
            "language": LANGUAGE,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"[TMDB] 搜索电影失败: {e}")
            return []

    async def search_tv(self, query: str, page: int = 1) -> list[dict]:
        """
        搜索电视剧
        """
        if not self.api_key:
            print("[TMDB] API key 未配置，请设置 TMDB_API_KEY 环境变量")
            return []

        url = f"{self.base_url}/search/tv"
        params = {
            "api_key": self.api_key,
            "query": query,
            "page": page,
            "language": LANGUAGE,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"[TMDB] 搜索电视剧失败: {e}")
            return []

    async def get_movie_details(self, movie_id: int) -> Optional[dict]:
        """
        获取电影详情
        """
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return None

        url = f"{self.base_url}/movie/{movie_id}"
        params = {
            "api_key": self.api_key,
            "language": LANGUAGE,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            print(f"[TMDB] 获取电影详情失败: {e}")
            return None

    async def get_tv_details(self, tv_id: int) -> Optional[dict]:
        """
        获取电视剧详情
        """
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return None

        url = f"{self.base_url}/tv/{tv_id}"
        params = {
            "api_key": self.api_key,
            "language": LANGUAGE,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json()
        except Exception as e:
            print(f"[TMDB] 获取电视剧详情失败: {e}")
            return None

    async def get_trending(self, media_type: str = "all", time_window: str = "week") -> list[dict]:
        """
        获取热门内容
        media_type: "all", "movie", "tv"
        time_window: "day", "week"
        """
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []

        url = f"{self.base_url}/trending/{media_type}/{time_window}"
        params = {
            "api_key": self.api_key,
            "language": LANGUAGE,
        }

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
                return data.get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取热门内容失败: {e}")
            return []

    def format_poster_url(self, poster_path: str, size: str = "w500") -> str:
        """
        格式化海报 URL
        """
        if not poster_path:
            return ""
        return f"https://image.tmdb.org/t/p/{size}{poster_path}"


# 全局单例
tmdb_service = TMDBService()
