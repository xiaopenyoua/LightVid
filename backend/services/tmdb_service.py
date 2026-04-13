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

    async def get_movie_genres(self) -> list[dict]:
        """获取电影类型列表"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/genre/movie/list"
        params = {"api_key": self.api_key, "language": LANGUAGE}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("genres", [])
        except Exception as e:
            print(f"[TMDB] 获取电影类型失败: {e}")
            return []

    async def get_tv_genres(self) -> list[dict]:
        """获取剧集类型列表"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/genre/tv/list"
        params = {"api_key": self.api_key, "language": LANGUAGE}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("genres", [])
        except Exception as e:
            print(f"[TMDB] 获取剧集类型失败: {e}")
            return []

    async def get_popular_movies(self, page: int = 1) -> list[dict]:
        """获取热门电影"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/movie/popular"
        params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取热门电影失败: {e}")
            return []

    async def get_popular_tv(self, page: int = 1) -> list[dict]:
        """获取热门剧集"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/tv/popular"
        params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取热门剧集失败: {e}")
            return []

    async def get_top_rated_movies(self, page: int = 1) -> list[dict]:
        """获取高分电影"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/movie/top_rated"
        params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取高分电影失败: {e}")
            return []

    async def get_top_rated_tv(self, page: int = 1) -> list[dict]:
        """获取高分剧集"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/tv/top_rated"
        params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取高分剧集失败: {e}")
            return []

    async def get_upcoming_movies(self, page: int = 1) -> list[dict]:
        """获取即将上映电影"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/movie/upcoming"
        params = {"api_key": self.api_key, "language": LANGUAGE, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 获取即将上映电影失败: {e}")
            return []

    async def discover_movies(
        self,
        page: int = 1,
        sort_by: str = "popularity.desc",
        year: int = None,
        genre_ids: str = None,
        language: str = None,
        vote_count_gte: int = None,
    ) -> list[dict]:
        """按类型发现电影，支持多种筛选条件"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/discover/movie"
        params = {
            "api_key": self.api_key,
            "language": LANGUAGE,
            "page": page,
            "sort_by": sort_by,
        }
        if genre_ids:
            params["with_genres"] = genre_ids
        if year:
            params["primary_release_year"] = year
        if language:
            params["with_original_language"] = language
        if vote_count_gte:
            params["vote_count.gte"] = vote_count_gte
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 发现电影失败: {e}")
            return []

    async def discover_tv(
        self,
        page: int = 1,
        sort_by: str = "popularity.desc",
        year: int = None,
        genre_ids: str = None,
        language: str = None,
        vote_count_gte: int = None,
    ) -> list[dict]:
        """按类型发现剧集，支持多种筛选条件"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/discover/tv"
        params = {
            "api_key": self.api_key,
            "language": LANGUAGE,
            "page": page,
            "sort_by": sort_by,
        }
        if genre_ids:
            params["with_genres"] = genre_ids
        if year:
            params["first_air_date_year"] = year
        if language:
            params["with_original_language"] = language
        if vote_count_gte:
            params["vote_count.gte"] = vote_count_gte
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 发现剧集失败: {e}")
            return []

    async def search_multi(self, query: str, page: int = 1) -> list[dict]:
        """混合搜索电影和剧集"""
        if not self.api_key:
            print("[TMDB] API key 未配置")
            return []
        url = f"{self.base_url}/search/multi"
        params = {"api_key": self.api_key, "language": LANGUAGE, "query": query, "page": page}
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                return resp.json().get("results", [])
        except Exception as e:
            print(f"[TMDB] 搜索失败: {e}")
            return []

    def format_tmdb_item(self, item: dict, media_type: str = None, season_number: int = None) -> dict:
        """格式化 TMDB 条目为统一结构"""
        # 判断 media_type
        if not media_type:
            media_type = "movie" if item.get("release_date") else "tv"

        # 处理剧集多季
        if media_type == "tv":
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


# 全局单例
tmdb_service = TMDBService()
